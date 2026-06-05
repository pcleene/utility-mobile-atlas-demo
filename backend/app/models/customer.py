from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.models.common import GeoPoint


class Address(BaseModel):
    line1: str
    line2: str | None = None
    city: str
    state: str
    postcode: str
    country: str = "MY"
    location: GeoPoint | None = None


class Account(BaseModel):
    """One contract / supply point. A customer can hold many."""

    account_no: str
    nickname: str
    relationship: Literal["OWNER", "TENANT"] = "OWNER"
    tariff_scheme: Literal["GENERAL", "TOU"] = "GENERAL"
    customer_class: Literal["RESIDENTIAL", "COMMERCIAL"] = "RESIDENTIAL"
    address: Address
    meter_no: str
    activated_at: str
    last_bill_amount: float | None = None
    last_bill_status: Literal["PAID", "UNPAID", "OVERDUE"] | None = None


class Customer(BaseModel):
    customer_id: str
    name: str
    salutation: str | None = None
    ic_masked: str = Field(..., description="IC with all but last 4 hidden")
    email: str
    phone: str
    primary_language: Literal["EN", "BM", "ZH"] = "EN"
    accounts: list[Account] = []
    avatar_color: str = "#EE7A23"
