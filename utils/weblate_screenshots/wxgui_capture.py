#!/usr/bin/env python3

"""Capture wxGUI screenshots and the translatable strings they show.

Each scenario opens a part of the GUI, saves a PNG of it, and records which
messages from a gettext template are visible in it. The result is meant to be
uploaded to Weblate as visual context for the strings.

Strings are found without OCR: the translation function is wrapped to learn
which msgid produced each piece of text, and the widget tree of the captured
window is walked to collect the text actually drawn (no tooltips, nothing
hidden or scrolled out of view).

Run in a GRASS session with a display, e.g., using Xvfb. The screen is read
with ImageMagick's import tool. A fixed project path (rather than a temporary
one) keeps the screenshots identical between runs:

    grass -e -c XY /tmp/grassdata/screenshots
    xvfb-run -s "-screen 0 1600x1200x24" \
        grass /tmp/grassdata/screenshots/PERMANENT --exec \
        python3 utils/weblate_screenshots/wxgui_capture.py \
        --pot locale/templates/grasswxpy.pot --output shots

Tooltips are not drawn, so each tool of icon-only toolbars gets a copy of
the screenshot with the tool framed, linked to its tooltip. The tool tree is
captured with each category expanded in turn, page by page.

The output directory gets one PNG file per screenshot and manifest.json
listing the messages shown in each of them, with their source locations
(file:line) from the template as Weblate shows them. Screenshots of a
framed tool also give the screenshot they are based on and the frame.
"""

import argparse
import ast
import builtins
import io
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

# ImageMagick's tool which reads the screen.
IMPORT = shutil.which("import")
PLACEHOLDER = re.compile(r"%(?:\([^)]*\))?[-#0 +]*\d*(?:\.\d+)?[sdifgxXr%]|\{[^{}]*\}")


def read_pot(path):
    """Return a map of (msgctxt, msgid) pairs to their source locations.

    The msgctxt is None for messages without a context. The locations are the
    file:line references of the template, as Weblate shows them.
    """
    entries = {}
    fields = {}
    locations = []
    current = None

    def flush():
        if fields.get("msgid"):
            entries[fields.get("msgctxt"), fields["msgid"]] = list(locations)
        fields.clear()
        locations.clear()

    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        keyword, _sep, value = line.partition(" ")
        if not line:
            flush()
            current = None
        elif keyword == "#:":
            locations.extend(value.split())
        elif keyword in {"msgctxt", "msgid"}:
            if "msgid" in fields:
                flush()
            current = keyword
            fields[current] = ast.literal_eval(value)
        elif line.startswith('"') and current:
            fields[current] += ast.literal_eval(line)
        else:
            # Other comments, plural forms, and msgstr end the msgctxt and msgid.
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

    Messages are (msgctxt, msgid) pairs, the keys of the map returned by
    read_pot().
    """

    def __init__(self, known):
        self.known = known
        self.by_exact_text = {}
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
        self.by_exact_text.setdefault(result, set()).add(message)
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
        """Return messages which could have produced the text.

        An exact match wins over a normalized one, so that, e.g., a "&File"
        menu does not also match a "File" label elsewhere. Text made of parts
        separated by several spaces, such as "Color tables   [r.colors]" in
        the tool tree, is otherwise looked up part by part.
        """
        if text in self.by_exact_text:
            return set(self.by_exact_text[text])
        key = normalize(text)
        if not key:
            return set()
        found = set(self.by_text.get(key, ()))
        if not found:
            found = {
                message for message, regex in self.patterns.items() if regex.match(key)
            }
        if not found:
            parts = re.split(r"\s{2,}", text.strip())
            if len(parts) > 1:
                found = set().union(*(self.lookup(part) for part in parts))
        return found


def visible_texts(window, clip=None):
    """Yield (kind, text) for text drawn by the window and its children.

    Only text drawn on screen is collected: tooltips, labels of icon-only
    toolbar tools, and widgets hidden or scrolled out of view by their
    parents are left out. The clip is the visible screen area of the parent.
    """
    import wx
    import wx.aui
    from core.globalvar import FN
    from gui_core.wrap import CustomTreeCtrl

    if not window.IsShownOnScreen():
        return
    rect = window.GetScreenRect()
    if clip is not None:
        rect = rect.Intersect(clip)
        if rect.IsEmpty():
            return
    if isinstance(window, wx.Frame):
        # The title is drawn by the window manager, not in the screenshot.
        if window.GetMenuBar():
            menubar = window.GetMenuBar()
            for i in range(menubar.GetMenuCount()):
                yield "menu", menubar.GetMenuLabel(i)
        if window.GetStatusBar():
            statusbar = window.GetStatusBar()
            for i in range(statusbar.GetFieldsCount()):
                yield "statusbar", statusbar.GetStatusText(i)
    elif isinstance(window, FN.FlatNotebook):
        if hasattr(window, "GetAGWWindowStyleFlag"):
            style = window.GetAGWWindowStyleFlag()
        else:
            style = window.GetWindowStyleFlag()
        single = style & FN.FNB_HIDE_ON_SINGLE_TAB and window.GetPageCount() == 1
        if not (style & FN.FNB_HIDE_TABS or single):
            for i in range(window.GetPageCount()):
                yield "tab", window.GetPageText(i)
    elif isinstance(window, (wx.Notebook, wx.aui.AuiNotebook)):
        for i in range(window.GetPageCount()):
            yield "tab", window.GetPageText(i)
    elif isinstance(window, wx.ToolBar):
        if window.HasFlag(wx.TB_TEXT):
            for i in range(window.GetToolsCount()):
                yield "label", window.GetToolByPos(i).GetLabel()
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
        # The hint is drawn only while the field is empty.
        yield "label", window.GetValue() or window.GetHint()
    elif isinstance(window, (wx.TreeCtrl, CustomTreeCtrl)):
        yield from (("label", text) for text in tree_texts(window))
    elif isinstance(window, wx.ListCtrl) and window.InReportView():
        for i in range(window.GetColumnCount()):
            yield "label", window.GetColumn(i).GetText()
    elif isinstance(window, wx.Control):
        yield "label", window.GetLabel()

    if isinstance(window, wx.TopLevelWindow):
        # The screenshot covers the whole window, including bars outside
        # its client area.
        client = rect
    else:
        client = wx.Rect(window.ClientToScreen(wx.Point(0, 0)), window.GetClientSize())
        client = client.Intersect(rect)
    for child in window.GetChildren():
        if not isinstance(child, wx.TopLevelWindow):
            yield from visible_texts(child, client)


def item_in_view(tree, item):
    """Tell if a tree item is entirely in view, not cut at the top or bottom."""
    if not tree.IsVisible(item):
        return False
    rect = tree.GetBoundingRect(item)
    return rect is not None and 0 <= rect.GetTop() <= rect.GetBottom() < (
        tree.GetClientSize().height
    )


def tree_texts(tree, item=None):
    """Yield the text of the tree items entirely in view."""

    def valid(item):
        # CustomTreeCtrl gives None where wx.TreeCtrl gives an invalid item.
        return item is not None and item.IsOk()

    if item is None:
        item = tree.GetRootItem()
        if not valid(item):
            return
    if item_in_view(tree, item):
        yield tree.GetItemText(item)
    # A hidden root item is always expanded.
    if item == tree.GetRootItem() or tree.IsExpanded(item):
        child, cookie = tree.GetFirstChild(item)
        while valid(child):
            yield from tree_texts(tree, child)
            child, cookie = tree.GetNextChild(item, cookie)


def settle(seconds=0.5):
    """Process pending events so that the GUI is fully drawn."""
    import wx

    end = time.monotonic() + seconds
    while time.monotonic() < end:
        wx.GetApp().Yield(onlyIfNeeded=True)
        time.sleep(0.02)


def read_screen(rect):
    """Return the PNG data of a screen rectangle.

    The screen is read with ImageMagick because wx.ScreenDC returns stale
    content with GTK 3.
    """
    return subprocess.run(
        [
            IMPORT,
            "-window",
            "root",
            "-crop",
            f"{rect.width}x{rect.height}+{rect.x}+{rect.y}",
            "+repage",
            "png:-",
        ],
        capture_output=True,
        check=True,
    ).stdout


def grab(window, path, target=None):
    """Save the on-screen area of a window, or of a part of it, as a PNG file.

    The window is the top-level window to raise, and the target the widget
    to capture, by default the whole window.
    """
    window.Raise()
    settle()
    Path(path).write_bytes(read_screen((target or window).GetScreenRect()))


def icon_toolbars(window):
    """Yield the shown toolbars in the window which draw no tool labels."""
    import wx
    from wx.lib.agw import aui

    for child in window.GetChildren():
        if not child.IsShownOnScreen() or isinstance(child, wx.TopLevelWindow):
            continue
        if isinstance(child, wx.ToolBar):
            if not child.HasFlag(wx.TB_TEXT):
                yield child
        elif isinstance(child, aui.AuiToolBar):
            if not child.GetAGWWindowStyleFlag() & aui.AUI_TB_TEXT:
                yield child
        else:
            yield from icon_toolbars(child)


def tool_rects(toolbar):
    """Yield (tool, screen rectangle) for the tools of a toolbar.

    wx.ToolBar does not give the position of its tools with GTK, so each
    tool is found by toggling its enabled state, which redraws its icon,
    and comparing the toolbar before and after.
    """
    import wx
    from PIL import Image, ImageChops
    from wx.lib.agw import aui

    if isinstance(toolbar, aui.AuiToolBar):
        for index in range(toolbar.GetToolCount()):
            tool = toolbar.FindToolByIndex(index)
            if tool.GetKind() not in {wx.ITEM_NORMAL, wx.ITEM_CHECK, wx.ITEM_RADIO}:
                continue
            rect = toolbar.GetToolRect(tool.GetId())
            # Tools in the overflow menu have no rectangle.
            if not rect.IsEmpty():
                position = toolbar.ClientToScreen(rect.GetPosition())
                yield tool, wx.Rect(position, rect.GetSize())
        return

    rect = toolbar.GetScreenRect()

    def image():
        return Image.open(io.BytesIO(read_screen(rect))).convert("RGB")

    before = image()
    for index in range(toolbar.GetToolsCount()):
        tool = toolbar.GetToolByPos(index)
        if tool.IsSeparator() or tool.IsControl():
            continue
        enabled = toolbar.GetToolEnabled(tool.GetId())
        toolbar.EnableTool(tool.GetId(), not enabled)
        settle(0.2)
        changed = ImageChops.difference(before, image()).getbbox()
        toolbar.EnableTool(tool.GetId(), enabled)
        settle(0.2)
        if changed:
            # Frame the whole height of the toolbar, with a small margin.
            left = max(changed[0] - 3, 0)
            right = min(changed[2] + 3, rect.width)
            yield tool, wx.Rect(rect.x + left, rect.y, right - left, rect.height)


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", normalize(text).lower()).strip("-")


class Capture:
    def __init__(self, recorder, output):
        self.recorder = recorder
        self.output = Path(output)
        self.output.mkdir(parents=True, exist_ok=True)
        self.records = []
        # Sets of messages of the tools already highlighted, so that tools
        # shown in several screenshots are highlighted only once.
        self.highlighted = set()

    def shoot(self, name, window, target=None, texts=None):
        """Save a screenshot of the window and the messages visible in it.

        The target is the widget to capture, by default the whole window.
        The texts, (kind, text) pairs, restrict the strings to link to those
        shown, by default all text drawn in the target.
        Each tool of icon-only toolbars gets its own copy of the screenshot,
        with the tool highlighted and linked to its tooltip.
        """
        import wx

        target = target or window
        # Other top-level windows could cover the captured one.
        hidden = [
            other
            for other in wx.GetTopLevelWindows()
            if other is not window and other.IsShown()
        ]
        for other in hidden:
            other.Hide()
        path = self.output / f"{name.replace('/', '__')}.png"
        grab(window, path, target)
        for other in hidden:
            other.Show()

        strings = {}
        unmatched = set()
        if texts is None:
            texts = visible_texts(target)
        for kind, text in texts:
            if not text.strip():
                continue
            messages = self.recorder.lookup(text)
            if not messages:
                unmatched.add(text)
            for message in messages:
                strings.setdefault(message, kind)
        self.add_record(name, path, strings, sorted(unmatched))
        self.highlight_tools(name, target, path)

    def add_record(self, name, path, strings, unmatched, **extra):
        """Add a screenshot and its strings, a map of messages to kinds."""
        self.records.append(
            {
                "name": name,
                "file": path.name,
                **extra,
                "strings": [
                    {
                        "msgctxt": context,
                        "msgid": msgid,
                        "kind": kind,
                        "locations": self.recorder.known[context, msgid],
                    }
                    for (context, msgid), kind in sorted(
                        strings.items(), key=lambda item: (item[0][0] or "", item[0][1])
                    )
                ],
                "unmatched": unmatched,
            }
        )
        print(f"{name}: {len(strings)} strings", file=sys.stderr)

    def highlight_tools(self, name, target, path):
        """Save a copy of the screenshot per tool of icon-only toolbars.

        Each copy has the tool framed and is linked to its tooltip and
        description, which are not drawn in the screenshot.
        """
        from PIL import Image, ImageDraw

        origin = target.GetScreenPosition()
        for toolbar in icon_toolbars(target):
            for tool, rect in tool_rects(toolbar):
                strings = {}
                for text in (tool.GetShortHelp(), tool.GetLongHelp()):
                    for message in self.recorder.lookup(text) if text.strip() else ():
                        strings.setdefault(message, "tool")
                if not strings or frozenset(strings) in self.highlighted:
                    continue
                self.highlighted.add(frozenset(strings))
                box = (rect.x - origin.x, rect.y - origin.y, rect.width, rect.height)
                image = Image.open(path).convert("RGB")
                ImageDraw.Draw(image).rectangle(
                    (box[0], box[1], box[0] + box[2] - 1, box[1] + box[3] - 1),
                    outline=(255, 0, 0),
                    width=3,
                )
                base = f"{name}/tool/{slug(min(msgid for _ctxt, msgid in strings))}"
                tool_name = base
                # Different tools can share a message, e.g., the same tooltip.
                number = 1
                while any(record["name"] == tool_name for record in self.records):
                    number += 1
                    tool_name = f"{base}-{number}"
                tool_path = self.output / f"{tool_name.replace('/', '__')}.png"
                image.save(tool_path)
                self.add_record(
                    tool_name,
                    tool_path,
                    strings,
                    [],
                    base=name,
                    highlight=list(box),
                )

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


def tree_children(tree, item):
    """Yield the children of a CustomTreeCtrl item."""
    child, cookie = tree.GetFirstChild(item)
    while child is not None:
        yield child
        child, cookie = tree.GetNextChild(item, cookie)


def expand_all(tree, item):
    """Expand a CustomTreeCtrl item and its descendants.

    Each item is expanded before its children are listed, because virtual
    trees, such as the tool tree, create the children when expanding.
    """
    tree.Expand(item)
    for child in tree_children(tree, item):
        expand_all(tree, child)


def tree_descendants(tree, item):
    """Yield a CustomTreeCtrl item and its descendants, in display order."""
    yield item
    for child in tree_children(tree, item):
        yield from tree_descendants(tree, child)


def capture_tool_tree(capture, frame):
    """Capture each category of the tool tree, expanded, page by page.

    The window is made taller so that fewer pages are needed. Only the tree
    is captured, as the rest of the window is in the Layer Manager scenario.
    """
    from gui_core.wrap import CustomTreeCtrl

    frame.notebook.SetSelectionByName("search")
    settle()
    tree = next(
        widget
        for widget in descendants(frame.notebook.GetCurrentPage())
        if isinstance(widget, CustomTreeCtrl)
    )
    width, height = frame.GetSize()
    frame.SetSize(width, 1100)
    settle()
    unit = tree.GetScrollPixelsPerUnit()[1]
    for category in list(tree_children(tree, tree.GetRootItem())):
        expand_all(tree, category)
        settle()
        items = list(tree_descendants(tree, category))
        prefix = f"wxgui/tool-tree/{slug(tree.GetItemText(category))}"
        first = 0
        page = 1
        while first < len(items):
            # Scroll the first item not captured yet to the top.
            tree.Scroll(-1, items[first].GetY() // unit)
            settle()
            shown = [i for i, item in enumerate(items) if item_in_view(tree, item)]
            # Other categories are linked to the screenshot of the tree
            # with all of them collapsed, not to every page.
            texts = [("label", tree.GetItemText(items[i])) for i in shown]
            capture.shoot(f"{prefix}/{page}", frame, target=tree, texts=texts)
            if not shown or shown[-1] < first:
                break
            first = shown[-1] + 1
            page += 1
        tree.Collapse(category)
    tree.Scroll(-1, 0)
    frame.SetSize(width, height)
    settle()


def descendants(window):
    """Yield the child widgets of a window, recursively."""
    for child in window.GetChildren():
        yield child
        yield from descendants(child)


# All scenarios get the Layer Manager because other windows need it as parent.
SCENARIOS = {
    "layer-manager": capture_layer_manager,
    "preferences": capture_preferences,
    "tool-tree": capture_tool_tree,
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

    if not IMPORT:
        sys.exit("The import tool of ImageMagick is required to read the screen.")

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
