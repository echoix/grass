"""Download real OSGeo4W packages to benchmark the setup extraction.

Package size says little about extraction cost: a few huge files (debug
symbols) are cheap per byte, while many small files (Python packages, JupyterLab
assets, development trees) are dominated by per-file work. Both kinds are used.
"""

import bz2
import os
import sys
import urllib.request

BASE = "https://download.osgeo.org/osgeo4w/v2/"
OUT = sys.argv[1]

WANTED = [
    "python3-jupyterlab",  # small download, very many small files
    "python3-notebook",  # small download, many small files
    "python3-core",  # Python standard library
    "grass-dev",  # development build with many files
    "qgis-ltr-pdb",  # control: large download, few huge files
]

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
            packages[name] = (path, int(size))
            break

for name in WANTED:
    path, size = packages[name]
    dest = os.path.join(OUT, os.path.basename(path))
    print(f"{name}: {path} ({size / 1e6:.1f} MB)", flush=True)
    urllib.request.urlretrieve(BASE + path, dest)
