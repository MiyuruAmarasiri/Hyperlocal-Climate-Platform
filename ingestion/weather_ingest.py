"""Weather forecast ingestion pipeline."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
import tempfile
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

import httpx
import numpy as np
import xarray as xr

try:
    import cdsapi
except ImportError:  # pragma: no cover - optional dependency for ECMWF
    cdsapi = None

from shared.config import get_settings

log = logging.getLogger(__name__)


class WeatherIngestor:
    """Ingest weather forecasts from external APIs into xarray datasets."""

    def __init__(
        self,
        base_url: str = "https://api.open-meteo.com/v1/forecast",
        variables: Optional[List[str]] = None,
        storage_path: Optional[Path] = None,
        http_client: Optional[httpx.AsyncClient] = None,
    ) -> None:
        self.base_url = base_url
        self.variables = variables or ["temperature_2m", "precipitation", "windspeed_10m"]
        settings = get_settings()
        self.storage_path = storage_path or (settings.data_root / "processed" / "weather_forecasts.nc")
        self.client = http_client or httpx.AsyncClient(timeout=30)
        self._lock = asyncio.Lock()
        self.settings = settings

    async def fetch_forecast(self, lat: float, lon: float) -> xr.Dataset:
        """Fetch forecast for a single point, returning a dataset."""

        if self.settings.weather_provider.lower() == "ecmwf" and self.settings.ecmwf_key:
            if cdsapi is None:
                log.error("cdsapi package not installed; falling back to Open-Meteo provider")
            else:
                return await self._fetch_ecmwf(lat, lon)

        return await self._fetch_open_meteo(lat, lon)

    async def _fetch_open_meteo(self, lat: float, lon: float) -> xr.Dataset:
        """Retrieve forecast data from the Open-Meteo public API."""

        params = {
            "latitude": lat,
            "longitude": lon,
            "hourly": ",".join(self.variables),
        }
        try:
            response = await self.client.get(self.base_url, params=params)
            response.raise_for_status()
            payload = response.json()
            dataset = self._dataset_from_payload(payload)
        except httpx.HTTPError as exc:
            log.warning("Weather API failed (%s), generating synthetic fallback", exc)
            dataset = self._synthetic_dataset(lat, lon)
        dataset.attrs.update({"lat": lat, "lon": lon})
        return dataset

    async def _fetch_ecmwf(self, lat: float, lon: float) -> xr.Dataset:
        """Retrieve a localised ECMWF dataset via CDS API."""

        request_payload = self._build_ecmwf_request(lat, lon)
        tmp_dir = Path(tempfile.mkdtemp())
        target = tmp_dir / f"ecmwf-{lat:.3f}-{lon:.3f}.nc"

        def _download() -> Path:
            client = cdsapi.Client(
                url=self.settings.ecmwf_url,
                key=self.settings.ecmwf_key,
                progress=False,
                verify=False,
            )
            client.retrieve(
                "reanalysis-era5-single-levels",
                request_payload,
                str(target),
            )
            return target

        try:
            path = await asyncio.to_thread(_download)
            raw_dataset = xr.open_dataset(path)
            dataset = self._ecmwf_to_dataset(raw_dataset)
            dataset.attrs.update({"source": "ecmwf-era5", "lat": lat, "lon": lon})
            return dataset
        except Exception as exc:  # pragma: no cover - requires network
            log.error("ECMWF retrieval failed (%s); generating synthetic data", exc)
            return self._synthetic_dataset(lat, lon)
        finally:
            try:
                if target.exists():
                    target.unlink()
                tmp_dir.rmdir()
            except OSError:
                pass

    def _build_ecmwf_request(self, lat: float, lon: float) -> dict:
        """Construct ECMWF request payload for ERA5 single-level variables."""

        now = datetime.utcnow()
        hours = [f"{hour:02d}" for hour in range(0, 24)]
        return {
            "product_type": "reanalysis",
            "variable": ["2m_temperature", "total_precipitation", "10m_u_component_of_wind"],
            "year": f"{now.year}",
            "month": f"{now.month:02d}",
            "day": f"{now.day:02d}",
            "time": hours,
            "area": self._point_to_area(lat, lon),
            "format": "netcdf",
        }

    @staticmethod
    def _point_to_area(lat: float, lon: float, delta: float = 0.1) -> List[float]:
        """Convert a point to an ECMWF bounding box [N, W, S, E]."""

        north = min(90.0, lat + delta)
        south = max(-90.0, lat - delta)
        east = lon + delta
        west = lon - delta
        return [north, west, south, east]

    def _ecmwf_to_dataset(self, raw_dataset: xr.Dataset) -> xr.Dataset:
        """Transform ERA5 dataset to the internal forecast schema."""

        rename_map = {
            "t2m": "temperature_2m",
            "total_precipitation": "precipitation",
            "tp": "precipitation",
            "u10": "u_component_10m",
            "v10": "v_component_10m",
        }

        data_rows: List[np.ndarray] = []
        variable_labels: List[str] = []
        vector_components: dict[str, np.ndarray] = {}

        if "time" not in raw_dataset.coords:
            return self._synthetic_dataset(0.0, 0.0)

        time_coord = raw_dataset["time"].values
        dims_to_reduce = [dim for dim in raw_dataset.dims if dim not in ("time",)]

        for original, target in rename_map.items():
            if original not in raw_dataset:
                continue
            arr = raw_dataset[original]
            reduced = arr
            for dim in dims_to_reduce:
                if dim in reduced.dims:
                    reduced = reduced.mean(dim=dim)
            values = reduced.values.astype(float)
            if target == "temperature_2m":
                values = values - 273.15  # Kelvin to Celsius
            if target in {"u_component_10m", "v_component_10m"}:
                vector_components[target] = values
                continue
            variable_labels.append(target)
            data_rows.append(values)

        if vector_components.get("u_component_10m") is not None and vector_components.get("v_component_10m") is not None:
            speed = np.sqrt(vector_components["u_component_10m"] ** 2 + vector_components["v_component_10m"] ** 2)
            variable_labels.append("windspeed_10m")
            data_rows.append(speed)

        if not data_rows:
            lat_coord = raw_dataset.coords["latitude"] if "latitude" in raw_dataset.coords else xr.DataArray([0])
            lon_coord = raw_dataset.coords["longitude"] if "longitude" in raw_dataset.coords else xr.DataArray([0])
            lat = float(lat_coord.mean())
            lon = float(lon_coord.mean())
            return self._synthetic_dataset(lat, lon)

        data_array = np.vstack(data_rows)
        dataset = xr.Dataset({"forecast": (("variable", "time"), data_array)}, coords={"variable": variable_labels, "time": time_coord})
        return dataset

    async def ingest_many(self, points: Iterable[tuple[float, float]]) -> xr.Dataset:
        """Fetch forecasts for multiple locations and merge into a single dataset."""

        datasets = await asyncio.gather(*(self.fetch_forecast(lat, lon) for lat, lon in points))
        combined = xr.concat(datasets, dim="location")
        combined = combined.assign_coords(location=list(range(len(datasets))))
        async with self._lock:
            combined.to_netcdf(self.storage_path)
        return combined

    def _dataset_from_payload(self, payload: dict) -> xr.Dataset:
        hourly = payload.get("hourly", {})
        time = hourly.get("time") or []
        coords = {
            "time": np.array([np.datetime64(t) for t in time]),
            "variable": np.array(self.variables),
        }
        data = [hourly.get(var, [np.nan] * len(time)) for var in self.variables]
        array = np.vstack(data)
        dataset = xr.Dataset({"forecast": (("variable", "time"), array)}, coords=coords)
        dataset.attrs.update({"source": payload.get("timezone", "open-meteo"), "generated_at": datetime.utcnow().isoformat()})
        return dataset

    def _synthetic_dataset(self, lat: float, lon: float) -> xr.Dataset:
        base_time = datetime.utcnow()
        times = np.array([np.datetime64(base_time + timedelta(hours=i)) for i in range(48)])
        coords = {"time": times, "variable": np.array(self.variables)}
        wave = np.sin(np.linspace(0, np.pi, num=times.size))
        data = np.vstack([
            20 + 5 * wave,
            np.clip(wave, 0, 1),
            3 + 2 * wave,
        ])
        dataset = xr.Dataset({"forecast": (("variable", "time"), data)}, coords=coords)
        dataset.attrs.update({"source": "synthetic", "lat": lat, "lon": lon})
        return dataset

    async def close(self) -> None:
        await self.client.aclose()


async def main(points: Iterable[tuple[float, float]]) -> None:
    ingestor = WeatherIngestor()
    await ingestor.ingest_many(points)
    await ingestor.close()


if __name__ == "__main__":
    asyncio.run(main(points=[(37.7749, -122.4194)]))
