"""Virtual gauge algorithms using remote sensing."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
import xarray as xr


@dataclass
class GaugeCalibration:
    slope: float
    intercept: float
    last_updated: datetime


class VirtualGauge:
    """Estimate river discharge from remote sensing precipitation inputs."""

    def __init__(self, calibration: Optional[GaugeCalibration] = None) -> None:
        self.calibration = calibration or GaugeCalibration(slope=1.0, intercept=0.0, last_updated=datetime.utcnow())

    def estimate_discharge(self, rainfall_ds: xr.Dataset, catchment_mask: xr.DataArray) -> pd.Series:
        rainfall = rainfall_ds["forecast"].mean(dim="variable")
        masked = rainfall.where(catchment_mask > 0)
        discharge = masked.mean(dim=("latitude", "longitude")).to_series()
        discharge = discharge.fillna(0.0)
        calibrated = self.calibration.slope * discharge + self.calibration.intercept
        calibrated.name = "discharge_cms"
        return calibrated

    def update_calibration(self, observed: pd.Series, simulated: pd.Series) -> None:
        if len(observed) != len(simulated):
            raise ValueError("Observed and simulated series must align")
        x = simulated.values.reshape(-1, 1)
        y = observed.values
        slope = (x.T @ y) / (x.T @ x)
        intercept = float(y.mean() - slope * x.mean())
        self.calibration = GaugeCalibration(slope=float(slope), intercept=intercept, last_updated=datetime.utcnow())

    def save(self, path: Path) -> None:
        path.write_text(
            pd.Series(
                {
                    "slope": self.calibration.slope,
                    "intercept": self.calibration.intercept,
                    "last_updated": self.calibration.last_updated.isoformat(),
                }
            ).to_json()
        )

    @classmethod
    def load(cls, path: Path) -> "VirtualGauge":
        data = pd.read_json(path.read_text(), typ="series")
        calibration = GaugeCalibration(
            slope=float(data["slope"]),
            intercept=float(data["intercept"]),
            last_updated=datetime.fromisoformat(data["last_updated"]),
        )
        return cls(calibration=calibration)


__all__ = ["VirtualGauge", "GaugeCalibration"]
