"""Server-Sent Events fed by Mongo change streams.

The backend tails two collections:
  - `bills`        — new bill insert  → "Your new bill is ready"
  - `outages`      — status update    → "Outage update for SUB-JB-014"
  - `notifications`— direct broadcast — used by `/outages/report` etc.

Each in-bound SSE client subscribes to a per-process broadcast queue;
the change-stream tasks fan out into every queue. If a client falls
behind we drop oldest messages rather than block the producer.
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, AsyncIterator

from fastapi import APIRouter, Request
from sse_starlette.sse import EventSourceResponse

from app.db import COL_BILLS, COL_NOTIFICATIONS, COL_OUTAGES, get_db

logger = logging.getLogger(__name__)
router = APIRouter()


# Per-process broadcast registry. Each subscriber gets a bounded asyncio.Queue;
# producers `put_nowait` and drop on full so a slow tab never wedges the tail.
_subscribers: set[asyncio.Queue] = set()
_QUEUE_MAX = 100

_change_stream_tasks: list[asyncio.Task] = []


def _safe_dump(obj: Any) -> Any:
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, dict):
        return {k: _safe_dump(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_safe_dump(v) for v in obj]
    return obj


def _broadcast(event: dict) -> None:
    payload = {"ts": datetime.utcnow().isoformat() + "Z", **event}
    for q in list(_subscribers):
        try:
            q.put_nowait(payload)
        except asyncio.QueueFull:
            try:
                q.get_nowait()
            except Exception:
                pass


async def _watch_bills() -> None:
    db = get_db()
    while True:
        try:
            async with db[COL_BILLS].watch(
                pipeline=[{"$match": {"operationType": "insert"}}],
                full_document="updateLookup",
            ) as stream:
                async for change in stream:
                    doc = change.get("fullDocument") or {}
                    _broadcast({
                        "type": "BILL_NEW",
                        "title": "New bill ready",
                        "body": (
                            f"Your bill for {doc.get('billing_period_end')} is ready — "
                            f"RM {doc.get('total_myr', 0):.2f}"
                        ),
                        "data": _safe_dump({
                            "bill_no": doc.get("bill_no"),
                            "account_no": doc.get("account_no"),
                            "total_myr": doc.get("total_myr"),
                            "due_at": doc.get("due_at"),
                        }),
                    })
        except asyncio.CancelledError:
            return
        except Exception as exc:  # pragma: no cover — connection blips
            logger.warning("bills change stream blip: %s", exc)
            await asyncio.sleep(2)


async def _watch_outages() -> None:
    db = get_db()
    while True:
        try:
            async with db[COL_OUTAGES].watch(
                pipeline=[{"$match": {"operationType": {"$in": ["update", "replace", "insert"]}}}],
                full_document="updateLookup",
            ) as stream:
                async for change in stream:
                    doc = change.get("fullDocument") or {}
                    _broadcast({
                        "type": "OUTAGE_UPDATE",
                        "title": f"Outage update — {doc.get('substation', 'unknown')}",
                        "body": (
                            f"Status: {doc.get('status', '?')}. "
                            f"{(doc.get('affected') or {}).get('label', '')}"
                        ),
                        "data": _safe_dump({
                            "outage_id": doc.get("outage_id"),
                            "status": doc.get("status"),
                            "eta": doc.get("eta_restoration"),
                        }),
                    })
        except asyncio.CancelledError:
            return
        except Exception as exc:  # pragma: no cover
            logger.warning("outages change stream blip: %s", exc)
            await asyncio.sleep(2)


async def _watch_notifications() -> None:
    db = get_db()
    while True:
        try:
            async with db[COL_NOTIFICATIONS].watch(
                pipeline=[{"$match": {"operationType": "insert"}}],
                full_document="updateLookup",
            ) as stream:
                async for change in stream:
                    doc = change.get("fullDocument") or {}
                    _broadcast({
                        "type": doc.get("type", "NOTIFICATION"),
                        "title": doc.get("title", "Notification"),
                        "body": doc.get("body", ""),
                        "data": _safe_dump({k: v for k, v in doc.items() if k != "_id"}),
                    })
        except asyncio.CancelledError:
            return
        except Exception as exc:  # pragma: no cover
            logger.warning("notifications change stream blip: %s", exc)
            await asyncio.sleep(2)


def start_change_stream_tasks() -> None:
    if _change_stream_tasks:
        return
    loop = asyncio.get_event_loop()
    _change_stream_tasks.extend([
        loop.create_task(_watch_bills(), name="cs-bills"),
        loop.create_task(_watch_outages(), name="cs-outages"),
        loop.create_task(_watch_notifications(), name="cs-notifications"),
    ])


async def stop_change_stream_tasks() -> None:
    for t in _change_stream_tasks:
        t.cancel()
    for t in _change_stream_tasks:
        try:
            await t
        except (asyncio.CancelledError, Exception):
            pass
    _change_stream_tasks.clear()


@router.get("/events/stream", summary="SSE feed of live notifications")
async def event_stream(request: Request) -> EventSourceResponse:
    queue: asyncio.Queue = asyncio.Queue(maxsize=_QUEUE_MAX)
    _subscribers.add(queue)

    async def _gen() -> AsyncIterator[dict]:
        try:
            yield {"event": "ready", "data": json.dumps({"ok": True})}
            while True:
                if await request.is_disconnected():
                    return
                try:
                    payload = await asyncio.wait_for(queue.get(), timeout=15)
                except asyncio.TimeoutError:
                    yield {"event": "ping", "data": "{}"}
                    continue
                yield {
                    "event": "notification",
                    "data": json.dumps(payload, default=str),
                }
        finally:
            _subscribers.discard(queue)

    return EventSourceResponse(_gen())
