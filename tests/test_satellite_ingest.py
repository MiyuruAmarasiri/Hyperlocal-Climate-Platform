import asyncio
from datetime import date

import pytest

from ingestion import satellite_ingest
from shared.config import get_settings


@pytest.mark.asyncio
async def test_satellite_ingestor_http(monkeypatch, tmp_path):
    monkeypatch.setenv("DATA_ROOT", str(tmp_path))
    monkeypatch.setenv("LOGS_DIR", str(tmp_path))
    monkeypatch.setenv("CHIRPS_BASE_URL", "https://example.com/chirps")
    get_settings.cache_clear()

    calls = []

    async def fake_http(self, filename: str):
        calls.append(filename)
        path = self.storage_dir / filename
        path.write_bytes(b"dummy")
        return path

    monkeypatch.setattr(satellite_ingest.SatelliteIngestor, "_download_via_http", fake_http, raising=False)

    ingestor = satellite_ingest.SatelliteIngestor()
    await ingestor.download_daily_chirps(date(2024, 1, 1))

    assert calls == ["chirps-v2.0.2024.01.01.tif"]
