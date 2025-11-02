import hashlib

from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient

from api.auth import get_current_client
from shared.config import get_settings


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def build_app():
    app = FastAPI()

    @app.get("/secure")
    async def secure(client: str = Depends(get_current_client)):
        return {"client": client}

    return app


def test_hashed_api_key(monkeypatch):
    hashed = _hash("secret-key")
    monkeypatch.setenv("API_KEY_HASHES", f"[\"{hashed}\"]")
    get_settings.cache_clear()

    app = build_app()
    client = TestClient(app)

    response = client.get("/secure", headers={"x-api-key": "secret-key"})
    assert response.status_code == 200
    assert response.json()["client"] == "secret-key"


def test_invalid_api_key(monkeypatch):
    hashed = _hash("secret-key")
    monkeypatch.setenv("API_KEY_HASHES", f"[\"{hashed}\"]")
    get_settings.cache_clear()

    app = build_app()
    client = TestClient(app)

    response = client.get("/secure", headers={"x-api-key": "wrong"})
    assert response.status_code == 403

def test_requires_client_certificate(monkeypatch):
    hashed = _hash("secret-key")
    monkeypatch.setenv("API_KEY_HASHES", f"[\"{hashed}\"]")
    monkeypatch.setenv("REQUIRE_CLIENT_CERT", "true")
    monkeypatch.setenv("ALLOWED_CLIENT_CERT_SUBJECTS", "[\"CN=device-1\"]")
    get_settings.cache_clear()

    app = build_app()
    client = TestClient(app)

    response = client.get("/secure", headers={"x-api-key": "secret-key"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Client certificate required"


def test_valid_client_certificate(monkeypatch):
    hashed = _hash("secret-key")
    monkeypatch.setenv("API_KEY_HASHES", f"[\"{hashed}\"]")
    monkeypatch.setenv("REQUIRE_CLIENT_CERT", "true")
    monkeypatch.setenv("ALLOWED_CLIENT_CERT_SUBJECTS", "[\"CN=device-1\"]")
    monkeypatch.setenv("CLIENT_CERT_HEADER", "x-client-cert")
    get_settings.cache_clear()

    app = build_app()
    client = TestClient(app)

    response = client.get(
        "/secure",
        headers={"x-api-key": "secret-key", "x-client-cert": "CN=device-1"},
    )
    assert response.status_code == 200
    assert response.json()["client"] == "secret-key"
