# SPDX-License-Identifier: GPL-2.0-or-later

"""pytest test fixtures for the wxPython GUI

The tests import the GUI code from the GRASS installation, the same way tests of
the Python packages use the installed *grass* package. The GUI modules need a
GRASS session in the process environment already when they are imported, e.g.,
*core.globalvar* exits when GISBASE is not set. The fixtures here provide that.

The tests need a display. Running them under Xvfb is handled by pytest-xvfb.
Modules of GUI tests skip themselves with ``pytest.importorskip("wx")``, so that
the tests are reported as skipped, rather than failed or not collected, when
wxPython is not installed.
"""

import os

import pytest

import grass.script as gs


@pytest.fixture(scope="module")
def gui_session(tmp_path_factory):
    """Session whose environment is mirrored to os.environ, GUI in sys.path

    The GUI code reads the session from os.environ and imports its own modules
    by top-level names such as *core* and *gui_core*. The environment and
    sys.path are restored at the end of the module, so tests using this fixture
    need to be marked needs_solo_run.
    """
    project = tmp_path_factory.mktemp("gui_project") / "xy_test"
    gs.create_project(project)
    with (
        pytest.MonkeyPatch.context() as monkeypatch,
        gs.setup.init(project, env=os.environ.copy()) as session,
    ):
        for name, value in session.env.items():
            monkeypatch.setenv(name, value)
        monkeypatch.syspath_prepend(session.env["GRASS_GUIWXDIR"])
        yield session


@pytest.fixture(scope="session")
def wx_app():
    """The wx.App needed to create any window or most of the other wx objects

    wxPython can reliably have only one application per process, so it is not
    destroyed at the end of the session.
    """
    wx = pytest.importorskip("wx")
    return wx.App()
