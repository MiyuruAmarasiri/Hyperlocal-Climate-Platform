"""Wrapper for executing WRF-Hydro simulations."""

from __future__ import annotations

import logging
import os
import subprocess
from pathlib import Path
from typing import Dict, Optional

from shared.config import get_settings

log = logging.getLogger(__name__)


def run_simulation(config_path: Path, output_dir: Path, extra_env: Optional[Dict[str, str]] = None) -> subprocess.CompletedProcess:
    """Execute WRF-Hydro with the provided configuration file."""

    settings = get_settings()
    wrf_binary = Path(settings.wrf_hydro_binary)
    if not wrf_binary.exists():
        raise FileNotFoundError(f"WRF-Hydro binary not found at {wrf_binary}")

    output_dir.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    env.update(extra_env or {})
    env.update({"WRF_HYDRO_CONFIG": str(config_path), "WRF_HYDRO_OUTPUT": str(output_dir)})

    log.info("Running WRF-Hydro: %s", wrf_binary)
    process = subprocess.run(
        [str(wrf_binary), "--config", str(config_path), "--output", str(output_dir)],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    if process.returncode != 0:
        log.error("WRF-Hydro failed: %s", process.stderr)
        raise RuntimeError("WRF-Hydro simulation failed")
    return process


__all__ = ["run_simulation"]
