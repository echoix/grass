# Copyright (C) 2026 by the GRASS Development Team
# SPDX-License-Identifier: GPL-2.0-or-later

"""Test the release of the WKB buffers returned by the vector library

The buffers are allocated with G_malloc() by the vector library, and the
pygrass functions have to release them with G_free(). Releasing a buffer
allocated by GEOS with G_free() crashes on Windows, and not releasing it
leaks memory on all platforms.

The checks run in a subprocess, see ``grass_pygrass_vector_wkb_checks.py``.
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest

import grass.script as gs

CHECKS = Path(__file__).with_name("grass_pygrass_vector_wkb_checks.py")
NOT_SUPPORTED = 77


@pytest.fixture(scope="module")
def session(tmp_path_factory):
    """Active session in an XY project (scope: module)"""
    project = tmp_path_factory.mktemp("wkb") / "project"
    gs.create_project(project)
    with gs.setup.init(project, env=os.environ.copy()) as session:
        yield session


def run_check(session, name):
    """Run a check in the session and fail the test when the check fails"""
    result = subprocess.run(
        [sys.executable, str(CHECKS), name],
        env=session.env,
        capture_output=True,
        text=True,
        check=False,
        timeout=240,
    )
    if result.returncode == NOT_SUPPORTED:
        pytest.skip(result.stdout.strip())
    assert result.returncode == 0, (
        f"Check {name} ended with status {result.returncode}\n"
        f"{result.stdout}\n{result.stderr}"
    )


@pytest.mark.parametrize(
    "check",
    [
        "line_wkb_is_freed",
        "area_wkb_is_freed",
        "wkb_lists_are_freed",
        "no_memory_growth",
        "all_functions_work_repeatedly",
    ],
)
def test_wkb_buffers(session, check):
    """Check that the WKB buffers are released and the functions work"""
    run_check(session, check)
