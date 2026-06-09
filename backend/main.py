"""
SpecterOps FastAPI application.

Run from inside the backend/ directory:
    uvicorn main:app --reload --port 8000
"""
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from agents.orchestrator import hydrate_from_storage
from connectors import dynatrace_mcp
from routes.incidents import router as incidents_router
from routes.meta import router as meta_router
from routes.stream import router as stream_router
from routes.webhook import router as webhook_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load any persisted incidents into memory on startup (no-op without a DB).
    try:
        await hydrate_from_storage()
    except Exception:
        pass
    yield
    # Tear down the shared Dynatrace MCP server session on shutdown.
    try:
        await dynatrace_mcp.close()
    except Exception:
        pass


app = FastAPI(
    title="SpecterOps",
    description="Autonomous Post-Incident Forensics Agent — Google Cloud Rapid Agent Hackathon 2026",
    version="1.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(incidents_router)
app.include_router(webhook_router)
app.include_router(stream_router)
app.include_router(meta_router)


@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.1.0", "demo_mode": os.getenv("DEMO_MODE", "true")}


@app.get("/")
async def root():
    return {
        "name": "SpecterOps",
        "tagline": "When your production dies at 3am, SpecterOps wakes up instead of you.",
        "hackathon": "Google Cloud Rapid Agent Hackathon 2026",
        "partner": "Dynatrace",
        "docs": "/docs",
    }
