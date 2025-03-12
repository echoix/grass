"""Fixtures for grass.script"""

import os
from collections.abc import Generator

import pytest

import grass.script as gs
from grass.script.setup import SessionHandle


@pytest.fixture
def mock_no_session(monkeypatch):
    """Set the environment variables as if there would be no background session.

    Use with usefixtures (not as a paramter) to avoid warnings about an unused
    parameter::

        @pytest.mark.usefixtures("mock_no_session")
        def test_session_handling():
            pass

    There may or may not be a session in the background (we don't check either way).
    """
    monkeypatch.delenv("GISRC", raising=False)
    monkeypatch.delenv("GISBASE", raising=False)


@pytest.fixture
def empty_session(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> Generator[SessionHandle]:
    """Set up a GRASS session for the tests."""
    project = tmp_path / "test_project"
    gs.create_project(project)
    with gs.setup.init(project, env=os.environ.copy()) as session:
        for key, value in session.env.items():
            monkeypatch.setenv(key, value)
        yield session


@pytest.fixture
def session_2x2(empty_session: SessionHandle) -> SessionHandle:
    """Set up a GRASS session for the tests."""
    gs.run_command("g.region", rows=2, cols=2, env=empty_session.env)
    gs.mapcalc("ones = 1", env=empty_session.env)
    gs.mapcalc(
        "nulls_and_one_1_1 = if(row() == 1 && col() == 1, 1, null())",
        env=empty_session.env,
    )
    return empty_session
