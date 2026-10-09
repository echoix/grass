"""Build a local OSGeo4W mirror for the real setup.exe from the real packages.

The mirror serves the unmodified published setup.ini (dependencies included),
and only the package files that installing the requested packages needs: the
requested packages and everything they require, so setup.exe resolves and
installs dependencies itself, as in a real installation. The md5 sums of the
real setup.ini stay valid because the real package files are served.

Also writes closures.json: for every requested package, the names of all
packages (itself included) that installing it extracts.
"""

import bz2
import json
import os
import sys
import urllib.request

BASE = "https://download.osgeo.org/osgeo4w/v2/"
out = sys.argv[1]
targets = sys.argv[2:]

with urllib.request.urlopen(BASE + "x86_64/setup.ini.bz2") as resp:
    ini_bz2 = resp.read()
text = bz2.decompress(ini_bz2).decode("utf-8", "replace")

packages = {}
for block in text.split("\n@ ")[1:]:
    lines = block.splitlines()
    name = lines[0].strip()
    requires, install = [], None
    for line in lines[1:]:
        if line.startswith("["):
            break
        if line.startswith("requires:"):
            requires = line.split()[1:]
        elif line.startswith("install:"):
            install = line.split()[1]
    packages[name] = (requires, install)


def closure(name, seen):
    if name in seen:
        return
    seen.append(name)
    for dep in packages[name][0]:
        closure(dep, seen)


closures = {}
needed = []
for target in targets:
    seen = []
    closure(target, seen)
    closures[target] = seen
    for name in seen:
        if name not in needed:
            needed.append(name)

for name in needed:
    path = packages[name][1]
    if not path:
        continue
    dest = os.path.join(out, path)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    urllib.request.urlretrieve(BASE + path, dest)
print(f"{len(needed)} packages downloaded for {len(targets)} targets", flush=True)
for target in targets:
    print(f"  {target}: {len(closures[target])} packages", flush=True)

ini_dir = os.path.join(out, "x86_64")
os.makedirs(ini_dir, exist_ok=True)
with open(os.path.join(ini_dir, "setup.ini"), "wb") as f:
    f.write(text.encode())
with open(os.path.join(ini_dir, "setup.ini.bz2"), "wb") as f:
    f.write(ini_bz2)
with open(os.path.join(out, "closures.json"), "w") as f:
    json.dump(closures, f)
