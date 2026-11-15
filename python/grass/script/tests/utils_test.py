"""Test functions in grass.script.utils"""

import multiprocessing
import operator
import os
import re
import sys

import pytest

import grass.script as gs
from grass.script import utils as gutils


def test_named_separators():
    """Check that named separators are recognized and correctly evaluated"""
    assert gs.separator("pipe") == "|"
    assert gs.separator("comma") == ","
    assert gs.separator("space") == " "
    assert gs.separator("tab") == "\t"
    assert gs.separator("newline") == "\n"


def test_backslash_separators():
    """Check that separators specified as an escape sequence are correctly evaluated"""
    assert gs.separator(r"\t") == "\t"
    assert gs.separator(r"\n") == "\n"


def test_unrecognized_separator():
    """Check that unknown strings are just passed through"""
    assert gs.separator("apple") == "apple"


@pytest.mark.parametrize(
    ("dms", "expected"),
    [
        ("26:45:30", 26.758333333333333),
        ("+26:45:30", 26.758333333333333),
        ("-26:45:30", -26.758333333333333),
        ("26:45:30N", 26.758333333333333),
        ("26:45:30E", 26.758333333333333),
        ("26:45:30S", -26.758333333333333),
        ("26:45:30W", -26.758333333333333),
        ("-0:30:0", -0.5),
        ("12.5", 12.5),
        ("-12.5", -12.5),
    ],
)
def test_float_or_dms(dms, expected):
    """Check that sign and hemisphere letters are applied to the whole value"""
    assert gs.float_or_dms(dms) == pytest.approx(expected)


def test_float_or_dms_empty():
    """Check that an empty string is reported as an invalid value"""
    with pytest.raises(ValueError, match="could not convert"):
        gs.float_or_dms("")


def test_KeyValue_keys():
    """Check that KeyValue class works like a Dict"""
    kv = gs.KeyValue()
    kv["key1"] = "value1"
    kv["key2"] = "value2"

    assert kv["key1"] == "value1"
    assert kv["key2"] == "value2"

    # Raises KeyError for non-existing keys
    with pytest.raises(KeyError):
        _ = kv["non_existing_key"]


def test_KeyValue_values():
    """Check that keys of KeyValue class can be accessed as attributes"""
    kv = gs.KeyValue()
    kv["key1"] = "value1"
    kv["key2"] = "value2"

    assert kv.key1 == "value1"
    assert kv.key2 == "value2"

    # Raises AttributeError for non-existing attribute
    with pytest.raises(AttributeError):
        _ = kv.non_existing_attribute


def test_resolve_nprocs(monkeypatch):
    """Check G_OPT_M_NPROCS resolution: positive as-is, 0 = all, negative reserves."""
    monkeypatch.setattr(gutils, "available_cpus", lambda: 8)
    assert gs.resolve_nprocs(1) == 1
    assert gs.resolve_nprocs(4) == 4
    assert gs.resolve_nprocs("3") == 3
    assert gs.resolve_nprocs(0) == 8
    assert gs.resolve_nprocs(-2) == 6
    assert gs.resolve_nprocs(-10) == 1
    with pytest.raises(ValueError, match="invalid literal for int"):
        gs.resolve_nprocs("not-a-number")


def test_get_multiprocessing_context():
    """Fork is used where available and safe, the platform default elsewhere."""
    ctx = gutils._get_multiprocessing_context()
    if sys.platform != "darwin" and "fork" in multiprocessing.get_all_start_methods():
        assert ctx.get_start_method() == "fork"
    else:
        assert ctx.get_start_method() == multiprocessing.get_start_method()


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("elevation", "elevation"),
        ("with space-and.dot", "with_space_and_dot"),
        ("1st", "x1st"),
        ("_hidden", "x_hidden"),
        # Only ASCII letters are legal, so accented letters are replaced.
        ("na\u00efve", "na_ve"),
        # SQL keywords get a suffix to be usable as column names.
        ("and", "and_"),
        ("or", "or_"),
        ("not", "not_"),
    ],
)
def test_legalize_vector_name(name, expected):
    """Check that invalid characters, leading digits and keywords are fixed"""
    assert gutils.legalize_vector_name(name) == expected


def test_legalize_vector_name_fallback_prefix():
    """Check that the prefix is configurable and can be empty"""
    assert gutils.legalize_vector_name("1st", fallback_prefix="map") == "map1st"
    # An empty prefix is for names used as a suffix of an already valid name.
    assert gutils.legalize_vector_name("1st", fallback_prefix="") == "1st"


def test_legalize_vector_name_invalid_arguments():
    """Check that an empty name and a prefix not starting with a letter fail"""
    with pytest.raises(ValueError, match="cannot be empty"):
        gutils.legalize_vector_name("")
    with pytest.raises(ValueError, match="must start with an ASCII letter"):
        gutils.legalize_vector_name("1st", fallback_prefix="1")


def test_append_random_suffix_length():
    """Check that the suffix has the requested length and legal characters"""
    result = gutils.append_random("tmp", suffix_length=8)
    assert re.fullmatch(r"tmp_[a-z0-9]{8}", result)


def test_append_random_total_length():
    """Check that the total length includes the name and the underscore"""
    result = gutils.append_random("tmp", total_length=16)
    assert len(result) == 16
    assert re.fullmatch(r"tmp_[a-z0-9]{12}", result)


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({}, "has to be provided"),
        ({"suffix_length": 4, "total_length": 16}, "not both"),
        # No room for the underscore plus at least one random character.
        ({"total_length": 4}, "No characters left"),
    ],
)
def test_append_random_invalid_arguments(kwargs, message):
    """Check that inconsistent length arguments are rejected"""
    with pytest.raises(ValueError, match=message):
        gutils.append_random("tmp", **kwargs)


def test_append_uuid():
    """Check that a full UUID4 hex string is appended and differs between calls"""
    first = gutils.append_uuid("tmp")
    assert re.fullmatch(r"tmp_[0-9a-f]{32}", first)
    assert first != gutils.append_uuid("tmp")


def test_append_node_pid():
    """Check that the name is followed by a legal node name and the process ID"""
    result = gutils.append_node_pid("tmp")
    assert re.fullmatch(rf"tmp_[A-Za-z0-9_]+_{os.getpid()}", result)
    assert gutils.legalize_vector_name(result) == result


def test_append_node_pid_legalizes_node_name(monkeypatch):
    """Check that characters of the host name which are not legal are replaced"""
    monkeypatch.setattr(gutils.platform, "node", lambda: "my-host.example.org")
    assert gutils.append_node_pid("tmp") == f"tmp_my_host_example_org_{os.getpid()}"


@pytest.mark.parametrize(
    ("path", "ext", "expected"),
    [
        ("/data/map.txt", None, "map.txt"),
        ("/data/map.txt", "txt", "map"),
        # The extension is compared ignoring the case of the path.
        ("/data/map.TXT", "txt", "map"),
        # Other extensions are kept, and only the last extension is removed.
        ("/data/map.txt", "csv", "map.txt"),
        ("/data/map.tar.gz", "gz", "map.tar"),
        ("/data/noext", "txt", "noext"),
    ],
)
def test_basename(path, ext, expected):
    """Check that directories and a matching extension are removed"""
    assert gutils.basename(path, ext) == expected


def test_try_remove(tmp_path):
    """Check that a file is removed and that failures are silent"""
    path = tmp_path / "file.txt"
    path.write_text("content")
    gutils.try_remove(path)
    assert not path.exists()
    # Already removed, no exception expected.
    gutils.try_remove(path)
    # A directory cannot be removed by os.remove(), no exception expected.
    gutils.try_remove(tmp_path)
    assert tmp_path.is_dir()


def test_try_rmdir(tmp_path):
    """Check that empty and non-empty directories are removed silently"""
    empty = tmp_path / "empty"
    empty.mkdir()
    gutils.try_rmdir(empty)
    assert not empty.exists()

    full = tmp_path / "full"
    (full / "nested").mkdir(parents=True)
    (full / "nested" / "file.txt").write_text("content")
    gutils.try_rmdir(full)
    assert not full.exists()

    # Missing directory, no exception expected.
    gutils.try_rmdir(full)


def test_diff_files(tmp_path):
    """Check that the differ output marks changed and unchanged lines"""
    first = tmp_path / "first.txt"
    second = tmp_path / "second.txt"
    first.write_text("same\nold\n")
    second.write_text("same\nnew\n")
    assert gutils.diff_files(first, second) == [
        "  same\n",
        "- old\n",
        "+ new\n",
    ]
    assert gutils.diff_files(first, first) == ["  same\n", "  old\n"]


def test_split_keeps_quoted_values_together():
    """Check that a quoted value with spaces is a single list item"""
    assert gutils.split('d.vect map=roads where="cat < 10"') == [
        "d.vect",
        "map=roads",
        "where=cat < 10",
    ]


def test_naturally_sorted():
    """Check that numbers are compared by value and letters ignoring case"""
    items = ["map10", "map2", "Map1", "map1a"]
    assert gutils.naturally_sorted(items) == ["Map1", "map1a", "map2", "map10"]
    # The input is left untouched, unlike with naturally_sort().
    assert items == ["map10", "map2", "Map1", "map1a"]
    gutils.naturally_sort(items)
    assert items == ["Map1", "map1a", "map2", "map10"]


def test_naturally_sorted_key():
    """Check that the key function selects the text used for sorting"""
    items = [("b", "file10"), ("a", "file9")]
    assert gutils.naturally_sorted(items, key=operator.itemgetter(1)) == [
        ("a", "file9"),
        ("b", "file10"),
    ]


@pytest.mark.parametrize(
    ("number", "max_number", "expected"),
    [(10, 1000, "0010"), (10, 10, "10"), (0, 9, "0"), (7, 100, "007")],
)
def test_get_num_suffix(number, max_number, expected):
    """Check that the padding depends on the digits of the maximum number"""
    assert gutils.get_num_suffix(number, max_number) == expected


def test_parse_key_val_bytes_and_separators():
    """Check parsing of bytes input and custom separators"""
    assert gutils.parse_key_val(b"min=20\nmax=50") == {"min": "20", "max": "50"}
    assert gutils.parse_key_val("min:20|max:50", sep=":", vsep="|") == {
        "min": "20",
        "max": "50",
    }


def test_parse_key_val_missing_value_uses_default():
    """Check that keys without a separator get the default value"""
    assert gutils.parse_key_val("a=1\nb", dflt="none") == {"a": "1", "b": "none"}
    assert gutils.parse_key_val("a=1\nb", val_type=int, dflt=0) == {"a": 1, "b": 0}
    assert gutils.parse_key_val("a=1\nb") == {"a": "1", "b": None}


def test_parse_key_val_splits_on_first_separator_only():
    """Check that a value may contain the separator itself"""
    assert gutils.parse_key_val("expr=a=b") == {"expr": "a=b"}
    assert gutils.parse_key_val("expr=a=b", val_type=str.upper) == {"expr": "A=B"}


def test_parse_key_val_empty_input():
    """Check that empty input results in an empty dictionary"""
    assert gutils.parse_key_val("") == {}
    assert gutils.parse_key_val(b"") == {}


def test_get_lib_path_from_grass_etc(monkeypatch, tmp_path):
    """Check that the module directory in GRASS_ETCDIR is preferred"""
    (tmp_path / "etc" / "mymod").mkdir(parents=True)
    (tmp_path / "addon" / "etc" / "mymod").mkdir(parents=True)
    monkeypatch.setenv("GRASS_ETCDIR", str(tmp_path / "etc"))
    monkeypatch.setenv("GRASS_ADDON_BASE", str(tmp_path / "addon"))
    assert gutils.get_lib_path("mymod") == str(tmp_path / "etc" / "mymod")


def test_get_lib_path_from_addon_base(monkeypatch, tmp_path):
    """Check the addon locations used when the module is not in GRASS_ETCDIR"""
    (tmp_path / "etc").mkdir()
    monkeypatch.setenv("GRASS_ETCDIR", str(tmp_path / "etc"))
    monkeypatch.setenv("GRASS_ADDON_BASE", str(tmp_path / "addon"))

    (tmp_path / "addon" / "etc" / "mymod").mkdir(parents=True)
    assert gutils.get_lib_path("mymod") == str(tmp_path / "addon" / "etc" / "mymod")

    # Without the etc directory, the module directory inside the addon is used.
    (tmp_path / "addon" / "etc" / "mymod").rmdir()
    (tmp_path / "addon" / "mymod" / "mymod").mkdir(parents=True)
    assert gutils.get_lib_path("mymod") == str(tmp_path / "addon" / "mymod" / "mymod")


def test_get_lib_path_not_found(monkeypatch, tmp_path):
    """Check that None is returned when no location and no build directory match"""
    monkeypatch.setenv("GRASS_ETCDIR", str(tmp_path))
    monkeypatch.delenv("GRASS_ADDON_BASE", raising=False)
    monkeypatch.chdir(tmp_path)
    assert gutils.get_lib_path("module_which_does_not_exist") is None


def test_set_path_local_directory(monkeypatch, tmp_path):
    """Check that an existing local directory makes its parent importable"""
    (tmp_path / "libmymod").mkdir()
    monkeypatch.setattr(sys, "path", list(sys.path))
    gutils.set_path("mymod", "libmymod", str(tmp_path))
    assert sys.path[-1] == str(tmp_path)


def test_set_path_not_found(monkeypatch, tmp_path):
    """Check that a library found neither locally nor in GRASS fails to import"""
    monkeypatch.setenv("GRASS_ETCDIR", str(tmp_path))
    monkeypatch.delenv("GRASS_ADDON_BASE", raising=False)
    monkeypatch.chdir(tmp_path)
    with pytest.raises(ImportError, match="Not able to find"):
        gutils.set_path("module_which_does_not_exist", "lib")
