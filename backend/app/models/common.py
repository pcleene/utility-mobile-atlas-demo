from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class Money(BaseModel):
    """Always Malaysian Ringgit. We keep it as a sub-doc so we can flip to
    multi-currency later without touching every endpoint."""

    amount: float
    currency: Literal["MYR"] = "MYR"


class GeoPoint(BaseModel):
    type: Literal["Point"] = "Point"
    coordinates: tuple[float, float] = Field(..., description="[lng, lat]")


class GeoPolygon(BaseModel):
    type: Literal["Polygon"] = "Polygon"
    coordinates: list[list[tuple[float, float]]]
