"""
Created on Wed Jul 18 10:49:26 2012

@author: pietro
"""

from typing import Literal, TypedDict
import grass.lib.vector as libvect
from enum import Enum, IntEnum


MAPTYPE = {
    libvect.GV_FORMAT_NATIVE: "native",
    libvect.GV_FORMAT_OGR: "OGR",
    libvect.GV_FORMAT_OGR_DIRECT: "OGR",
    libvect.GV_FORMAT_POSTGIS: "PostGIS",
}


class VectorPrimitives(IntEnum):
    GV_POINT = libvect.GV_POINT  # 1
    GV_LINE = libvect.GV_LINE  # 2
    GV_BOUNDARY = libvect.GV_BOUNDARY  # 3
    GV_CENTROID = libvect.GV_CENTROID  # 4
    GV_FACE = libvect.GV_FACE  # 5
    GV_KERNEL = libvect.GV_KERNEL  # 6
    GV_AREA = libvect.GV_AREA  # 7
    GV_VOLUME = libvect.GV_VOLUME  # 8


class VectorPrimitives2(Enum):
    GV_POINT = libvect.GV_POINT  # 1
    GV_LINE = libvect.GV_LINE  # 2
    GV_BOUNDARY = libvect.GV_BOUNDARY  # 3
    GV_CENTROID = libvect.GV_CENTROID  # 4
    GV_FACE = libvect.GV_FACE  # 5
    GV_KERNEL = libvect.GV_KERNEL  # 6
    GV_AREA = libvect.GV_AREA  # 7
    GV_VOLUME = libvect.GV_VOLUME  # 8


class VectorType(TypedDict):
    # point: libvect.GV_POINT
    # point: Literal[1]
    # point: Literal[libvect.GV_POINT]
    point: Literal[VectorPrimitives.GV_POINT]
    line: Literal[VectorPrimitives.GV_LINE]
    boundary: Literal[VectorPrimitives.GV_BOUNDARY]
    centroid: Literal[VectorPrimitives.GV_CENTROID]
    face: Literal[VectorPrimitives.GV_FACE]
    kernel: Literal[VectorPrimitives.GV_KERNEL]
    area: Literal[VectorPrimitives.GV_AREA]
    volume: Literal[VectorPrimitives.GV_VOLUME]


# class VectorType(TypedDict):
#     # point: libvect.GV_POINT
#     point: Literal[1]
#     # point: Literal[libvect.GV_POINT]
#     # line: Literal[VectorPrimitives.GV_LINE]
#     line: Literal[VectorPrimitives.GV_LINE]
#     boundary: int
#     centroid: int
#     face: int
#     kernel: int
#     area: int
#     volume: Literal[VectorPrimitives.GV_VOLUME]


VTYPE: VectorType = {
    "point": VectorPrimitives.GV_POINT,  # 1
    "line": VectorPrimitives.GV_LINE,  # 2
    "boundary": VectorPrimitives.GV_BOUNDARY,  # 3
    "centroid": VectorPrimitives.GV_CENTROID,  # 4
    "face": VectorPrimitives.GV_FACE,  # 5
    "kernel": VectorPrimitives.GV_KERNEL,  # 6
    "area": VectorPrimitives.GV_AREA,  # 7
    "volume": VectorPrimitives.GV_VOLUME,  # 8
}

VTYPE2 = {
    "point": libvect.GV_POINT,  # 1
    "line": libvect.GV_LINE,  # 2
    "boundary": libvect.GV_BOUNDARY,  # 3
    "centroid": libvect.GV_CENTROID,  # 4
    "face": libvect.GV_FACE,  # 5
    "kernel": libvect.GV_KERNEL,  # 6
    "area": libvect.GV_AREA,  # 7
    "volume": libvect.GV_VOLUME,  # 8
}
