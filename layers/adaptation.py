"""Adaptation rules and recommendations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

import geopandas as gpd


@dataclass
class AdaptationRule:
    risk_level: str
    exposure_threshold: float
    recommendation: str


class AdaptationEngine:
    """Generate adaptation actions based on risk levels."""

    def __init__(self, rules: List[AdaptationRule]) -> None:
        self._rules: Dict[str, AdaptationRule] = {rule.risk_level: rule for rule in rules}

    def generate(self, risk_map: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        risk_map = risk_map.copy()
        recommendations = []
        for _, row in risk_map.iterrows():
            rule = self._rules.get(row["risk_level"])
            if rule and row["exposure_index"] >= rule.exposure_threshold:
                recommendations.append(rule.recommendation)
            else:
                recommendations.append("Monitor conditions")
        risk_map["recommendation"] = recommendations
        return risk_map


DEFAULT_RULES = [
    AdaptationRule("low", exposure_threshold=0.2, recommendation="Prepare community bulletins"),
    AdaptationRule("medium", exposure_threshold=0.4, recommendation="Activate evacuation shelters"),
    AdaptationRule("high", exposure_threshold=0.5, recommendation="Issue evacuation order"),
]


__all__ = ["AdaptationRule", "AdaptationEngine", "DEFAULT_RULES"]
