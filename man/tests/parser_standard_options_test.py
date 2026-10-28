# SPDX-License-Identifier: GPL-2.0-or-later
"""Tests for the extraction of standard parser options from the C source."""

import re
import sys
from pathlib import Path

import pytest

MAN_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(MAN_DIR))

import parser_standard_options as pso  # noqa: E402

STANDARD_OPTIONS_SOURCE = MAN_DIR.parent / "lib" / "gis" / "parser_standard_options.c"

# Excerpt of lib/gis/parser_standard_options.c with the constructs the parser
# has to handle: a dynamic answer, a description split into two string
# literals, translation macros, and a multiline function call.
C_SOURCE = """\
        /* raster maps */
    case G_OPT_MEMORYMB:
        Opt->key = "memory";
        Opt->type = TYPE_INTEGER;
        Opt->key_desc = "memory in MB";
        Opt->required = NO;
        Opt->multiple = NO;
        Opt->answer = "300";
        /* start dynamic answer */
        /* check MEMORYMB in GISRC, set with g.gisenv */
        memstr = G_store(G_getenv_nofatal("MEMORYMB"));
        if (memstr && *memstr)
            Opt->answer = memstr;
        /* end dynamic answer */
        Opt->label = _("Maximum memory to be used (in MB)");
        Opt->description = _("Cache size for raster rows");
        break;
    case G_OPT_R_TYPE:
        Opt->key = "type";
        Opt->type = TYPE_STRING;
        Opt->required = YES;
        Opt->multiple = NO;
        Opt->label = _("Type of raster map to be created");
        Opt->description = _("Storage type for resultant raster map");
        Opt->options = "CELL,FCELL,DCELL";
        G_asprintf((char **)&(Opt->descriptions), "CELL;%s;FCELL;%s;DCELL;%s",
                   _("Integer"), _("Single precision floating point"),
                   _("Double precision floating point"));
        break;
    case G_OPT_M_NPROCS:
        Opt->key = "nprocs";
        Opt->type = TYPE_INTEGER;
        Opt->required = NO;
        Opt->multiple = NO;
        Opt->answer = "0";
        Opt->label = _("Number of threads for parallel computing");
        Opt->description = _("0: use OpenMP default; >0: use nprocs; "
                             "<0: use MAX-nprocs");
        break;
"""


def parse_c_source():
    return dict(pso.parse_options(C_SOURCE.splitlines()))


def test_parse_options_names_and_order():
    """Check that each case label is an option, in the order of the source"""
    names = [name for name, _ in pso.parse_options(C_SOURCE.splitlines())]
    assert names == ["G_OPT_MEMORYMB", "G_OPT_R_TYPE", "G_OPT_M_NPROCS"]


def test_parse_options_values_are_cleaned():
    """Check that quotes, translation macros and semicolons are removed"""
    option = parse_c_source()["G_OPT_R_TYPE"]
    assert option == {
        "key": "type",
        "type": "TYPE_STRING",
        "required": "YES",
        "multiple": "NO",
        "label": "Type of raster map to be created",
        "description": "Storage type for resultant raster map",
        "options": "CELL,FCELL,DCELL",
    }


def test_parse_options_ignores_dynamic_answer():
    """Check that the static answer is used instead of the computed one"""
    option = parse_c_source()["G_OPT_MEMORYMB"]
    assert option["answer"] == "300"
    assert option["key_desc"] == "memory in MB"


def test_parse_options_joins_multiline_strings():
    """Check that a description split into several literals is one string"""
    option = parse_c_source()["G_OPT_M_NPROCS"]
    assert option["description"] == (
        "0: use OpenMP default; >0: use nprocs; <0: use MAX-nprocs"
    )


def test_parse_options_skips_multiline_function_calls():
    """Check that the arguments of a multiline call are not taken as options"""
    option = parse_c_source()["G_OPT_R_TYPE"]
    assert "descriptions" not in option
    assert not any("Integer" in value for value in option.values())


def test_parse_options_continues_after_multiline_function_call():
    """Check that an assignment following a multiline call is still extracted"""
    lines = [
        "case G_OPT_AFTER_CALL:",
        'Opt->key = "after";',
        "G_asprintf(",
        '(char **)&(Opt->descriptions), "a;%s",',
        '_("A"));',
        'Opt->description = _("After the call");',
        "break;",
    ]
    assert pso.parse_options(lines) == [
        ("G_OPT_AFTER_CALL", {"key": "after", "description": "After the call"})
    ]


def test_parse_options_ignores_lines_outside_cases():
    """Check that nothing is extracted before the first case or without a body"""
    assert pso.parse_options([]) == []
    assert pso.parse_options(['Opt->key = "stray";', "break;"]) == []
    assert pso.parse_options(["case G_OPT_EMPTY:", "break;"]) == []


def test_parse_options_unescapes_quotes():
    """Check that escaped double quotes in a string become plain quotes"""
    lines = [
        "case G_OPT_QUOTED:",
        r'Opt->description = _("Use \"auto\" for default");',
        "break;",
    ]
    assert pso.parse_options(lines) == [
        ("G_OPT_QUOTED", {"description": 'Use "auto" for default'})
    ]


def test_parse_options_all_standard_options():
    """Check that every standard option in the real source file is extracted"""
    source = STANDARD_OPTIONS_SOURCE.read_text(encoding="utf-8")
    expected = re.findall(r"^\s*case (G_OPT_\w+):", source, flags=re.MULTILINE)
    options = pso.parse_options(source.splitlines())
    assert [name for name, _ in options] == expected


def test_parse_options_real_raster_input():
    """Check a well known option from the real source file"""
    source = STANDARD_OPTIONS_SOURCE.read_text(encoding="utf-8")
    option = dict(pso.parse_options(source.splitlines()))["G_OPT_R_INPUT"]
    assert option["key"] == "input"
    assert option["required"] == "YES"
    assert option["gisprompt"] == "old,cell,raster"


@pytest.mark.parametrize(
    ("name", "heading"),
    [
        ("G_OPT_R_INPUT", "Raster"),
        ("G_OPT_R3_INPUT", "Raster 3D"),
        ("G_OPT_V_OUTPUT", "Vector"),
        ("G_OPT_V3_TYPE", "Vector"),
        ("G_OPT_STRDS_INPUT", "Temporal"),
        ("G_OPT_CN", "Color"),
        ("G_OPT_MEMORYMB", "Other"),
        ("G_OPT_UNKNOWN_PREFIX", "Other"),
    ],
)
def test_get_heading(name, heading):
    """Check that the heading is selected by the part after G_OPT_"""
    assert pso.get_heading(name) == heading


def test_get_heading_invalid_identifier():
    """Check that an identifier not starting with G_OPT_ is reported"""
    with pytest.raises(ValueError, match="Strangely formatted"):
        pso.get_heading("R_INPUT")


def test_write_markdown_option_string_option():
    """Check the usage examples generated for an option of type string"""
    md = []
    option = {
        "key": "input",
        "type": "TYPE_STRING",
        "key_desc": "name",
        "required": "YES",
        "multiple": "NO",
    }
    pso.write_markdown_option(
        md, "G_OPT_R_INPUT", option, ["key", "type", "required", "multiple"]
    )
    text = "\n".join(md)
    assert "| key | input |" in md
    assert "| type | TYPE_STRING (`type: string`) |" in md
    assert "| required | YES (`required: yes`) |" in md
    assert "| multiple | NO (`multiple: no`) |" in md
    assert "# %option G_OPT_R_INPUT" in text
    assert 'input = options["input"]' in text
    # A string is quoted and the key description is the example without answer.
    assert 'input="name"' in md


def test_write_markdown_option_answer_example():
    """Check that the answer is the example unless it is a constant"""
    md = []
    pso.write_markdown_option(
        md,
        "G_OPT_M_NPROCS",
        {"key": "nprocs", "type": "TYPE_INTEGER", "answer": "0"},
        ["key", "answer"],
    )
    assert "nprocs=0" in md

    md = []
    pso.write_markdown_option(
        md,
        "G_OPT_C",
        {
            "key": "color",
            "type": "TYPE_STRING",
            "answer": "DEFAULT_FG_COLOR",
            "key_desc": "name",
        },
        ["key", "answer"],
    )
    assert 'color="name"' in md


def test_write_markdown_option_dynamic_value():
    """Check that a computed value is described as such"""
    md = []
    pso.write_markdown_option(
        md,
        "G_OPT_EXAMPLE",
        {"key": "example", "answer": "G_getenv_nofatal(NAME)"},
        ["key", "answer"],
    )
    assert "| answer | Computed dynamically by *G_getenv_nofatal(NAME)* |" in md


def test_write_markdown_option_without_key():
    """Check that no Python usage examples are generated without a key"""
    md = []
    pso.write_markdown_option(md, "G_OPT_NOKEY", {"type": "TYPE_STRING"}, ["type"])
    assert "To use the value in Python:" not in "\n".join(md)


def test_option_table_columns_are_sorted_union():
    """Check that the columns are all keys used by any option, sorted"""
    table = pso.OptTable([("A", {"type": "t", "key": "k"}), ("B", {"required": "YES"})])
    assert table.columns == ["key", "required", "type"]


def test_option_table_csv_rows():
    """Check that missing values are empty and the delimiter is configurable"""
    table = pso.OptTable([("A", {"key": "k", "type": "t"}), ("B", {"key": "l"})])
    rows = table.csv(delimiter="|").splitlines()[1:]
    assert rows == ["A|k|t", "B|l|"]


def test_option_table_html():
    """Check the table structure, the header and the empty cells"""
    table = pso.OptTable([("A", {"key": "k"}), ("B", {})])
    html = table.html(toptions=None).splitlines()
    assert html[0] == "<table>"
    assert "    <th>option</th>" in html
    assert "    <th>key</th>" in html
    assert "    <td>A</td>" in html
    assert "    <td>k</td>" in html
    assert "    <td></td>" in html
    assert html[-1] == "</table>"
    assert pso.OptTable([]).html().splitlines()[0] == "<table border=1>"


def test_option_table_markdown_groups_options_by_heading():
    """Check that options are listed in a section of their heading"""
    table = pso.OptTable(
        [
            ("G_OPT_V_INPUT", {"key": "map"}),
            ("G_OPT_R_INPUT", {"key": "input"}),
            ("G_OPT_MEMORYMB", {"key": "memory"}),
        ]
    )
    lines = table.markdown().splitlines()
    assert pso.MARKDOWN_INTRO_TEXT.splitlines()[0] in lines
    raster = lines.index("## Raster")
    vector = lines.index("## Vector")
    other = lines.index("## Other")
    assert lines.index("### G_OPT_R_INPUT") > raster
    assert lines.index("### G_OPT_V_INPUT") > vector
    assert lines.index("### G_OPT_MEMORYMB") > other
    # Headings are sorted, with the catch-all one last.
    assert raster < vector < other
