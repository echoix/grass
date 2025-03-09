import os
from collections.abc import Generator

import pytest

import grass.script as gs
from grass.script.setup import SessionHandle


@pytest.fixture
def setup_session(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> Generator[SessionHandle]:
    """Set up a GRASS session"""
    # Initialize GRASS project
    project = tmp_path / "r_coin_project"
    gs.create_project(project)
    with gs.setup.init(project, env=os.environ.copy()) as session:
        for key, value in session.env.items():
            monkeypatch.setenv(key, value)
        yield session


@pytest.fixture
def setup_maps(setup_session: SessionHandle) -> SessionHandle:
    """Creates test raster maps."""
    # Set the region
    gs.run_command(
        "g.region",
        n=3,
        s=0,
        e=3,
        w=0,
        res=1,
        env=setup_session.env,
    )

    # Create the raster maps
    # map1:
    # 1 1 2
    # 1 2 3
    # 2 2 3
    gs.mapcalc(
        "map1 = "
        "if(row() == 1 && col() <= 2, 1, "
        "if(row() == 1 && col() == 3, 2, "
        "if(row() == 2 && col() == 1, 1, "
        "if(row() == 2 && col() == 2, 2, "
        "if(row() == 2 && col() == 3, 3, "
        "if(row() == 3 && col() <= 2, 2, 3))))))",
        overwrite=True,
        env=setup_session.env,
    )

    # map2:
    # 1 2 2
    # 2 1 3
    # 3 3 3
    gs.mapcalc(
        "map2 = "
        "if(row() == 1 && col() == 1, 1, "
        "if(row() == 1 && col() >= 2, 2, "
        "if(row() == 2 && col() == 1, 2, "
        "if(row() == 2 && col() == 2, 1, "
        "if(row() == 2 && col() == 3, 3, "
        "if(row() >= 3, 3, null()))))))",
        overwrite=True,
        env=setup_session.env,
    )
    return setup_session  # Pass the session to tests
