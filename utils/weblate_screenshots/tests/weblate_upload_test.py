"""Tests of weblate_upload.py against a fake Weblate API server.

The responses model Weblate 5.16.2 and 2026.10.1, which do not differ for the
endpoints used.
"""

import io
import json
import re
import sys
import threading
from email.parser import BytesParser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest
from PIL import Image

# The requests package is not a GRASS dependency.
pytest.importorskip("requests")
sys.path.insert(0, str(Path(__file__).parent.parent))

import weblate_upload  # noqa: E402

TOKEN = "secret-token"  # noqa: S105
PAGE_SIZE = 2

UNITS = [
    (1, "", "Layout settings"),
    (2, "", "Cancel"),
    (3, "Menu", "Cancel"),
    (4, "", "Apply"),
]


def multipart_fields(handler):
    """Return the form fields of a multipart request, files as bytes."""
    length = int(handler.headers["Content-Length"])
    message = BytesParser().parsebytes(
        b"Content-Type: "
        + handler.headers["Content-Type"].encode()
        + b"\r\n\r\n"
        + handler.rfile.read(length)
    )
    return {
        part.get_param("name", header="content-disposition"): part.get_payload(
            decode=True
        )
        for part in message.get_payload()
    }


class FakeWeblate(BaseHTTPRequestHandler):
    """Model the responses of the Weblate API for one component."""

    def log_message(self, *args):
        pass

    def reply(self, status, body=None, raw=None):
        payload = raw if raw is not None else json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def paginate(self, items):
        query = self.path.partition("?")[2]
        page = int(query.partition("page=")[2] or 1)
        chunk = items[(page - 1) * PAGE_SIZE : page * PAGE_SIZE]
        base = f"{self.server.url}{self.path.partition('?')[0]}"
        more = page * PAGE_SIZE < len(items)
        self.reply(
            200,
            {
                "count": len(items),
                "next": f"{base}?page={page + 1}" if more else None,
                "previous": None,
                "results": chunk,
            },
        )

    def serialize(self, shot_id):
        shot = self.server.screenshots[shot_id]
        url = self.server.url
        return {
            "id": shot_id,
            "name": shot["name"],
            "translation": f"{url}/api/translations/p/c/{shot['language']}/",
            "file_url": f"{url}/api/screenshots/{shot_id}/file/",
            "units": [f"{url}/api/units/{unit}/" for unit in sorted(shot["units"])],
            "url": f"{url}/api/screenshots/{shot_id}/",
        }

    def handle_request(self, method):
        self.server.requests.append((method, self.path))
        if self.headers["Authorization"] != f"Token {TOKEN}":
            return self.reply(403, {"detail": "Bad token"})
        path = self.path.partition("?")[0]
        shots = self.server.screenshots
        if method == "GET" and path == "/api/components/p/c/":
            return self.reply(200, {"source_language": {"code": "en"}})
        if method == "GET" and path == "/api/components/p/c/screenshots/":
            return self.paginate([self.serialize(shot_id) for shot_id in shots])
        if method == "GET" and path == "/api/translations/p/c/en/units/":
            return self.paginate(
                [
                    {"id": unit_id, "context": context, "source": [source]}
                    for unit_id, context, source in UNITS
                ]
            )
        if method == "POST" and path == "/api/screenshots/":
            fields = multipart_fields(self)
            shot_id = self.server.next_id
            self.server.next_id += 1
            shots[shot_id] = {
                "name": fields["name"].decode(),
                "language": fields["language_code"].decode(),
                "image": fields["image"],
                "units": set(),
            }
            # Like Weblate, the reply does not have the id field.
            body = self.serialize(shot_id)
            del body["id"]
            return self.reply(201, body)
        # Like the Weblate router, require the trailing slash.
        match = re.fullmatch(r"/api/screenshots/(\d+)/(file/|units/(?:(\d+)/)?)?", path)
        if not match or int(match[1]) not in shots:
            return self.reply(404, {"detail": "Not found."})
        shot = shots[int(match[1])]
        if method == "GET" and match[2] == "file/":
            return self.reply(200, raw=shot["image"])
        if method == "POST" and match[2] == "file/":
            shot["image"] = multipart_fields(self)["image"]
            return self.reply(200, {"result": True})
        if method == "POST" and match[2] == "units/":
            length = int(self.headers["Content-Length"])
            form = self.rfile.read(length).decode()
            unit_id = int(form.partition("unit_id=")[2])
            if unit_id not in {unit[0] for unit in UNITS}:
                return self.reply(400, {"unit_id": "Unit not found"})
            shot["units"].add(unit_id)
            return self.reply(200, self.serialize(int(match[1])))
        if method == "DELETE" and match[3]:
            shot["units"].discard(int(match[3]))
            return self.reply(204, raw=b"")
        if method == "DELETE" and match[2] is None:
            del shots[int(match[1])]
            return self.reply(204, raw=b"")
        return self.reply(405, {"detail": "Method not allowed."})

    def do_GET(self):
        self.handle_request("GET")

    def do_POST(self):
        self.handle_request("POST")

    def do_DELETE(self):
        self.handle_request("DELETE")


@pytest.fixture
def weblate():
    server = HTTPServer(("127.0.0.1", 0), FakeWeblate)
    server.url = f"http://127.0.0.1:{server.server_port}"
    server.screenshots = {}
    server.next_id = 10
    server.requests = []
    thread = threading.Thread(target=server.serve_forever)
    thread.start()
    yield server
    server.shutdown()
    server.server_close()
    thread.join()


def png(path, color, size=(8, 6)):
    Image.new("RGB", size, color).save(path)


def write_capture(directory, shots):
    """Write a capture output directory.

    Shots are given as name: (color, [(msgctxt, msgid), ...]).
    """
    directory.mkdir(exist_ok=True)
    entries = []
    for name, (color, strings) in shots.items():
        file = name.replace("/", "__") + ".png"
        png(directory / file, color)
        entries.append(
            {
                "name": name,
                "file": file,
                "strings": [
                    {"msgctxt": context, "msgid": msgid, "kind": "label"}
                    for context, msgid in strings
                ],
                "unmatched": [],
            }
        )
    (directory / "manifest.json").write_text(json.dumps({"screenshots": entries}))


@pytest.fixture
def run(weblate, monkeypatch, tmp_path, capsys):
    """Run the uploader, return its output and the modifying requests."""
    monkeypatch.setenv("WEBLATE_TOKEN", TOKEN)

    def upload(*options):
        weblate.requests.clear()
        argv = [
            "weblate_upload.py",
            "--url",
            weblate.url,
            "--project",
            "p",
            "--component",
            "c",
            "--input",
            str(tmp_path / "shots"),
            *options,
        ]
        monkeypatch.setattr(sys, "argv", argv)
        capsys.readouterr()
        weblate_upload.main()
        changes = [r for r in weblate.requests if r[0] != "GET"]
        return capsys.readouterr(), changes

    return upload


def linked(weblate):
    return {shot["name"]: shot["units"] for shot in weblate.screenshots.values()}


SHOTS = {
    "wxgui/a": ((255, 0, 0), [(None, "Layout settings"), (None, "Cancel")]),
    "wxgui/b": ((0, 255, 0), [("Menu", "Cancel"), (None, "Apply")]),
    "wxgui/c": ((0, 0, 255), [(None, "Apply")]),
}


def test_first_sync_creates_and_links(weblate, run, tmp_path):
    write_capture(tmp_path / "shots", SHOTS)
    output, changes = run()
    assert linked(weblate) == {"wxgui/a": {1, 2}, "wxgui/b": {3, 4}, "wxgui/c": {4}}
    assert {s["language"] for s in weblate.screenshots.values()} == {"en"}
    assert "3 created, 0 updated, 0 unchanged, 0 deleted, 5 links added" in output.out
    assert len(changes) == 3 + 5


def test_second_sync_changes_nothing(weblate, run, tmp_path):
    write_capture(tmp_path / "shots", SHOTS)
    run()
    output, changes = run()
    assert changes == []
    assert "0 created, 0 updated, 3 unchanged, 0 deleted, 0 links added" in output.out


def test_changed_image_is_replaced(weblate, run, tmp_path):
    write_capture(tmp_path / "shots", SHOTS)
    run()
    png(tmp_path / "shots" / "wxgui__a.png", (1, 2, 3))
    # Same pixels as before but a differently encoded file is not a change.
    Image.new("RGB", (8, 6), (0, 255, 0)).save(
        tmp_path / "shots" / "wxgui__b.png", compress_level=0
    )
    output, changes = run()
    assert [m for m, _ in changes] == ["POST"]
    assert changes[0][1].endswith("/file/")
    assert "1 updated, 2 unchanged" in output.out
    stored = Image.open(io.BytesIO(weblate.screenshots[10]["image"]))
    assert stored.getpixel((0, 0)) == (1, 2, 3)


def test_size_change_is_replaced(weblate, run, tmp_path):
    write_capture(tmp_path / "shots", SHOTS)
    run()
    png(tmp_path / "shots" / "wxgui__a.png", (255, 0, 0), size=(9, 6))
    output, changes = run()
    assert len(changes) == 1
    assert "1 updated" in output.out


def test_removed_string_is_unlinked(weblate, run, tmp_path):
    write_capture(tmp_path / "shots", SHOTS)
    run()
    shots = dict(SHOTS)
    shots["wxgui/a"] = ((255, 0, 0), [(None, "Layout settings"), (None, "Apply")])
    write_capture(tmp_path / "shots", shots)
    output, changes = run()
    assert linked(weblate)["wxgui/a"] == {1, 4}
    assert sorted(changes) == [
        ("DELETE", "/api/screenshots/10/units/2/"),
        ("POST", "/api/screenshots/10/units/"),
    ]
    assert "1 links added, 1 links removed" in output.out


def test_prune_deletes_only_managed_stale(weblate, run, tmp_path):
    write_capture(tmp_path / "shots", SHOTS)
    run()
    weblate.screenshots[50] = {
        "name": "manual/other",
        "language": "en",
        "image": b"",
        "units": {1},
    }
    weblate.screenshots[51] = {
        "name": "wxgui/gone",
        "language": "en",
        "image": b"",
        "units": set(),
    }
    shots = {name: shot for name, shot in SHOTS.items() if name != "wxgui/c"}
    write_capture(tmp_path / "shots", shots)

    _output, changes = run()
    assert changes == []
    assert len(weblate.screenshots) == 5

    output, changes = run("--prune")
    assert sorted(changes) == [
        ("DELETE", "/api/screenshots/12/"),
        ("DELETE", "/api/screenshots/51/"),
    ]
    assert set(linked(weblate)) == {"wxgui/a", "wxgui/b", "manual/other"}
    assert linked(weblate)["manual/other"] == {1}
    assert "2 deleted" in output.out


def test_dry_run_changes_nothing(weblate, run, tmp_path):
    write_capture(tmp_path / "shots", SHOTS)
    output, changes = run("--dry-run")
    assert changes == []
    assert weblate.screenshots == {}
    assert "Would create screenshot wxgui/a" in output.out
    assert "3 created" in output.out
    assert "5 links added" in output.out

    run()
    shots = {name: shot for name, shot in SHOTS.items() if name != "wxgui/c"}
    shots["wxgui/a"] = ((1, 2, 3), [(None, "Apply")])
    write_capture(tmp_path / "shots", shots)
    before = {k: dict(v) for k, v in weblate.screenshots.items()}
    output, changes = run("--dry-run", "--prune")
    assert changes == []
    assert weblate.screenshots == before
    assert "Would replace image" in output.out
    assert "Would delete screenshot wxgui/c" in output.out


def test_unknown_string_is_warned(weblate, run, tmp_path):
    shots = {
        "wxgui/a": (
            (255, 0, 0),
            [(None, "Layout settings"), (None, "Not in Weblate"), ("Ctx", "Cancel")],
        )
    }
    write_capture(tmp_path / "shots", shots)
    output, _changes = run()
    assert "'Not in Weblate'" in output.err
    assert "'Ctx'" in output.err
    assert "2 unknown strings" in output.out
    assert linked(weblate) == {"wxgui/a": {1}}


def test_http_error_exits_without_token(weblate, run, tmp_path, monkeypatch):
    write_capture(tmp_path / "shots", SHOTS)
    monkeypatch.setenv("WEBLATE_TOKEN", "wrong-token")
    with pytest.raises(SystemExit) as error:
        run()
    message = str(error.value)
    assert "HTTP 403" in message
    assert "Bad token" in message
    assert "wrong-token" not in message


def test_missing_token_exits(run, tmp_path, monkeypatch):
    write_capture(tmp_path / "shots", SHOTS)
    monkeypatch.delenv("WEBLATE_TOKEN")
    with pytest.raises(SystemExit, match="WEBLATE_TOKEN"):
        run()


def test_name_outside_prefix_exits(weblate, run, tmp_path):
    write_capture(tmp_path / "shots", {"other/a": ((0, 0, 0), [])})
    with pytest.raises(SystemExit, match="does not start with"):
        run()
    assert weblate.requests == []
