import os
import pytest
import grass.script as gs


@pytest.fixture
def session(tmp_path_factory, monkeypatch):
    """Set up a GRASS session for the tests."""
    tmp_path = tmp_path_factory.mktemp("grass_session")
    project = "test_project"
    monkeypatch.delenv("GISBASE", raising=False)

    # Create a test location
    gs.create_project(tmp_path, project)

    # Initialize the GRASS session
    with gs.setup.init(tmp_path / project, env=os.environ.copy()) as session:
        yield session
