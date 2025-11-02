"""Common API utilities."""

from __future__ import annotations

from datetime import datetime
from typing import Iterable

import numpy as np
import xarray as xr

from . import models


def dataset_to_forecast_response(dataset: xr.Dataset, latitude: float, longitude: float) -> models.ForecastResponse:
    weather_points = []
    forecast_data = dataset["forecast"].values
    times = dataset.coords["time"].values
    variables = list(dataset.coords["variable"].values)

    for idx, time in enumerate(times):
        entry = {var: float(forecast_data[variables.index(var)][idx]) for var in variables}
        weather_points.append(
            models.WeatherPoint(
                time=np.datetime64(time).astype("datetime64[s]").tolist(),
                temperature_c=entry.get("temperature_2m", 0.0),
                precipitation_mm=entry.get("precipitation", 0.0),
                windspeed_ms=entry.get("windspeed_10m", 0.0),
            )
        )
    return models.ForecastResponse(location=(latitude, longitude), hourly=weather_points, source=str(dataset.attrs.get("source", "unknown")))


def geo_dataframe_to_geojson_features(gdf) -> Iterable[models.GeoJSONFeature]:
    for _, row in gdf.iterrows():
        yield models.GeoJSONFeature(geometry=row.geometry.__geo_interface__, properties=row.drop(labels="geometry").to_dict())


__all__ = ["dataset_to_forecast_response", "geo_dataframe_to_geojson_features"]
