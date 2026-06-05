"""Build `_inspect` payloads for the MongoDB query inspector UI."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from bson import ObjectId
from bson.timestamp import Timestamp


def _sanitize(value: Any) -> Any:
    if isinstance(value, ObjectId):
        return str(value)
    if isinstance(value, Timestamp):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {k: _sanitize(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_sanitize(v) for v in value]
    return value


def sanitize_docs(docs: list[dict] | dict | None, *, limit: int = 3) -> list[dict]:
    if docs is None:
        return []
    if isinstance(docs, dict):
        docs = [docs]
    out: list[dict] = []
    for doc in docs[:limit]:
        d = dict(doc)
        d.pop("_id", None)
        out.append(_sanitize(d))
    return out


def inspect_meta(
    *,
    title: str,
    collection: str,
    operation: str,
    features: list[str],
    endpoint: str,
    filter: dict | None = None,
    pipeline: list | None = None,
    sort: dict | list | None = None,
    limit: int | None = None,
    index: str | None = None,
    indexes: list[str] | None = None,
    sample_documents: list[dict] | dict | None = None,
    note: str | None = None,
    engine: str | None = None,
) -> dict[str, Any]:
    return {
        "title": title,
        "collection": collection,
        "operation": operation,
        "features": features,
        "endpoint": endpoint,
        "filter": _sanitize(filter) if filter is not None else None,
        "pipeline": _sanitize(pipeline) if pipeline is not None else None,
        "sort": _sanitize(sort) if sort is not None else None,
        "limit": limit,
        "index": index,
        "indexes": indexes or ([index] if index else []),
        "sample_documents": sanitize_docs(sample_documents),
        "note": note,
        "engine": engine,
    }


def wrap(data: Any, meta: dict[str, Any], enabled: bool) -> Any:
    if not enabled:
        return data
    return {"data": data, "_inspect": meta}
