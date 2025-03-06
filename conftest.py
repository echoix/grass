# SPDX-License-Identifier: GPL-2.0-or-later AND MIT
"""General pytest test fixtures for the complete repo

Author: Edouard Choinière (2025-02-16)
SPDX-License-Identifier: GPL-2.0-or-later
"""

import os
import shutil
import sys
from pathlib import Path

import pytest


def _win32_longpath(path):
    """
    Helper function to add the long path prefix for Windows, so that shutil.copytree
    won't fail while working with paths with 255+ chars.

    From: https://github.com/gabrielcnr/pytest-datadir/blob/4c6557e4b4e33dc1fc0645dfc43bbe0527733c17/src/pytest_datadir/plugin.py#L8-L30
    Pytest plugin: "pytest-datadir"
    Author of pytest plugin: "Gabriel Reis"
    License of plugin: MIT
    SPDX-License-Identifier: MIT
    """
    if sys.platform == "win32":
        # The use of os.path.normpath here is necessary since "the "\\?\" prefix
        # to a path string tells the Windows APIs to disable all string parsing
        # and to send the string that follows it straight to the file system".
        # (See https://docs.microsoft.com/pt-br/windows/desktop/FileIO/naming-a-file)
        normalized = os.path.normpath(path)
        if not normalized.startswith("\\\\?\\"):
            is_unc = normalized.startswith("\\\\")
            # see https://en.wikipedia.org/wiki/Path_(computing)#Universal_Naming_Convention # noqa: E501
            if (
                is_unc
            ):  # then we need to insert an additional "UNC\" to the longpath prefix
                normalized = normalized.replace("\\\\", "\\\\?\\UNC\\")
            else:
                normalized = "\\\\?\\" + normalized
        return normalized
    return path


@pytest.fixture(autouse=True)
def gunittest_datadir(
    monkeypatch: pytest.MonkeyPatch, request: pytest.FixtureRequest, tmp_path: Path
) -> None:
    """Fixture to change directory to a temporary directory containing a copy of the data directory"""
    print("request.path: ", request.path)
    parent_path = request.path.parent
    if parent_path.name == "testsuite":
        original_data_path = os.path.join(parent_path, "data")
        if (
            os.path.isdir(original_data_path)
            and os.path.basename(os.path.dirname(original_data_path)) == "testsuite"
        ):
            temp_path = tmp_path / "data"
            print("in a testsuite/data folder, copying to", temp_path)
            shutil.copytree(
                src=_win32_longpath(original_data_path),
                dst=_win32_longpath(str(temp_path)),
            )

        monkeypatch.chdir(tmp_path)
    else:
        print("not in a testsuite dir")
