"""Test fallback of resource directories to GISBASE"""

import pytest

import grass.script as gs
from grass.app.runtime import RuntimePaths


@pytest.fixture
def env_with_only_gisbase(xy_session_for_module):
    """Session environment without the GRASS_*DIR variables, but with GISBASE"""
    env = xy_session_for_module.env.copy()
    for name in RuntimePaths.env_variable_names():
        if name != "GISBASE":
            env.pop(name, None)
    return env


def test_colors_dir_falls_back_to_gisbase(env_with_only_gisbase):
    """Color rules are found without GRASS_COLORSDIR"""
    rules = gs.read_command("r.colors", flags="l", env=env_with_only_gisbase)
    assert "viridis" in rules.split()


def test_etc_dir_falls_back_to_gisbase(env_with_only_gisbase):
    """Element list in etc is found without GRASS_ETCDIR"""
    gs.run_command("g.list", type="raster", env=env_with_only_gisbase)
