# SPDX-License-Identifier: GPL-2.0-or-later

"""Test that all wxPython GUI modules can be imported"""

import importlib
from pathlib import Path

import pytest

import grass.script as gs

pytest.importorskip("wx")

# Modules use top-level imports such as core or gui_core, so they are imported
# the same way, from the installed GUI directory.
GUI_DIR = Path(gs.setup.get_install_path()) / "gui" / "wxpython"

pytestmark = pytest.mark.needs_solo_run


def _is_importable_module(path):
    """Return true if the file is a module which should be imported"""
    return not any(
        # Compiled caches.
        part == "__pycache__"
        # Tests, such as mapdisp/test_mapdisp.py, are not part of the GUI.
        or part.startswith("test")
        # Tool launchers such as g.gui.gcp.py, which can't be imported by name.
        or "." in part.removesuffix(".py")
        for part in path.parts
    )


def _module_names():
    names = []
    for path in sorted(GUI_DIR.rglob("*.py")):
        relative = path.relative_to(GUI_DIR)
        if not _is_importable_module(relative):
            continue
        parts = relative.with_suffix("").parts
        if parts[-1] == "__init__":
            parts = parts[:-1]
        names.append(".".join(parts))
    return names


@pytest.mark.parametrize("module_name", _module_names())
def test_module_imports(gui_session, wx_app, module_name):
    """Module can be imported in a GRASS session with a display"""
    try:
        importlib.import_module(module_name)
    except ModuleNotFoundError as error:
        if error.name and error.name.split(".")[0] == "matplotlib":
            pytest.skip("Optional dependency matplotlib is not installed")
        raise
