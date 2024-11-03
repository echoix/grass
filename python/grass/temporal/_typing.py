from __future__ import annotations

from typing import Generic, TypeVar


class AnyRasterT:
    pass


class RasterT(AnyRasterT):
    pass


class Raster3DT(AnyRasterT):
    pass


class VectorT:
    pass


# class RasterT:
#     pass


# class Raster3DT:
#     pass


# AnyRasterT = RasterT | Raster3DT
# AnyRasterT = Union[RasterT, Raster3DT]
# RTT = TypeVar("RTT", AnyRasterT)
# RTT = TypeVar("RTT", bound=AnyRasterT)
RTT = TypeVar("RTT", bound=AnyRasterT)
# RTT = TypeVar("RTT", bound=AnyRasterT, contravariant=True)
# RTT = TypeVar("RTT", bound=AnyRasterT, covariant=True)
# RTT = TypeVar("RTT", RasterT, Raster3DT)
# RTT = TypeVar("RTT", bound=AnyRasterT)
# TT = TypeVar("TT", RasterT, Raster3DT, VectorT)
# TT = TypeVar("TT", bound=AnyRasterT | VectorT)
# TT = TypeVar("TT", RTT, VectorT)
# TT = TypeVar("TT", AnyRasterT, RasterT, Raster3DT, VectorT, covariant=True)
TT = TypeVar("TT", AnyRasterT, RasterT, Raster3DT, VectorT)
# TT = TypeVar("TT", AnyRasterT, RasterT, Raster3DT, VectorT, contravariant=True)
# TT = TypeVar("TT", AnyRasterT, RasterT, Raster3DT, VectorT)
# TT = TypeVar("TT", RasterT, Raster3DT, VectorT)
# TT = TypeVar("TT", AnyRasterT, VectorT)
# TT = TypeVar("TT", AnyRasterT, VectorT, contravariant=True)
# TT = TypeVar("TT", AnyRasterT, VectorT, covariant=True)


class SpaceTimeT(Generic[TT]):
    pass


class AnySpaceTimeT(SpaceTimeT[TT], Generic[TT]):
    pass

# class AnySpaceTimeT(SpaceTimeT[TT]):
#     pass


SpaceTimeTT = SpaceTimeT[TT]
STT2 = TypeVar("STT2", bound=SpaceTimeTT)
STT = TypeVar("STT", bound=SpaceTimeT)
STT3 = TypeVar("STT3", bound=AnySpaceTimeT)
# STT = TypeVar("STT", bound=SpaceTimeT, contravariant=True)
# STT = TypeVar("STT", bound=SpaceTimeT, covariant=True)
# SpaceTimeTT = SpaceTimeT[TT]
# STT = TypeVar("STT", bound=SpaceTimeTT)
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
AnyTTST = TypeVar("AnyTTST", AnyRasterT, RasterT, Raster3DT, VectorT, SpaceTimeT)
AnyTTST3 = TypeVar(
    "AnyTTST3",
    AnyRasterT,
    RasterT,
    Raster3DT,
    VectorT,
    SpaceTimeT,
    SpaceTimeT[AnyRasterT],
    SpaceTimeT[RasterT],
    SpaceTimeT[Raster3DT],
    SpaceTimeT[VectorT],
)
AnyTTST4 = TypeVar(
    "AnyTTST4",
    AnyRasterT,
    RasterT,
    Raster3DT,
    VectorT,
    AnySpaceTimeT,
    SpaceTimeT,
    SpaceTimeT[AnyRasterT],
    SpaceTimeT[RasterT],
    SpaceTimeT[Raster3DT],
    SpaceTimeT[VectorT],
)
# AnyTTST = TypeVar(
#     "AnyTTST",
#     AnyRasterT,
#     RasterT,
#     Raster3DT,
#     VectorT,
#     SpaceTimeT[AnyRasterT],
#     SpaceTimeT[RasterT],
#     SpaceTimeT[Raster3DT],
#     SpaceTimeT[VectorT],
# )
# AnyTTST = TypeVar("AnyTTST", AnyRasterT, RasterT, Raster3DT, VectorT, SpaceTimeT)
# AnyTTST = TypeVar("AnyTTST", AnyRasterT, RasterT, Raster3DT, VectorT, SpaceTimeTT)
# AnyTTST = TypeVar("AnyTTST", AnyRasterT, RasterT, Raster3DT, VectorT, SpaceTimeT,
#  SpaceTimeTT)
# AnyTTST = TypeVar("AnyTTST", RasterT, Raster3DT, VectorT, SpaceTimeT)
# AnyTTST = TypeVar("AnyTTST",RasterT,Raster3DT,VectorT,SpaceTimeT, contravariant=True)
# AnyTTST = TypeVar("AnyTTST", AnyRasterT, VectorT, SpaceTimeT, contravariant=True)
# AnyTTST = TypeVar("AnyTTST", AnyRasterT, VectorT, SpaceTimeT, covariant=True)
# AnyTTST = TypeVar("AnyTTST", AnyRasterT, VectorT, SpaceTimeT)
