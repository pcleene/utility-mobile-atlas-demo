from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.models.common import GeoPoint, GeoPolygon


class OutageAffected(BaseModel):
    label: str
    area: GeoPolygon
    centroid: GeoPoint


class Outage(BaseModel):
    outage_id: str
    status: Literal["ACTIVE", "INVESTIGATING", "RESTORING", "RESOLVED"]
    cause: str
    substation: str | None = None
    started_at: str
    eta_restoration: str | None = None
    last_update: str
    affected: OutageAffected
    customers_affected: int


class OutageReport(BaseModel):
    account_no: str
    description: str
    location: GeoPoint
    severity: Literal["LOW", "MEDIUM", "HIGH"] = "MEDIUM"
    contact_phone: str | None = None
