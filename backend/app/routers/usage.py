"""Usage aggregation backed by the `meter_readings_ts` time series."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, Query

from app.db import COL_METER_READINGS_TS, get_db
from app.deps import inspect_enabled
from app.services.insights import derive
from app.services.mongo_inspect import inspect_meta, wrap
from app.services.tariff import (
    CAPACITY,
    ENERGY_GENERAL_TIER1,
    ENERGY_TOU_OFFPEAK,
    ENERGY_TOU_PEAK,
    NETWORK,
)

router = APIRouter()

KL = timezone(timedelta(hours=8))


def _est_cost(peak: float, offpeak: float, scheme: str) -> float:
    total = peak + offpeak
    if scheme == "TOU":
        energy = peak * ENERGY_TOU_PEAK + offpeak * ENERGY_TOU_OFFPEAK
    else:
        energy = total * ENERGY_GENERAL_TIER1
    return round(energy + total * (CAPACITY + NETWORK), 2)


def _daily_pipeline(account_no: str, start: datetime, end: datetime) -> list[dict]:
    return [
        {"$match": {"meta.account_no": account_no, "ts": {"$gte": start, "$lt": end}}},
        {"$group": {
            "_id": {
                "day": {"$dateTrunc": {"date": "$ts", "unit": "day", "timezone": "Asia/Kuala_Lumpur"}},
                "period": "$tariffPeriod",
            },
            "kwh": {"$sum": "$kwh"},
        }},
        {"$group": {
            "_id": "$_id.day",
            "breakdown": {"$push": {"period": "$_id.period", "kwh": "$kwh"}},
            "total_kwh": {"$sum": "$kwh"},
        }},
        {"$sort": {"_id": 1}},
    ]


def _monthly_pipeline(account_no: str, start: datetime, end: datetime) -> list[dict]:
    return [
        {"$match": {"meta.account_no": account_no, "ts": {"$gte": start, "$lt": end}}},
        {"$group": {
            "_id": {
                "month": {"$dateTrunc": {"date": "$ts", "unit": "month", "timezone": "Asia/Kuala_Lumpur"}},
                "period": "$tariffPeriod",
            },
            "kwh": {"$sum": "$kwh"},
        }},
        {"$group": {
            "_id": "$_id.month",
            "breakdown": {"$push": {"period": "$_id.period", "kwh": "$kwh"}},
            "total_kwh": {"$sum": "$kwh"},
        }},
        {"$sort": {"_id": 1}},
    ]


async def _account_scheme(account_no: str) -> str:
    db = get_db()
    sample = await db[COL_METER_READINGS_TS].find_one(
        {"meta.account_no": account_no}, {"meta.scheme": 1}
    )
    return ((sample or {}).get("meta") or {}).get("scheme", "GENERAL")


async def _fetch_daily(account_no: str, days: int) -> tuple[list[dict], list[dict], list[dict]]:
    db = get_db()
    end = datetime.now(KL).replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
    start = end - timedelta(days=days)
    pipeline = _daily_pipeline(account_no, start, end)
    rows = [r async for r in db[COL_METER_READINGS_TS].aggregate(pipeline)]
    sample_cursor = db[COL_METER_READINGS_TS].find(
        {"meta.account_no": account_no},
        {"_id": 0, "ts": 1, "kwh": 1, "tariffPeriod": 1, "meta": 1},
    ).sort("ts", -1).limit(2)
    samples = [s async for s in sample_cursor]
    scheme = await _account_scheme(account_no)
    out = []
    for r in rows:
        peak = next((b["kwh"] for b in r["breakdown"] if b["period"] == "PEAK"), 0.0)
        off = next((b["kwh"] for b in r["breakdown"] if b["period"] == "OFFPEAK"), 0.0)
        out.append({
            "date": r["_id"].date().isoformat(),
            "total_kwh": round(r["total_kwh"], 2),
            "peak_kwh": round(peak, 2),
            "offpeak_kwh": round(off, 2),
            "estimated_cost_myr": _est_cost(peak, off, scheme),
        })
    return out, pipeline, samples


@router.get("/usage/{account_no}/daily", summary="Daily usage for last N days")
async def daily_usage(
    account_no: str,
    days: int = Query(30, ge=1, le=180),
    inspect: bool = Depends(inspect_enabled),
) -> Any:
    out, pipeline, samples = await _fetch_daily(account_no, days)
    meta = inspect_meta(
        title="Daily usage (time series)",
        collection=COL_METER_READINGS_TS,
        operation="aggregate",
        features=["Time series", "Aggregation", "$dateTrunc", "Range sharding"],
        endpoint=f"GET /api/v1/usage/{account_no}/daily",
        pipeline=pipeline,
        indexes=["account_ts"],
        sample_documents=samples,
        note="Time series: timeField=ts, metaField=meta, granularity=minutes. Shard key: { meta.account_no: 1, ts: 1 }",
    )
    return wrap(out, meta, inspect)


@router.get("/usage/{account_no}/monthly", summary="Monthly usage for last N months")
async def monthly_usage(
    account_no: str,
    months: int = Query(12, ge=1, le=24),
    inspect: bool = Depends(inspect_enabled),
) -> Any:
    db = get_db()
    end = datetime.now(KL).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    start = (end - timedelta(days=32 * months)).replace(day=1)
    pipeline = _monthly_pipeline(account_no, start, end)
    rows = [r async for r in db[COL_METER_READINGS_TS].aggregate(pipeline)]
    scheme = await _account_scheme(account_no)
    out = []
    for r in rows:
        peak = next((b["kwh"] for b in r["breakdown"] if b["period"] == "PEAK"), 0.0)
        off = next((b["kwh"] for b in r["breakdown"] if b["period"] == "OFFPEAK"), 0.0)
        out.append({
            "month": r["_id"].strftime("%Y-%m"),
            "total_kwh": round(r["total_kwh"], 1),
            "peak_kwh": round(peak, 1),
            "offpeak_kwh": round(off, 1),
            "estimated_cost_myr": _est_cost(peak, off, scheme),
        })
    meta = inspect_meta(
        title="Monthly usage (time series)",
        collection=COL_METER_READINGS_TS,
        operation="aggregate",
        features=["Time series", "Aggregation", "$dateTrunc"],
        endpoint=f"GET /api/v1/usage/{account_no}/monthly",
        pipeline=pipeline,
        sample_documents=out[:2],
    )
    return wrap(out, meta, inspect)


@router.get("/usage/{account_no}/insights", summary="Semantic usage insights")
async def insights(
    account_no: str,
    inspect: bool = Depends(inspect_enabled),
) -> Any:
    daily, pipeline, _ = await _fetch_daily(account_no, 30)
    scheme = await _account_scheme(account_no)
    result = {"insights": derive(daily, scheme)}
    meta = inspect_meta(
        title="Usage insights",
        collection=COL_METER_READINGS_TS,
        operation="aggregate + derive",
        features=["Time series", "Aggregation", "App logic"],
        endpoint=f"GET /api/v1/usage/{account_no}/insights",
        pipeline=pipeline,
        sample_documents=daily[-3:],
        note="Runs the daily aggregation pipeline, then applies threshold-based insight rules in Python (derive()).",
    )
    return wrap(result, meta, inspect)
