from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Query

from app.db import COL_BILLS, get_db
from app.deps import inspect_enabled
from app.services.mongo_inspect import inspect_meta, wrap

router = APIRouter()


def _days_until(date_str: str | None) -> int | None:
    if not date_str:
        return None
    try:
        d = datetime.fromisoformat(date_str)
    except ValueError:
        return None
    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)
    delta = d - datetime.now(timezone.utc)
    return delta.days


@router.get("/bills", summary="List bills for an account")
async def list_bills(
    account_no: str = Query(..., alias="accountNo"),
    status: Literal["PAID", "UNPAID", "OVERDUE", "ALL"] = Query("ALL"),
    limit: int = Query(24, ge=1, le=120),
    inspect: bool = Depends(inspect_enabled),
) -> Any:
    db = get_db()
    q: dict = {"account_no": account_no}
    if status != "ALL":
        q["status"] = status
    cursor = (
        db[COL_BILLS]
        .find(q, {"_id": 0})
        .sort("billing_period_end", -1)
        .limit(limit)
    )
    raw = [b async for b in cursor]
    bills = []
    for b in raw:
        b = dict(b)
        b["days_until_due"] = _days_until(b.get("due_at"))
        bills.append(b)
    meta = inspect_meta(
        title="Bills list",
        collection=COL_BILLS,
        operation="find",
        features=["Document model", "Range sharding", "RP4 tariff"],
        endpoint="GET /api/v1/bills",
        filter=q,
        sort={"billing_period_end": -1},
        limit=limit,
        indexes=["account_period_recent"],
        sample_documents=raw[:3],
        note="Shard key: { account_no: 1, billing_period_end: 1 }",
    )
    return wrap(bills, meta, inspect)


@router.get("/bills/{bill_no}", summary="Bill detail")
async def get_bill(
    bill_no: str,
    inspect: bool = Depends(inspect_enabled),
) -> Any:
    db = get_db()
    filt = {"bill_no": bill_no}
    bill = await db[COL_BILLS].find_one(filt, {"_id": 0})
    if not bill:
        raise HTTPException(404, "bill not found")
    bill = dict(bill)
    bill["days_until_due"] = _days_until(bill.get("due_at"))
    meta = inspect_meta(
        title="Bill detail (RP4 breakdown)",
        collection=COL_BILLS,
        operation="findOne",
        features=["Document model", "Nested breakdown"],
        endpoint=f"GET /api/v1/bills/{bill_no}",
        filter=filt,
        indexes=["bill_no"],
        sample_documents=[bill],
    )
    return wrap(bill, meta, inspect)
