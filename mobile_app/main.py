"""Kivy / PWA bootstrap."""

from __future__ import annotations

from pathlib import Path

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates


def create_mobile_app(api_url: str = "http://localhost:8000") -> FastAPI:
    app = FastAPI(title="Hyperlocal Mobile Companion")
    templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))
    static_dir = Path(__file__).parent / "static"
    static_dir.mkdir(exist_ok=True)
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    @app.get("/", response_class=HTMLResponse)
    async def index(request: Request) -> HTMLResponse:
        return templates.TemplateResponse("index.html", {"request": request})

    @app.get("/forecast")
    async def forecast(lat: float, lon: float):
        payload = {"latitude": lat, "longitude": lon, "horizon_hours": 48}
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{api_url}/forecast", json=payload)
            response.raise_for_status()
            return response.json()

    return app


app = create_mobile_app()


__all__ = ["create_mobile_app", "app"]
