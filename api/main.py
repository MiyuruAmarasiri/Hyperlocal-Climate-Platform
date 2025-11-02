"""FastAPI application entrypoint."""

from __future__ import annotations

from datetime import datetime
from typing import List

import geopandas as gpd
from fastapi import Depends, FastAPI
from shapely.geometry import box

from api import models
from api.auth import get_current_client
from api.utils import dataset_to_forecast_response, geo_dataframe_to_geojson_features
from ingestion.weather_ingest import WeatherIngestor
from layers.adaptation import AdaptationEngine, DEFAULT_RULES
from layers.mapping import RiskLayerConfig, build_risk_map
from shared.config import get_settings

app = FastAPI(title="Hyperlocal Climate-Risk API", version="0.1.0")


@app.on_event("startup")
async def on_startup() -> None:
    app.state.settings = get_settings()
    app.state.weather_ingestor = WeatherIngestor()
    app.state.adaptation_engine = AdaptationEngine(DEFAULT_RULES)


@app.on_event("shutdown")
async def on_shutdown() -> None:
    await app.state.weather_ingestor.close()


@app.get("/health", response_model=models.HealthResponse)
async def health() -> models.HealthResponse:
    return models.HealthResponse(status="ok", time=datetime.utcnow(), services=["weather", "risk", "adaptation"])


@app.post("/forecast", response_model=models.ForecastResponse)
async def forecast(request: models.ForecastRequest, client: str = Depends(get_current_client)) -> models.ForecastResponse:
    dataset = await app.state.weather_ingestor.fetch_forecast(request.latitude, request.longitude)
    return dataset_to_forecast_response(dataset, request.latitude, request.longitude)


@app.post("/risk-map", response_model=models.RiskMapResponse)
async def risk_map(request: models.RiskMapRequest, client: str = Depends(get_current_client)) -> models.RiskMapResponse:
    hazard = gpd.GeoDataFrame(
        {
            "flood_probability": [0.3, 0.6, 0.8],
            "geometry": [box(i, i, i + 0.1, i + 0.1) for i in range(3)],
        },
        crs="EPSG:4326",
    )
    vulnerability = [
        gpd.GeoDataFrame(
            {
                "population_density": [100, 450, 1000],
                "geometry": [box(i, i, i + 0.1, i + 0.1) for i in range(3)],
            },
            crs="EPSG:4326",
        )
    ]
    config = RiskLayerConfig(hazard_fields=["flood_probability"], vulnerability_fields=["population_density"])
    risk = build_risk_map(hazard, vulnerability, config)
    features = list(geo_dataframe_to_geojson_features(risk))
    return models.RiskMapResponse(features=features, generated_at=datetime.utcnow())


@app.get("/adaptation", response_model=models.AdaptationResponse)
async def adaptation(basin_id: str, client: str = Depends(get_current_client)) -> models.AdaptationResponse:
    hazard = gpd.GeoDataFrame(
        {
            "flood_probability": [0.2, 0.7, 0.9],
            "geometry": [box(i, i, i + 0.2, i + 0.2) for i in range(3)],
        },
        crs="EPSG:4326",
    )
    vulnerability = [
        gpd.GeoDataFrame(
            {
                "population_density": [200, 500, 800],
                "geometry": [box(i, i, i + 0.2, i + 0.2) for i in range(3)],
            },
            crs="EPSG:4326",
        )
    ]
    config = RiskLayerConfig(hazard_fields=["flood_probability"], vulnerability_fields=["population_density"])
    risk = build_risk_map(hazard, vulnerability, config)
    recommendations_df = app.state.adaptation_engine.generate(risk)
    recommendations: List[models.Recommendation] = [
        models.Recommendation(
            area_id=str(idx),
            recommendation=row["recommendation"],
            risk_level=row["risk_level"],
        )
        for idx, row in recommendations_df.iterrows()
    ]
    return models.AdaptationResponse(recommendations=recommendations, generated_at=datetime.utcnow())


@app.post("/sensor", status_code=202)
async def sensor_ingest(message: models.SensorMessageIn, client: str = Depends(get_current_client)) -> None:
    # Placeholder for streaming message queue logic.
    return None


__all__ = ["app"]
