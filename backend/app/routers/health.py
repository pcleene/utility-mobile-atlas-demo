"""Health + cluster observability.

`/health`         — liveness ping
`/health/cluster` — server build info + sharding state, used by the README
                    to verify the demo is connected to the right cluster.
"""

from __future__ import annotations

from fastapi import APIRouter

from typing import Any

from bson import ObjectId
from bson.timestamp import Timestamp

from app.config import settings
from app.db import COL_TRANSACTIONS, get_client, get_db

router = APIRouter()


def _bson_safe(v: Any) -> Any:
    """Recursively coerce BSON-only types into JSON-friendly forms.

    `hello`/`buildInfo`/`listShards` responses can contain ObjectIds and
    Timestamps that Pydantic v2 refuses to serialise. We render them as
    strings — that's what the frontend needs anyway."""
    if isinstance(v, (ObjectId, Timestamp)):
        return str(v)
    if isinstance(v, dict):
        return {k: _bson_safe(x) for k, x in v.items()}
    if isinstance(v, list):
        return [_bson_safe(x) for x in v]
    return v


@router.get("/health")
async def health() -> dict:
    return {"ok": True, "db": settings.mongodb_db}


@router.get("/health/cluster", summary="Cluster + sharding observability")
async def health_cluster() -> dict:
    """Surface enough cluster metadata that the README's `curl` snippet
    proves the demo is plugged into a real Atlas cluster — including
    whether sharding is on and how the heaviest collection is split."""
    db = get_db()
    client = get_client()

    info = await client.admin.command("buildInfo")
    out: dict = {
        "version": info.get("version"),
        "modules": info.get("modules"),
        "database": settings.mongodb_db,
    }

    try:
        is_master = await client.admin.command("hello")
        out["msg"] = is_master.get("msg")
        out["topology_version"] = _bson_safe(is_master.get("topologyVersion"))
    except Exception as exc:
        out["topology_error"] = str(exc)

    # Shard map (fails on non-sharded cluster; we treat that as informational).
    try:
        shards = await client.admin.command("listShards")
        out["shards"] = _bson_safe([
            {"_id": s.get("_id"), "host": s.get("host"), "state": s.get("state")}
            for s in shards.get("shards", [])
        ])
    except Exception:
        out["shards"] = []

    # Per-collection chunk distribution — only meaningful on a sharded
    # cluster; we ignore failures so this works on a replica set too.
    try:
        ns = f"{settings.mongodb_db}.{COL_TRANSACTIONS}"
        coll_stats = await db.command(
            "collStats", COL_TRANSACTIONS, scale=1024 * 1024
        )
        out["transactions_collstats"] = _bson_safe({
            "size_mb": coll_stats.get("size"),
            "count": coll_stats.get("count"),
            "avg_obj_size": coll_stats.get("avgObjSize"),
            "sharded": coll_stats.get("sharded", False),
            "shards": list((coll_stats.get("shards") or {}).keys()),
        })
    except Exception as exc:
        out["transactions_collstats"] = {"error": str(exc)}

    return _bson_safe(out)
