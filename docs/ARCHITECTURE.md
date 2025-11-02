# Architecture Overview

## Data Flow
1. **Ingestion services** pull NWP forecasts, satellite precipitation (CHIRPS), and IoT sensor streams.
2. **Hydrologic modelling** orchestrates WRF-Hydro runs while the PyTorch LSTM / virtual gauge produces discharge estimates from sparse observations.
3. **Risk analytics** leverage GeoPandas + RasterIO to merge hazard outputs with socio-economic vulnerability layers, generating exposure scores.
4. **Delivery surfaces** expose insights through FastAPI endpoints, an operations dashboard (Dash), and a community-facing PWA.

## Module Contracts
- `ingestion.weather_ingest.WeatherIngestor`: async fetch to xarray dataset, persisted to `data/processed/weather_forecasts.nc`.
- `models.hydrologic_lstm.HydrologicLSTM`: streamflow predictor trained via `models.train_utils`.
- `layers.mapping.build_risk_map`: merges hazard/vulnerability layers into scored GeoDataFrame with `risk_level` and `exposure_index` columns.
- `layers.adaptation.AdaptationEngine`: transforms risk map into actionable recommendations.
- `api.main.app`: orchestrates dependencies, enforces API-key guard, exposes `/forecast`, `/risk-map`, `/adaptation`, `/sensor` routes.
- `dashboard.app.create_dash_app`: Plotly Dash UI hitting API endpoints for rainfall plots, risk choropleths, and adaptation summaries.
- `mobile_app.create_mobile_app`: FastAPI-based PWA providing offline-capable community experience.

## Deployment Considerations
- Containerise API, dashboard, and mobile PWA as discrete services behind an API gateway with TLS termination.
- Schedule ingestion via async workers (Celery/Prefect) and persist to time-series (InfluxDB/TimescaleDB) plus spatial DB (PostGIS).
- Integrate with observability stack (Prometheus, Loki/Grafana) for health metrics and log aggregation.
- Harden MQTT brokers with TLS client certificates and segregated topics per community cluster.
