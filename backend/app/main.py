"""FastAPI application entrypoint.

`uvicorn app.main:app --reload`

The lifespan opens the Motor client, kicks off the change-stream tail
tasks for SSE, and tears them down on shutdown.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db import connect, disconnect
from app.routers import bills, customers, events, health, outages, support, usage

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect()
    events.start_change_stream_tasks()
    try:
        yield
    finally:
        await events.stop_change_stream_tasks()
        await disconnect()


app = FastAPI(
    title="UtilityApp Clone API",
    version="1.0.0",
    description=(
        "Reference implementation for the UtilityApp mobile clone. Showcases "
        "MongoDB Atlas: document model, time series, geospatial, "
        "aggregation framework, Atlas Search, Atlas Vector Search "
        "(AutoEmbed → Voyage), and change streams."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API = "/api/v1"
app.include_router(health.router, prefix=API, tags=["health"])
app.include_router(customers.router, prefix=API, tags=["customers"])
app.include_router(bills.router, prefix=API, tags=["bills"])
app.include_router(usage.router, prefix=API, tags=["usage"])
app.include_router(outages.router, prefix=API, tags=["outages"])
app.include_router(support.router, prefix=API, tags=["support"])
app.include_router(events.router, prefix=API, tags=["events"])


@app.get("/", include_in_schema=False)
def root() -> dict:
    return {
        "name": "UtilityApp Clone API",
        "version": app.version,
        "docs": "/docs",
        "openapi": "/openapi.json",
        "api_prefix": API,
    }
