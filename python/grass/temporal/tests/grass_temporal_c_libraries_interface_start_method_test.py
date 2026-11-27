# Copyright (C) 2026 by the GRASS Development Team
# SPDX-License-Identifier: GPL-2.0-or-later

"""Test that GRASS server processes start with every multiprocessing start method.

Python 3.14 made forkserver the default start method on Linux, while macOS and Windows use
spawn. This test sets each available start method as the default in a subprocess,
so that all of them are tested on any platform and Python version.
"""

import multiprocessing
import subprocess
import sys

import pytest

SCRIPT = """
import multiprocessing
import sys


def main():
    import grass.script as gs
    import grass.temporal as tgis
    from grass.pygrass.messages import Messenger
    from grass.pygrass.rpc import DataProvider
    from grass.pygrass.rpc.base import RPCServerBase

    project = sys.argv[1]
    gs.create_project(project)
    # Legacy init without env so that os.environ is set for grass.temporal.
    session = gs.setup.init(project)
    gs.run_command("g.region", n=10, s=0, e=10, w=0, res=1)
    gs.run_command("r.mapcalc", expression="a = 1")
    mapset = gs.gisenv()["MAPSET"]

    messenger = Messenger()
    messenger.message("test")
    messenger.stop()

    server = RPCServerBase()
    server.stop()

    provider = DataProvider()
    assert provider.get_raster_image_as_np("a").size > 0
    provider.stop()

    tgis.init()
    ciface = tgis.CLibrariesInterface()
    assert ciface.raster_map_exists("a", mapset)
    ciface.stop()

    session.finish()


if __name__ == "__main__":
    multiprocessing.set_start_method(sys.argv[2])
    main()
"""


@pytest.mark.parametrize("start_method", multiprocessing.get_all_start_methods())
def test_servers_start_with_start_method(tmp_path, start_method):
    """Servers work and exit cleanly with the start method set as the default."""
    script = tmp_path / "script.py"
    script.write_text(SCRIPT)
    result = subprocess.run(
        [sys.executable, str(script), str(tmp_path / "project"), start_method],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    # A failing server check thread does not change the exit code.
    assert "Traceback" not in result.stderr, result.stderr
    assert "leaked semaphore" not in result.stderr, result.stderr
