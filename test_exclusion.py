from __future__ import annotations

import os
import fnmatch
import pytest
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable, MutableSequence


from pathlib import PurePath, PurePosixPath

# Private imports for patching
from pathlib import (
    _make_selector,
    # _PreciseSelector,
    _RecursiveWildcardSelector,
    _TerminatingSelector,
    _WildcardSelector,
)


def _PreciseSelector_globmatch(self, parts, idx):
    if parts[idx] != self.name:
        return False
    return self.successor.globmatch(parts, idx + 1)


def _RecursiveWildcardSelector_globmatch(self, parts, idx):
    successor_globmatch = self.successor.globmatch
    for starting_point in range(idx, len(parts)):
        if successor_globmatch(parts, starting_point):
            return True

    return False


def _TerminatingSelector_globmatch(self, parts, idx):
    return True


def _WildcardSelector_globmatch(self, parts, idx):
    plen = len(parts)
    if idx < plen and (not self.dironly or idx != plen - 1):
        if self.pat.match(parts[idx]):
            return self.successor.globmatch(parts, idx + 1)

    return False


# _PreciseSelector.globmatch = _PreciseSelector_globmatch
_RecursiveWildcardSelector.globmatch = _RecursiveWildcardSelector_globmatch
_TerminatingSelector.globmatch = _TerminatingSelector_globmatch
_WildcardSelector.globmatch = _WildcardSelector_globmatch


def _globmatch(self, pattern):
    """Determine if this path matches the given glob pattern."""
    if not pattern:
        raise ValueError("Unacceptable pattern: {0!r}".format(pattern))
    pattern = self._flavour.casefold(pattern)
    drv, root, pattern_parts = self._flavour.parse_parts((pattern,))
    if drv or root:
        raise NotImplementedError("Non-relative patterns are unsupported")
    selector = _make_selector(tuple(pattern_parts))
    return selector.globmatch(self._cparts, 0)


PurePath.globmatch = _globmatch


def fnmatch_exclude_with_base_old(
    files: Iterable[str | Path], base: str | os.PathLike, exclude: Iterable[str]
) -> list[str | Path]:
    """Return list of files not matching any exclusion pattern

    :param files: list of file names
    :param base: directory (path) where the files are
    :param exclude: list of fnmatch glob patterns for exclusion
    """
    not_excluded: list[str | Path] = []
    patterns: MutableSequence[str] = []
    # base_path = Path(base)
    # Make all dir separators slashes and drop leading current dir
    # for both patterns and (later) for files.
    for pattern in exclude:
        pattern = pattern.replace(os.sep, "/")
        if pattern.startswith("./"):
            patterns.append(pattern[2:])
        else:
            patterns.append(pattern)
    for filename in files:
        # full_file_path: Path = base_path / filename
        full_file_path = os.path.join(base, filename)
        test_filename = full_file_path.replace(os.sep, "/")
        # test_filename = full_file_path
        if full_file_path.startswith("./"):
            test_filename = full_file_path[2:]
        matches = False
        for pattern in patterns:
            if fnmatch.fnmatch(test_filename, pattern):
                matches = True
                break
            # if test_filename.match(pattern):
            #     matches = True
            #     break
        if not matches:
            not_excluded.append(filename)

    # print(f"Ed: fnmatch_exclude_with_base, exclude: {exclude}")
    # print(f"Ed: fnmatch_exclude_with_base, patterns: {patterns}")
    # print(f"Ed: fnmatch_exclude_with_base, base: {base}")
    # print(f"Ed: fnmatch_exclude_with_base, base_path: {base_path}")
    # print(f"Ed: fnmatch_exclude_with_base, files: {files}")
    # print(f"Ed: fnmatch_exclude_with_base, not_excluded: {not_excluded}")
    return not_excluded


def fnmatch_exclude_with_base(
    files: Iterable[str | Path], base: str | os.PathLike, exclude: Iterable[str]
) -> list[str | Path]:
    """Return list of files not matching any exclusion pattern

    :param files: list of file names
    :param base: directory (path) where the files are
    :param exclude: list of fnmatch glob patterns for exclusion
    """
    not_excluded: list[str | Path] = []
    patterns: MutableSequence[str] = []
    base_path = Path(base)
    # Make all dir separators slashes and drop leading current dir
    # for both patterns and (later) for files.
    for pattern in exclude:
        pattern = pattern.replace(os.sep, "/")
        if pattern.startswith("./"):
            patterns.append(pattern[2:])
        else:
            patterns.append(pattern)
    for filename in files:
        full_file_path: Path = base_path / filename
        # test_filename = full_file_path.replace(os.sep, "/")
        test_filename = full_file_path
        # if full_file_path.startswith("./"):
        #     test_filename = full_file_path[2:]
        matches = False
        for pattern in patterns:
            # if fnmatch.fnmatch(test_filename, pattern):
            #     matches = True
            #     break
            if test_filename.match(pattern):
                matches = True
                break
        if not matches:
            not_excluded.append(filename)

    print(f"Ed: fnmatch_exclude_with_base, exclude: {exclude}")
    print(f"Ed: fnmatch_exclude_with_base, patterns: {patterns}")
    print(f"Ed: fnmatch_exclude_with_base, base: {base}")
    print(f"Ed: fnmatch_exclude_with_base, base_path: {base_path}")
    print(f"Ed: fnmatch_exclude_with_base, files: {files}")
    print(f"Ed: fnmatch_exclude_with_base, not_excluded: {not_excluded}")
    return not_excluded


def fnmatch_exclude_with_base_globmatch(
    files: Iterable[str | Path], base: str | os.PathLike, exclude: Iterable[str]
) -> list[str | Path]:
    """Return list of files not matching any exclusion pattern

    :param files: list of file names
    :param base: directory (path) where the files are
    :param exclude: list of fnmatch glob patterns for exclusion
    """
    not_excluded: list[str | Path] = []
    patterns: MutableSequence[str] = []
    base_path = Path(base)
    # Make all dir separators slashes and drop leading current dir
    # for both patterns and (later) for files.
    for pattern in exclude:
        pattern = pattern.replace(os.sep, "/")
        if pattern.startswith("./"):
            patterns.append(pattern[2:])
        else:
            patterns.append(pattern)
    for filename in files:
        full_file_path: Path = base_path / filename
        # test_filename = full_file_path.replace(os.sep, "/")
        test_filename = full_file_path
        # if full_file_path.startswith("./"):
        #     test_filename = full_file_path[2:]
        matches = False
        for pattern in patterns:
            # if fnmatch.fnmatch(test_filename, pattern):
            #     matches = True
            #     break
            if test_filename.globmatch(pattern):
                matches = True
                break
        if not matches:
            not_excluded.append(filename)

    print(f"Ed: fnmatch_exclude_with_base_globmatch, exclude: {exclude}")
    print(f"Ed: fnmatch_exclude_with_base_globmatch, patterns: {patterns}")
    print(f"Ed: fnmatch_exclude_with_base_globmatch, base: {base}")
    print(f"Ed: fnmatch_exclude_with_base_globmatch, base_path: {base_path}")
    print(f"Ed: fnmatch_exclude_with_base_globmatch, files: {files}")
    print(f"Ed: fnmatch_exclude_with_base_globmatch, not_excluded: {not_excluded}")
    return not_excluded


def fnmatch_exclude_with_base_fnmatch(
    files: Iterable[str | Path], base: str | os.PathLike, exclude: Iterable[str]
) -> list[str | Path]:
    """Return list of files not matching any exclusion pattern

    :param files: list of file names
    :param base: directory (path) where the files are
    :param exclude: list of fnmatch glob patterns for exclusion
    """
    not_excluded: list[str | Path] = []
    patterns: MutableSequence[str] = []
    base_path = Path(base)
    # Make all dir separators slashes and drop leading current dir
    # for both patterns and (later) for files.
    for pattern in exclude:
        pattern = pattern.replace(os.sep, "/")
        if pattern.startswith("./"):
            patterns.append(pattern[2:])
        else:
            patterns.append(pattern)
    for filename in files:
        full_file_path: Path = base_path / filename
        # test_filename = full_file_path.replace(os.sep, "/")
        test_filename = full_file_path
        # if full_file_path.startswith("./"):
        #     test_filename = full_file_path[2:]
        matches = False
        for pattern in patterns:
            if fnmatch.fnmatch(test_filename, pattern):
                matches = True
                break
            # if test_filename.match(pattern):
            #     matches = True
            #     break
        if not matches:
            not_excluded.append(filename)

    print(f"Ed: fnmatch_exclude_with_base, exclude: {exclude}")
    print(f"Ed: fnmatch_exclude_with_base, patterns: {patterns}")
    print(f"Ed: fnmatch_exclude_with_base, base: {base}")
    print(f"Ed: fnmatch_exclude_with_base, base_path: {base_path}")
    print(f"Ed: fnmatch_exclude_with_base, files: {files}")
    print(f"Ed: fnmatch_exclude_with_base, not_excluded: {not_excluded}")
    return not_excluded


pytestmark = pytest.mark.parametrize(
    "filter_fn",
    [
        fnmatch_exclude_with_base,
        fnmatch_exclude_with_base_fnmatch,
        fnmatch_exclude_with_base_old,
        # fnmatch_exclude_with_base_globmatch,
    ],
)


# @pytest.mark.parametrize(
#     "filter_fn", [fnmatch_exclude_with_base, fnmatch_exclude_with_base_old]
# )
@pytest.mark.parametrize(
    "base",
    [
        "./gui/wxpython/core/testsuite",
        ".\\gui\\wxpython\\core\\testsuite",
        "gui\\wxpython\\core\\testsuite",
    ],
)
def test_all_excluded(filter_fn, base):
    files = ["toolboxes.sh", "test_gcmd.py"]
    # base = "./gui/wxpython/core/testsuite"
    exclude = [
        "gui/wxpython/core/testsuite/test_gcmd.py",
        "gui/wxpython/core/testsuite/toolboxes.sh",
        "lib/init/testsuite/test_grass_tmp_mapset.py",
    ]
    not_excluded = filter_fn(files, base, exclude)
    assert not_excluded == []


def test_not_excluded(filter_fn):
    files = ["toolboxes.sh", "test_gcmd.py"]
    base = "./temporal/t.rast.import/testsuite"
    exclude = [
        "gui/wxpython/core/testsuite/test_gcmd.py",
        "gui/wxpython/core/testsuite/toolboxes.sh",
        "lib/init/testsuite/test_grass_tmp_mapset.py",
    ]
    not_excluded = filter_fn(files, base, exclude)
    assert not_excluded == ["toolboxes.sh", "test_gcmd.py"]


@pytest.mark.parametrize(
    "base",
    [
        "./gui/wxpython/core/testsuite",
        ".\\gui\\wxpython\\core\\testsuite",
        "gui\\wxpython\\core\\testsuite",
    ],
)
def test_exclude_parent_folder_not_matching(filter_fn, base):
    files = ["toolboxes.sh", "test_gcmd.py"]
    # base = "./gui/wxpython/core/testsuite"
    exclude = [
        "temporal/*",
        "lib/init/testsuite/test_grass_tmp_mapset.py",
    ]
    # not_excluded = fnmatch_exclude_with_base(files, base, exclude)
    not_excluded = filter_fn(files, base, exclude)
    assert not_excluded == ["toolboxes.sh", "test_gcmd.py"]


@pytest.mark.parametrize(
    "base",
    [
        "./gui/wxpython/core/testsuite",
        ".\\gui\\wxpython\\core\\testsuite",
        "gui\\wxpython\\core\\testsuite",
    ],
)
def test_exclude_parent_folder_matching_simple(filter_fn, base):
    files = ["toolboxes.sh", "test_gcmd.py"]
    # base = "./gui/wxpython/core/testsuite"
    exclude = [
        "gui/*",
        "lib/init/testsuite/test_grass_tmp_mapset.py",
    ]
    not_excluded = filter_fn(files, base, exclude)
    # not_excluded = fnmatch_exclude_with_base(files, base, exclude)
    assert not_excluded == []


@pytest.mark.parametrize(
    "base",
    [
        "./gui/wxpython/core/testsuite",
        ".\\gui\\wxpython\\core\\testsuite",
        "gui\\wxpython\\core\\testsuite",
    ],
)
def test_exclude_parent_folder_matching_recursive(filter_fn, base):
    files = ["toolboxes.sh", "test_gcmd.py"]
    # base = "./gui/wxpython/core/testsuite"
    exclude = [
        "gui/**",
        "lib/init/testsuite/test_grass_tmp_mapset.py",
    ]
    not_excluded = filter_fn(files, base, exclude)
    # not_excluded = fnmatch_exclude_with_base(files, base, exclude)
    assert not_excluded == []


# def test_exclude_parent_folder_matching_recursive_windows(filter_fn):
#     files = ["toolboxes.sh", "test_gcmd.py"]
#     base = ".\\gui\\wxpython\\core\\testsuite"
#     exclude = [
#         "gui/**",
#         "lib/init/testsuite/test_grass_tmp_mapset.py",
#     ]
#     not_excluded = filter_fn(files, base, exclude)
#     # not_excluded = fnmatch_exclude_with_base(files, base, exclude)
#     assert not_excluded == []


@pytest.mark.parametrize(
    "base",
    [
        "./gui/wxpython/core/testsuite",
        ".\\gui\\wxpython\\core\\testsuite",
        "gui\\wxpython\\core\\testsuite",
    ],
)
def test_exclude_parent_folder_not_matching_recursive(filter_fn, base):
    files = ["toolboxes.sh", "test_gcmd.py"]
    # base = "./gui/wxpython/core/testsuite"
    exclude = [
        "temporal/**",
        "lib/init/testsuite/test_grass_tmp_mapset.py",
    ]
    not_excluded = filter_fn(files, base, exclude)
    # not_excluded = fnmatch_exclude_with_base(files, base, exclude)
    assert not_excluded == ["toolboxes.sh", "test_gcmd.py"]


# def test_glob(filter_fn):
#     assert 1 == 1
