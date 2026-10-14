"""FastAPI entry point with development and release-bundled frontend support."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes import router

APP_VERSION = "0.1.0"

app = FastAPI(
    title="Odoo Module Explorer", version=APP_VERSION,
    description="Read-only static filesystem analysis of Odoo addons (v16–19)",
)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost", "testserver"])
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)
app.include_router(router)

# Prefer the portable UI embedded in the installed wheel. In a source checkout,
# still support npm run build without requiring a package rebuild.
BUNDLED_WEB = Path(__file__).resolve().parent / "web_dist"
DEVELOPMENT_WEB = Path(__file__).resolve().parents[2] / "frontend" / "dist"


def frontend_directory() -> Path | None:
    for candidate in (BUNDLED_WEB, DEVELOPMENT_WEB):
        if (candidate / "index.html").is_file():
            return candidate
    return None


frontend_dist = frontend_directory()
if frontend_dist is not None:
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")
