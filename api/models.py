"""Pydantic models for API schema."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional, Tuple

from pydantic import BaseModel, Field


class ForecastRequest(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    horizon_hours: int = Field(48, ge=1, le=168)


class WeatherPoint(BaseModel):
    time: datetime
    temperature_c: float
    precipitation_mm: float
    windspeed_ms: float


class ForecastResponse(BaseModel):
    location: Tuple[float, float]
    hourly: List[WeatherPoint]
    source: str


class RiskMapRequest(BaseModel):
    basin_id: str


class GeoJSONFeature(BaseModel):
    type: str = Field(default="Feature", const=True)
    geometry: dict
    properties: dict


class RiskMapResponse(BaseModel):
    features: List[GeoJSONFeature]
    generated_at: datetime


class SensorMessageIn(BaseModel):
    topic: str
    payload: dict


class HealthResponse(BaseModel):
    status: str
    time: datetime
    services: List[str]


class Recommendation(BaseModel):
    area_id: str
    recommendation: str
    risk_level: str


class AdaptationResponse(BaseModel):
    recommendations: List[Recommendation]
    generated_at: datetime


__all__ = [
    "ForecastRequest",
    "ForecastResponse",
    "WeatherPoint",
    "RiskMapRequest",
    "RiskMapResponse",
    "GeoJSONFeature",
    "SensorMessageIn",
    "HealthResponse",
    "AdaptationResponse",
    "Recommendation",
]
