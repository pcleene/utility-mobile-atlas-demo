<!-- Portfolio repository -->

> **Utility Mobile App (Atlas Patterns)** — portfolio demonstration.
> SvelteKit + FastAPI showcasing sharding, time series, geospatial, AutoEmbed
>
> This is a sanitized public version of a real-world prototype. Client names,
> credentials, internal endpoints, and proprietary assets have been removed; all
> configuration is environment-driven (`.env.example`). Authored by
> [Paul Cleenewerck](https://github.com/pcleene).

---

# Utility App Clone — SvelteKit + FastAPI + MongoDB Atlas

A production-grade reference implementation of the **UtilityApp** mobile app
(National Utility — Malaysia's national electricity utility),
designed to look and feel like the real app while showcasing the **full
breadth of MongoDB Atlas** capabilities under a single coherent
domain.

It runs against a real Atlas cluster, scales the heavy collections to
**1 million customers and 10 million transactions** via range-sharded
collections, and uses **AutoEmbed → Voyage `voyage-4-large` (1024-d)**
for semantic search on a Careline conversation corpus.

```
┌─────────────────────────────────────────────────────────────────────────┐
│  SvelteKit 2 / Svelte 5 runes / Tailwind 4 / Lucide   (port 5173)        │
│  fade-up transitions · hand-rolled SVG charts · skeletons · SSE toasts   │
└─────────────────────────────────────────────────────────────────────────┘
                              │ REST + SSE
                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  FastAPI / Motor / Pydantic v2                        (port 8000)        │
│  routers: customers · accounts · bills · usage · outages · support · SSE │
│  services: tariff (RP4) · insights · change-stream tail                  │
└─────────────────────────────────────────────────────────────────────────┘
                              │ TLS+SRV
                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  MongoDB Atlas (sharded · 8.0 enterprise · Voyage AutoEmbed)             │
│   • Document model         (customers, accounts, bills)                  │
│   • Time series            (meter_readings_ts · 30-min granularity)      │
│   • Geospatial 2dsphere    (outage polygons · kedai_Utility · accounts)   │
│   • Aggregation framework  ($dateTrunc, $group, $rankFusion)             │
│   • Atlas Search (BM25)    (support_text_idx)                            │
│   • Atlas Vector Search    (support_autoembed_idx → Voyage 1024-d)       │
│   • Change Streams → SSE   (live bill / outage / notification toasts)    │
│   • Range sharding         (5 collections, observability-first chunk map)│
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Atlas capabilities, screen-by-screen

| Screen | MongoDB feature(s) demonstrated |
|---|---|
| **Home → account switcher** | Document model — accounts embedded in customer doc |
| **Home → current bill** | Aggregation `$lookup`-equivalent denormalised access pattern |
| **Home → outage card** | Geospatial `$geoIntersects` on a 2dsphere polygon |
| **Home → 7-day usage chart** | Time series collection + `$dateTrunc` + 2-stage `$group` |
| **Bills list** | Range-sharded `bills` (`{account_no, billing_period_end}`) |
| **Bill detail** | RP4 tariff math reconciles to itemised breakdown |
| **Usage page** | Time series aggregation with peak/off-peak split + insights |
| **Outages page** | Geospatial centroids → SVG map + change-stream-driven updates |
| **Support search** | Atlas Search (BM25) + Atlas Vector Search (AutoEmbed → Voyage) — hybrid `$rankFusion` with reciprocal-rank-fusion fallback |
| **Toast notifications (every screen)** | Mongo change streams → SSE |
| **`/health/cluster`** | `listShards` + `collStats` for live sharding observability |

---

## Quick start

### Prerequisites

- **Node.js 20+**
- **Python 3.11+**
- A **MongoDB Atlas cluster** with:
  - Atlas Search & Vector Search enabled (M10 or above)
  - The Voyage AI provider integration configured at the **project level**
    (Atlas → Project Settings → AI Provider Integrations → Voyage AI)
  - Sharding enabled if you want to demonstrate the chunk distribution
    (works on Atlas serverless or sharded dedicated clusters)

The connection string + Voyage API key in this repo's `backend/.env`
already point at an Atlas Enterprise 8.0 cluster with sharding, Vector
Search, and the Voyage integration pre-configured. Replace them for your
own deployment.

### 1 — Backend

```bash
cd backend
python3.11 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env       # then edit MONGODB_URI / VOYAGE_API_KEY
.venv/bin/uvicorn app.main:app --reload --port 8000
```

OpenAPI docs: <http://localhost:8000/docs>

### 2 — Seed data (idempotent)

The seed script supports three modes:

```bash
# 1) Quick — 10k customers / 100k transactions / 500 tickets   (~30s)
.venv/bin/python -m app.seed.seed_data --quick

# 2) Demo only — no bulk customers/txn at all                  (~10s)
.venv/bin/python -m app.seed.seed_data --no-bulk

# 3) Full — 1M customers / 10M transactions / 2k tickets       (~10–20 min on M30+)
.venv/bin/python -m app.seed.seed_data
```

The script:

1. Drops & recreates all collections (idempotent — safe to re-run)
2. Creates the **`meter_readings_ts` time series collection**
   (`timeField: ts`, `metaField: meta`, `granularity: minutes`)
3. Inserts the demo customer **`Ahmad bin Ismail`** (CUST-MY-00184729)
   with two linked accounts — JB (ToU residential) + Bangsar (general
   commercial) — plus realistic Malaysian neighbourhoods, IC formats,
   and bilingual touches
4. Generates **60 days of 30-min smart-meter readings** with realistic
   AM/PM peak shapes for residential and 9–7 business-hour shapes for
   commercial, including a `tariffPeriod` field computed from the timestamp
5. Generates **12 months of bills × 2 accounts** (24 bills) under the
   **July 2025 RP4 tariff schedule** — most recent residential bill =
   **UNPAID, due in 4 days**
6. Inserts **2 active outages** (one whose polygon intersects Ahmad's JB
   address) and **10 Service Centre** service centres with 2dsphere coords
7. Bulk-loads customers + transactions in 5k-document batches (~23k tx/s
   on M30 from your laptop)
8. Inserts **2,000 support tickets** with `embed_source.text` so the
   AutoEmbed index can populate vectors via Voyage in-cluster
9. Creates **regular indexes** for every routing pattern + the
   geospatial 2dsphere indexes
10. (If `ENABLE_SHARDING=true`) issues `enableSharding` + `shardCollection`
    for the five heavy collections with **range shard keys**
11. Issues `createSearchIndexes` for the **Atlas Search** lexical index
    and the **Atlas Vector Search** AutoEmbed index
12. Prints a per-collection count summary

### 3 — Apply the search indexes (if you didn't run the seed)

If you applied the seed end-to-end the indexes already exist. To create
them manually:

```bash
# Atlas CLI
atlas search indexes create --clusterName Cluster0 \
  --file backend/atlas_indexes/support_text_idx.json
atlas search indexes create --clusterName Cluster0 --type vectorSearch \
  --file backend/atlas_indexes/support_autoembed_idx.json
```

Or use the **Atlas UI** → Atlas Search / Atlas Vector Search → JSON
editor. See `backend/atlas_indexes/README.md` for the full walkthrough.

### 4 — Frontend

```bash
cd frontend
npm install
npm run dev          # http://localhost:5173
```

Build / preview:

```bash
npm run build && npm run preview
```

---

## Sharding observability

The seed shards five collections with **range** keys (not hashed) so
that `sh.status()` and `db.getSiblingDB('config').chunks.find()` return
ranges that map directly to the seed's structure — perfect for demos
and screen-captures.

| Collection | Shard key | Why |
|---|---|---|
| `customers` | `{customer_id: 1}` | Lexicographic prefix → contiguous Mongo chunks per customer cohort |
| `accounts` | `{customer_id: 1, account_no: 1}` | Co-locates a customer's accounts on the same chunk |
| `bills` | `{account_no: 1, billing_period_end: 1}` | Chunk per (account, recent-period) pair → bill-list query is single-shard |
| `transactions` | `{customer_id: 1, ts: 1}` | Customer-scoped time-range sweeps stay on one shard |
| `meter_readings_ts` | `{meta.account_no: 1, ts: 1}` | Time-series sharding constraint: ascending on the time field |

**Constraint reminder:** every unique index on a sharded collection must
be *prefixed* by the shard key. The seed therefore replaces the original
`bill_no_unique` and `transaction_id_unique` with **compound unique**
`{account_no, billing_period_end, bill_no}` /
`{customer_id, ts, transaction_id}` indexes. Lookup-by-id is preserved
via separate non-unique indexes.

Verify with:

```bash
curl http://localhost:8000/api/v1/health/cluster | jq
```

```jsonc
{
  "msg": "isdbgrid",                          // proves we're talking to mongos
  "shards": [{"_id": "atlas-...-shard-0", ...}, {"_id": "atlas-...-shard-1", ...}],
  "transactions_collstats": {
    "count": 100000,
    "sharded": true,
    "shards": ["atlas-...-shard-0", "atlas-...-shard-1"]
  }
}
```

In the Atlas UI, drill into **Cluster → Collections → `UtilityApp.transactions`
→ Distribution** to watch the balancer migrate chunks across shards over
the first few hours after seeding.

---

## Voyage AutoEmbed — what's actually embedded?

The application code **never** calls Voyage. Atlas does it
in-cluster, on every insert/update of `support_conversations.embed_source.text`,
using the project-level Voyage credential. The vector materialises
inside the index and is invisible to the application.

The leaf string the index points at is built deterministically from the
ticket category, title, summary, and resolution steps — that template
lives in `app/seed/seed_data.py::_embed_text` and **must remain stable**
or the existing corpus is invalidated on the next index rebuild.

The seed loads only **2,000 tickets** to demo the feature without
running up a Voyage bill.

---

## Repo layout

```
UtilityApp-clone/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app + lifespan + CORS
│   │   ├── config.py            # pydantic-settings reads .env
│   │   ├── db.py                # Motor client + collection-name constants
│   │   ├── models/              # Pydantic v2 schemas (customer, bill, …)
│   │   ├── routers/             # customers, bills, usage, outages,
│   │   │                        # support, events (SSE), health
│   │   ├── services/
│   │   │   ├── tariff.py        # RP4 math (Energy / Capacity / Network /
│   │   │   │                    # Retail / AFA · ToU peak/off-peak)
│   │   │   └── insights.py      # Usage coach (week-on-week trends)
│   │   └── seed/
│   │       ├── seed_data.py     # idempotent end-to-end seeder
│   │       └── realism.py       # Malaysian neighbourhoods + names
│   ├── atlas_indexes/           # JSON for both Atlas Search indexes
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── routes/              # +layout, +page, bills/, bills/[billNo]/,
│   │   │                        # usage/, outages/, support/, more/
│   │   ├── lib/
│   │   │   ├── api.ts           # typed fetch wrapper
│   │   │   ├── stores.svelte.ts # Svelte 5 runes — session, toasts
│   │   │   ├── sse.ts           # EventSource client
│   │   │   ├── format.ts        # MYR / kWh / dates / time-of-day
│   │   │   ├── types.ts         # mirror of Pydantic models
│   │   │   └── components/      # AppBar, BottomTabBar, AccountCard,
│   │   │                        # CurrentBillCard, UsageGlanceCard,
│   │   │                        # UsageMiniChart, OutageBanner,
│   │   │                        # MalaysiaMap, PaySheet, PromoStrip,
│   │   │                        # QuickActions, Skeleton, StatusPill,
│   │   │                        # TimeBanner, Toasts
│   │   ├── app.css              # design tokens + skeletons + sheets
│   │   └── app.html
│   ├── svelte.config.js
│   ├── vite.config.ts
│   └── package.json
├── docker-compose.yml           # one-shot dev convenience
└── README.md
```

---

## Demo flows worth showing

1. **Home → account switcher → Bills**
   Tap the JB (TOU residential) card. The current-bill card pulses
   orange because it's due in 4 days. Tap **Pay Now** to see the
   bottom sheet slide up; tap **Pay** again to see the success state.

2. **Bill detail**
   The breakdown reconciles line-for-line to the RP4 schedule —
   Energy peak/off-peak, Capacity 4.55 sen, Network 12.85 sen, Retail
   waived because total ≤ 600 kWh, AFA rebate.

3. **Usage page**
   Switch between Daily and Monthly. The hand-rolled SVG chart
   re-animates. The "Insights" card surfaces a peak-share warning if
   ≥55% of usage is during the 14:00–22:00 peak window.

4. **Outages → map**
   The pulsing dot near JB is Ahmad's substation outage. Tap **Report**
   to insert a `notifications` document — within ~1 second a toast
   appears in the top-right driven by the Mongo change stream → SSE
   pipeline.

5. **Support → hybrid search**
   - Type `"how can I save money on my bill"` (EN) — vector search
     surfaces the BM Tarif ToU article (cross-lingual match)
   - Type `"bekalan elektrik terputus"` (BM) — Vector matches the BM
     outage runbook before any lexical hits
   - Type `"JomPAY 8881"` — lexical and vector both match the JomPAY
     ticket (`matched_via: hybrid`)

6. **`curl /api/v1/health/cluster`**
   Shows `msg: isdbgrid` (mongos), the two Atlas shards, and the
   `sharded: true` flag on the transactions collection.

---

## Configuration reference (`backend/.env`)

| Variable | Default | Notes |
|---|---|---|
| `MONGODB_URI` | — | mongodb+srv://<user>:<password>@<cluster>.mongodb.net/<db> (must point at a sharded cluster for full demo) |
| `MONGODB_DB` | `UtilityApp` | Database name |
| `VOYAGE_API_KEY` | — | Used by the seed for status logging only — Atlas calls Voyage from your project integration |
| `VOYAGE_MODEL` | `voyage-4-large` | Must match the AutoEmbed index definition |
| `VOYAGE_DIMENSIONS` | `1024` | Implied by the model — declarative only |
| `CORS_ORIGINS` | `http://localhost:5173,...` | Comma-separated |
| `DEMO_CUSTOMER_ID` | `CUST-MY-00184729` | Hard-bound demo session |
| `SEED_CUSTOMERS` | `1000000` | Override for full bulk |
| `SEED_TRANSACTIONS` | `10000000` | Override for full bulk |
| `SEED_EMBEDDED_TICKETS` | `2000` | Keeps the Voyage bill bounded |
| `SEED_TIMESERIES_DAYS` | `60` | Demo range |
| `SEED_TIMESERIES_INTERVAL_MINUTES` | `30` | Smart-meter cadence |
| `ENABLE_SHARDING` | `false` | Set to `true` only on a sharded cluster |

---

## Production hardening checklist (out of scope for the prototype)

- [ ] Replace the hardcoded `DEMO_CUSTOMER_ID` with real auth (MyDigital ID, JWT)
- [ ] Move the Voyage API key out of `.env` — it's only there because the
  AutoEmbed integration is project-level on Atlas
- [ ] Add request-level rate limiting in front of the SSE endpoint
- [ ] Add `pytest` integration tests against a Mongo in-memory replica
- [ ] Wire OpenTelemetry / Datadog tracing through Motor + FastAPI
- [ ] Pre-build the SvelteKit app on a real adapter (vercel / node)
- [ ] Localise the BM/EN copy via a real i18n bundle

---

## Acknowledgements

- Tariff schedule: National Utility's RP4 (effective 1 July 2025)
- Voyage AI: `voyage-4-large` 1024-dimensional embedding model
- Stock UtilityApp UI patterns informed the orange + clean-white visual language
- Built end-to-end as a portfolio reference for MongoDB Atlas
