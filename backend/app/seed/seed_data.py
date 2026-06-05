"""End-to-end seed for the UtilityApp demo cluster.

Targets (all overridable via env in `.env`):
  - ~1M customers          (default `SEED_CUSTOMERS=1000000`)
  - ~10M transactions      (default `SEED_TRANSACTIONS=10000000`)
  -  60 days of 30-min smart-meter time series for the 2 *demo* meters
  -  12 months of bills per *demo* account
  -  2 active outages, one intersecting the demo customer's JB address
  -  10 Service Centre service centres (geospatial 2dsphere)
  -  ~2k support tickets with `embed_source.text` for AutoEmbed →
     `voyage-4-large` 1024-d vectors generated *in-cluster* by Atlas

Run:
    python -m app.seed.seed_data            # full
    python -m app.seed.seed_data --quick    # ~10k customers / 100k tx for a fast iteration

The script is idempotent — every collection is dropped before insert. The
heavy collections stream batched `insert_many` calls so the working set
stays bounded; on a free-tier M0 you'll want to drop the targets to
`SEED_CUSTOMERS=10000 SEED_TRANSACTIONS=100000` because M0 is RAM-bound.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import math
import random
import sys
import time
from datetime import datetime, timedelta, timezone
from typing import Any

from pymongo import ASCENDING, DESCENDING, GEOSPHERE
from pymongo.errors import CollectionInvalid

from app.config import settings
from app.db import (
    COL_ACCOUNTS,
    COL_BILLS,
    COL_CUSTOMERS,
    COL_KEDAI_Utility,
    COL_METER_READINGS_TS,
    COL_METERS,
    COL_NOTIFICATIONS,
    COL_OUTAGES,
    COL_SUPPORT_CONVERSATIONS,
    COL_TRANSACTIONS,
    IDX_SUPPORT_AUTOEMBED,
    IDX_SUPPORT_SEARCH,
    admin_db,
    connect,
    disconnect,
    get_db,
)
from app.seed.realism import (
    FIRST_NAMES,
    KEDAI_Utility,
    LAST_NAMES,
    NEIGHBOURHOODS,
    OUTAGE_CAUSES,
    SUPPORT_TEMPLATES_BM,
    SUPPORT_TEMPLATES_EN,
    _polygon_around,
)
from app.services.tariff import compute_breakdown


KL = timezone(timedelta(hours=8))  # Asia/Kuala_Lumpur


# ---------------------------------------------------------------------- utils

def _eta(start: float, done: int, total: int) -> str:
    if done == 0:
        return "?"
    elapsed = time.time() - start
    rate = done / elapsed
    remaining = (total - done) / max(rate, 0.0001)
    return f"{rate:,.0f}/s · ETA {int(remaining)}s"


def _mask_ic(ic: str) -> str:
    return f"{ic[:6]}•••••{ic[-4:]}"


def _hash_phone(name: str, idx: int) -> str:
    h = abs(hash((name, idx))) % 10_000_000
    return f"+60 1{h//1_000_000}-{h%1_000_000:06d}"


# ---------------------------------------------------------------------- demo doc

def _build_demo_customer() -> dict:
    """The home-screen 'logged in' user — `settings.demo_customer_id`."""
    jb = next(n for n in NEIGHBOURHOODS if n[0] == "Johor Bahru")
    kl = next(n for n in NEIGHBOURHOODS if n[0] == "Kuala Lumpur")
    return {
        "customer_id": settings.demo_customer_id,
        "name": "Ahmad bin Ismail",
        "salutation": "Encik",
        "ic_masked": "880412•••••0145",
        "email": "ahmad.ismail@example.my",
        "phone": "+60 12-345 6789",
        "primary_language": "BM",
        "avatar_color": "#EE7A23",
        "created_at": datetime(2019, 8, 14, tzinfo=KL),
        "tier": "RESIDENTIAL",
        "accounts": [
            {
                "account_no": "220018472901",
                "nickname": "Rumah Setia Tropika",
                "relationship": "OWNER",
                "tariff_scheme": "TOU",
                "customer_class": "RESIDENTIAL",
                "address": {
                    "line1": "12, Jalan Setia Tropika 8/3",
                    "line2": "Taman Setia Tropika",
                    "city": jb[0],
                    "state": jb[1],
                    "postcode": jb[2],
                    "country": "MY",
                    "location": {"type": "Point", "coordinates": [jb[4], jb[5]]},
                },
                "meter_no": "SM-JB-880412-01",
                "activated_at": "2019-08-14",
            },
            {
                "account_no": "220018472902",
                "nickname": "Kedai Bangsar",
                "relationship": "OWNER",
                "tariff_scheme": "GENERAL",
                "customer_class": "COMMERCIAL",
                "address": {
                    "line1": "27A, Jalan Telawi 2",
                    "line2": "Bangsar Baru",
                    "city": kl[0],
                    "state": kl[1],
                    "postcode": kl[2],
                    "country": "MY",
                    "location": {"type": "Point", "coordinates": [kl[4], kl[5]]},
                },
                "meter_no": "SM-KL-880412-02",
                "activated_at": "2021-03-02",
            },
        ],
    }


# ---------------------------------------------------------------------- bulk customers

async def _seed_customers_bulk(target: int, demo_customer: dict) -> None:
    db = get_db()
    coll = db[COL_CUSTOMERS]
    print(f"\n[customers] target={target:,}")

    await coll.insert_one(demo_customer)

    if target <= 1:
        return

    rng = random.Random(42)
    BATCH = 5_000
    start = time.time()
    done = 0

    # 7% commercial, 93% residential — matches Utility's real split roughly.
    # Phone numbers + IC numbers are deterministic per index so re-running
    # the seed produces a stable corpus (helpful for the demo & screenshots).
    while done < target - 1:
        chunk = min(BATCH, target - 1 - done)
        docs: list[dict] = []
        for i in range(chunk):
            idx = done + i + 1
            first = FIRST_NAMES[idx % len(FIRST_NAMES)]
            last = LAST_NAMES[(idx * 31) % len(LAST_NAMES)]
            name = f"{first} {last}"
            n = NEIGHBOURHOODS[idx % len(NEIGHBOURHOODS)]
            customer_id = f"CUST-MY-{idx:08d}"
            account_no = f"22{idx:010d}"
            ic = f"{80 + (idx % 25):02d}{(idx % 12) + 1:02d}{(idx % 28) + 1:02d}-{(idx % 14) + 1:02d}-{idx % 10000:04d}"
            is_commercial = (idx % 14 == 0)
            docs.append({
                "customer_id": customer_id,
                "name": name,
                "ic_masked": _mask_ic(ic),
                "email": f"{first.lower()}.{last.split()[-1].lower()}{idx}@example.my",
                "phone": _hash_phone(name, idx),
                "primary_language": ("EN", "BM", "ZH")[idx % 3],
                "avatar_color": ("#EE7A23", "#1B3A6B", "#16A34A", "#F59E0B")[idx % 4],
                "tier": "COMMERCIAL" if is_commercial else "RESIDENTIAL",
                "created_at": datetime(2019, 1, 1, tzinfo=KL) + timedelta(days=idx % 2200),
                "accounts": [{
                    "account_no": account_no,
                    "nickname": ("Kedai " if is_commercial else "Rumah ") + n[3],
                    "relationship": "OWNER",
                    "tariff_scheme": "GENERAL" if is_commercial else ("TOU" if idx % 3 == 0 else "GENERAL"),
                    "customer_class": "COMMERCIAL" if is_commercial else "RESIDENTIAL",
                    "address": {
                        "line1": f"{(idx % 200) + 1}, Jalan {n[3]} {(idx % 30) + 1}",
                        "line2": n[3],
                        "city": n[0],
                        "state": n[1],
                        "postcode": n[2],
                        "country": "MY",
                        "location": {"type": "Point", "coordinates": [n[4], n[5]]},
                    },
                    "meter_no": f"SM-{n[1][:2].upper()}-{idx:06d}",
                    "activated_at": "2020-01-01",
                }],
            })
        await coll.insert_many(docs, ordered=False)
        done += chunk
        if done % 50_000 == 0 or done == target - 1:
            print(f"  customers {done:,}/{target-1:,}  {_eta(start, done, target-1)}")
    print(f"[customers] done in {int(time.time()-start)}s")


# ---------------------------------------------------------------------- accounts mirror

async def _seed_accounts_view(demo_customer: dict) -> None:
    """Materialise a flat `accounts` collection so the API can shard/serve
    accounts without unwinding the customer doc on every request.

    For the demo customer + a sampled chunk of the bulk customers we copy
    out one account each; that's enough to show the shard-router routing
    behaviour without ballooning the collection.
    """
    db = get_db()
    coll = db[COL_ACCOUNTS]
    print("\n[accounts] mirroring out of customers …")

    docs = []
    for acc in demo_customer["accounts"]:
        d = dict(acc)
        d["customer_id"] = demo_customer["customer_id"]
        d["customer_name"] = demo_customer["name"]
        docs.append(d)
    await coll.insert_many(docs, ordered=False)

    # Stream a flat copy of every customer's first account from the
    # canonical `customers` collection. We pull only the small accounts
    # subdoc to keep the working set tiny.
    cursor = db[COL_CUSTOMERS].find(
        {"customer_id": {"$ne": demo_customer["customer_id"]}},
        {"customer_id": 1, "name": 1, "accounts": {"$slice": 1}},
        no_cursor_timeout=False,
    )
    BATCH = 5_000
    batch: list[dict] = []
    n = 0
    async for c in cursor:
        if not c.get("accounts"):
            continue
        a = dict(c["accounts"][0])
        a["customer_id"] = c["customer_id"]
        a["customer_name"] = c["name"]
        batch.append(a)
        if len(batch) >= BATCH:
            await coll.insert_many(batch, ordered=False)
            n += len(batch)
            batch.clear()
            if n % 50_000 == 0:
                print(f"  accounts mirrored {n:,}")
    if batch:
        await coll.insert_many(batch, ordered=False)
        n += len(batch)
    print(f"[accounts] mirrored {n:,}")


# ---------------------------------------------------------------------- meters + ts

async def _seed_meters_and_timeseries(demo_customer: dict) -> None:
    db = get_db()
    print("\n[meters] seeding 2 demo meters")
    meters = []
    for acc in demo_customer["accounts"]:
        meters.append({
            "meter_no": acc["meter_no"],
            "account_no": acc["account_no"],
            "customer_id": demo_customer["customer_id"],
            "tariff_scheme": acc["tariff_scheme"],
            "customer_class": acc["customer_class"],
            "installed_at": datetime(2022, 6, 1, tzinfo=KL),
            "address_state": acc["address"]["state"],
        })
    await db[COL_METERS].insert_many(meters)

    print(f"[meter_readings_ts] creating time series (granularity=minutes, "
          f"{settings.seed_timeseries_days} days × "
          f"{60 // settings.seed_timeseries_interval_minutes} samples/h × 2 meters)")

    try:
        await db.create_collection(
            COL_METER_READINGS_TS,
            timeseries={
                "timeField": "ts",
                "metaField": "meta",
                "granularity": "minutes",
            },
        )
    except CollectionInvalid:
        pass  # already exists (idempotent re-run after partial seed)

    ts_coll = db[COL_METER_READINGS_TS]

    interval_min = settings.seed_timeseries_interval_minutes
    samples_per_day = (24 * 60) // interval_min
    days = settings.seed_timeseries_days
    end = datetime.now(KL).replace(minute=0, second=0, microsecond=0)
    start = end - timedelta(days=days)

    rng = random.Random(7)
    BATCH = 4_000
    total = 0
    started = time.time()

    for meter in meters:
        is_residential = meter["customer_class"] == "RESIDENTIAL"
        is_tou = meter["tariff_scheme"] == "TOU"
        cursor_ts = start
        batch: list[dict] = []
        while cursor_ts < end:
            hour = cursor_ts.hour
            weekday = cursor_ts.weekday()

            # Realistic shapes:
            # residential — gentle baseline + AM (7-9) + PM (18-22) peaks
            # commercial  — flat business-hour ramp (9-19), low overnight
            if is_residential:
                base = 0.18 + 0.08 * math.sin((hour - 6) / 24 * 2 * math.pi)
                if 7 <= hour <= 9:
                    base += 0.35
                if 18 <= hour <= 22:
                    base += 0.55
            else:
                base = 0.10
                if 9 <= hour <= 19 and weekday < 6:
                    base += 0.95
            kwh = max(0.02, base + rng.uniform(-0.04, 0.06)) * (interval_min / 30)

            tariff_period = "PEAK" if (is_tou and 14 <= hour < 22 and weekday < 5) else "OFFPEAK"

            batch.append({
                "ts": cursor_ts,
                "meta": {
                    "meter_no": meter["meter_no"],
                    "account_no": meter["account_no"],
                    "customer_id": meter["customer_id"],
                    "scheme": meter["tariff_scheme"],
                    "class": meter["customer_class"],
                },
                "kwh": round(kwh, 4),
                "tariffPeriod": tariff_period,
                "voltage_v": round(rng.uniform(228, 242), 1),
                "powerFactor": round(rng.uniform(0.92, 0.99), 3),
            })
            if len(batch) >= BATCH:
                await ts_coll.insert_many(batch, ordered=False)
                total += len(batch)
                batch.clear()
            cursor_ts += timedelta(minutes=interval_min)
        if batch:
            await ts_coll.insert_many(batch, ordered=False)
            total += len(batch)

    print(f"[meter_readings_ts] inserted {total:,} samples in {int(time.time()-started)}s")


# ---------------------------------------------------------------------- bills

def _build_bill_for(account: dict, customer_id: str, period_end: datetime, status: str) -> dict:
    rng = random.Random(int(period_end.timestamp()) ^ hash(account["account_no"]) & 0x7fffffff)
    if account["customer_class"] == "COMMERCIAL":
        total_kwh = round(rng.uniform(900, 1900), 1)
        peak = off = None
    else:
        if account["tariff_scheme"] == "TOU":
            total_kwh = round(rng.uniform(280, 580), 1)
            peak = round(total_kwh * rng.uniform(0.30, 0.55), 1)
            off = round(total_kwh - peak, 1)
        else:
            total_kwh = round(rng.uniform(220, 520), 1)
            peak = off = None
    afa = round(rng.uniform(-0.018, -0.008), 4)
    out = compute_breakdown(
        scheme=account["tariff_scheme"],
        total_kwh=total_kwh,
        peak_kwh=peak,
        offpeak_kwh=off,
        afa_rate=afa,
    )
    period_start = (period_end.replace(day=1)).date().isoformat()
    bill_no = (
        f"B{period_end:%Y%m}-{account['account_no'][-6:]}"
    )
    issued = period_end + timedelta(days=2)
    due = issued + timedelta(days=21)
    return {
        "bill_no": bill_no,
        "account_no": account["account_no"],
        "customer_id": customer_id,
        "billing_period_start": period_start,
        "billing_period_end": period_end.date().isoformat(),
        "issued_at": issued.isoformat(),
        "due_at": due.isoformat(),
        "status": status,
        "paid_at": None if status != "PAID" else (issued + timedelta(days=rng.randint(2, 18))).isoformat(),
        "total_kwh": total_kwh,
        "peak_kwh": peak,
        "offpeak_kwh": off,
        **out,
    }


def _month_offset(base: datetime, months_back: int) -> datetime:
    """Return the first-of-the-month `months_back` months before `base`.

    Avoids the trap of subtracting 30 days repeatedly — that drifts every
    few months because months aren't 30 days. Pure month arithmetic on
    a calendar.
    """
    y, m = base.year, base.month - months_back
    while m <= 0:
        m += 12
        y -= 1
    return base.replace(year=y, month=m, day=1)


async def _seed_bills(demo_customer: dict) -> None:
    db = get_db()
    coll = db[COL_BILLS]
    print("\n[bills] seeding 12 months × 2 accounts for the demo customer")
    docs: list[dict] = []
    today = datetime.now(KL).replace(hour=0, minute=0, second=0, microsecond=0)
    first_of_this_month = today.replace(day=1)
    for acc in demo_customer["accounts"]:
        for i in range(12, 0, -1):
            # i=1 → bill for the cycle that just closed (last month).
            # i=12 → 12th oldest cycle, end-of-month is `i-1` months earlier
            # than that — i.e. _month_offset(first_of_this_month, i-1) - 1 day.
            month_end = _month_offset(first_of_this_month, i - 1) - timedelta(days=1)
            # `i == 1` = current cycle. Residential demo: UNPAID + due in 4d.
            if i == 1:
                if acc["customer_class"] == "RESIDENTIAL":
                    bill = _build_bill_for(
                        acc, demo_customer["customer_id"], month_end, "UNPAID",
                    )
                    bill["due_at"] = (today + timedelta(days=4)).date().isoformat()
                else:
                    bill = _build_bill_for(
                        acc, demo_customer["customer_id"], month_end, "PAID",
                    )
            else:
                bill = _build_bill_for(
                    acc, demo_customer["customer_id"], month_end, "PAID",
                )
            docs.append(bill)
    await coll.insert_many(docs, ordered=False)
    print(f"[bills] inserted {len(docs)} bills")


# ---------------------------------------------------------------------- transactions

async def _seed_transactions_bulk(target: int, demo_customer: dict) -> None:
    """High-volume bill-payment transactions across the whole customer base.

    Schema is deliberately wide so the same collection can drive:
      - Home screen "recent payments" for the demo user
      - Sharded analytics queries (range key on customer_id+ts)
      - Change-stream notifications (insert into the demo customer fires SSE)
    """
    db = get_db()
    coll = db[COL_TRANSACTIONS]
    print(f"\n[transactions] target={target:,}")

    rng = random.Random(123)
    now = datetime.now(KL)
    BATCH = 5_000
    done = 0
    started = time.time()
    customer_total = max(settings.seed_customers, 1)
    channels = ("JomPAY", "FPX", "InstantTransfer", "Card", "Counter")
    states = list({n[1] for n in NEIGHBOURHOODS})

    # Reserve ~1% of the volume for the demo customer (so they have a
    # rich payments history on the Bills screen).
    demo_share = max(50, target // 1000)

    # First, the demo customer's payments — varied amounts/channels.
    demo_docs: list[dict] = []
    for i in range(demo_share):
        ts = now - timedelta(days=rng.randint(0, 365), minutes=rng.randint(0, 1440))
        amount = round(rng.uniform(80, 720), 2)
        acc = rng.choice(demo_customer["accounts"])
        demo_docs.append({
            "transaction_id": f"TXN-{ts:%Y%m%d}-{i:08d}-DEMO",
            "customer_id": demo_customer["customer_id"],
            "account_no": acc["account_no"],
            "ts": ts,
            "amount_myr": amount,
            "channel": rng.choice(channels),
            "status": "SUCCESS",
            "type": "BILL_PAYMENT",
            "reference": f"JOMP{rng.randint(10**8, 10**9 - 1)}",
            "state": acc["address"]["state"],
        })
        if len(demo_docs) >= BATCH:
            await coll.insert_many(demo_docs, ordered=False)
            done += len(demo_docs)
            demo_docs.clear()
    if demo_docs:
        await coll.insert_many(demo_docs, ordered=False)
        done += len(demo_docs)

    # Bulk for the rest of the corpus
    while done < target:
        chunk = min(BATCH, target - done)
        docs: list[dict] = []
        for j in range(chunk):
            idx = done + j
            cust_idx = idx % customer_total
            customer_id = (
                settings.demo_customer_id if cust_idx == 0
                else f"CUST-MY-{cust_idx:08d}"
            )
            account_no = f"22{cust_idx:010d}" if cust_idx != 0 else "220018472901"
            ts = now - timedelta(seconds=rng.randint(0, 365 * 86400))
            amount = round(rng.uniform(45, 950), 2)
            docs.append({
                "transaction_id": f"TXN-{ts:%Y%m%d}-{idx:09d}",
                "customer_id": customer_id,
                "account_no": account_no,
                "ts": ts,
                "amount_myr": amount,
                "channel": channels[idx % len(channels)],
                "status": "SUCCESS" if idx % 47 != 0 else "FAILED",
                "type": "BILL_PAYMENT",
                "reference": f"JOMP{(idx*7919) % 10**9:09d}",
                "state": states[idx % len(states)],
            })
        await coll.insert_many(docs, ordered=False)
        done += chunk
        if done % 100_000 == 0 or done == target:
            print(f"  transactions {done:,}/{target:,}  {_eta(started, done, target)}")
    print(f"[transactions] done in {int(time.time()-started)}s")


# ---------------------------------------------------------------------- outages + service centres

async def _seed_outages(demo_customer: dict) -> None:
    db = get_db()
    print("\n[outages] seeding 2 active outages (one intersects demo JB address)")
    jb = demo_customer["accounts"][0]["address"]["location"]["coordinates"]
    pj_neighbour = next(n for n in NEIGHBOURHOODS if n[0] == "Petaling Jaya")
    now = datetime.now(KL)
    outages = [
        {
            "outage_id": "OUT-2025-08-014",
            "status": "RESTORING",
            "cause": OUTAGE_CAUSES[0],
            "substation": "SUB-JB-014",
            "started_at": (now - timedelta(hours=2, minutes=18)).isoformat(),
            "eta_restoration": (now + timedelta(hours=1, minutes=20)).isoformat(),
            "last_update": (now - timedelta(minutes=12)).isoformat(),
            "affected": {
                "label": "Taman Setia Tropika & Bukit Indah",
                "area": _polygon_around(jb[0], jb[1], 0.014),
                "centroid": {"type": "Point", "coordinates": jb},
            },
            "customers_affected": 318,
        },
        {
            "outage_id": "OUT-2025-08-021",
            "status": "INVESTIGATING",
            "cause": OUTAGE_CAUSES[2],
            "substation": "SUB-PJ-007",
            "started_at": (now - timedelta(minutes=42)).isoformat(),
            "eta_restoration": None,
            "last_update": (now - timedelta(minutes=3)).isoformat(),
            "affected": {
                "label": "Kelana Jaya & SS6",
                "area": _polygon_around(pj_neighbour[4], pj_neighbour[5], 0.011),
                "centroid": {
                    "type": "Point",
                    "coordinates": [pj_neighbour[4], pj_neighbour[5]],
                },
            },
            "customers_affected": 142,
        },
    ]
    await db[COL_OUTAGES].insert_many(outages)


async def _seed_kedai() -> None:
    db = get_db()
    print("[kedai_Utility] seeding 10 service centres")
    docs = [
        {
            "name": k["name"],
            "city": k["city"],
            "state": k["state"],
            "phone": k["phone"],
            "hours": k["hours"],
            "location": {"type": "Point", "coordinates": [k["lng"], k["lat"]]},
        }
        for k in KEDAI_Utility
    ]
    await db[COL_KEDAI_Utility].insert_many(docs)


# ---------------------------------------------------------------------- support tickets (AutoEmbed)

def _embed_text(category: str, title: str, summary: str, steps: list[str]) -> str:
    """Canonical text the AutoEmbed index will read & embed in-cluster."""
    return (
        f"Category: {category}. Title: {title}. Summary: {summary} "
        f"Resolution: {' '.join(steps)}"
    )


async def _seed_support_tickets() -> None:
    """Seed N support tickets with a leaf string Atlas can AutoEmbed.

    The AutoEmbed index points at `embed_source.text` and uses the
    project-level Voyage credential — we never call Voyage from this
    process. The vector materialises invisibly inside the index.
    """
    db = get_db()
    coll = db[COL_SUPPORT_CONVERSATIONS]
    target = settings.seed_embedded_tickets
    print(f"\n[support_conversations] seeding {target:,} tickets for AutoEmbed")
    rng = random.Random(2025)
    pool = [(t, "EN") for t in SUPPORT_TEMPLATES_EN] + [(t, "BM") for t in SUPPORT_TEMPLATES_BM]
    BATCH = 1_000
    done = 0
    docs: list[dict] = []
    for i in range(target):
        (cat, title, steps), lang = rng.choice(pool)
        # Vary the surface text a little so the AutoEmbed corpus has
        # diversity; the categorical structure stays stable.
        suffix_pool = [
            "I tried restarting the meter but it didn't help.",
            "Saya cuba bayar guna FPX tetapi gagal.",
            "Saya ingin tahu lebih lanjut tentang ToU.",
            "Bill saya naik dua kali ganda bulan ini.",
            "Power cut tadi tengah hari di kawasan saya.",
        ]
        body = title + " — " + suffix_pool[i % len(suffix_pool)]
        text = _embed_text(cat, title, body, steps)
        docs.append({
            "ticket_id": f"TIK-2025-{i:06d}",
            "title": title,
            "summary": body,
            "category": cat,
            "lang": lang,
            "resolution_steps": steps,
            "created_at": datetime.now(KL) - timedelta(days=rng.randint(0, 365)),
            # The leaf the AutoEmbed index points at:
            "embed_source": {"text": text},
        })
        if len(docs) >= BATCH:
            await coll.insert_many(docs, ordered=False)
            done += len(docs)
            docs.clear()
            if done % 1_000 == 0:
                print(f"  tickets {done:,}/{target:,}")
    if docs:
        await coll.insert_many(docs, ordered=False)
        done += len(docs)
    print(f"[support_conversations] inserted {done:,}")


# ---------------------------------------------------------------------- indexes

async def _create_regular_indexes() -> None:
    db = get_db()
    print("\n[indexes] creating regular indexes")

    await db[COL_CUSTOMERS].create_index([("customer_id", ASCENDING)],
                                          unique=True, name="customer_id_unique")
    await db[COL_CUSTOMERS].create_index([("accounts.account_no", ASCENDING)],
                                          name="accounts_account_no")
    await db[COL_CUSTOMERS].create_index(
        [("accounts.address.location", GEOSPHERE)],
        name="account_address_2dsphere",
        partialFilterExpression={"accounts.address.location": {"$exists": True}},
    )

    await db[COL_ACCOUNTS].create_index(
        [("customer_id", ASCENDING), ("account_no", ASCENDING)],
        unique=True, name="customer_account_unique",
    )
    await db[COL_ACCOUNTS].create_index([("account_no", ASCENDING)],
                                          name="account_no")

    # Shard-key alignment: when bills is sharded on
    # `{account_no, billing_period_end}`, any unique index must be prefixed
    # by the shard key. We make the unique compound on `{account_no,
    # billing_period_end, bill_no}` — same uniqueness guarantee, sharding-
    # compatible. A separate non-unique `bill_no` lookup index covers the
    # `GET /bills/{bill_no}` route.
    await db[COL_BILLS].create_index(
        [("account_no", ASCENDING), ("billing_period_end", ASCENDING),
         ("bill_no", ASCENDING)],
        unique=True, name="account_period_bill_unique",
    )
    await db[COL_BILLS].create_index([("bill_no", ASCENDING)], name="bill_no")
    await db[COL_BILLS].create_index(
        [("account_no", ASCENDING), ("billing_period_end", DESCENDING)],
        name="account_period_recent",
    )
    await db[COL_BILLS].create_index(
        [("customer_id", ASCENDING), ("status", ASCENDING),
         ("billing_period_end", DESCENDING)],
        name="customer_status_recent",
    )

    # Same prefix rule for transactions on shard key `{customer_id, ts}`.
    await db[COL_TRANSACTIONS].create_index(
        [("customer_id", ASCENDING), ("ts", ASCENDING),
         ("transaction_id", ASCENDING)],
        unique=True, name="customer_ts_txn_unique",
    )
    await db[COL_TRANSACTIONS].create_index(
        [("transaction_id", ASCENDING)], name="transaction_id",
    )
    await db[COL_TRANSACTIONS].create_index(
        [("customer_id", ASCENDING), ("ts", DESCENDING)],
        name="customer_ts_desc",
    )
    await db[COL_TRANSACTIONS].create_index(
        [("account_no", ASCENDING), ("ts", DESCENDING)],
        name="account_ts_desc",
    )
    # Time series — sharding requires the supporting index to start with
    # the proposed shard key in *ascending* order on the time field.
    await db[COL_METER_READINGS_TS].create_index(
        [("meta.account_no", ASCENDING), ("ts", ASCENDING)],
        name="account_ts",
    )

    await db[COL_OUTAGES].create_index(
        [("affected.area", GEOSPHERE)], name="outage_area_2dsphere",
    )
    await db[COL_OUTAGES].create_index([("status", ASCENDING)], name="status")

    await db[COL_KEDAI_Utility].create_index(
        [("location", GEOSPHERE)], name="kedai_location_2dsphere",
    )

    await db[COL_SUPPORT_CONVERSATIONS].create_index(
        [("category", ASCENDING)], name="category",
    )

    await db[COL_NOTIFICATIONS].create_index(
        [("customer_id", ASCENDING), ("created_at", DESCENDING)],
        name="customer_recent",
    )
    print("[indexes] regular indexes ready")


async def _create_search_indexes() -> None:
    """Atlas Search (lexical) + Atlas Vector Search (AutoEmbed) on
    `support_conversations`.

    Both definitions live in `backend/atlas_indexes/`; here we just
    issue the createSearchIndexes command. If the cluster tier doesn't
    support search indexes (e.g. M0 free without search enabled), the
    failure is logged and the seed completes — the rest of the demo
    (REST endpoints, change streams, geo, time series) still works.
    """
    db = get_db()
    print("\n[search] creating Atlas Search + Atlas Vector Search indexes")

    lexical_def = {
        "mappings": {
            "dynamic": False,
            "fields": {
                "title": [{"type": "string"}, {"type": "autocomplete"}],
                "summary": {"type": "string"},
                "category": {"type": "token"},
                "lang": {"type": "token"},
                "resolution_steps": {"type": "string"},
                "embed_source": {
                    "type": "document",
                    "fields": {"text": {"type": "string"}},
                },
            },
        }
    }
    vector_def = {
        "fields": [
            {
                "type": "autoEmbed",
                "path": "embed_source.text",
                "modality": "text",
                "model": settings.voyage_model,
            },
            {"type": "filter", "path": "category"},
            {"type": "filter", "path": "lang"},
        ]
    }
    try:
        await db.command({
            "createSearchIndexes": COL_SUPPORT_CONVERSATIONS,
            "indexes": [{"name": IDX_SUPPORT_SEARCH, "definition": lexical_def}],
        })
        print(f"  ✔ {IDX_SUPPORT_SEARCH} created (lexical)")
    except Exception as exc:  # pragma: no cover — cluster-tier dependent
        print(f"  ! lexical search index skipped: {exc}")
    try:
        await db.command({
            "createSearchIndexes": COL_SUPPORT_CONVERSATIONS,
            "indexes": [{
                "name": IDX_SUPPORT_AUTOEMBED,
                "definition": vector_def,
                "type": "vectorSearch",
            }],
        })
        print(f"  ✔ {IDX_SUPPORT_AUTOEMBED} created (AutoEmbed → {settings.voyage_model})")
    except Exception as exc:  # pragma: no cover
        print(f"  ! vector search index skipped: {exc}")


# ---------------------------------------------------------------------- sharding

SHARD_PLAN = [
    # (collection, shard key, doc)
    (COL_CUSTOMERS, {"customer_id": 1}),
    (COL_ACCOUNTS, {"customer_id": 1, "account_no": 1}),
    (COL_BILLS, {"account_no": 1, "billing_period_end": 1}),
    (COL_TRANSACTIONS, {"customer_id": 1, "ts": 1}),
    (COL_METER_READINGS_TS, {"meta.account_no": 1, "ts": 1}),
]


async def _enable_sharding() -> None:
    """Enable sharding with *range* shard keys on the heavy collections.

    Why range and not hashed: the spec asks for sharding-as-observability,
    not write-throughput. Range keys make the chunk map legible —
    `sh.status()` shows ranges like `[CUST-MY-00200000, CUST-MY-00400000)`
    that map directly to the seed's structure, which is great for screen
    captures.

    Idempotent — `shardCollection` returns code 20 ("already sharded")
    on re-run; we treat that as success.
    """
    if not settings.enable_sharding:
        print("\n[sharding] skipped (ENABLE_SHARDING=false). Set to true on a sharded cluster.")
        return
    print("\n[sharding] enabling sharding (range keys)")
    admin = admin_db()
    try:
        await admin.command({"enableSharding": settings.mongodb_db})
    except Exception as exc:
        print(f"  ! enableSharding warned: {exc}")
    for coll, key in SHARD_PLAN:
        ns = f"{settings.mongodb_db}.{coll}"
        try:
            await admin.command({"shardCollection": ns, "key": key})
            print(f"  ✔ {ns} sharded on {key}")
        except Exception as exc:
            msg = str(exc).lower()
            if "already sharded" in msg or "code 20" in msg or "alreadyinitialized" in msg:
                print(f"  • {ns} already sharded on {key}")
            else:
                print(f"  ! shardCollection {ns} failed: {exc}")


# ---------------------------------------------------------------------- summary

async def _print_summary() -> None:
    db = get_db()
    print("\n[summary]")
    for coll in [
        COL_CUSTOMERS, COL_ACCOUNTS, COL_METERS, COL_METER_READINGS_TS,
        COL_BILLS, COL_TRANSACTIONS, COL_OUTAGES, COL_KEDAI_Utility,
        COL_SUPPORT_CONVERSATIONS,
    ]:
        try:
            n = await db[coll].estimated_document_count()
            print(f"  {coll:<26} {n:>14,}")
        except Exception as exc:
            print(f"  {coll:<26} ERROR {exc}")


# ---------------------------------------------------------------------- main

async def _drop_collections() -> None:
    db = get_db()
    print("\n[reset] dropping existing collections")
    for coll in [
        COL_CUSTOMERS, COL_ACCOUNTS, COL_METERS, COL_METER_READINGS_TS,
        COL_BILLS, COL_TRANSACTIONS, COL_OUTAGES, COL_KEDAI_Utility,
        COL_SUPPORT_CONVERSATIONS, COL_NOTIFICATIONS,
    ]:
        try:
            await db[coll].drop()
        except Exception as exc:
            print(f"  ! drop {coll} warned: {exc}")


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--quick", action="store_true",
                        help="Use 10k customers / 100k transactions instead of the env defaults.")
    parser.add_argument("--no-bulk", action="store_true",
                        help="Skip the 1M / 10M bulk loads — only seed the demo data.")
    parser.add_argument("--keep", action="store_true",
                        help="Don't drop existing collections.")
    args = parser.parse_args()

    if args.quick:
        # Override settings for a fast iteration.
        object.__setattr__(settings, "seed_customers", 10_000)
        object.__setattr__(settings, "seed_transactions", 100_000)
        object.__setattr__(settings, "seed_embedded_tickets", 500)
    if args.no_bulk:
        object.__setattr__(settings, "seed_customers", 1)
        object.__setattr__(settings, "seed_transactions", 200)

    await connect()
    try:
        if not args.keep:
            await _drop_collections()
        demo = _build_demo_customer()
        await _seed_customers_bulk(settings.seed_customers, demo)
        await _seed_accounts_view(demo)
        await _seed_meters_and_timeseries(demo)
        await _seed_bills(demo)
        await _seed_transactions_bulk(settings.seed_transactions, demo)
        await _seed_outages(demo)
        await _seed_kedai()
        await _seed_support_tickets()

        await _create_regular_indexes()
        await _enable_sharding()
        await _create_search_indexes()
        await _print_summary()
        print("\n✔ seed complete")
    finally:
        await disconnect()


if __name__ == "__main__":
    asyncio.run(main())
