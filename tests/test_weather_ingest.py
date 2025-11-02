import asyncio
from datetime import datetime

import numpy as np
import pytest
import xarray as xr

from ingestion import weather_ingest
from shared.config import get_settings


class DummyCDSClient:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def retrieve(self, _dataset, _request, target):
        time = np.array([np.datetime64("2024-01-01T00:00"), np.datetime64("2024-01-01T01:00")])
        lat = np.array([1.0])
        lon = np.array([2.0])
        data = xr.Dataset(
            {
                "t2m": (("time", "latitude", "longitude"), np.full((2, 1, 1), 280.0)),
                "tp": (("time", "latitude", "longitude"), np.full((2, 1, 1), 0.01)),
                "u10": (("time", "latitude", "longitude"), np.full((2, 1, 1), 3.0)),
                "v10": (("time", "latitude", "longitude"), np.full((2, 1, 1), 4.0)),
            },
            coords={"time": time, "latitude": lat, "longitude": lon},
        )
        data.to_netcdf(target)


@pytest.mark.asyncio
async def test_weather_ingestor_ecmwf(monkeypatch, tmp_path):
    monkeypatch.setenv("WEATHER_PROVIDER", "ecmwf")
    monkeypatch.setenv("ECMWF_KEY", "uid:secret")
    monkeypatch.setenv("DATA_ROOT", str(tmp_path))
    monkeypatch.setenv("LOGS_DIR", str(tmp_path / "logs"))
    get_settings.cache_clear()

    monkeypatch.setattr(weather_ingest, "cdsapi", type("CDS", (), {"Client": DummyCDSClient}))

    ingestor = weather_ingest.WeatherIngestor()
    dataset = await ingestor.fetch_forecast(1.0, 2.0)

    assert "temperature_2m" in dataset.coords["variable"].values
    assert dataset.attrs["source"] == "ecmwf-era5"
