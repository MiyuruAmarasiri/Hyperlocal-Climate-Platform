"""Authentication and security helpers."""

from __future__ import annotations

import hashlib
import hmac
import logging
from typing import Iterable

from fastapi import Depends, HTTPException, Request, Security, status
from fastapi.security import APIKeyHeader

from shared.config import get_settings

log = logging.getLogger(__name__)

api_key_header = APIKeyHeader(name="x-api-key", auto_error=False)


def _hash_key(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _match_hashes(candidate: str, hashes: Iterable[str]) -> bool:
    candidate_hash = _hash_key(candidate)
    return any(hmac.compare_digest(candidate_hash, allowed.strip()) for allowed in hashes)


def _has_valid_plaintext(candidate: str, allowed: Iterable[str]) -> bool:
    return any(candidate == value for value in allowed)


def _enforce_client_certificate(request: Request, settings) -> None:
    if not settings.require_client_cert:
        return

    header_name = settings.client_cert_header.lower()
    client_cert = request.headers.get(header_name)

    if not client_cert:
        log.warning(
            "Client certificate missing",
            extra={"client_host": request.client.host if request.client else None},
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Client certificate required")

    if settings.allowed_client_cert_subjects and client_cert not in settings.allowed_client_cert_subjects:
        log.warning(
            "Client certificate subject rejected",
            extra={"client_host": request.client.host if request.client else None},
        )
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized client certificate")


async def require_api_key(request: Request, api_key: str = Security(api_key_header)) -> str:
    settings = get_settings()

    if not api_key:
        log.warning("API key missing", extra={"client_host": request.client.host if request.client else None})
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="API key required")

    if settings.api_key_hashes or settings.api_key_next_hashes:
        allowed_hashes = list(settings.api_key_hashes) + list(settings.api_key_next_hashes)
        if _match_hashes(api_key, allowed_hashes):
            _enforce_client_certificate(request, settings)
            return api_key
        log.warning(
            "API key rejected (hashed)",
            extra={"client_host": request.client.host if request.client else None},
        )
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid API key")

    if settings.api_keys:
        if _has_valid_plaintext(api_key, settings.api_keys):
            _enforce_client_certificate(request, settings)
            return api_key
        log.warning(
            "API key rejected (plaintext)",
            extra={"client_host": request.client.host if request.client else None},
        )
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid API key")

    log.warning("API key validation not configured; denying by default")
    raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="API auth not configured")


def get_current_client(api_key: str = Depends(require_api_key)) -> str:
    return api_key or "public"


__all__ = ["require_api_key", "get_current_client"]

