from __future__ import annotations

import os
from os.path import sep
import sys
import fnmatch
import pytest
from posixpath import sep as posix_sep
from pathlib import Path, PurePath, PurePosixPath, PureWindowsPath, WindowsPath
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


def fnmatch_ex(pattern: str, path: str | os.PathLike[str]) -> bool:
    """A port of FNMatcher from py.path.common which works with PurePath() instances.

    The difference between this algorithm and PurePath.match() is that the
    latter matches "**" glob expressions for each part of the path, while
    this algorithm uses the whole path instead.

    For example:
        "tests/foo/bar/doc/test_foo.py" matches pattern "tests/**/doc/test*.py"
        with this algorithm, but not with PurePath.match().

    This algorithm was ported to keep backward-compatibility with existing
    settings which assume paths match according this logic.

    References:
    * https://bugs.python.org/issue29249
    * https://bugs.python.org/issue34731
    """
    path = PurePath(path)
    iswin32 = sys.platform.startswith("win")

    if iswin32 and sep not in pattern and posix_sep in pattern:
        # Running on Windows, the pattern has no Windows path separators,
        # and the pattern has one or more Posix path separators. Replace
        # the Posix path separators with the Windows path separator.
        pattern = pattern.replace(posix_sep, sep)

    if sep not in pattern:
        name = path.name
    else:
        name = str(path)
        if path.is_absolute() and not os.path.isabs(pattern):
            pattern = f"*{os.sep}{pattern}"
    return fnmatch.fnmatch(name, pattern)


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
    base_path = PurePath(base)
    # Make all dir separators slashes and drop leading current dir
    # for both patterns and (later) for files.

    for pattern in exclude:
        pattern = pattern.replace(os.sep, "/")
        pattern = pattern.removeprefix("./")
        # pattern = pattern.replace(posix_sep, os.sep)
        # pattern = pattern.replace(posix_sep, "\\")
        patterns.append(pattern)
    for filename in files:
        full_file_path: PurePath = base_path / filename
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


def fnmatch_exclude_with_base_fnmatch_ex(
    files: Iterable[str | Path], base: str | os.PathLike, exclude: Iterable[str]
) -> list[str | Path]:
    """Return list of files not matching any exclusion pattern

    :param files: list of file names
    :param base: directory (path) where the files are
    :param exclude: list of fnmatch glob patterns for exclusion
    """
    not_excluded: list[str | Path] = []
    patterns: MutableSequence[str] = []
    base_path = PurePath(base)
    # Make all dir separators slashes and drop leading current dir
    # for both patterns and (later) for files.

    for pattern in exclude:
        pattern = pattern.replace(os.sep, "/")
        pattern = pattern.removeprefix("./")
        pattern = pattern.replace(posix_sep, os.sep)
        # pattern = pattern.replace(posix_sep, "\\")
        patterns.append(pattern)
    for filename in files:
        full_file_path: PurePath = base_path / filename
        # test_filename = full_file_path.replace(os.sep, "/")
        test_filename = full_file_path
        # if full_file_path.startswith("./"):
        #     test_filename = full_file_path[2:]
        matches = False
        for pattern in patterns:
            if fnmatch_ex(pattern, test_filename):
                matches = True
                break
        if not matches:
            not_excluded.append(filename)

    print(f"Ed: fnmatch_exclude_with_base_fnmatch_ex, exclude: {exclude}")
    print(f"Ed: fnmatch_exclude_with_base_fnmatch_ex, patterns: {patterns}")
    print(f"Ed: fnmatch_exclude_with_base_fnmatch_ex, base: {base}")
    print(f"Ed: fnmatch_exclude_with_base_fnmatch_ex, base_path: {base_path}")
    print(f"Ed: fnmatch_exclude_with_base_fnmatch_ex, files: {files}")
    print(f"Ed: fnmatch_exclude_with_base_fnmatch_ex, not_excluded: {not_excluded}")
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
    base_path = PurePath(base)
    # Make all dir separators slashes and drop leading current dir
    # for both patterns and (later) for files.
    for pattern in exclude:
        pattern = pattern.replace(os.sep, "/")
        if pattern.startswith("./"):
            patterns.append(pattern[2:])
        else:
            patterns.append(pattern)
    for filename in files:
        full_file_path: PurePath = base_path / filename
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


# pytestmark = pytest.mark.parametrize(
#     "filter_fn",
#     [
#         fnmatch_exclude_with_base,
#         fnmatch_exclude_with_base_fnmatch,
#         fnmatch_exclude_with_base_old,
#         # fnmatch_exclude_with_base_globmatch,
#     ],
# )


@pytest.fixture(
    params=[
        # fnmatch_exclude_with_base,
        # fnmatch_exclude_with_base_fnmatch,
        # fnmatch_exclude_with_base_old,
        # # fnmatch_exclude_with_base_globmatch,
        fnmatch_exclude_with_base_fnmatch_ex,
    ],
)
def filter_fn(request):
    return request.param


@pytest.fixture(
    params=[
        "./gui/wxpython/core/testsuite",
        ".\\gui\\wxpython\\core\\testsuite",
        # WindowsPath(".\\gui\\wxpython\\core\\testsuite"),
        PureWindowsPath(".\\gui\\wxpython\\core\\testsuite"),
        "gui\\wxpython\\core\\testsuite",
        PurePosixPath("./gui/wxpython/core/testsuite"),
    ],
)
def base(request):
    return request.param


base_paths2 = [
    "./gui/wxpython/core/testsuite",
    ".\\gui\\wxpython\\core\\testsuite",
    # WindowsPath(".\\gui\\wxpython\\core\\testsuite"),
    PureWindowsPath(".\\gui\\wxpython\\core\\testsuite"),
    "gui\\wxpython\\core\\testsuite",
]


# @pytest.mark.parametrize(
#     "filter_fn", [fnmatch_exclude_with_base, fnmatch_exclude_with_base_old]
# )
# @pytest.mark.parametrize("base", base_paths)
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


# @pytest.mark.parametrize("base", base_paths)
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


# @pytest.mark.parametrize("base", base_paths)
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


# @pytest.mark.parametrize("base", base_paths)
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


# @pytest.mark.parametrize("base", base_paths)
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
class TestFNMatcherPort:
    """Test our port of py.common.FNMatcher (fnmatch_ex)."""

    if sys.platform == "win32":
        drv1 = "c:"
        drv2 = "d:"
    else:
        drv1 = "/c"
        drv2 = "/d"

    @pytest.mark.parametrize(
        "pattern, path",
        [
            ("*.py", "foo.py"),
            ("*.py", "bar/foo.py"),
            ("test_*.py", "foo/test_foo.py"),
            ("tests/*.py", "tests/foo.py"),
            (f"{drv1}/*.py", f"{drv1}/foo.py"),
            (f"{drv1}/foo/*.py", f"{drv1}/foo/foo.py"),
            ("tests/**/test*.py", "tests/foo/test_foo.py"),
            ("tests/**/doc/test*.py", "tests/foo/bar/doc/test_foo.py"),
            ("tests/**/doc/**/test*.py", "tests/foo/doc/bar/test_foo.py"),
        ],
    )
    def test_matching(self, pattern: str, path: str) -> None:
        assert fnmatch_ex(pattern, path)

    def test_matching_abspath(self) -> None:
        abspath = os.path.abspath(os.path.join("tests/foo.py"))
        assert fnmatch_ex("tests/foo.py", abspath)

    @pytest.mark.parametrize(
        "pattern, path",
        [
            ("*.py", "foo.pyc"),
            ("*.py", "foo/foo.pyc"),
            ("tests/*.py", "foo/foo.py"),
            (f"{drv1}/*.py", f"{drv2}/foo.py"),
            (f"{drv1}/foo/*.py", f"{drv2}/foo/foo.py"),
            ("tests/**/test*.py", "tests/foo.py"),
            ("tests/**/test*.py", "foo/test_foo.py"),
            ("tests/**/doc/test*.py", "tests/foo/bar/doc/foo.py"),
            ("tests/**/doc/test*.py", "tests/foo/bar/test_foo.py"),
        ],
    )
    def test_not_matching(self, pattern: str, path: str) -> None:
        assert not fnmatch_ex(pattern, path)
