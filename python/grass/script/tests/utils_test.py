"""Test functions in grass.script.utils"""

from __future__ import annotations

import multiprocessing
import os
import sys
from typing import TYPE_CHECKING

import pytest

import grass.script as gs
from grass.script import utils as gutils

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path


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


def test_resolve_nprocs_from_gisenv(empty_session):
    """None takes NPROCS from g.gisenv, or is 0 when NPROCS is not set

    As with the nprocs option of tools, a value given explicitly, 0
    included, is used instead of NPROCS.
    """
    env = empty_session.env
    assert gs.resolve_nprocs(None, env=env) == gs.resolve_nprocs(0)
    gs.run_command("g.gisenv", set="NPROCS=3", env=env)
    assert gs.resolve_nprocs(None, env=env) == 3
    assert gs.resolve_nprocs(2, env=env) == 2
    assert gs.resolve_nprocs(0, env=env) == gs.resolve_nprocs(0)
    for nprocs in (-1, 0):
        gs.run_command("g.gisenv", set=f"NPROCS={nprocs}", env=env)
        assert gs.resolve_nprocs(None, env=env) == gs.resolve_nprocs(nprocs)


def write_environ_value(path: Path) -> None:
    """Write a variable from the environment to a file (worker process target)"""
    path.write_text(os.environ["GRASS_TEST_ENVIRON_PROCESS"])


# Fork is unsafe on macOS, which is why spawn is the default there.
START_METHODS = [
    method
    for method in multiprocessing.get_all_start_methods()
    if not (method == "fork" and sys.platform == "darwin")
]


@pytest.fixture(params=START_METHODS)
def start_method(request: pytest.FixtureRequest) -> Iterator[str]:
    """Set each available multiprocessing start method as the default"""
    original = multiprocessing.get_start_method(allow_none=True)
    multiprocessing.set_start_method(request.param, force=True)
    yield request.param
    multiprocessing.set_start_method(original, force=True)


def test_environ_process_sees_current_environment(
    start_method: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Worker gets the current environment with any start method

    With forkserver, a worker would otherwise get the environment from the time
    the fork server was started, so start it with a different value first.
    """
    for value in ("first", "second"):
        monkeypatch.setenv("GRASS_TEST_ENVIRON_PROCESS", value)
        path = tmp_path / value
        process = gutils._environ_process(write_environ_value, (path,))
        process.start()
        process.join()
        assert process.exitcode == 0
        assert path.read_text() == value


@pytest.mark.parametrize("method", START_METHODS)
def test_environ_process_uses_given_context(
    method: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Worker is started with the given context, not the default one"""
    monkeypatch.setenv("GRASS_TEST_ENVIRON_PROCESS", "value")
    ctx = multiprocessing.get_context(method)
    path = tmp_path / "result"
    process = gutils._environ_process(write_environ_value, (path,), ctx)
    # The type stubs miss Process in BaseContext.
    assert isinstance(process, ctx.Process)  # type: ignore[attr-defined]  # ty: ignore[missing-attribute]
    process.start()
    process.join()
    assert process.exitcode == 0
    assert path.read_text() == "value"


@pytest.mark.parametrize(
    "name", ["and", "AND", "aNd", "or", "OR", "Or", "not", "NOT", "nOt"]
)
def test_legalize_vector_name_keywords(name):
    """Escape SQL keywords regardless of case, preserving the original case."""
    assert gs.legalize_vector_name(name) == f"{name}_"


@pytest.mark.parametrize(
    "name", ["my_map", "My_Map", "AND_", "border", "NOTable", "sand"]
)
def test_legalize_vector_name_valid(name):
    """Preserve valid names, including names containing SQL keywords."""
    assert gs.legalize_vector_name(name) == name
