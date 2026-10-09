"""Download a few real OSGeo4W packages to benchmark the setup extraction."""

import bz2
import os
import sys
import urllib.request

BASE = "https://download.osgeo.org/osgeo4w/v2/"
OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)

with urllib.request.urlopen(BASE + "x86_64/setup.ini.bz2") as resp:
    text = bz2.decompress(resp.read()).decode("utf-8", "replace")

packages = {}
for block in text.split("\n@ ")[1:]:
    lines = block.splitlines()
    name = lines[0].strip()
    for line in lines[1:]:
        if line.startswith("["):
            break
        if line.startswith("install:"):
            _, path, size = line.split()[:3]
            if path.endswith(".tar.bz2"):
                packages[name] = (path, int(size))
            break

chosen = {}
if "python3-core" in packages:
    chosen["python3-core"] = packages["python3-core"]
limit = 200 * 1024 * 1024
candidates = [
    (size, name)
    for name, (path, size) in packages.items()
    if size <= limit and not name.endswith(("-debug", "-src"))
]
for size, name in sorted(candidates, reverse=True)[:1]:
    chosen[name] = packages[name]

for name, (path, size) in chosen.items():
    dest = os.path.join(OUT, os.path.basename(path))
    print(f"{name}: {path} ({size / 1e6:.1f} MB)", flush=True)
    urllib.request.urlretrieve(BASE + path, dest)
