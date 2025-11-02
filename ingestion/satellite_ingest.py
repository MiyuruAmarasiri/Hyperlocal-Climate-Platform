"""Satellite data ingestion pipeline."""

from __future__ import annotations

import asyncio
import logging
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Iterable, List, Optional

import aioftp
import httpx
import rasterio
from rasterio.io import DatasetReader

from shared.config import get_settings

log = logging.getLogger(__name__)


class SatelliteIngestor:
    """Download satellite precipitation grids (e.g. CHIRPS) and persist to disk."""

    def __init__(
        self,
        api_endpoint: Optional[str] = None,
        storage_dir: Optional[Path] = None,
        http_client: Optional[httpx.AsyncClient] = None,
    ) -> None:
        settings = get_settings()
        self.storage_dir = storage_dir or (settings.data_root / "raw" / "satellite")
        self.api_endpoint = (api_endpoint or settings.chirps_base_url).rstrip("/")
        self.client = http_client or httpx.AsyncClient(timeout=60)
        self.settings = settings
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    async def download_daily_chirps(self, target_date: date, fmt: str = "tif") -> Path:
        """Download a CHIRPS daily grid for the specified date."""

        file_name = self._resolve_chirps_filename(target_date, fmt=fmt)
        if self.api_endpoint.startswith("ftp://") or self.api_endpoint.startswith("sftp://"):
            return await self._download_via_ftp(file_name)
        return await self._download_via_http(file_name)

    async def download_range(self, start: date, end: date, fmt: str = "tif") -> List[Path]:
        """Download a range of CHIRPS grids (inclusive)."""

        delta_days = (end - start).days
        if delta_days < 0:
            raise ValueError("end date must be on or after start date")
        tasks = [self.download_daily_chirps(start + timedelta(days=offset), fmt=fmt) for offset in range(delta_days + 1)]
        return await asyncio.gather(*tasks)

    async def _download_via_http(self, file_name: str) -> Path:
        url = f"{self.api_endpoint.rstrip('/')}/{file_name}"
        target = self.storage_dir / file_name
        if target.exists():
            return target
        auth = None
        if self.settings.chirps_username and self.settings.chirps_password:
            auth = (self.settings.chirps_username, self.settings.chirps_password)
        try:
            response = await self.client.get(url, auth=auth)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            log.error("Failed to download %s: %s", url, exc)
            raise
        target.write_bytes(response.content)
        return target

    async def _download_via_ftp(self, file_name: str) -> Path:
        target = self.storage_dir / file_name
        if target.exists():
            return target
        url = self.api_endpoint
        parsed = aioftp.parse_address(url)
        user = self.settings.chirps_username or parsed.user or "anonymous"
        password = self.settings.chirps_password or parsed.password or "anonymous@"
        remote_path = str(parsed.path / file_name)
        async with aioftp.Client.context(parsed.host, parsed.port or 21, user=user, password=password) as client:
            async with client.download_stream(remote_path) as stream:
                target.write_bytes(await stream.read())
        return target

    def _resolve_chirps_filename(self, target_date: date, fmt: str = "tif") -> str:
        suffix = fmt.lower()
        return f"chirps-v2.0.{target_date:%Y.%m.%d}.{suffix}"

    def open_dataset(self, path: Path) -> DatasetReader:
        return rasterio.open(path)

    async def close(self) -> None:
        await self.client.aclose()


async def main() -> None:
    ingestor = SatelliteIngestor()
    result = await ingestor.download_daily_chirps(date.today())
    log.info("Downloaded %s", result)
    await ingestor.close()


if __name__ == "__main__":
    asyncio.run(main())
