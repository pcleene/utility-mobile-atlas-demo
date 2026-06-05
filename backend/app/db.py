"""Async Motor client + lifespan helpers.

One client per process. Routers grab the database via `get_db()`.
Collection name constants live next to the client so import order stays
trivial and there's exactly one place to change a collection name.
"""

from __future__ import annotations

from typing import Any

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.config import settings

# --- Collection names ---------------------------------------------------
COL_CUSTOMERS = "customers"
COL_ACCOUNTS = "accounts"
COL_METERS = "meters"
COL_METER_READINGS_TS = "meter_readings_ts"
COL_BILLS = "bills"
COL_TRANSACTIONS = "transactions"
COL_OUTAGES = "outages"
COL_KEDAI_Utility = "kedai_Utility"
COL_SUPPORT_CONVERSATIONS = "support_conversations"
COL_NOTIFICATIONS = "notifications"

# Atlas Search / Vector Search index names
IDX_SUPPORT_SEARCH = "support_text_idx"
IDX_SUPPORT_AUTOEMBED = "support_autoembed_idx"

_client: AsyncIOMotorClient | None = None
_db: AsyncIOMotorDatabase | None = None


async def connect() -> None:
    global _client, _db
    if _client is not None:
        return
    _client = AsyncIOMotorClient(
        settings.mongodb_uri,
        appname="UtilityApp-clone-api",
        # Modest pool — most of the heavy lifting is offloaded to Atlas.
        # Bumping past ~50 on a free-tier cluster just queues server-side.
        maxPoolSize=50,
        minPoolSize=5,
        # Keep connect failures fast so the app surfaces the misconfig
        # rather than hanging the lifespan on import.
        serverSelectionTimeoutMS=8_000,
    )
    _db = _client[settings.mongodb_db]
    # Cheap warmup — surfaces auth/DNS failures at boot, not first request.
    await _db.command("ping")


async def disconnect() -> None:
    global _client, _db
    if _client is not None:
        _client.close()
    _client = None
    _db = None


def get_db() -> AsyncIOMotorDatabase:
    if _db is None:
        raise RuntimeError("DB not initialised — call connect() first")
    return _db


def get_client() -> AsyncIOMotorClient:
    if _client is None:
        raise RuntimeError("Client not initialised — call connect() first")
    return _client


def admin_db() -> Any:
    """Admin DB handle for cluster-level commands (sharding, dbStats)."""
    return get_client()["admin"]
