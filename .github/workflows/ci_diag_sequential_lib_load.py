"""CI diagnostic, not for merge.

Imports every grass.lib.* ctypes submodule one at a time in a single
process, flushing progress after each import, to find exactly how many
(and which) sequential ctypes library loads it takes to reproduce the
"Windows fatal exception: code 0xc0000139" crash seen under
pytest-xdist. A plain `python -c "from grass.pygrass import utils"`
in a single fresh process (see the sibling diagnostic PR) does not
crash, so this checks whether the crash is tied to the number of
distinct DLLs loaded cumulatively within one process.
"""

import faulthandler
import pkgutil

faulthandler.enable()

import grass.lib  # noqa: E402

modules = sorted(m.name for m in pkgutil.iter_modules(grass.lib.__path__))
print(f"Found {len(modules)} grass.lib submodules: {modules}", flush=True)

for i, name in enumerate(modules, 1):
    print(f"[{i}/{len(modules)}] importing grass.lib.{name} ...", flush=True)
    __import__(f"grass.lib.{name}")
    print(f"[{i}/{len(modules)}] OK", flush=True)

print("ALL grass.lib submodules imported successfully", flush=True)
