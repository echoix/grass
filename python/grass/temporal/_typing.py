from __future__ import annotations

from typing import Generic, TypeVar, Union


class RasterT:
    pass


class Raster3DT:
    pass


class VectorT:
    pass


# AnyRasterT = RasterT | Raster3DT
AnyRasterT = Union[RasterT, Raster3DT]
# RTT = TypeVar("RTT", AnyRasterT)
RTT = TypeVar("RTT", RasterT, Raster3DT)
# RTT = TypeVar("RTT", bound=AnyRasterT)
# TT = TypeVar("TT", RasterT, Raster3DT, VectorT)
# TT = TypeVar("TT", bound=AnyRasterT | VectorT)
# TT = TypeVar("TT", RTT, VectorT)
TT = TypeVar("TT", AnyRasterT, VectorT)


class SpaceTimeT(Generic[TT]):
    pass


STT = TypeVar("STT", bound=SpaceTimeT)
# AnyTTST = Union[TT, STT]
# AnyTTST = TypeVar("AnyTTST", bound=TT|STT)
# AnyTTST = TypeVar("AnyTTST", bound=Union[TT, STT])
AnyTTST2 = TypeVar(
    "AnyTTST2",
    RasterT,
    Raster3DT,
    VectorT,
    SpaceTimeT[RasterT],
    SpaceTimeT[Raster3DT],
    SpaceTimeT[VectorT],
)
# AnyTTST = TypeVar("AnyTTST", RasterT, Raster3DT, VectorT, SpaceTimeT)
AnyTTST = TypeVar("AnyTTST", AnyRasterT, VectorT, SpaceTimeT)
