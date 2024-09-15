"""
GRASS Python testing framework test loading functionality

Copyright (C) 2014 by the GRASS Development Team
This program is free software under the GNU General Public
License (>=v2). Read the file COPYING that comes with GRASS GIS
for details.

:authors: Vaclav Petras
"""

from __future__ import annotations

import os
from os.path import sep
import sys
import fnmatch
import unittest
import collections
import re
from pathlib import Path, PurePath
from posixpath import sep as posix_sep
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable, MutableSequence


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


def fnmatch_exclude_with_base_fnmatch_ex3(
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
    iswin32 = sys.platform.startswith("win")
    # Make all dir separators slashes and drop leading current dir
    # for both patterns and (later) for files.

    for pattern in exclude:
        if iswin32 and sep not in pattern and posix_sep in pattern:
            # Running on Windows, the pattern has no Windows path separators,
            # and the pattern has one or more Posix path separators. Replace
            # the Posix path separators with the Windows path separator.
            pattern = pattern.replace(posix_sep, sep)
            print("ED: IN IFWIN32 pattern.replace(posix_sep, sep)")
        pattern = pattern.removeprefix(f".{sep}")
        patterns.append(pattern)
    for filename in files:
        full_file_path: PurePath = base_path / filename
        # test_filename = full_file_path.replace(os.sep, "/")
        test_filename = full_file_path
        matches = False
        for pattern in patterns:
            if sep not in pattern:
                name = test_filename.name
                print('ED: IN "if sep not in pattern:"')
            else:
                name = str(test_filename)
                print('ED: IN ELSE of "if sep not in pattern:"')
                if test_filename.is_absolute() and not os.path.isabs(pattern):
                    pattern = f"*{os.sep}{pattern}"

            if fnmatch.fnmatch(name, pattern):
                matches = True
                break
        if not matches:
            not_excluded.append(filename)
    # print(f"Ed: fnmatch_exclude_with_base_fnmatch_ex, exclude: {exclude}")
    print(f"Ed: fnmatch_exclude_with_base_fnmatch_ex3, patterns: {patterns}")
    print(f"Ed: fnmatch_exclude_with_base_fnmatch_ex3, base: {base}")
    print(f"Ed: fnmatch_exclude_with_base_fnmatch_ex3, base_path: {base_path}")
    print(f"Ed: fnmatch_exclude_with_base_fnmatch_ex3, files: {files}")
    print(f"Ed: fnmatch_exclude_with_base_fnmatch_ex3, not_excluded: {not_excluded}")
    return not_excluded


def fnmatch_exclude_with_base_fnmatch_ex2(
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
    iswin32 = sys.platform.startswith("win")
    # Make all dir separators slashes and drop leading current dir
    # for both patterns and (later) for files.

    for pattern in exclude:
        pattern = pattern.replace(os.sep, "/")
        pattern = pattern.removeprefix("./")
        if iswin32 and sep not in pattern and posix_sep in pattern:
            # Running on Windows, the pattern has no Windows path separators,
            # and the pattern has one or more Posix path separators. Replace
            # the Posix path separators with the Windows path separator.
            pattern = pattern.replace(posix_sep, sep)
            print("ED: IN IFWIN32 pattern.replace(posix_sep, sep)")

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
            if sep not in pattern:
                name = test_filename.name
                print('ED: IN "if sep not in pattern:"')
            else:
                name = str(test_filename)
                print('ED: IN ELSE of "if sep not in pattern:"')
                if test_filename.is_absolute() and not os.path.isabs(pattern):
                    pattern = f"*{os.sep}{pattern}"
                    print(
                        'ED: IN "test_filename.is_absolute() and not os.path.isabs(pattern):"'
                    )

            if fnmatch.fnmatch(name, pattern):
                matches = True
                break
        if not matches:
            not_excluded.append(filename)

    # print(f"Ed: fnmatch_exclude_with_base_fnmatch_ex, exclude: {exclude}")
    print(f"Ed: fnmatch_exclude_with_base_fnmatch_ex2, patterns: {patterns}")
    print(f"Ed: fnmatch_exclude_with_base_fnmatch_ex2, base: {base}")
    print(f"Ed: fnmatch_exclude_with_base_fnmatch_ex2, base_path: {base_path}")
    print(f"Ed: fnmatch_exclude_with_base_fnmatch_ex2, files: {files}")
    print(f"Ed: fnmatch_exclude_with_base_fnmatch_ex2, not_excluded: {not_excluded}")
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
            if fnmatch_ex(pattern, test_filename):
                matches = True
                break
        if not matches:
            not_excluded.append(filename)

    # print(f"Ed: fnmatch_exclude_with_base_fnmatch_ex, exclude: {exclude}")
    print(f"Ed: fnmatch_exclude_with_base_fnmatch_ex, patterns: {patterns}")
    print(f"Ed: fnmatch_exclude_with_base_fnmatch_ex, base: {base}")
    print(f"Ed: fnmatch_exclude_with_base_fnmatch_ex, base_path: {base_path}")
    print(f"Ed: fnmatch_exclude_with_base_fnmatch_ex, files: {files}")
    print(f"Ed: fnmatch_exclude_with_base_fnmatch_ex, not_excluded: {not_excluded}")
    return not_excluded


def fnmatch_exclude_with_base_old1(
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


def fnmatch_exclude_with_base_pathlib(files, base, exclude):
    """Return list of files not matching any exclusion pattern

    :param files: list of file names
    :param base: directory (path) where the files are
    :param exclude: list of fnmatch glob patterns for exclusion
    """
    not_excluded = []
    patterns = []
    base_path = Path(base)
    # Make all dir separators slashes and drop leading current dir
    # for both patterns and (later) for files.
    for pattern in exclude:
        patterns.append(Path(pattern))
    for filename in files:
        test_filename: Path = base_path / filename
        matches = False
        for pattern in patterns:
            if fnmatch.fnmatch(str(test_filename), pattern):
                matches = True
                break
        if not matches:
            not_excluded.append(filename)
    # print(f"Ed: fnmatch_exclude_with_base_pathlib, exclude: {exclude}")
    print(f"Ed: fnmatch_exclude_with_base_pathlib, patterns: {patterns}")
    print(f"Ed: fnmatch_exclude_with_base_pathlib, base: {base}")
    print(f"Ed: fnmatch_exclude_with_base_pathlib, base_path: {base_path}")
    print(f"Ed: fnmatch_exclude_with_base_pathlib, files: {files}")
    print(f"Ed: fnmatch_exclude_with_base_pathlib, not_excluded: {not_excluded}")
    return not_excluded


def fnmatch_exclude_with_base(
    files: Iterable[str | Path], base: str | os.PathLike, exclude: Iterable[str]
) -> list[str | Path]:
    return fnmatch_exclude_with_base_pathlib(files, base, exclude)


# TODO: resolve test file versus test module
GrassTestPythonModule = collections.namedtuple(
    "GrassTestPythonModule",
    [
        "name",
        "module",
        "file_type",
        "tested_dir",
        "file_dir",
        "file_path",
        "abs_file_path",
    ],
)


# TODO: implement loading without the import
def discover_modules(
    start_dir,
    skip_dirs,
    testsuite_dir,
    grass_location,
    all_locations_value,
    universal_location_value,
    import_modules,
    add_failed_imports=True,
    file_pattern=None,
    file_regexp=None,
    exclude=None,
):
    """Find all test files (modules) in a directory tree.

    The function is designed specifically for GRASS testing framework
    test layout. It expects some directories to have a "testsuite"
    directory where test files (test modules) are present.
    Additionally, it also handles loading of test files which specify
    in which location they can run.

    :param start_dir: directory to start the search
    :param file_pattern: pattern of files in a test suite directory
        (using Unix shell-style wildcards)
    :param skip_dirs: directories not to recurse to (e.g. ``.svn``)
    :param testsuite_dir: name of directory where the test files are found,
        the function will not recurse to this directory
    :param grass_location: string with an accepted location type (category, shortcut)
    :param all_locations_value: string used to say that all locations
        should be loaded (grass_location can be set to this value)
    :param universal_location_value: string marking a test as
        location-independent (same as not providing any)
    :param import_modules: True if files should be imported as modules,
        False if the files should be just searched for the needed values

    :returns: a list of GrassTestPythonModule objects

    .. todo::
        Implement import_modules.
    """
    modules = []
    for root, dirs, unused_files in os.walk(start_dir, topdown=True):
        dirs.sort()
        for dir_pattern in skip_dirs:
            to_skip = fnmatch.filter(dirs, dir_pattern)
            for skip in to_skip:
                dirs.remove(skip)

        if testsuite_dir in dirs:
            dirs.remove(testsuite_dir)  # do not recurse to testsuite
            full = os.path.join(root, testsuite_dir)

            all_files = os.listdir(full)
            files = [f for f in all_files]
            if file_pattern:
                files = fnmatch.filter(files, file_pattern)
            if file_regexp:
                files = [f for f in files if re.match(file_regexp, f)]
            if exclude:
                files = fnmatch_exclude_with_base(files, full, exclude)
            files = sorted(files)
            # get test/module name without .py
            # extpecting all files to end with .py
            # this will not work for invoking bat files but it works fine
            # as long as we handle only Python files (and using Python
            # interpreter for invoking)

            # TODO: warning about no tests in a testsuite
            # (in what way?)
            for file_name in files:
                # TODO: add also import if requested
                # (see older versions of this file)
                # TODO: check if there is some main in .py
                # otherwise we can have successful test just because
                # everything was loaded into Python
                # TODO: check if there is set -e or exit !0 or ?
                # otherwise we can have successful because nothing was reported
                abspath = os.path.abspath(full)
                abs_file_path = os.path.join(abspath, file_name)
                if file_name.endswith(".py"):
                    if file_name == "__init__.py":
                        # we always ignore __init__.py
                        continue
                    file_type = "py"
                    name = file_name[:-3]
                elif file_name.endswith(".sh"):
                    file_type = "sh"
                    name = file_name[:-3]
                else:
                    file_type = None  # alternative would be '', now equivalent
                    name = file_name

                add = False
                try:
                    if grass_location == all_locations_value:
                        add = True
                    else:
                        try:
                            locations = ["nc", "stdmaps", "all"]
                        except AttributeError:
                            add = True  # test is universal
                        else:
                            if universal_location_value in locations:
                                add = True  # cases when it is explicit
                            if grass_location in locations:
                                add = True  # standard case with given location
                            if not locations:
                                add = True  # count not specified as universal
                except ImportError as e:
                    if add_failed_imports:
                        add = True
                    else:
                        raise ImportError(
                            "Cannot import module named"
                            " %s in %s (%s)" % (name, full, e.message)
                        )
                        # alternative is to create TestClass which will raise
                        # see unittest.loader
                if add:
                    modules.append(
                        GrassTestPythonModule(
                            name=name,
                            module=None,
                            tested_dir=root,
                            file_dir=full,
                            abs_file_path=abs_file_path,
                            file_path=os.path.join(full, file_name),
                            file_type=file_type,
                        )
                    )
                # in else with some verbose we could tell about skipped test
    return modules


# TODO: find out if this is useful for us in some way
# we are now using only discover_modules directly
class GrassTestLoader(unittest.TestLoader):
    """Class handles GRASS-specific loading of test modules."""

    skip_dirs = [".git", ".svn", "dist.*", "bin.*", "OBJ.*"]
    testsuite_dir = "testsuite"
    files_in_testsuite = "*.py"
    all_tests_value = "all"
    universal_tests_value = "universal"

    def __init__(self, grass_location):
        super().__init__()
        self.grass_location = grass_location

    # TODO: what is the purpose of top_level_dir, can it be useful?
    # probably yes, we need to know grass src or dist root
    # TODO: not using pattern here
    def discover(self, start_dir, pattern="test*.py", top_level_dir=None):
        """Load test modules from in GRASS testing framework way."""
        modules = discover_modules(
            start_dir=start_dir,
            file_pattern=self.files_in_testsuite,
            skip_dirs=self.skip_dirs,
            testsuite_dir=self.testsuite_dir,
            grass_location=self.grass_location,
            all_locations_value=self.all_tests_value,
            universal_location_value=self.universal_tests_value,
            import_modules=True,
        )
        tests = []
        for module in modules:
            tests.append(self.loadTestsFromModule(module.module))
        return self.suiteClass(tests)


if __name__ == "__main__":
    GrassTestLoader().discover()
