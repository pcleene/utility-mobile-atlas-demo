from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class BillLine(BaseModel):
    """One row in the itemised breakdown.

    `detail` is the human-readable rate explanation
    (e.g. "198.3 kWh × 28.52 sen/kWh"). The frontend renders it under the
    label in slightly muted text.
    """

    label: str
    detail: str
    amount_myr: float
    code: str


class BillBreakdown(BaseModel):
    energy: BillLine
    energy_offpeak: BillLine | None = None
    capacity: BillLine
    network: BillLine
    retail: BillLine
    afa: BillLine

    incentives: list[BillLine] = []
    waivers: list[BillLine] = []


class Bill(BaseModel):
    bill_no: str
    account_no: str
    customer_id: str
    billing_period_start: str
    billing_period_end: str
    issued_at: str
    due_at: str
    status: Literal["PAID", "UNPAID", "OVERDUE"]
    paid_at: str | None = None

    total_kwh: float
    peak_kwh: float | None = None
    offpeak_kwh: float | None = None

    breakdown: BillBreakdown
    subtotal_myr: float
    rounding_myr: float = 0.0
    total_myr: float

    pdf_url: str | None = None
    days_until_due: int | None = Field(default=None, description="Server-derived")
