"""FastAPI dependencies shared across routers."""

from __future__ import annotations

from fastapi import Header


def inspect_enabled(
    x_mongo_inspect: str | None = Header(default=None, alias="X-Mongo-Inspect"),
) -> bool:
    """When the client sends `X-Mongo-Inspect: 1`, responses are wrapped as
    `{ data, _inspect }` so the UI can show the query + sample documents."""
    return (x_mongo_inspect or "").lower() in ("1", "true", "yes")
