# Live Data Integration Plan

## Weather Forecasts (ECMWF/GFS via CDS API)
1. Register for [Copernicus Climate Data Store](https://cds.climate.copernicus.eu) access and generate an API key.
2. Add the key to `.env` (`WEATHER_API_KEY`) and persist the `~/.cdsapirc` file inside `configs/` (avoiding VCS).
3. Extend `ingestion/weather_ingest.py` to switch to ECMWF endpoints when the key is present:
   - Use `cdsapi.Client` to request the `ecmwf` dataset (e.g., `efi_flood` or `seasonal-original-single-levels`).
   - Store results as GRIB or NetCDF in `data/raw/weather/`.
   - Convert to `xarray.Dataset` via `xarray.open_dataset` and publish to the processed store.
4. Implement caching with `diskcache` or `sqlite` to avoid repeated downloads for the same lead time.
5. Add unit tests covering the new path with `pytest` using VCR.py-style fixtures.

## Satellite Precipitation (CHIRPS/IMERG)
1. Request API credentials from [CHC](https://data.chc.ucsb.edu/products/CHIRPS-2.0/) or configure anonymous FTP.
2. Populate `.env` with `SATELLITE_API_KEY` when required; update `SatelliteIngestor` to form authorised requests.
3. For large-area pulls, integrate `aioftp` or `asyncssh` to stream tiles directly into `data/raw/satellite/`.
4. Use `rasterio.merge.merge` to mosaic daily tiles into catchment subsets and promote the outputs into `data/processed/hydro_inputs/`.
5. Register ingestion cron via `Prefect`/`Airflow` triggered after weather fetch completes for temporal alignment.

## Community Sensors (MQTT/LoRa)
1. Stand up an MQTT broker (e.g., Eclipse Mosquitto) with TLS; register credentials in `.env`.
2. Update `SensorMQTTIngestor` to support TLS certificates and QoS=1 delivery; persist raw payloads to `InfluxDB` (Timescale fallback).
3. Implement a background task (FastAPI `BackgroundTasks` or Celery worker) to consume the buffered queue and append to `data/processed/sensors/` parquet files.

## Risk Layer Enrichment
1. Source vulnerability layers:
   - Population: [HRSL](https://data.humdata.org) or [Facebook Data for Good].
   - Infrastructure: OpenStreetMap via `osmnx`; health facilities from WHO datasets.
   - Elevation: SRTM/ALOS using `rio-cogeo` to convert to Cloud-Optimised GeoTIFF.
2. Add download scripts under `scripts/download_layers.py` with CLI arguments for AOI bounding boxes.
3. Harmonise CRS/extent using `shared.geo_utils.harmonise_layers` and persist cleaned layers under `data/processed/exposure/`.
4. Extend `layers.mapping.build_risk_map` config to accept dynamic weightings loaded from YAML (place file in `configs/risk_weights.yaml`).
5. Generate automated QA notebooks inside `notebooks/` to visualise coverage and detect missing geometries.

## Operationalisation
1. Containerise ingestion, API, dashboard, and mobile app; publish images to GHCR/ACR.
2. Provision PostGIS + TimescaleDB (or InfluxDB) and update connection strings in `.env`.
3. Wire observability: expose Prometheus metrics (FastAPI instrumentor), ship logs via Loki; add uptime alerts.
4. Automate deployments with GitHub Actions; include smoke tests invoking `scripts/run_uvicorn_check.py` and `scripts/run_dash_check.py`.
