"""RP4 tariff math (Malaysia, July 2025 schedule).

Energy
  GENERAL: 27.03 sen/kWh (≤ 1500), 37.03 sen/kWh (> 1500)
  TOU:     28.52 sen/kWh peak, 24.43 sen/kWh off-peak
Capacity charge:        4.55 sen/kWh
Network charge:        12.85 sen/kWh
Retail charge:         RM 10.00/month   (waived if total ≤ 600 kWh)
AFA (Automatic Fuel Adjustment): variable monthly, signed.

The numbers are intentionally hard-coded — the prototype demonstrates a
real bill, not a configurable tariff engine. A production app would read
these from a `tariffs` collection keyed by effective date.
"""

from __future__ import annotations

from typing import Literal

# All in MYR/kWh except `RETAIL_FLAT` (MYR/month) and `AFA` (MYR/kWh).
ENERGY_GENERAL_TIER1 = 0.2703  # ≤ 1500 kWh
ENERGY_GENERAL_TIER2 = 0.3703  # > 1500 kWh
ENERGY_TOU_PEAK = 0.2852
ENERGY_TOU_OFFPEAK = 0.2443
CAPACITY = 0.0455
NETWORK = 0.1285
RETAIL_FLAT = 10.00
RETAIL_WAIVER_KWH = 600
AFA_DEFAULT = -0.0145  # negative most months in 2025; rebate to bill

TariffScheme = Literal["GENERAL", "TOU"]


def _round2(x: float) -> float:
    return round(x + 1e-9, 2)


def compute_breakdown(
    *,
    scheme: TariffScheme,
    total_kwh: float,
    peak_kwh: float | None = None,
    offpeak_kwh: float | None = None,
    afa_rate: float = AFA_DEFAULT,
    apply_retail_waiver: bool = True,
) -> dict:
    """Return a serialisable breakdown ready to merge into a `Bill` doc."""
    if scheme == "TOU":
        assert peak_kwh is not None and offpeak_kwh is not None
        energy_peak_amt = peak_kwh * ENERGY_TOU_PEAK
        energy_off_amt = offpeak_kwh * ENERGY_TOU_OFFPEAK
        breakdown_energy = [
            {
                "label": "Energy (Peak)",
                "detail": f"{peak_kwh:.1f} kWh × {ENERGY_TOU_PEAK*100:.2f} sen/kWh",
                "amount_myr": _round2(energy_peak_amt),
                "code": "ENERGY_PEAK",
            },
            {
                "label": "Energy (Off-Peak)",
                "detail": (
                    f"{offpeak_kwh:.1f} kWh × {ENERGY_TOU_OFFPEAK*100:.2f} sen/kWh"
                ),
                "amount_myr": _round2(energy_off_amt),
                "code": "ENERGY_OFFPEAK",
            },
        ]
        energy_total = energy_peak_amt + energy_off_amt
    else:
        tier1 = min(total_kwh, 1500)
        tier2 = max(0.0, total_kwh - 1500)
        energy_amt = tier1 * ENERGY_GENERAL_TIER1 + tier2 * ENERGY_GENERAL_TIER2
        if tier2 > 0:
            detail = (
                f"1500 kWh × {ENERGY_GENERAL_TIER1*100:.2f} sen + "
                f"{tier2:.1f} kWh × {ENERGY_GENERAL_TIER2*100:.2f} sen/kWh"
            )
        else:
            detail = (
                f"{tier1:.1f} kWh × {ENERGY_GENERAL_TIER1*100:.2f} sen/kWh"
            )
        breakdown_energy = [
            {
                "label": "Energy",
                "detail": detail,
                "amount_myr": _round2(energy_amt),
                "code": "ENERGY",
            },
        ]
        energy_total = energy_amt

    capacity_amt = total_kwh * CAPACITY
    network_amt = total_kwh * NETWORK
    afa_amt = total_kwh * afa_rate
    retail_waived = apply_retail_waiver and total_kwh <= RETAIL_WAIVER_KWH
    retail_amt = 0.0 if retail_waived else RETAIL_FLAT

    capacity_line = {
        "label": "Capacity Charge",
        "detail": f"{total_kwh:.1f} kWh × {CAPACITY*100:.2f} sen/kWh",
        "amount_myr": _round2(capacity_amt),
        "code": "CAPACITY",
    }
    network_line = {
        "label": "Network Charge",
        "detail": f"{total_kwh:.1f} kWh × {NETWORK*100:.2f} sen/kWh",
        "amount_myr": _round2(network_amt),
        "code": "NETWORK",
    }
    retail_line = {
        "label": "Retail Charge",
        "detail": (
            "Waived (usage ≤ 600 kWh)"
            if retail_waived
            else f"RM {RETAIL_FLAT:.2f} flat/month"
        ),
        "amount_myr": _round2(retail_amt),
        "code": "RETAIL",
    }
    afa_line = {
        "label": "AFA (Fuel Adjustment)",
        "detail": (
            f"{total_kwh:.1f} kWh × {afa_rate*100:.2f} sen/kWh "
            + ("(rebate)" if afa_rate < 0 else "(surcharge)")
        ),
        "amount_myr": _round2(afa_amt),
        "code": "AFA",
    }

    subtotal = energy_total + capacity_amt + network_amt + retail_amt + afa_amt
    rounding = _round2(round(subtotal * 20) / 20 - subtotal)
    total = _round2(subtotal + rounding)

    breakdown = {
        "energy": breakdown_energy[0],
        "capacity": capacity_line,
        "network": network_line,
        "retail": retail_line,
        "afa": afa_line,
        "incentives": [],
        "waivers": (
            [
                {
                    "label": "Retail charge waiver",
                    "detail": "Total monthly consumption ≤ 600 kWh",
                    "amount_myr": 0.0,
                    "code": "RETAIL_WAIVER",
                }
            ]
            if retail_waived
            else []
        ),
    }
    if scheme == "TOU":
        breakdown["energy_offpeak"] = breakdown_energy[1]

    return {
        "breakdown": breakdown,
        "subtotal_myr": _round2(subtotal),
        "rounding_myr": rounding,
        "total_myr": total,
    }
