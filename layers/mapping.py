"""Risk mapping utilities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List

import geopandas as gpd
import pandas as pd

from shared.geo_utils import compute_exposure_score, harmonise_layers


@dataclass
class RiskLayerConfig:
    hazard_fields: List[str]
    vulnerability_fields: List[str]


def build_risk_map(
    hazard_layer: gpd.GeoDataFrame,
    vulnerability_layers: Iterable[gpd.GeoDataFrame],
    config: RiskLayerConfig,
) -> gpd.GeoDataFrame:
    """Combine hazard and vulnerability layers into a scored risk map."""

    required_fields = config.hazard_fields + ["geometry"]
    merged = harmonise_layers(hazard_layer[required_fields], vulnerability_layers)
    scored = compute_exposure_score(merged, weight_fields=config.vulnerability_fields)
    scored["risk_level"] = pd.qcut(scored["exposure_index"], q=3, labels=["low", "medium", "high"])
    return scored


__all__ = ["RiskLayerConfig", "build_risk_map"]
