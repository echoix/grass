"""Build a tiny OSGeo4W mirror for the real setup.exe from the real packages.

The published setup.ini lists every package with its dependencies. To run
setup.exe unattended against a local server without fetching the dependency
closure, this writes a setup.ini containing only the requested packages (no
requires:, source: or previous versions) and downloads the real package files,
so the md5 sums from the real setup.ini stay valid.
"""

import bz2
import os
import sys
import urllib.request

BASE = "https://download.osgeo.org/osgeo4w/v2/"
out = sys.argv[1]
names = sys.argv[2:]

with urllib.request.urlopen(BASE + "x86_64/setup.ini.bz2") as resp:
    text = bz2.decompress(resp.read()).decode("utf-8", "replace")

blocks = text.split("\n@ ")
ini = ["arch: x86_64", "setup-timestamp: 1", ""]
wanted = {}
for block in blocks[1:]:
    lines = block.splitlines()
    name = lines[0].strip()
    if name not in names:
        continue
    kept = [f"@ {name}"]
    for line in lines[1:]:
        if line.startswith("["):
            break
        if line.startswith(("requires:", "source:")):
            continue
        kept.append(line)
        if line.startswith("install:"):
            wanted[name] = line.split()[1]
    ini += kept + [""]

for name in names:
    path = wanted[name]
    dest = os.path.join(out, path)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    print(f"{name}: {path}", flush=True)
    urllib.request.urlretrieve(BASE + path, dest)

data = "\n".join(ini).encode()
ini_dir = os.path.join(out, "x86_64")
os.makedirs(ini_dir, exist_ok=True)
with open(os.path.join(ini_dir, "setup.ini"), "wb") as f:
    f.write(data)
with open(os.path.join(ini_dir, "setup.ini.bz2"), "wb") as f:
    f.write(bz2.compress(data))
