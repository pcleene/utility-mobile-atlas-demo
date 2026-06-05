"""Support search — hybrid lexical + AutoEmbed Vector search."""

from __future__ import annotations

import asyncio
from typing import Any  # noqa: F401

from fastapi import APIRouter, Depends

from app.db import (
    COL_SUPPORT_CONVERSATIONS,
    IDX_SUPPORT_AUTOEMBED,
    IDX_SUPPORT_SEARCH,
    get_db,
)
from app.deps import inspect_enabled
from app.models.support import SupportSearchRequest
from app.services.mongo_inspect import inspect_meta, wrap

router = APIRouter()


def _lexical_pipeline(query: str, top_k: int) -> list[dict[str, Any]]:
    return [
        {"$search": {
            "index": IDX_SUPPORT_SEARCH,
            "compound": {
                "should": [
                    {"text": {"query": query,
                              "path": ["title", "summary", "embed_source.text"]}},
                ],
            },
        }},
        {"$limit": top_k * 4},
        {"$project": {"_id": 0, "ticket_id": 1, "title": 1, "summary": 1,
                      "category": 1, "lang": 1, "resolution_steps": 1,
                      "_score": {"$meta": "searchScore"}}},
    ]


def _vector_pipeline(query: str, top_k: int) -> list[dict[str, Any]]:
    return [
        {"$vectorSearch": {
            "index": IDX_SUPPORT_AUTOEMBED,
            "path": "embed_source.text",
            "query": query,
            "limit": top_k * 4,
            "numCandidates": top_k * 20,
        }},
        {"$project": {"_id": 0, "ticket_id": 1, "title": 1, "summary": 1,
                      "category": 1, "lang": 1, "resolution_steps": 1,
                      "_score": {"$meta": "vectorSearchScore"}}},
    ]


def _rank_fusion_pipeline(query: str, top_k: int) -> list[dict[str, Any]]:
    return [
        {"$rankFusion": {
            "input": {
                "pipelines": {
                    "lexical": _lexical_pipeline(query, top_k)[:2],
                    "semantic": _vector_pipeline(query, top_k)[:1],
                }
            },
        }},
        {"$limit": top_k},
    ]


async def _rank_fusion_search(query: str, top_k: int) -> tuple[list[dict], list[dict]]:
    db = get_db()
    pipeline = [
        {"$rankFusion": {
            "input": {
                "pipelines": {
                    "lexical": [
                        {"$search": {
                            "index": IDX_SUPPORT_SEARCH,
                            "compound": {
                                "should": [
                                    {"text": {"query": query,
                                              "path": ["title", "summary",
                                                       "embed_source.text"]}},
                                ],
                            },
                        }},
                        {"$limit": top_k * 4},
                    ],
                    "semantic": [
                        {"$vectorSearch": {
                            "index": IDX_SUPPORT_AUTOEMBED,
                            "path": "embed_source.text",
                            "query": query,
                            "limit": top_k * 4,
                            "numCandidates": top_k * 20,
                        }},
                    ],
                }
            },
        }},
        {"$limit": top_k},
        {"$project": {
            "_id": 0, "ticket_id": 1, "title": 1, "summary": 1,
            "category": 1, "lang": 1, "resolution_steps": 1,
            "score": {"$meta": "scoreDetails"},
        }},
    ]
    rows = [r async for r in db[COL_SUPPORT_CONVERSATIONS].aggregate(pipeline)]
    out: list[dict] = []
    for r in rows:
        score_detail = r.pop("score", None)
        score = 0.0
        if isinstance(score_detail, dict):
            score = float(score_detail.get("value") or 0.0)
        out.append({**r, "score": round(score, 4), "matched_via": "hybrid"})
    return out, pipeline


async def _client_side_rrf(query: str, top_k: int) -> tuple[list[dict], str, list[dict]]:
    db = get_db()
    lex_pipe = _lexical_pipeline(query, top_k)
    vec_pipe = _vector_pipeline(query, top_k)

    async def _lexical() -> list[dict]:
        try:
            cursor = db[COL_SUPPORT_CONVERSATIONS].aggregate(lex_pipe)
            return [r async for r in cursor]
        except Exception:
            return []

    async def _semantic() -> list[dict]:
        try:
            cursor = db[COL_SUPPORT_CONVERSATIONS].aggregate(vec_pipe)
            return [r async for r in cursor]
        except Exception:
            return []

    lex, sem = await asyncio.gather(_lexical(), _semantic())
    k = 60
    fused: dict[str, dict] = {}
    for rank, doc in enumerate(lex):
        fused.setdefault(doc["ticket_id"], {**doc, "_fused": 0.0, "_via": set()})
        fused[doc["ticket_id"]]["_fused"] += 1.0 / (k + rank + 1)
        fused[doc["ticket_id"]]["_via"].add("lexical")
    for rank, doc in enumerate(sem):
        fused.setdefault(doc["ticket_id"], {**doc, "_fused": 0.0, "_via": set()})
        fused[doc["ticket_id"]]["_fused"] += 1.0 / (k + rank + 1)
        fused[doc["ticket_id"]]["_via"].add("vector")

    ordered = sorted(fused.values(), key=lambda d: d["_fused"], reverse=True)[:top_k]
    out = []
    for d in ordered:
        via_set: set = d.pop("_via", set())
        d.pop("_score", None)
        score = d.pop("_fused", 0.0)
        out.append({
            **d,
            "score": round(score, 4),
            "matched_via": "hybrid" if len(via_set) > 1 else next(iter(via_set), "hybrid"),
        })
    combined = [
        {"stage": "lexical", "pipeline": lex_pipe},
        {"stage": "semantic (AutoEmbed → Voyage)", "pipeline": vec_pipe},
        {"stage": "rrf_fusion", "note": "Reciprocal rank fusion in Python (k=60)"},
    ]
    return out, "rrf-fallback", combined


@router.post("/support/search", summary="Hybrid lexical + AutoEmbed search")
async def support_search(
    req: SupportSearchRequest,
    inspect: bool = Depends(inspect_enabled),
) -> Any:
    pipeline: list | dict = []
    engine = "rrf-fallback"
    hits: list[dict] = []

    try:
        hits, pipeline = await _rank_fusion_search(req.query, req.top_k)
        if hits:
            engine = "rankFusion"
    except Exception:
        hits, engine, pipeline = await _client_side_rrf(req.query, req.top_k)

    if not hits and engine == "rrf-fallback" and not pipeline:
        hits, engine, pipeline = await _client_side_rrf(req.query, req.top_k)

    result = {"hits": hits, "engine": engine}
    meta = inspect_meta(
        title="Support hybrid search",
        collection=COL_SUPPORT_CONVERSATIONS,
        operation="aggregate",
        features=[
            "Atlas Search",
            "Atlas Vector Search",
            "AutoEmbed (Voyage)",
            "Hybrid search",
        ],
        endpoint="POST /api/v1/support/search",
        pipeline=pipeline if isinstance(pipeline, list) else [pipeline],
        indexes=[IDX_SUPPORT_SEARCH, IDX_SUPPORT_AUTOEMBED],
        sample_documents=hits[:3],
        engine=engine,
        note="Lexical BM25 on title/summary + semantic AutoEmbed on embed_source.text. Fused via $rankFusion or RRF fallback.",
    )
    return wrap(result, meta, inspect)
