"""Tests of the extraction of translatable strings from tool headers"""

import importlib.util
import io
import re
import shutil
import subprocess
from pathlib import Path

import pytest

UTILS_DIR = Path(__file__).resolve().parent.parent
SOURCE_DIR = UTILS_DIR.parent

spec = importlib.util.spec_from_file_location(
    "grass_tool_header_pot", UTILS_DIR / "grass_tool_header_pot.py"
)
pot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pot)

HEADER = """\
#!/usr/bin/env python3
# %module
# % description: Does something useful
# % keyword: raster
# %end
#%flag
#% key: i
#% label: Invert the result
#% guisection: Output
#%end
# %option G_OPT_R_INPUT
# % label: Input map with "quotes"
# % description: {NULL}
# %end
# %option
# % key: format
# % options: plain,json
# % descriptions: plain; Plain text output ;json;JSON output;
# % guidependency: input
# % guisection: Output
# %end
# %rules
# % description: Not a field of a rule
# %end
import grass.script as gs
# % description: Not in a block
"""

# Header without the space after #, in the capitalized form used by some
# shell scripts. The extractor reads it from any file whatever its language.
SHELL_HEADER = """\
#%Module
#% Description: Does something in a shell
#% keyword: raster
#%End
#%flag
#% key: q
#%end
#%Option G_OPT_R_OUTPUT
#% Description: Output map
#%end
#%option
#% key: format
#% DESCRIPTIONS: plain;Plain text output
#%end
"""


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def messages_by_key(messages):
    return {(message.context, message.msgid): message for message in messages}


def test_fields_and_line_numbers(tmp_path):
    """Translatable fields are extracted with their line and a comment."""
    tool = write(tmp_path / "r.tool.py", HEADER)
    messages = messages_by_key(pot.extract([tool]))
    reference = tool.as_posix()

    assert set(messages) == {
        (None, "Does something useful"),
        (None, "raster"),
        (None, "Invert the result"),
        (None, "Output"),
        (None, 'Input map with "quotes"'),
        (pot.VALUE_DESCRIPTION_CONTEXT, "Plain text output"),
        (pot.VALUE_DESCRIPTION_CONTEXT, "JSON output"),
    }
    assert messages[None, "Does something useful"].references == [f"{reference}:3"]
    assert messages[None, "Does something useful"].comments == ["Tool description"]
    assert messages[None, "raster"].comments == ["Tool keyword"]
    assert messages[None, "Invert the result"].comments == ['Label of flag "-i"']
    assert messages[None, 'Input map with "quotes"'].comments == [
        "Label of standard option G_OPT_R_INPUT"
    ]
    output = messages[None, "Output"]
    assert output.references == [f"{reference}:9", f"{reference}:20"]
    assert output.comments == [pot.GUISECTION_COMMENT]


def test_value_descriptions(tmp_path):
    """Each value description is a separate message with a context."""
    tool = write(tmp_path / "r.tool.py", HEADER)
    messages = messages_by_key(pot.extract([tool]))

    plain = messages[pot.VALUE_DESCRIPTION_CONTEXT, "Plain text output"]
    assert plain.references == [f"{tool.as_posix()}:18"]
    assert plain.comments == [
        'Description of value "plain" of option "format" (do not use semicolons)'
    ]
    assert (pot.VALUE_DESCRIPTION_CONTEXT, "JSON output") in messages


def test_unpaired_description_is_ignored(tmp_path):
    """As in G_parser(), an unpaired trailing item is not used."""
    tool = write(
        tmp_path / "r.tool.py",
        "# %option\n# % key: a\n# % descriptions: Not a pair\n# %end\n",
    )
    assert pot.extract([tool]) == []


def test_messages_are_merged(tmp_path):
    """The same string from several tools gives one message."""
    first = write(tmp_path / "a" / "r.a.py", HEADER)
    second = write(tmp_path / "b" / "r.b.py", HEADER)
    messages = messages_by_key(pot.extract([first, second]))

    raster = messages[None, "raster"]
    assert raster.references == [f"{first.as_posix()}:4", f"{second.as_posix()}:4"]
    assert raster.comments == ["Tool keyword"]


def test_po_string_escaping():
    assert pot.po_string('a "b" \\ c\td') == '"a \\"b\\" \\\\ c\\td"'


def test_write_pot(tmp_path):
    """The output is a valid PO template."""
    tool = write(tmp_path / "r.tool.py", HEADER)
    output = io.StringIO()
    pot.write_pot(pot.extract([tool]), output)
    text = output.getvalue()

    assert (
        f"#. {pot.GUISECTION_COMMENT}\n"
        f"#: {tool.as_posix()}:9 {tool.as_posix()}:20\n"
        'msgid "Output"\n'
        'msgstr ""\n'
    ) in text
    assert (f'msgctxt "{pot.VALUE_DESCRIPTION_CONTEXT}"\nmsgid "JSON output"\n') in text
    msgfmt = shutil.which("msgfmt")
    if not msgfmt:
        pytest.skip("msgfmt not available")
    pot_file = write(tmp_path / "test.pot", text)
    subprocess.run([msgfmt, "--check-format", "-o", "/dev/null", pot_file], check=True)


def test_find_tool_files(tmp_path):
    """Tools are found by their Makefile as in the build."""
    include = "include $(MODULE_TOPDIR)/include/Make/{}.make\n"
    script = write(tmp_path / "scripts" / "r.a" / "r.a.py", HEADER)
    write(script.parent / "Makefile", f"PGM = r.a\n\n{include.format('Script')}")
    write(script.parent / "helper.py", HEADER)
    gui = write(tmp_path / "gui" / "wxpython" / "x" / "g.gui.x.py", HEADER)
    write(gui.parent / "Makefile", include.format("GuiScript"))
    write(gui.parent / "other.py", HEADER)
    shell = write(tmp_path / "scripts" / "r.c" / "r.c.sh", SHELL_HEADER)
    write(shell.parent / "Makefile", f"PGM = r.c\n\n{include.format('ShScript')}")
    no_extension = write(tmp_path / "scripts" / "r.d" / "r.d", SHELL_HEADER)
    write(no_extension.parent / "Makefile", f"PGM = r.d\n\n{include.format('Script')}")
    plain = write(tmp_path / "gui" / "scripts" / "d.x.py", HEADER)
    write(plain.parent / "Makefile", include.format("Python"))
    testsuite = tmp_path / "scripts" / "r.a" / "testsuite"
    write(testsuite / "r.b.py", HEADER)
    write(testsuite / "Makefile", f"PGM = r.b\n\n{include.format('Script')}")

    assert sorted(pot.find_tool_files(tmp_path)) == sorted(
        str(path) for path in (script, gui, shell, no_extension, plain)
    )


@pytest.mark.parametrize("name", ["r.tool.sh", "r.tool", "r.tool.pl"])
def test_non_python_files(tmp_path, name):
    """Headers are read from any file, and their commands ignore case."""
    tool = write(tmp_path / name, SHELL_HEADER)
    messages = messages_by_key(pot.extract([tool]))

    assert set(messages) == {
        (None, "Does something in a shell"),
        (None, "raster"),
        (None, "Output map"),
        (pot.VALUE_DESCRIPTION_CONTEXT, "Plain text output"),
    }
    assert messages[None, "Output map"].references == [f"{tool.as_posix()}:9"]
    assert messages[None, "Output map"].comments == [
        "Description of standard option G_OPT_R_OUTPUT"
    ]


def test_context_matches_g_parser():
    """The context is the one g.parser uses at runtime."""
    source = (SOURCE_DIR / "general" / "g.parser" / "translate.c").read_text()
    match = re.search(r'#define VALUE_DESCRIPTION_CONTEXT "(.*)"', source)
    assert match
    assert match.group(1) == pot.VALUE_DESCRIPTION_CONTEXT
