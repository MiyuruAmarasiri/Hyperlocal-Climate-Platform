# Hyperlocal Climate-Risk Early-Warning and Adaptation Platform

## Overview
This repository provides an end-to-end prototype of a hyperlocal flood early-warning and adaptation platform. It combines near real-time weather ingestion, hydrologic modelling, risk mapping, authoritative dashboards, and a lightweight progressive web app for community alerts.

## Highlights
- **Data ingestion**: Async pipelines for numerical weather predictions, satellite precipitation tiles (CHIRPS), and MQTT-based community sensors.
- **Hydrologic modelling**: PyTorch LSTM for discharge estimation, virtual gauge calibration, and WRF-Hydro orchestration hooks.
- **Risk intelligence**: GeoPandas + RasterIO utilities to overlay hazard forecasts with exposure layers, plus rule-based adaptation engine.
- **Delivery channels**: FastAPI services, Plotly Dash operations dashboard, and a PWA-ready mobile companion.
- **Security & observability**: API key guard, centralised logging, and environment-driven configuration via `shared.config`.

## Quickstart
1. Create and activate a virtual environment: `python -m venv .venv && .venv\Scripts\Activate.ps1` (PowerShell) or `source .venv/bin/activate` (Unix).
2. Install dependencies: `pip install -r requirements.txt`.
3. Copy `.env.example` to `.env` and populate secrets (weather/satellite API keys, database URLs, MQTT broker credentials, API key list).
4. Launch both API and dashboard with automatic port detection: `python scripts/run_dev_stack.py` (press `Ctrl+C` to stop). The script selects free ports starting at 8000 (API) and 8050 (dashboard) and falls back if those are occupied.
   - Manual start remains supported: `uvicorn api.main:app --reload --port 8000` and `python -m dashboard.app`. If you encounter a “port already in use” error, set `API_PORT`/`DASH_PORT` in your environment or pass `--port` explicitly.
5. Run the mobile PWA backend: `uvicorn mobile_app.main:app --reload --port 8100`.

## Repository layout
```
api/                 FastAPI application, schemas, authentication
ingestion/           Weather, satellite, and sensor ingestion pipelines
models/              Hydrologic LSTM, virtual gauge, training utilities
layers/              Risk map fusion and adaptation rules
hydrology/           WRF-Hydro integration helpers
shared/              Configuration, logging, geospatial helpers
dashboard/           Plotly Dash dashboard UI and callbacks
mobile_app/          Progressive web app server, templates, service worker
scripts/             Automation hooks (placeholders)
configs/             Configuration assets (placeholder)
notebooks/           Exploratory analysis notebooks (placeholder)
tests/               Pytest suite stubs
```

## Data paths
- Raw downloads: `data/raw/`
- Processed datasets: `data/processed/`
- Sensor archives: `data/processed/sensors/`

## Running tests
```
pytest
```

## Roadmap
- Connect to real weather APIs (ECMWF/GFS) with API management and caching.
- Implement true WRF-Hydro job submission and result ingestion.
- Expand risk layers (population, infrastructure, health facilities) from authoritative geospatial sources.
- Harden security posture (JWT, OAuth2, device certificates) and add monitoring/alerting pipelines.

## Web frontend

A Next.js marketing and interaction site lives in `web/`. To run it:

```
cd web
cp .env.local.example .env.local
npm install
npm run dev
```

This will launch the site at http://localhost:3000 and proxy requests to the API defined by `NEXT_PUBLIC_API_BASE` (default http://localhost:8000).

- Use the `web/middleware.ts` zero-trust guard by configuring `ZERO_TRUST_*` variables (SSO header, MDM posture headers, IP allowlists, Turnstile secret, rate limits). Requests failing these checks are blocked before reaching the app or proxy.
