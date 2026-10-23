#!/usr/bin/env python3

"""Synchronize screenshots captured by wxgui_capture.py to Weblate.

The PNG files in the capture output directory are uploaded to a Weblate
component as screenshots of its source language, so that they are shown with
the strings for all languages. The strings listed in manifest.json are linked
to the screenshots. Only the requests which change something are sent: a
screenshot is created when missing, its image is replaced when the pixels
differ, and its links to strings are added or removed to match the manifest.

Only the screenshots with a name starting with the managed prefix are modified
or deleted, so screenshots uploaded by hand are left alone. Only REST API
endpoints available in both Weblate 5.16.2 and 2026.10.1 are used. Create an
API token in the Weblate user profile and pass it in the environment (not as
an argument, to keep it out of process lists and logs):

    export WEBLATE_TOKEN=wlu_...
    python3 utils/weblate_screenshots/weblate_upload.py \
        --url https://weblate.osgeo.org --project grass-gis \
        --component <component> --input shots --dry-run

Strings which are not (yet) in Weblate, for example because it has not
updated the template, are reported as warnings and not linked.
"""

import argparse
import io
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import quote

import requests
from PIL import Image

TIMEOUT = 60


class Weblate:
    """Minimal client of the Weblate REST API."""

    def __init__(self, url, token, dry_run=False):
        self.base = url.rstrip("/") + "/api/"
        self.dry_run = dry_run
        self.session = requests.Session()
        self.session.headers["Authorization"] = f"Token {token}"

    def request(self, method, url, data=None, image=None):
        """Send a request and return the response, exit on an HTTP error."""
        files = (
            {"image": (image.name, image.read_bytes(), "image/png")} if image else None
        )
        url = url if url.startswith("http") else self.base + url
        try:
            response = self.session.request(
                method, url, data=data, files=files, timeout=TIMEOUT
            )
        except requests.RequestException as error:
            sys.exit(f"{method} {url} failed: {error}")
        if not response.ok:
            sys.exit(
                f"{method} {url} failed with HTTP {response.status_code}: "
                f"{response.text[:300]}"
            )
        return response

    def get_json(self, url):
        return self.request("GET", url).json()

    def get_pages(self, url):
        """Yield the results of a paginated list, following the next links."""
        while url:
            page = self.get_json(url)
            yield from page["results"]
            url = page["next"]

    def change(self, description, method, url, **kwargs):
        """Report a modifying request and send it unless in a dry run."""
        print(f"{'Would ' if self.dry_run else ''}{description}")
        if self.dry_run:
            return None
        return self.request(method, url, **kwargs)


def object_id(url):
    """Return the numeric ID at the end of an API object URL."""
    return int(re.search(r"/(\d+)/?$", url).group(1))


def same_pixels(old, new):
    """Tell if two images (as bytes) have the same size and pixels."""
    try:
        old_image = Image.open(io.BytesIO(old)).convert("RGBA")
    except OSError:
        return False
    new_image = Image.open(io.BytesIO(new)).convert("RGBA")
    return (
        old_image.size == new_image.size and old_image.tobytes() == new_image.tobytes()
    )


def read_units(api, project, component):
    """Return a map of (context, msgid) to the unit ID in the source language.

    Weblate gives an empty context for a message without msgctxt.
    """
    base = f"{quote(project, safe='')}/{quote(component, safe='')}/"
    language = api.get_json(f"components/{base}")["source_language"]["code"]
    units = {}
    for unit in api.get_pages(f"translations/{base}{quote(language, safe='')}/units/"):
        # The source is a list of the plural forms, the first one is the msgid.
        units[unit["context"], unit["source"][0]] = unit["id"]
    return language, units


def sync_screenshot(api, entry, input_dir, existing, units, args, language, stats):
    name = entry["name"]
    path = input_dir / entry["file"]
    wanted = set()
    for string in entry["strings"]:
        unit_id = units.get((string["msgctxt"] or "", string["msgid"]))
        if unit_id is None:
            context = f" (context {string['msgctxt']!r})" if string["msgctxt"] else ""
            print(
                f"Warning: {name}: string not in Weblate: {string['msgid']!r}{context}",
                file=sys.stderr,
            )
            stats["unknown strings"] += 1
        else:
            wanted.add(unit_id)

    shot = existing.get(name)
    if shot is None:
        response = api.change(
            f"create screenshot {name}",
            "POST",
            "screenshots/",
            data={
                "name": name,
                "project_slug": args.project,
                "component_slug": args.component,
                "language_code": language,
            },
            image=path,
        )
        stats["created"] += 1
        # The response of the creation has no id field, only URLs.
        shot_id = object_id(response.json()["url"]) if response else None
        current = set()
    else:
        shot_id = shot["id"]
        old = api.request("GET", shot["file_url"]).content
        if same_pixels(old, path.read_bytes()):
            stats["unchanged"] += 1
        else:
            api.change(
                f"replace image of screenshot {name}",
                "POST",
                f"screenshots/{shot_id}/file/",
                image=path,
            )
            stats["updated"] += 1
        current = {object_id(url) for url in shot["units"]}

    for unit_id in sorted(wanted - current):
        api.change(
            f"link unit {unit_id} to screenshot {name}",
            "POST",
            f"screenshots/{shot_id}/units/",
            data={"unit_id": unit_id},
        )
        stats["links added"] += 1
    for unit_id in sorted(current - wanted):
        api.change(
            f"unlink unit {unit_id} from screenshot {name}",
            "DELETE",
            f"screenshots/{shot_id}/units/{unit_id}/",
        )
        stats["links removed"] += 1


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--url", required=True, help="Weblate base URL")
    parser.add_argument("--project", required=True, help="project slug")
    parser.add_argument("--component", required=True, help="component slug")
    parser.add_argument("--input", required=True, help="wxgui_capture.py output")
    parser.add_argument(
        "--prefix",
        default="wxgui/",
        help="prefix of the names of managed screenshots (default: %(default)s)",
    )
    parser.add_argument(
        "--prune",
        action="store_true",
        help="delete managed screenshots which are not in the manifest",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="only print the planned changes"
    )
    args = parser.parse_args()

    token = os.environ.get("WEBLATE_TOKEN")
    if not token:
        sys.exit("Set the API token in the WEBLATE_TOKEN environment variable.")
    input_dir = Path(args.input)
    manifest = json.loads((input_dir / "manifest.json").read_text(encoding="utf-8"))
    for entry in manifest["screenshots"]:
        if not entry["name"].startswith(args.prefix):
            sys.exit(
                f"Screenshot {entry['name']!r} does not start with {args.prefix!r}."
            )

    api = Weblate(args.url, token, args.dry_run)
    project = quote(args.project, safe="")
    component = quote(args.component, safe="")
    language, units = read_units(api, args.project, args.component)
    existing = {}
    for shot in api.get_pages(f"components/{project}/{component}/screenshots/"):
        if shot["name"].startswith(args.prefix):
            existing.setdefault(shot["name"], shot)

    stats = Counter()
    for entry in manifest["screenshots"]:
        sync_screenshot(api, entry, input_dir, existing, units, args, language, stats)
    if args.prune:
        names = {entry["name"] for entry in manifest["screenshots"]}
        for name, shot in existing.items():
            if name not in names:
                api.change(
                    f"delete screenshot {name}", "DELETE", f"screenshots/{shot['id']}/"
                )
                stats["deleted"] += 1

    print(
        ("Dry run: " if args.dry_run else "")
        + ", ".join(
            f"{stats[key]} {key}"
            for key in (
                "created",
                "updated",
                "unchanged",
                "deleted",
                "links added",
                "links removed",
                "unknown strings",
            )
        )
    )


if __name__ == "__main__":
    main()
