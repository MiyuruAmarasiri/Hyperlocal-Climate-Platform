"""Download and prepare vulnerability layers for risk mapping."""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Iterable, Tuple

import httpx

from shared.config import get_settings

logger = logging.getLogger(__name__)

DATASETS = {
    "population": "https://data.humdata.org/hxlproxy/data/download?dataset=high-resolution-settlement-layer-latest-v1&format=geojson",
    "infrastructure": "https://overpass-api.de/api/interpreter",
    "health": "https://storage.googleapis.com/worldbank-health-facilities/health_facilities.geojson",
    "elevation": "https://copernicus-dem-30m.s3.amazonaws.com/{tile}.tif",
}


def parse_bbox(bbox: str) -> Tuple[float, float, float, float]:
    parts = bbox.split(",")
    if len(parts) != 4:
        raise ValueError("Bounding box must have 4 comma separated values: minLon,minLat,maxLon,maxLat")
    return tuple(float(value) for value in parts)  # type: ignore[return-value]


async def download_dataset(dataset: str, output: Path, bbox: Tuple[float, float, float, float] | None) -> Path:
    url = DATASETS[dataset]
    output.parent.mkdir(parents=True, exist_ok=True)
    async with httpx.AsyncClient(timeout=120) as client:
        # For complex APIs (e.g., Overpass) we would craft a query. Here we just persist instructions.
        response = await client.get(url)
        response.raise_for_status()
    output.write_bytes(response.content)
    if bbox:
        metadata_path = output.with_suffix(".bbox.json")
        metadata_path.write_text(json.dumps({"bbox": bbox}))
    return output


async def main() -> None:
    parser = argparse.ArgumentParser(description="Download vulnerability layers for risk mapping.")
    parser.add_argument("--dataset", choices=DATASETS.keys(), required=True, help="Dataset to download")
    parser.add_argument("--bbox", help="Optional bounding box minLon,minLat,maxLon,maxLat")
    parser.add_argument("--output", help="Custom output path")
    args = parser.parse_args()

    settings = get_settings()
    default_dir = settings.data_root / "processed" / "exposure"
    target_path = Path(args.output) if args.output else default_dir / f"{args.dataset}.geojson"
    bbox = parse_bbox(args.bbox) if args.bbox else None
    await download_dataset(args.dataset, target_path, bbox)
    logger.info("Dataset saved to %s", target_path)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
