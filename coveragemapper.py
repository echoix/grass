import os
import subprocess
from coverage import CoverageData
from pathlib import Path


def get_grass_config_path():
    # grass_config_path: str = ""
    # try:

    # except:
    #     grass_config_path = 

    # subprocess.run(
    #     ["grass", "--config", "path"], capture_output=True, text=True, check=True
    # ).stdout
    return subprocess.run(
        ["grass", "--config", "path"], capture_output=True, text=True, check=True
    ).stdout


INITIAL_GISBASE = os.getenv("INITIAL_GISBASE", get_grass_config_path())
INITIAL_PWD = os.getenv("INITIAL_PWD", str(Path.cwd().absolute()))


def map_scripts_paths(old_path):
    p = Path(old_path)
    base = Path(INITIAL_GISBASE) / "scripts" / "*"
    if p.match(str(base)):
        return str(Path(INITIAL_PWD) / (p.name) / (p.name)) + ".py"
    return old_path


if __name__ == "__main__":
    a = CoverageData(".coverage")
    b = CoverageData(".coverage.ed2")
    b.update(a, map_path=map_scripts_paths)
