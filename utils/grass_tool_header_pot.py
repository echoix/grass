#!/usr/bin/env python3
"""Extract translatable strings from the interface headers of tools to a POT file.

Python and shell tools declare their interface in specially formatted
comments (`# %module`, `# %flag`, `# %option`, ...) which g.parser reads at
runtime. This script reads these comments directly, using only the Python
standard library, so no GRASS build is needed. It writes a standard gettext
template with:

- references (`#:`) to the real source file and line,
- extracted comments (`#.`) telling translators what each string is,
- the `option value description` message context (`msgctxt`) for
  descriptions of option values, which g.parser translates one by one.

The fields extracted here must match the fields g.parser translates
(see general/g.parser/parse.c and general/g.parser/translate.c).

Usage (from the locale directory, as in `make pot`):

    python ../utils/grass_tool_header_pot.py -o tool_headers.pot
    python ../utils/grass_tool_header_pot.py -o r_example.pot ../path/to/r.example.py
"""

import argparse
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

# Must be the same as VALUE_DESCRIPTION_CONTEXT in general/g.parser/translate.c.
VALUE_DESCRIPTION_CONTEXT = "option value description"

# Directories with tools, relative to the source root.
DEFAULT_DIRS = ("gui", "scripts", "temporal")
# Directories where each Python file is a tool installed without the script
# Makefile rules, relative to the source root.
PLAIN_SCRIPT_DIRS = ("gui/scripts",)

TRANSLATABLE_FIELDS = {
    "module": {"label", "description", "keyword", "keywords"},
    "flag": {"label", "description", "guisection"},
    "option": {"label", "description", "descriptions", "guisection"},
}

GUISECTION_COMMENT = "Name of a GUI section (tab) in the tool dialog"

SCRIPT_MAKEFILE = re.compile(
    r"^include\s.*/include/Make/(Sh)?Script\.make\s*$", re.MULTILINE
)
GUI_SCRIPT_MAKEFILE = re.compile(
    r"^include\s.*/include/Make/GuiScript\.make\s*$", re.MULTILINE
)
PGM_VARIABLE = re.compile(r"^PGM\s*=\s*(\S+)\s*$", re.MULTILINE)


@dataclass
class Message:
    msgid: str
    context: str | None = None
    comments: list[str] = field(default_factory=list)
    references: list[str] = field(default_factory=list)


@dataclass
class Block:
    kind: str
    standard_option: str | None = None
    key: str | None = None
    # (line number, field name, value)
    fields: list[tuple[int, str, str]] = field(default_factory=list)

    @property
    def name(self):
        if self.kind == "flag":
            return f'flag "-{self.key}"'
        if self.key:
            return f'option "{self.key}"'
        return f"standard option {self.standard_option}"


def header_command(line):
    """Return the text after the header comment prefix, or None.

    Accepts the same prefixes as g.parser: `#%` and `# %`.
    """
    line = line.rstrip("\r\n")
    if len(line) > 2 and line.startswith("#%"):
        return line[2:]
    if len(line) > 3 and line.startswith("# %"):
        return line[3:]
    return None


def parse_header(lines):
    """Yield the blocks of a tool header with their translatable fields."""
    block = None
    in_rules = False
    for number, line in enumerate(lines, start=1):
        command = header_command(line)
        if command is None:
            continue
        name, _, value = command.strip().partition(":")
        name = name.strip().lower()
        value = value.strip()
        if name == "end":
            if block:
                yield block
            block = None
            in_rules = False
            continue
        if in_rules:
            continue
        if block is None:
            if name in {"module", "flag"}:
                block = Block(kind=name)
            elif name.startswith("option"):
                block = Block(kind="option")
                tokens = command.split()
                if len(tokens) > 1:
                    block.standard_option = tokens[1]
            elif name == "rules":
                in_rules = True
            continue
        if name == "key":
            block.key = value[:1] if block.kind == "flag" else value
        elif name in TRANSLATABLE_FIELDS[block.kind]:
            # As g.parser, ignore empty values and the {NULL} placeholder.
            if value and value.lower() != "{null}":
                block.fields.append((number, name, value))
    if block:
        yield block


def messages_from_block(block):
    """Yield (line number, Message) pairs for the fields of a block."""
    for number, name, value in block.fields:
        if name == "descriptions":
            yield from value_description_messages(block, number, value)
            continue
        if name == "guisection":
            comment = GUISECTION_COMMENT
        elif block.kind == "module":
            comment = "Tool keyword" if name.startswith("keyword") else f"Tool {name}"
        else:
            comment = f"{name.capitalize()} of {block.name}"
        yield number, Message(msgid=value, comments=[comment])


def value_description_messages(block, number, value):
    """Yield messages for descriptions of option values.

    The value is "value;description;value;description...". Pairs are formed
    as in G_parser() and an unpaired trailing item is ignored.
    """
    items = value.split(";")
    for i in range(1, len(items), 2):
        description = items[i].strip()
        if not description:
            continue
        comment = (
            f'Description of value "{items[i - 1].strip()}" of {block.name}'
            " (do not use semicolons)"
        )
        yield (
            number,
            Message(
                msgid=description,
                context=VALUE_DESCRIPTION_CONTEXT,
                comments=[comment],
            ),
        )


def extract(paths):
    """Return messages from the given files, merged by context and msgid."""
    messages = {}
    for path in paths:
        reference_path = Path(path).as_posix()
        with open(path, encoding="utf-8") as file:
            blocks = list(parse_header(file))
        for block in blocks:
            for number, message in messages_from_block(block):
                merged = messages.setdefault((message.context, message.msgid), message)
                if merged is not message:
                    for comment in message.comments:
                        if comment not in merged.comments:
                            merged.comments.append(comment)
                merged.references.append(f"{reference_path}:{number}")
    return list(messages.values())


def find_tool_files(root):
    """Return the tool source files built with the script Makefile rules.

    Also return the Python files in PLAIN_SCRIPT_DIRS.
    """
    files = []
    plain_script_dirs = {
        os.path.normpath(os.path.join(root, path)) for path in PLAIN_SCRIPT_DIRS
    }
    for directory in DEFAULT_DIRS:
        for dirpath, dirnames, filenames in os.walk(os.path.join(root, directory)):
            dirnames[:] = sorted(
                name
                for name in dirnames
                if not name.startswith(".") and name not in {"tests", "testsuite"}
            )
            if os.path.normpath(dirpath) in plain_script_dirs:
                files.extend(
                    os.path.join(dirpath, name)
                    for name in sorted(filenames)
                    if name.endswith(".py")
                )
                continue
            if "Makefile" not in filenames:
                continue
            makefile = Path(dirpath, "Makefile").read_text(encoding="utf-8")
            if GUI_SCRIPT_MAKEFILE.search(makefile):
                files.extend(
                    os.path.join(dirpath, name)
                    for name in sorted(filenames)
                    if name.startswith("g.gui.") and name.endswith(".py")
                )
            elif SCRIPT_MAKEFILE.search(makefile):
                match = PGM_VARIABLE.search(makefile)
                if not match:
                    continue
                program = match.group(1)
                for name in (f"{program}.py", f"{program}.sh", program):
                    if name in filenames:
                        files.append(os.path.join(dirpath, name))
                        break
    return files


def po_string(text):
    """Return text as a quoted PO string."""
    escaped = (
        text.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\t", "\\t")
        .replace("\r", "\\r")
    )
    return f'"{escaped}"'


def write_pot(messages, file):
    file.write(
        'msgid ""\n'
        'msgstr ""\n'
        '"MIME-Version: 1.0\\n"\n'
        '"Content-Type: text/plain; charset=UTF-8\\n"\n'
        '"Content-Transfer-Encoding: 8bit\\n"\n'
    )
    for message in messages:
        file.write("\n")
        for comment in message.comments:
            file.write(f"#. {comment}\n")
        file.write(f"#: {' '.join(message.references)}\n")
        if message.context is not None:
            file.write(f"msgctxt {po_string(message.context)}\n")
        file.write(f"msgid {po_string(message.msgid)}\n")
        file.write('msgstr ""\n')


def main(argv=None):
    parser = argparse.ArgumentParser(
        description=(
            "Extract translatable strings from the interface headers of tools"
            " to a gettext template (POT)."
        )
    )
    parser.add_argument(
        "files",
        nargs="*",
        help=(
            "tool source files to read (default: tools found in the source"
            " tree; references use the paths as found)"
        ),
    )
    parser.add_argument(
        "--root",
        default=os.path.relpath(Path(__file__).resolve().parent.parent),
        help="root of the source tree to search for tools (default: %(default)s)",
    )
    parser.add_argument(
        "-o", "--output", help="output POT file (default: standard output)"
    )
    args = parser.parse_args(argv)

    messages = extract(args.files or find_tool_files(args.root))
    if args.output:
        with open(args.output, "w", encoding="utf-8") as file:
            write_pot(messages, file)
    else:
        write_pot(messages, sys.stdout)


if __name__ == "__main__":
    main()
