from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class SupportSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    lang: Literal["EN", "BM", "ZH"] = "EN"
    top_k: int = Field(default=10, ge=1, le=25)


class SupportHit(BaseModel):
    ticket_id: str
    title: str
    summary: str
    category: str
    lang: Literal["EN", "BM", "ZH"]
    resolution_steps: list[str] = []
    score: float
    matched_via: Literal["lexical", "vector", "hybrid"]
