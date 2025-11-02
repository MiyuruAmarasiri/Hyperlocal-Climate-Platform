"""Hydrology helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Tuple

import numpy as np
import pandas as pd


def load_hydrograph(path: Path) -> pd.Series:
    """Load a hydrograph CSV with columns time, discharge."""

    df = pd.read_csv(path, parse_dates=["time"])
    df = df.set_index("time")
    return df["discharge"]


def smooth_series(series: pd.Series, window: int = 3) -> pd.Series:
    return series.rolling(window=window, center=True, min_periods=1).mean()


def compute_nash_sutcliffe(observed: pd.Series, simulated: pd.Series) -> float:
    if len(observed) != len(simulated):
        raise ValueError("Series must be aligned")
    numerator = ((observed - simulated) ** 2).sum()
    denominator = ((observed - observed.mean()) ** 2).sum()
    return 1 - numerator / denominator


def bias_correct(simulated: pd.Series, bias: float) -> pd.Series:
    return simulated * (1 + bias)


__all__ = ["load_hydrograph", "smooth_series", "compute_nash_sutcliffe", "bias_correct"]
