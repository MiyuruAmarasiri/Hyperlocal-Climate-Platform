"""Configuration loading utilities for the hyperlocal platform."""

from functools import lru_cache
from pathlib import Path
from typing import List, Optional, Union

from pydantic import BaseSettings, Field, validator


class Settings(BaseSettings):
    """Central application settings loaded from environment variables."""

    weather_provider: str = Field(
        default="open-meteo",
        description="Primary weather provider identifier (open-meteo|ecmwf)",
    )
    weather_api_key: str = Field(default="", description="Key for external weather APIs")
    satellite_api_key: str = Field(default="", description="Key for satellite imagery providers")
    ecmwf_url: str = Field(
        default="https://cds.climate.copernicus.eu/api/v2",
        description="ECMWF CDS API URL",
    )
    ecmwf_key: str = Field(default="", description="ECMWF CDS API key")
    ecmwf_email: str = Field(default="", description="ECMWF account email")
    chirps_base_url: str = Field(
        default="https://data.chc.ucsb.edu/products/CHIRPS-2.0/",
        description="Base URL for CHIRPS downloads (HTTP/FTP endpoint)",
    )
    chirps_username: Optional[str] = Field(default=None, description="CHIRPS authenticated username")
    chirps_password: Optional[str] = Field(default=None, description="CHIRPS authenticated password")
    mqtt_broker_url: str = Field(default="mqtt://localhost")
    mqtt_username: Optional[str] = None
    mqtt_password: Optional[str] = None
    mqtt_ca_cert: Optional[Path] = Field(default=None, description="Path to MQTT CA certificate")
    mqtt_client_cert: Optional[Path] = Field(default=None, description="Path to MQTT client certificate")
    mqtt_client_key: Optional[Path] = Field(default=None, description="Path to MQTT client private key")
    database_url: str = Field(
        default="sqlite:///./data/processed/hyperlocal.db",
        description="Primary time-series database connection string",
    )
    geodb_url: str = Field(
        default="sqlite:///./data/processed/geospatial.db",
        description="Spatial database connection string",
    )
    wrf_hydro_binary: str = Field(
        default="/usr/local/bin/wrf_hydro",
        description="Path to the WRF-Hydro executable or wrapper script",
    )
    data_root: Path = Field(default=Path("./data"))
    logs_dir: Path = Field(default=Path("./logs"))
    environment: str = Field(default="development")
    api_keys: List[str] = Field(default_factory=list, description="Allowed API keys for clients (legacy plaintext)")
    api_key_hashes: List[str] = Field(
        default_factory=list,
        description="Hex-encoded SHA-256 hashes for active API keys",
    )
    api_key_next_hashes: List[str] = Field(
        default_factory=list,
        description="Hashes for next rotation window; accepted alongside active hashes",
    )
    require_client_cert: bool = Field(
        default=False,
        description="Require a verified client certificate forwarded by the gateway",
    )
    client_cert_header: str = Field(
        default="x-client-cert",
        description="Header name populated by the gateway with client certificate info",
    )
    allowed_client_cert_subjects: List[str] = Field(
        default_factory=list,
        description="Optional list of permitted certificate subject strings",
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @validator("data_root", "logs_dir", pre=True)
    def _expand_path(cls, value: Union[str, Path]) -> Path:
        return Path(value).expanduser().resolve()

    @validator("mqtt_ca_cert", "mqtt_client_cert", "mqtt_client_key", pre=True)
    def _optional_path(cls, value: Optional[Union[str, Path]]) -> Optional[Path]:
        if value in (None, "", "null"):
            return None
        return Path(value).expanduser().resolve()


@lru_cache()
def get_settings() -> Settings:
    """Load and cache configuration settings."""

    settings = Settings()
    settings.logs_dir.mkdir(parents=True, exist_ok=True)
    settings.data_root.mkdir(parents=True, exist_ok=True)
    return settings

