import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routers import snapchat

app = FastAPI(
    title="SnapIntel API",
    description=(
        "REST API for SnapIntel — an OSINT tool for investigating Snapchat users. "
        "Provides endpoints to retrieve user profiles, stories, curated highlights, "
        "spotlights, lenses, bitmojis, statistics, and upload-time heatmap data."
    ),
    version="1.0.0",
    contact={
        "name": "SnapIntel (by KrowZ)",
        "url": "https://github.com/Kr0wZ/SnapIntel",
    },
    license_info={
        "name": "AGPL-3.0",
        "url": "https://www.gnu.org/licenses/agpl-3.0.html",
    },
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(snapchat.router)


@app.get("/", tags=["Health"], summary="Health check", description="Returns API status and version.")
def health_check():
    return {
        "status": "ok",
        "api": "SnapIntel API",
        "version": "1.0.0",
        "instance_id": os.getenv("INSTANCE_ID", "local"),
        "proxy_enabled": bool(os.getenv("WEBSHARE_PASS")),
        "docs": "/docs",
        "redoc": "/redoc",
    }
