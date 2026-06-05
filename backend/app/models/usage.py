from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class UsageBreakdown(BaseModel):
    period: Literal["PEAK", "OFFPEAK"]
    kwh: float


class DailyUsage(BaseModel):
    date: str
    total_kwh: float
    peak_kwh: float
    offpeak_kwh: float
    estimated_cost_myr: float


class MonthlyUsage(BaseModel):
    month: str  # YYYY-MM
    total_kwh: float
    peak_kwh: float
    offpeak_kwh: float
    estimated_cost_myr: float


class Insight(BaseModel):
    """One actionable insight string + optional savings hint.

    These are rendered as cards in the Usage screen.
    """

    icon: Literal["trend-up", "trend-down", "lightbulb", "clock", "leaf"]
    title: str
    body: str
    estimated_savings_myr: float | None = None
