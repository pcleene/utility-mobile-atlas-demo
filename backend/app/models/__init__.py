"""Pydantic v2 response/request models.

Kept thin: only fields the frontend actually reads. Fields the seed
populates but nobody surfaces (raw provenance, scratch metadata) live
on the document but stay off the API contract.
"""

from app.models.common import GeoPoint, GeoPolygon, Money
from app.models.customer import Account, Customer
from app.models.bill import Bill, BillBreakdown, BillLine
from app.models.usage import DailyUsage, Insight, MonthlyUsage
from app.models.outage import Outage, OutageReport
from app.models.support import SupportHit, SupportSearchRequest

__all__ = [
    "Account",
    "Bill",
    "BillBreakdown",
    "BillLine",
    "Customer",
    "DailyUsage",
    "GeoPoint",
    "GeoPolygon",
    "Insight",
    "Money",
    "MonthlyUsage",
    "Outage",
    "OutageReport",
    "SupportHit",
    "SupportSearchRequest",
]
