"""Fixtures for v.edit tool tests"""

import pytest
import os

import grass.script as gs


@pytest.fixture
def xy_dataset_session(tmp_path):
    """Creates a session with XY project"""
    gs.create_project(tmp_path / "test")
    with gs.setup.init(tmp_path / "test", env=os.environ.copy()) as session:
        yield session


@pytest.fixture(scope="session", autouse=True)
def english_messages():
    """Keep messages in English for tests which check them

    The tests are written for English messages, so they would fail in a
    translated locale, e.g., when running on a system which is not English.
    """
    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setenv("LANGUAGE", "C")
        yield
