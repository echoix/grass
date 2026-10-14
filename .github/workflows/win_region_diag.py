"""Diagnostic for the Windows-only region problem (not meant for merging).

Prints what the C library sees after a variable is set from Python.
"""

import ctypes
import os
import sys
import traceback


def step(title):
    print("\n=== " + title, flush=True)


def safe(title, func):
    step(title)
    try:
        func()
    except Exception:
        traceback.print_exc()
        sys.stdout.flush()


import numpy  # noqa: E402

import grass.script as gs  # noqa: E402
from grass.gunittest.case import TestCase  # noqa: E402
from grass.pygrass.gis.region import Region  # noqa: E402

print("python", sys.version, sys.executable)
print("numpy", numpy.__version__)
print("GISRC", os.environ.get("GISRC"))


def show(label):
    r = Region()
    print(f"{label}: rows={r.rows} cols={r.cols} nsres={r.nsres} ewres={r.ewres}")


def region_default():
    show("default region")


def region_after_env():
    TestCase.use_temp_region()
    print("WIND_OVERRIDE in os.environ:", os.environ.get("WIND_OVERRIDE"))
    gs.run_command("g.region", n=40, s=0, e=40, w=0, res=10)
    out = gs.read_command("g.region", flags="p")
    print("g.region -p (subprocess) says:\n" + out)
    show("Region() after use_temp_region + g.region n=40 s=0 e=40 w=0 res=10")


def crt_view():
    for dll in ("ucrtbase", "msvcrt"):
        try:
            lib = ctypes.CDLL(dll)
            lib.getenv.restype = ctypes.c_char_p
            print(dll, "getenv(WIND_OVERRIDE) =", lib.getenv(b"WIND_OVERRIDE"))
        except OSError as err:
            print(dll, "not loadable:", err)


def imports():
    import glob

    import pefile

    root = os.environ["GISBASE"]
    cands = glob.glob(os.path.join(root, "**", "*grass_gis*.dll"), recursive=True)
    cands += glob.glob(os.path.join(root, "**", "*grass_raster*.dll"), recursive=True)
    cands += [os.path.join(os.path.dirname(sys.executable), "python3*.dll")]
    for pattern in cands:
        for path in glob.glob(pattern):
            pe = pefile.PE(path, fast_load=True)
            pe.parse_data_directories(
                directories=[pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_IMPORT"]]
            )
            names = sorted(
                {e.dll.decode().lower() for e in getattr(pe, "DIRECTORY_ENTRY_IMPORT", [])}
            )
            crt = [n for n in names if "crt" in n or n.startswith("api-ms-win-crt")]
            print(os.path.basename(path), "->", crt)


def other_crts():
    name = os.environ.get("WIND_OVERRIDE")
    for dll in ("ucrtbase", "msvcrt"):
        try:
            lib = ctypes.CDLL(dll)
        except OSError:
            continue
        lib._putenv(b"WIND_OVERRIDE=")
        show(f"after {dll}._putenv(WIND_OVERRIDE=) (cleared)")
        lib._putenv(f"WIND_OVERRIDE={name}".encode())
        show(f"after {dll}._putenv(WIND_OVERRIDE=name)")


def grass_region_var():
    os.environ.pop("WIND_OVERRIDE", None)
    os.environ["GRASS_REGION"] = gs.region_env(n=40, s=0, e=40, w=0, res=10)
    show("os.environ GRASS_REGION set (no WIND_OVERRIDE)")
    os.environ.pop("GRASS_REGION")


safe("1. default region", region_default)
safe("2. region after os.environ WIND_OVERRIDE", region_after_env)
safe("3. what each C runtime sees", crt_view)
safe("4. C runtimes imported by the DLLs", imports)
safe("5. setting the variable through each C runtime", other_crts)
safe("6. GRASS_REGION set in os.environ", grass_region_var)
