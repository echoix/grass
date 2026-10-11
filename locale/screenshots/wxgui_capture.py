#!/usr/bin/env python3

"""Capture wxGUI screenshots and the translatable strings they show.

Each scenario opens a part of the GUI, saves a PNG of it, and records which
messages from a gettext template are visible in it. The result is meant to be
uploaded to Weblate as visual context for the strings.

Strings are found without OCR: the translation function is wrapped to learn
which msgid produced each piece of text, and the widget tree of the captured
window is walked to collect the text actually shown.

Run in a GRASS session with a display, e.g., using Xvfb. The screen is read
with ImageMagick's import tool. A fixed project path (rather than a temporary
one) keeps the screenshots identical between runs:

    grass -e -c XY /tmp/grassdata/screenshots
    xvfb-run -s "-screen 0 1600x1200x24" \
        grass /tmp/grassdata/screenshots/PERMANENT --exec \
        python3 locale/screenshots/wxgui_capture.py \
        --pot locale/templates/grasswxpy.pot --output shots

The output directory gets one PNG file per screenshot and manifest.json
listing the messages shown in each of them.
"""

import argparse
import ast
import builtins
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

PLACEHOLDER = re.compile(r"%(?:\([^)]*\))?[-#0 +]*\d*(?:\.\d+)?[sdifgxXr%]|\{[^{}]*\}")


def read_pot(path):
    """Return the set of (msgctxt, msgid) pairs in a gettext template.

    The msgctxt is None for messages without a context.
    """
    entries = set()
    fields = {}
    current = None

    def flush():
        if fields.get("msgid"):
            entries.add((fields.get("msgctxt"), fields["msgid"]))
        fields.clear()

    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        keyword, _sep, value = line.partition(" ")
        if keyword in {"msgctxt", "msgid"}:
            if keyword == "msgctxt" or "msgid" in fields:
                flush()
            current = keyword
            fields[current] = ast.literal_eval(value)
        elif line.startswith('"') and current:
            fields[current] += ast.literal_eval(line)
        else:
            # Comments, plural forms, and msgstr end the msgctxt and msgid.
            current = None
    flush()
    return entries


def normalize(text):
    """Reduce a label to the form used for matching.

    Mnemonic markers, accelerators after a tab, trailing colons and
    ellipses are often added or removed between the msgid and the widget.
    """
    text = text.split("\t", 1)[0]
    text = re.sub(r"&(.)", r"\1", text)
    text = " ".join(text.split())
    return text.rstrip(":").rstrip(".").rstrip("\u2026").strip()


class Recorder:
    """Wrap translation functions to map rendered text back to messages.

    Messages are (msgctxt, msgid) pairs as returned by read_pot().
    """

    def __init__(self, known):
        self.known = known
        self.by_text = {}
        self.patterns = {}

    def wrap(self, namespace, name):
        """Record messages translated by namespace[name](message)."""
        original = namespace[name]

        def translate(message):
            result = original(message)
            self.record((None, message), result)
            return result

        namespace[name] = translate

    def wrap_with_context(self, namespace, name):
        """Record messages translated by namespace[name](context, message)."""
        original = namespace[name]

        def translate(context, message):
            result = original(context, message)
            self.record((context, message), result)
            return result

        namespace[name] = translate

    def record(self, message, result):
        if message not in self.known:
            return
        self.by_text.setdefault(normalize(result), set()).add(message)
        if PLACEHOLDER.search(result) and message not in self.patterns:
            parts = PLACEHOLDER.split(normalize(result))
            if not re.search(r"\w", "".join(parts)):
                # A message made only of placeholders, such as "{name}",
                # would match any text.
                return
            regex = ".+?".join(re.escape(part) for part in parts)
            self.patterns[message] = re.compile(f"^{regex}$", re.DOTALL)

    def lookup(self, text):
        """Return messages which could have produced the text."""
        key = normalize(text)
        if not key:
            return set()
        found = set(self.by_text.get(key, ()))
        if not found:
            found = {
                message for message, regex in self.patterns.items() if regex.match(key)
            }
        return found


def visible_texts(window):
    """Yield (kind, text) for text shown by the window and its children."""
    import wx
    import wx.aui
    import wx.lib.agw.flatnotebook as fnb

    if not window.IsShown():
        return
    if isinstance(window, wx.TopLevelWindow):
        yield "title", window.GetTitle()
        if isinstance(window, wx.Frame) and window.GetMenuBar():
            menubar = window.GetMenuBar()
            for i in range(menubar.GetMenuCount()):
                yield "menu", menubar.GetMenuLabel(i)
        if isinstance(window, wx.Frame) and window.GetStatusBar():
            statusbar = window.GetStatusBar()
            for i in range(statusbar.GetFieldsCount()):
                yield "statusbar", statusbar.GetStatusText(i)
    elif isinstance(window, (wx.Notebook, wx.aui.AuiNotebook, fnb.FlatNotebook)):
        for i in range(window.GetPageCount()):
            yield "tab", window.GetPageText(i)
    elif isinstance(window, wx.ToolBar):
        for i in range(window.GetToolsCount()):
            tool = window.GetToolByPos(i)
            yield "tooltip", tool.GetShortHelp()
            if tool.GetLabel():
                yield "label", tool.GetLabel()
    elif isinstance(window, wx.RadioBox):
        yield "label", window.GetLabel()
        for i in range(window.GetCount()):
            yield "label", window.GetString(i)
    elif isinstance(window, (wx.Choice, wx.ComboBox, wx.ListBox)):
        # Only the selected item of a drop-down list is visible.
        if isinstance(window, wx.ListBox):
            yield from (("label", item) for item in window.GetItems())
        else:
            yield "label", window.GetStringSelection()
    elif isinstance(window, wx.TextCtrl):
        yield "label", window.GetValue()
        yield "label", window.GetHint()
    elif isinstance(window, wx.ListCtrl) and window.InReportView():
        for i in range(window.GetColumnCount()):
            yield "label", window.GetColumn(i).GetText()
    elif isinstance(window, wx.Control):
        yield "label", window.GetLabel()

    tooltip = window.GetToolTipText()
    if tooltip:
        yield "tooltip", tooltip
    for child in window.GetChildren():
        if not isinstance(child, wx.TopLevelWindow):
            yield from visible_texts(child)


def settle(seconds=0.5):
    """Process pending events so that the GUI is fully drawn."""
    import wx

    end = time.monotonic() + seconds
    while time.monotonic() < end:
        wx.GetApp().Yield(onlyIfNeeded=True)
        time.sleep(0.02)


def grab(window, path):
    """Save the on-screen area of a top-level window as a PNG file.

    The screen is read with ImageMagick because wx.ScreenDC returns stale
    content with GTK 3.
    """
    window.Raise()
    settle()
    rect = window.GetScreenRect()
    subprocess.run(
        [
            "import",
            "-window",
            "root",
            "-crop",
            f"{rect.width}x{rect.height}+{rect.x}+{rect.y}",
            "+repage",
            str(path),
        ],
        check=True,
    )


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", normalize(text).lower()).strip("-")


class Capture:
    def __init__(self, recorder, output):
        self.recorder = recorder
        self.output = Path(output)
        self.output.mkdir(parents=True, exist_ok=True)
        self.records = []

    def shoot(self, name, window):
        """Save a screenshot of the window and the messages visible in it."""
        import wx

        # Other top-level windows could cover the captured one.
        hidden = [
            other
            for other in wx.GetTopLevelWindows()
            if other is not window and other.IsShown()
        ]
        for other in hidden:
            other.Hide()
        path = self.output / f"{name.replace('/', '__')}.png"
        grab(window, path)
        for other in hidden:
            other.Show()

        strings = {}
        unmatched = set()
        for kind, text in visible_texts(window):
            if not text.strip():
                continue
            messages = self.recorder.lookup(text)
            if not messages:
                unmatched.add(text)
            for message in messages:
                # Prefer the kind under which the string is visible as text.
                if strings.get(message) != "label":
                    strings[message] = kind
        self.records.append(
            {
                "name": name,
                "file": path.name,
                "strings": [
                    {"msgctxt": context, "msgid": msgid, "kind": kind}
                    for (context, msgid), kind in sorted(
                        strings.items(), key=lambda item: (item[0][0] or "", item[0][1])
                    )
                ],
                "unmatched": sorted(unmatched),
            }
        )
        print(f"{name}: {len(strings)} strings", file=sys.stderr)

    def notebook_pages(self, prefix, window, notebook, names=None):
        """Capture each page of a notebook.

        Screenshot names use the internal page name when available (stable
        across languages), otherwise the page label.
        """
        for index in range(notebook.GetPageCount()):
            notebook.SetSelection(index)
            settle()
            page = names[index] if names else slug(notebook.GetPageText(index))
            self.shoot(f"{prefix}/{page}", window)

    def write_manifest(self):
        manifest = self.output / "manifest.json"
        manifest.write_text(
            json.dumps({"screenshots": self.records}, indent=2, ensure_ascii=False)
            + "\n",
            encoding="utf-8",
        )


def fit_pages(window, notebook):
    """Enlarge the window so that no notebook page needs to scroll.

    Otherwise, strings scrolled out of view would be linked to a screenshot
    which does not show them.
    """
    extra = max(
        notebook.GetPage(index).GetVirtualSize().height
        - notebook.GetPage(index).GetClientSize().height
        for index in range(notebook.GetPageCount())
    )
    if extra > 0:
        width, height = window.GetSize()
        window.SetSize(width, height + extra)
        settle()


def create_layer_manager():
    from lmgr.frame import GMFrame

    frame = GMFrame(parent=None)
    # The frame redirects output to its console, which would hide errors.
    sys.stdout = sys.__stdout__
    sys.stderr = sys.__stderr__
    settle(2)
    return frame


def capture_layer_manager(capture, frame):
    notebook = frame.notebook
    names = {notebook.GetPageIndexByName(name): name for name in notebook.notebookPages}
    capture.notebook_pages("wxgui/layer-manager", frame, notebook, names)


def capture_preferences(capture, frame):
    from gui_core.preferences import PreferencesDialog

    dialog = PreferencesDialog(parent=frame, giface=frame._giface)
    dialog.Show()
    settle()
    fit_pages(dialog, dialog.notebook)
    capture.notebook_pages("wxgui/preferences", dialog, dialog.notebook)
    dialog.Destroy()


# All scenarios get the Layer Manager because other windows need it as parent.
SCENARIOS = {
    "layer-manager": capture_layer_manager,
    "preferences": capture_preferences,
}


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--pot", required=True, help="gettext template to match")
    parser.add_argument("--output", required=True, help="output directory")
    parser.add_argument(
        "--scenario",
        action="append",
        choices=sorted(SCENARIOS),
        help="scenario to capture (default: all)",
    )
    args = parser.parse_args()

    sys.path.insert(0, os.path.join(os.environ["GISBASE"], "gui", "wxpython"))
    import grass  # noqa: F401  Installs the translation function.

    known = read_pot(args.pot)
    recorder = Recorder(known)
    recorder.wrap(builtins.__dict__, "_")
    # Context-aware translation, if the GUI defines it, follows gettext.pgettext().
    if "pgettext" in builtins.__dict__:
        recorder.wrap_with_context(builtins.__dict__, "pgettext")

    import wx
    from core.settings import UserSettings

    # The Layer Manager is the main window only in the multi-window mode.
    UserSettings.Set(
        group="appearance", key="singleWindow", subkey="enabled", value=False
    )

    app = wx.App(False)
    app.locale = wx.Locale(language=wx.LANGUAGE_DEFAULT)
    capture = Capture(recorder, args.output)
    scenarios = args.scenario or sorted(SCENARIOS)

    # Events are processed by settle(), so the main loop is not started.
    # It would return at once anyway because there is no window yet.
    try:
        frame = create_layer_manager()
        for name in scenarios:
            SCENARIOS[name](capture, frame)
        capture.write_manifest()
    finally:
        for window in wx.GetTopLevelWindows():
            window.Destroy()
        settle()


if __name__ == "__main__":
    main()
