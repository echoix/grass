"""Tests of option value descriptions and GUI dependencies in g.parser

g.parser translates each value description separately (see translate.c),
so without a translation, the interface must be the same as written.
The header is the same in Python and shell scripts.
"""

import os
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET

import pytest

import grass.script as gs

HEADER = """\
# %module
# % description: Test of option value descriptions
# %end
# %option
# % key: format
# % type: string
# % options: plain,json,shell
# % descriptions: plain;Plain text output; json ; JSON output ;shell;Shell style;
# % guidependency: input,maps
# % answer: plain
# %end
"""

PYTHON_SCRIPT = f"""\
#!/usr/bin/env python3
{HEADER}
import grass.script as gs
gs.parser()
"""

SHELL_SCRIPT = f"""\
#!/bin/sh
{HEADER}
if [ "$1" != "@ARGS_PARSED@" ] ; then
    exec g.parser "$0" "$@"
fi
"""


@pytest.fixture(scope="module")
def session(tmp_path_factory):
    """Set up a GRASS session for the tests."""
    tmp_path = tmp_path_factory.mktemp("grass_session")
    project = "test_project"
    gs.create_project(tmp_path, project)
    with gs.setup.init(tmp_path / project, env=os.environ.copy()) as session:
        yield session


@pytest.fixture(scope="module", params=["python", "shell"])
def parameter(request, session, tmp_path_factory):
    """Return the parameter element from the interface description."""
    if request.param == "python":
        name, text, interpreter = "t_example.py", PYTHON_SCRIPT, sys.executable
    else:
        name, text, interpreter = "t_example.sh", SHELL_SCRIPT, shutil.which("sh")
        if not interpreter:
            pytest.skip("sh not available")
    script = tmp_path_factory.mktemp("script") / name
    script.write_text(text, encoding="utf-8")
    result = subprocess.run(
        [interpreter, script, "--interface-description"],
        capture_output=True,
        check=True,
        env=session.env,
    )
    return ET.fromstring(result.stdout).find("parameter")


def test_value_descriptions(parameter):
    """Values are matched with their descriptions which are kept as written."""
    values = {
        value.findtext("name").strip(): value.findtext("description")
        for value in parameter.iter("value")
    }
    assert values == {
        "plain": "Plain text output",
        "json": " JSON output ",
        "shell": "Shell style",
    }


def test_guidependency(parameter):
    """GUI dependency is a list of option keys, kept as written."""
    assert parameter.findtext("guidependency").strip() == "input,maps"
