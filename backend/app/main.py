"""FastAPI application entry point."""

from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.api.websocket import router as ws_router
from app.config import config
from app.services.code_executor import MODELS_DIR

logging.basicConfig(
    level=getattr(logging, config.log_level),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

app = FastAPI(
    title="Dreamscape",
    description="AI-powered interactive 3D world builder",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.server.cors_origins + ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ws_router)

# Serve generated 3D model files
MODELS_DIR.mkdir(exist_ok=True)
app.mount("/models", StaticFiles(directory=str(MODELS_DIR)), name="models")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
