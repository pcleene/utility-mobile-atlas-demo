"""Derive semantic 'usage insights' from aggregated daily data.

Lightweight, deterministic — no ML, just thresholds chosen to feel like
a real utility-app coach. Each insight returns one short title + body
and an optional MYR savings hint.
"""

from __future__ import annotations

from datetime import datetime, timezone


def _peak_share(daily: list[dict]) -> float:
    total = sum(d.get("total_kwh", 0) for d in daily) or 1.0
    peak = sum(d.get("peak_kwh", 0) for d in daily)
    return peak / total


def _avg(daily: list[dict], key: str) -> float:
    if not daily:
        return 0.0
    return sum(d.get(key, 0) for d in daily) / len(daily)


def derive(daily: list[dict], scheme: str) -> list[dict]:
    """daily entries: {date, total_kwh, peak_kwh, offpeak_kwh, estimated_cost_myr}"""
    insights: list[dict] = []
    if not daily:
        return insights

    last7 = daily[-7:]
    prev7 = daily[-14:-7] if len(daily) >= 14 else []

    last_avg = _avg(last7, "total_kwh")
    prev_avg = _avg(prev7, "total_kwh") if prev7 else last_avg
    if prev_avg > 0:
        delta_pct = (last_avg - prev_avg) / prev_avg * 100
        if delta_pct >= 8:
            insights.append({
                "icon": "trend-up",
                "title": f"Usage up {delta_pct:.0f}% week-on-week",
                "body": (
                    "Your daily average climbed from "
                    f"{prev_avg:.1f} kWh to {last_avg:.1f} kWh. "
                    "Check for newly added appliances or longer aircond runtimes."
                ),
                "estimated_savings_myr": None,
            })
        elif delta_pct <= -8:
            insights.append({
                "icon": "trend-down",
                "title": f"Nice — usage down {-delta_pct:.0f}%",
                "body": (
                    "Daily average dropped from "
                    f"{prev_avg:.1f} kWh to {last_avg:.1f} kWh. "
                    "Keep the habits going."
                ),
                "estimated_savings_myr": None,
            })

    if scheme == "TOU":
        share = _peak_share(last7)
        if share > 0.55:
            est_save = round(last_avg * 7 * 0.05, 2)
            insights.append({
                "icon": "clock",
                "title": f"{share*100:.0f}% of usage is during peak",
                "body": (
                    "Peak hours are 14:00–22:00 weekdays. Shifting laundry "
                    "and dishwashing to after 22:00 can trim ~RM "
                    f"{est_save:.2f} from next month's bill."
                ),
                "estimated_savings_myr": est_save,
            })

    if last_avg > 18:
        insights.append({
            "icon": "lightbulb",
            "title": "Cooling is your biggest spend",
            "body": (
                "On warm days, raising the aircond setpoint by 1°C "
                "saves ~6% per unit. Try 24°C overnight and a fan instead "
                "of two ACs running together."
            ),
            "estimated_savings_myr": round(last_avg * 7 * 0.04, 2),
        })

    insights.append({
        "icon": "leaf",
        "title": "Going green",
        "body": (
            "Apply for myGreen+ to subscribe to Renewable Energy Certificates "
            "and offset your monthly footprint."
        ),
        "estimated_savings_myr": None,
    })
    return insights


def time_of_day_banner(now: datetime | None = None) -> dict:
    """Home-page hint banner: changes copy by current time and weekday."""
    now = now or datetime.now(timezone.utc).astimezone()
    hour = now.hour
    weekday = now.weekday()  # 0=Mon
    is_peak = (14 <= hour < 22) and (weekday < 5)
    if is_peak:
        return {
            "tone": "warning",
            "title": "Peak hours now",
            "body": (
                "Energy is priced higher between 2pm–10pm on weekdays. "
                "Heavy loads after 10pm cost ~14% less."
            ),
        }
    if hour < 6:
        return {
            "tone": "calm",
            "title": "Off-peak overnight",
            "body": (
                "Right now is the cheapest time to run washing or charge EVs."
            ),
        }
    return {
        "tone": "calm",
        "title": "Off-peak hours",
        "body": (
            "Off-peak rates apply right now — a great time for high-load "
            "appliances."
        ),
    }


def greeting(now: datetime | None = None, name_first: str = "") -> str:
    now = now or datetime.now(timezone.utc).astimezone()
    h = now.hour
    if 5 <= h < 12:
        en, bm = "Good morning", "Selamat pagi"
    elif 12 <= h < 15:
        en, bm = "Good afternoon", "Selamat tengah hari"
    elif 15 <= h < 19:
        en, bm = "Good evening", "Selamat petang"
    else:
        en, bm = "Good evening", "Selamat malam"
    suffix = f", {name_first}" if name_first else ""
    return f"{en}{suffix} · {bm}"
