# Copyright (C) 2026 by the GRASS Development Team
# SPDX-License-Identifier: GPL-2.0-or-later

"""Checks of the WKB buffers of pygrass vector, run in a GRASS session

This is run by ``grass_pygrass_vector_wkb_test.py`` in a subprocess with
the name of a check as the argument. A subprocess is used because the C
libraries can be initialized only once per process, and because a crash
(heap corruption) then fails one test instead of ending the test run.

Exit status 0 means success, ``NOT_SUPPORTED`` means that the check cannot
run on this platform and anything else is a failure.
"""

import ctypes
import sys

from grass.pygrass import utils
from grass.pygrass.vector import VectorTopo, geometry
from grass.pygrass.vector.geometry import Area, Line

NOT_SUPPORTED = 77
MAP_NAME = "wkb_test_vector"
# Sizes in bytes of the WKB of the areas of the test vector map
AREA_WKB_SIZES = [225, 141, 93, 141]


class Mallinfo2(ctypes.Structure):
    """struct mallinfo2 of glibc"""

    _fields_ = [
        (name, ctypes.c_size_t)
        for name in (
            "arena",
            "ordblks",
            "smblks",
            "hblks",
            "hblkhd",
            "usmblks",
            "fsmblks",
            "uordblks",
            "fordblks",
            "keepcost",
        )
    ]


def bytes_in_use():
    """Return the number of bytes allocated with malloc and not freed"""
    try:
        mallinfo2 = ctypes.CDLL(None).mallinfo2
    except (AttributeError, OSError):
        print("mallinfo2 of glibc is not available")
        sys.exit(NOT_SUPPORTED)
    mallinfo2.restype = Mallinfo2
    return mallinfo2().uordblks


def open_test_map():
    """Create the test vector map and open it for reading"""
    utils.create_test_vector_map(MAP_NAME)
    vector = VectorTopo(MAP_NAME)
    vector.open("r")
    return vector


class FreeSpy:
    """Record the calls of G_free() of the GRASS library, which are forwarded"""

    def __init__(self):
        self.calls = []

    def __enter__(self):
        self._original = geometry.libgis.G_free

        def spy(pointer):
            self.calls.append(ctypes.cast(pointer, ctypes.c_void_p).value)
            self._original(pointer)

        geometry.libgis.G_free = spy
        return self

    def __exit__(self, *args):
        geometry.libgis.G_free = self._original


def line():
    """Return a line which needs a WKB buffer of 41 bytes"""
    return Line([(0, 0), (1, 1)])


def check_line_wkb_is_freed():
    """The buffer of Line.to_wkb() is released with G_free()"""
    a_line = line()
    with FreeSpy() as spy:
        wkb = a_line.to_wkb()
    assert len(wkb) == 41, len(wkb)
    assert len(spy.calls) == 1, f"G_free() was called {len(spy.calls)} times"
    assert spy.calls[0], "G_free() was called with NULL"


def check_area_wkb_is_freed():
    """The buffer of Area.to_wkb() is released with G_free()"""
    vector = open_test_map()
    with FreeSpy() as spy:
        wkb = Area(v_id=1, c_mapinfo=vector.c_mapinfo).to_wkb()
    vector.close()
    assert len(wkb) == AREA_WKB_SIZES[0], len(wkb)
    assert len(spy.calls) == 1, f"G_free() was called {len(spy.calls)} times"
    assert spy.calls[0], "G_free() was called with NULL"


def check_wkb_lists_are_freed():
    """Each buffer of the functions returning a list is released with G_free()"""
    vector = open_test_map()
    with FreeSpy() as spy:
        areas = vector.areas_to_wkb_list()
        features = vector.features_to_wkb_list(feature_type="point")
    vector.close()
    assert [len(wkb) for _, _, wkb in areas] == AREA_WKB_SIZES
    assert len(features) == 3, len(features)
    expected = len(areas) + len(features)
    assert len(spy.calls) == expected, f"{len(spy.calls)} calls, not {expected}"


def check_no_memory_growth():
    """Calling the functions many times does not leave memory allocated"""
    vector = open_test_map()
    area = Area(v_id=1, c_mapinfo=vector.c_mapinfo)
    a_line = line()
    for _ in range(1000):
        a_line.to_wkb()
        area.to_wkb()
    before = bytes_in_use()
    calls = 20000
    for _ in range(calls):
        a_line.to_wkb()
        area.to_wkb()
    growth = bytes_in_use() - before
    vector.close()
    # One leaked buffer per call would be at least 21 bytes + 225 bytes
    assert growth < 200_000, f"{growth} bytes more in use after {calls} calls"


def check_all_functions_work_repeatedly():
    """The functions return WKB and survive many calls

    Releasing a buffer with the wrong allocator crashes the process on
    Windows, which would fail this check.
    """
    vector = open_test_map()
    area = Area(v_id=1, c_mapinfo=vector.c_mapinfo)
    a_line = line()
    for _ in range(500):
        wkb = a_line.to_wkb()
        assert wkb[0] in (0, 1)
        assert len(wkb) == 41
        wkb = area.to_wkb()
        assert wkb[0] in (0, 1)
        assert len(wkb) == AREA_WKB_SIZES[0]
        areas = vector.areas_to_wkb_list()
        assert [len(wkb) for _, _, wkb in areas] == AREA_WKB_SIZES
        assert len(vector.features_to_wkb_list(feature_type="point")) == 3
    vector.close()


def main():
    """Run the check named by the first argument"""
    name = sys.argv[1]
    globals()[f"check_{name}"]()


if __name__ == "__main__":
    main()
