from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Body, Depends, Query

from app.db import COL_NOTIFICATIONS, COL_OUTAGES, get_db
from app.deps import inspect_enabled
from app.models.outage import OutageReport
from app.services.mongo_inspect import inspect_meta, wrap

router = APIRouter()

_ACTIVE = {"$in": ["ACTIVE", "INVESTIGATING", "RESTORING"]}


@router.get("/outages", summary="All active outages")
async def list_outages(inspect: bool = Depends(inspect_enabled)) -> Any:
    db = get_db()
    filt = {"status": _ACTIVE}
    cursor = db[COL_OUTAGES].find(filt, {"_id": 0})
    raw = [o async for o in cursor]
    meta = inspect_meta(
        title="Active outages (network-wide)",
        collection=COL_OUTAGES,
        operation="find",
        features=["Document model", "Geospatial"],
        endpoint="GET /api/v1/outages",
        filter=filt,
        indexes=["status", "outage_area_2dsphere"],
        sample_documents=raw[:3],
    )
    return wrap(raw, meta, inspect)


@router.get("/outages/nearby", summary="Outages intersecting a point")
async def outages_nearby(
    lng: float = Query(..., ge=-180, le=180),
    lat: float = Query(..., ge=-90, le=90),
    inspect: bool = Depends(inspect_enabled),
) -> Any:
    db = get_db()
    filt = {
        "status": _ACTIVE,
        "affected.area": {
            "$geoIntersects": {
                "$geometry": {"type": "Point", "coordinates": [lng, lat]},
            }
        },
    }
    cursor = db[COL_OUTAGES].find(filt, {"_id": 0})
    raw = [o async for o in cursor]
    meta = inspect_meta(
        title="Outages near account",
        collection=COL_OUTAGES,
        operation="find",
        features=["Geospatial", "$geoIntersects", "2dsphere index"],
        endpoint="GET /api/v1/outages/nearby",
        filter=filt,
        indexes=["outage_area_2dsphere"],
        sample_documents=raw[:2],
        note="Uses 2dsphere index on affected.area — polygon intersects customer Point.",
    )
    return wrap(raw, meta, inspect)


@router.post("/outages/report", summary="Customer-reported outage")
async def report_outage(
    report: OutageReport = Body(...),
    inspect: bool = Depends(inspect_enabled),
) -> Any:
    db = get_db()
    now = datetime.now(timezone.utc)
    payload = {
        "type": "OUTAGE_REPORT_ACK",
        "customer_id": None,
        "account_no": report.account_no,
        "title": "Report received",
        "body": (
            "We've logged your outage report. A crew will be dispatched once "
            "we have enough corroborating reports for your area."
        ),
        "severity": report.severity,
        "created_at": now,
    }
    res = await db[COL_NOTIFICATIONS].insert_one(payload)
    result = {"ok": True, "notification_id": str(res.inserted_id)}
    meta = inspect_meta(
        title="Report outage",
        collection=COL_NOTIFICATIONS,
        operation="insertOne",
        features=["Change Streams", "Write concern"],
        endpoint="POST /api/v1/outages/report",
        filter={"document": payload},
        sample_documents=[{**payload, "_id": str(res.inserted_id)}],
        note="Insert triggers change stream → SSE toast on connected clients.",
    )
    return wrap(result, meta, inspect)
