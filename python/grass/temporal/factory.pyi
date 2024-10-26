from typing import Literal, overload

from .space_time_datasets import (
    Raster3DDataset,
    RasterDataset,
    SpaceTimeRaster3DDataset,
    SpaceTimeRasterDataset,
    SpaceTimeVectorDataset,
    VectorDataset,
)

@overload
def dataset_factory(type: Literal["strds"], id: str) -> SpaceTimeRasterDataset: ...
@overload
def dataset_factory(type: Literal["str3ds"], id: str) -> SpaceTimeRaster3DDataset: ...
@overload
def dataset_factory(type: Literal["stvds"], id: str) -> SpaceTimeVectorDataset: ...
@overload
def dataset_factory(type: Literal["rast", "raster"], id: str) -> RasterDataset: ...
@overload
def dataset_factory(
    type: Literal["raster_3d", "rast3d", "raster3d"],
    id: str,
) -> Raster3DDataset: ...
@overload
def dataset_factory(type: Literal["vect", "vector"], id: str) -> VectorDataset: ...
