"""Static reference data for realistic Malaysian seeding.

Real Malaysian neighbourhoods, IC numbers shaped correctly, plausible
phone-number formats, real RM-denominated salaries — just enough that
the prototype passes a quick visual smell-test from a Malaysian user.
"""

from __future__ import annotations

import random

# (city, state, postcode prefix, neighbourhood, lng, lat) — real points
NEIGHBOURHOODS: list[tuple[str, str, str, str, float, float]] = [
    ("Johor Bahru", "Johor", "81200", "Taman Setia Tropika", 103.6896, 1.5325),
    ("Johor Bahru", "Johor", "81100", "Taman Pelangi", 103.7548, 1.4720),
    ("Johor Bahru", "Johor", "80300", "Larkin", 103.7331, 1.4890),
    ("Iskandar Puteri", "Johor", "79200", "Bukit Indah", 103.6628, 1.4889),
    ("Kuala Lumpur", "Wilayah Persekutuan", "59100", "Bangsar", 101.6792, 3.1294),
    ("Kuala Lumpur", "Wilayah Persekutuan", "50450", "KLCC", 101.7117, 3.1581),
    ("Kuala Lumpur", "Wilayah Persekutuan", "50490", "Bukit Bintang", 101.7110, 3.1466),
    ("Kuala Lumpur", "Wilayah Persekutuan", "53100", "Setapak", 101.7159, 3.1937),
    ("Petaling Jaya", "Selangor", "47301", "Kelana Jaya", 101.5984, 3.1052),
    ("Petaling Jaya", "Selangor", "46100", "PJ Old Town", 101.6334, 3.1052),
    ("Subang Jaya", "Selangor", "47500", "USJ", 101.5848, 3.0438),
    ("Shah Alam", "Selangor", "40100", "Section 7", 101.5335, 3.0717),
    ("Shah Alam", "Selangor", "40400", "Setia Alam", 101.4571, 3.1200),
    ("Klang", "Selangor", "41200", "Bukit Tinggi", 101.4424, 3.0419),
    ("Cyberjaya", "Selangor", "63000", "Cyber 6", 101.6474, 2.9285),
    ("Putrajaya", "Wilayah Persekutuan", "62000", "Presint 9", 101.6841, 2.9264),
    ("George Town", "Pulau Pinang", "10350", "Gurney Drive", 100.3173, 5.4364),
    ("Bayan Lepas", "Pulau Pinang", "11900", "Bayan Baru", 100.2776, 5.3328),
    ("Ipoh", "Perak", "31400", "Bandar Baru Medan", 101.1063, 4.6201),
    ("Seremban", "Negeri Sembilan", "70200", "Seremban 2", 101.9492, 2.7297),
    ("Melaka", "Melaka", "75200", "Bukit Beruang", 102.2873, 2.2459),
    ("Alor Setar", "Kedah", "05100", "Simpang Kuala", 100.3608, 6.1184),
    ("Kota Bharu", "Kelantan", "15300", "Kubang Kerian", 102.2833, 6.1064),
    ("Kuantan", "Pahang", "25300", "Indera Mahkota", 103.3043, 3.8232),
    ("Kuching", "Sarawak", "93350", "Petra Jaya", 110.3411, 1.5724),
    ("Kota Kinabalu", "Sabah", "88300", "Likas", 116.0735, 5.9783),
]

FIRST_NAMES = [
    "Ahmad", "Aisyah", "Aminah", "Arif", "Aziz", "Daniel", "Dina", "Faizal",
    "Farah", "Hafiz", "Hakim", "Hanis", "Idris", "Iman", "Ismail", "Izzat",
    "Khalid", "Lim", "Liyana", "Mahirah", "Mansor", "Mazlan", "Nadia", "Najib",
    "Nor", "Nurul", "Omar", "Ong", "Rashid", "Rina", "Rosli", "Salim",
    "Shazwan", "Siti", "Sofia", "Suzana", "Tan", "Wong", "Yusof", "Zainab",
    "Zara", "Zul",
]
LAST_NAMES = [
    "Abdullah", "Bakar", "Bin Ahmad", "Bin Ismail", "Bin Mohamed",
    "Bin Yusof", "Binti Hassan", "Binti Ibrahim", "Chong", "Goh",
    "Ismail", "Lee", "Lim", "Mansor", "Rahman", "Tan", "Teh", "Wong", "Yew",
]

OUTAGE_CAUSES = [
    "Cable fault at SUB-JB-014 substation",
    "Underground cable damage during roadworks",
    "Lightning strike on 132kV transmission line",
    "Transformer overheat protection trip",
    "Tree branch fallen on overhead line",
    "Substation maintenance — planned",
    "Vehicle impact on pole structure",
    "Equipment failure on incoming feeder",
]

# Stable Voyage-like text fragments per category — used by the AutoEmbed
# index. Mixed BM/EN to demo bilingual semantic search.
SUPPORT_TEMPLATES_EN: list[tuple[str, str, list[str]]] = [
    ("Billing", "How do I pay my bill via JomPAY?", [
        "Open your bank app, choose JomPAY, enter Biller Code 8881, key in your account number, confirm the amount.",
        "Save the JomPAY reference — it's your proof of payment.",
    ]),
    ("Billing", "Why is my bill higher than last month?", [
        "Compare daily kWh in the Usage screen to spot a trend.",
        "Check if any appliance was added (water heater, EV charger) or AC ran longer.",
        "Review the AFA (Fuel Adjustment) line — it varies monthly.",
    ]),
    ("Tariff", "What is the difference between General and Time-of-Use tariffs?", [
        "General is a flat tier-based rate by total kWh.",
        "ToU charges peak (14:00–22:00 weekdays) higher and off-peak lower.",
        "ToU rewards shifting laundry, ironing, and EV charging to off-peak.",
    ]),
    ("Tariff", "How is the Retail Charge calculated?", [
        "Retail Charge is RM 10.00 per month, fixed.",
        "It is waived if your monthly usage stays at or below 600 kWh.",
    ]),
    ("Outage", "Power is out at my address — what do I do?", [
        "Check the Outages screen first — your area might already be on our list.",
        "If not listed, tap 'Report Outage' and submit your address.",
        "We text you when a crew is dispatched and again on restoration.",
    ]),
    ("Smart Meter", "What does the blinking red LED on my smart meter mean?", [
        "A blinking red LED indicates active energy consumption — this is normal.",
        "If the LED is solid red, the meter has detected a tamper alarm; please call Careline.",
    ]),
]

SUPPORT_TEMPLATES_BM: list[tuple[str, str, list[str]]] = [
    ("Billing", "Bagaimana saya boleh bayar bil melalui JomPAY?", [
        "Buka aplikasi bank, pilih JomPAY, masukkan Biller Code 8881, kemudian nombor akaun anda.",
        "Simpan rujukan JomPAY — itu bukti pembayaran.",
    ]),
    ("Tariff", "Apakah Tarif Time-of-Use (ToU)?", [
        "ToU mengenakan kadar lebih tinggi semasa waktu puncak (2 ptg–10 mlm hari bekerja).",
        "Anda menjimat kos jika basuh baju atau cas EV pada waktu luar puncak.",
    ]),
    ("Outage", "Bekalan elektrik terputus di rumah saya — apa nak buat?", [
        "Lihat skrin Outages — kawasan anda mungkin sudah disenaraikan.",
        "Jika tidak, tekan 'Report Outage' untuk laporkan alamat anda.",
    ]),
    ("Smart Meter", "Apakah maksud LED merah berkelip pada meter pintar?", [
        "LED merah berkelip menandakan penggunaan Utility aktif — ini normal.",
        "Jika LED malap menyala merah tetap, hubungi Careline Utility.",
    ]),
]


# Service Centre (Utility service centres) — real branches across Malaysia
KEDAI_Utility: list[dict] = [
    {"name": "Service Centre Wangsa Maju", "city": "Kuala Lumpur",
     "state": "Wilayah Persekutuan", "lng": 101.7373, "lat": 3.2050,
     "phone": "1300-88-5454", "hours": "Mon–Fri 08:30–17:00"},
    {"name": "Service Centre Bangsar", "city": "Kuala Lumpur",
     "state": "Wilayah Persekutuan", "lng": 101.6792, "lat": 3.1294,
     "phone": "1300-88-5454", "hours": "Mon–Fri 08:30–17:00"},
    {"name": "Service Centre Petaling Jaya", "city": "Petaling Jaya",
     "state": "Selangor", "lng": 101.6334, "lat": 3.1052,
     "phone": "1300-88-5454", "hours": "Mon–Fri 08:30–17:00"},
    {"name": "Service Centre Shah Alam", "city": "Shah Alam",
     "state": "Selangor", "lng": 101.5335, "lat": 3.0717,
     "phone": "1300-88-5454", "hours": "Mon–Fri 08:30–17:00"},
    {"name": "Service Centre Subang Jaya", "city": "Subang Jaya",
     "state": "Selangor", "lng": 101.5848, "lat": 3.0438,
     "phone": "1300-88-5454", "hours": "Mon–Fri 08:30–17:00"},
    {"name": "Service Centre Johor Bahru", "city": "Johor Bahru",
     "state": "Johor", "lng": 103.7548, "lat": 1.4720,
     "phone": "1300-88-5454", "hours": "Mon–Fri 08:30–17:00"},
    {"name": "Service Centre Iskandar Puteri", "city": "Iskandar Puteri",
     "state": "Johor", "lng": 103.6628, "lat": 1.4889,
     "phone": "1300-88-5454", "hours": "Mon–Fri 08:30–17:00"},
    {"name": "Service Centre Penang Bayan Lepas", "city": "Bayan Lepas",
     "state": "Pulau Pinang", "lng": 100.2776, "lat": 5.3328,
     "phone": "1300-88-5454", "hours": "Mon–Fri 08:30–17:00"},
    {"name": "Service Centre Ipoh", "city": "Ipoh", "state": "Perak",
     "lng": 101.1063, "lat": 4.6201, "phone": "1300-88-5454",
     "hours": "Mon–Fri 08:30–17:00"},
    {"name": "Service Centre Kuantan", "city": "Kuantan", "state": "Pahang",
     "lng": 103.3043, "lat": 3.8232, "phone": "1300-88-5454",
     "hours": "Mon–Fri 08:30–17:00"},
]


def _polygon_around(lng: float, lat: float, half_width: float = 0.012) -> dict:
    """Square GeoJSON polygon (closed ring) around a point.

    half_width≈0.012° ≈ 1.3km — the kind of footprint a localised
    distribution outage would actually cover.
    """
    return {
        "type": "Polygon",
        "coordinates": [[
            [lng - half_width, lat - half_width],
            [lng + half_width, lat - half_width],
            [lng + half_width, lat + half_width],
            [lng - half_width, lat + half_width],
            [lng - half_width, lat - half_width],
        ]],
    }


def random_neighbourhood(rng: random.Random) -> tuple[str, str, str, str, float, float]:
    return rng.choice(NEIGHBOURHOODS)
