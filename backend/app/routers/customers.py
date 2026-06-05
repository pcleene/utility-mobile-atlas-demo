"""Customer + accounts."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from app.config import settings
from app.db import COL_ACCOUNTS, COL_BILLS, COL_CUSTOMERS, get_db
from app.deps import inspect_enabled
from app.services.mongo_inspect import inspect_meta, sanitize_docs, wrap

router = APIRouter()


def _doc_to_response(doc: dict) -> dict:
    doc.pop("_id", None)
    return doc


async def _attach_last_bill(account: dict) -> tuple[dict, dict | None]:
    db = get_db()
    filt = {"account_no": account["account_no"]}
    last = await db[COL_BILLS].find_one(filt, sort=[("billing_period_end", -1)])
    if last:
        account["last_bill_amount"] = last.get("total_myr")
        account["last_bill_status"] = last.get("status")
    return account, last


@router.get("/customers/me", summary="Demo session — current customer")
async def get_me(inspect: bool = Depends(inspect_enabled)) -> Any:
    db = get_db()
    filt = {"customer_id": settings.demo_customer_id}
    doc = await db[COL_CUSTOMERS].find_one(filt)
    if not doc:
        raise HTTPException(404, "demo customer not seeded")
    raw = dict(doc)
    doc = _doc_to_response(doc)
    enriched = []
    bill_samples = []
    for a in doc.get("accounts", []):
        acc, last_bill = await _attach_last_bill(dict(a))
        enriched.append(acc)
        if last_bill:
            bill_samples.append(last_bill)
    doc["accounts"] = enriched
    meta = inspect_meta(
        title="Customer profile",
        collection=COL_CUSTOMERS,
        operation="findOne",
        features=["Document model", "Embedded accounts"],
        endpoint="GET /api/v1/customers/me",
        filter=filt,
        indexes=["customer_id_unique"],
        sample_documents=[raw, *bill_samples[:2]],
        note="Also runs findOne on bills per account for last_bill_amount.",
    )
    return wrap(doc, meta, inspect)


@router.get("/accounts", summary="List accounts for the current customer")
async def list_accounts(inspect: bool = Depends(inspect_enabled)) -> Any:
    db = get_db()
    filt = {"customer_id": settings.demo_customer_id}
    cursor = db[COL_ACCOUNTS].find(filt, {"_id": 0})
    raw = [a async for a in cursor]
    accounts = []
    for a in raw:
        acc, _ = await _attach_last_bill(dict(a))
        accounts.append(acc)
    meta = inspect_meta(
        title="Linked accounts",
        collection=COL_ACCOUNTS,
        operation="find",
        features=["Document model", "Range sharding"],
        endpoint="GET /api/v1/accounts",
        filter=filt,
        indexes=["customer_account_unique"],
        sample_documents=raw[:3],
        note="Shard key: { customer_id: 1, account_no: 1 }",
    )
    return wrap(accounts, meta, inspect)


@router.get("/accounts/{account_no}", summary="Account detail")
async def get_account(
    account_no: str,
    inspect: bool = Depends(inspect_enabled),
) -> Any:
    db = get_db()
    filt = {"account_no": account_no}
    doc = await db[COL_ACCOUNTS].find_one(filt, {"_id": 0})
    if not doc:
        raise HTTPException(404, "account not found")
    acc, last = await _attach_last_bill(dict(doc))
    meta = inspect_meta(
        title="Account detail",
        collection=COL_ACCOUNTS,
        operation="findOne",
        features=["Document model"],
        endpoint=f"GET /api/v1/accounts/{account_no}",
        filter=filt,
        sample_documents=[acc, last] if last else [acc],
    )
    return wrap(acc, meta, inspect)
