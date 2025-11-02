"""Geospatial helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, List, Optional

import geopandas as gpd
import numpy as np
import rasterio
from rasterio.features import rasterize
from shapely.geometry import mapping


def load_vector_layer(path: Path | str, target_crs: Optional[str] = None) -> gpd.GeoDataFrame:
    """Load a vector dataset and optionally reproject to ``target_crs``."""

    gdf = gpd.read_file(path)
    if target_crs:
        gdf = gdf.to_crs(target_crs)
    return gdf


def load_raster(path: Path | str) -> rasterio.io.DatasetReader:
    """Open a raster data source for downstream processing."""

    return rasterio.open(path)


def harmonise_layers(
    hazard_layer: gpd.GeoDataFrame,
    vulnerability_layers: Iterable[gpd.GeoDataFrame],
    how: str = "intersection",
) -> gpd.GeoDataFrame:
    """Overlay hazard forecasts with vulnerability layers to compute exposure."""

    merged = hazard_layer
    for layer in vulnerability_layers:
        merged = gpd.overlay(merged, layer, how=how)
    return merged


def rasterise_layer(layer: gpd.GeoDataFrame, template: rasterio.io.DatasetReader) -> np.ndarray:
    """Rasterise a vector layer into the template grid."""

    shapes = ((mapping(geom), 1) for geom in layer.geometry)
    return rasterize(shapes=shapes, out_shape=template.shape, transform=template.transform)


def compute_exposure_score(merged_layer: gpd.GeoDataFrame, weight_fields: List[str]) -> gpd.GeoDataFrame:
    """Compute an exposure index using the weighted sum of provided fields."""

    df = merged_layer.copy()
    weights = np.linspace(1, len(weight_fields), num=len(weight_fields))
    total = 0.0
    for weight, field in zip(weights, weight_fields):
        total += weight * df[field].fillna(0)
    df["exposure_index"] = total / weights.sum()
    return df


__all__ = [
    "load_vector_layer",
    "load_raster",
    "harmonise_layers",
    "rasterise_layer",
    "compute_exposure_score",
]
