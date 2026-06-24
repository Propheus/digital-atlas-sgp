# Atlas Team → nous Team — V5 Response

**Re:** `brand-analysis/ATLAS_TEAM_FIXES_V5.md` (optional improvements, post-v5.8.0)
**Atlas:** Plexis SGP **v5.8.1** · Data: `azold-test-server:/home/azureuser/da-sgp/v5/`

Thanks for the clean bill of health on v5.8.0. Here's where we land on the three optional asks.

| Ask | Verdict |
|---|---|
| **A1** — measured pedestrian-footfall layer | ⛔ **Declined — no data source** |
| **A2** — `store_perf_all` catalog↔disk | ✅ **Already consistent** (no change needed) |
| **A3** — observed retail rent in the 3 URA localities | ✅ **Done — observed anchors added** (v5.8.1) |

---

## A1 — Measured pedestrian footfall · **NO**

We have **no measured pedestrian-volume source** — no telco mobility-ping feed, no GPS/SDK visit
counts, no pedestrian-counter network licensed for this build. Sourcing one is a data-procurement
effort, not an engineering fix, and isn't on the table right now.

`retail_footfall_score` stays as the **modeled** demand signal (dt_pop-based, V4-decontaminated).
It already ranks the known hubs top-decile and your Anytime Fitness run was clean on it. If a
measured layer is later licensed, it slots in as `ped_volume_measured` with `retail_footfall_score`
as the documented fallback — but that's a future procurement, not v5.x.

## A2 — `store_perf_all` catalog↔disk · **Already consistent**

We checked the **v5.8.0** catalog directly:

- `store_perf` appears in **zero** catalog files (`grep -r store_perf catalog/` → nothing).
- The catalog↔disk invariant **passes**: **0 of 50** listed datasets are missing on disk.

So the v5.8.0 catalog does **not** list `derived/store_perf_all.parquet` — the entry you saw was
from a pre-v5.8.0 catalog (the old build did carry a `derived/` registry). Nothing to remove on our
side. `store_perf_all` remains a **NOUS-owned derived dataset** (your `scripts/build_store_perf.py`)
— it was never an atlas-produced layer, and the current catalog correctly doesn't claim it.

> Re-check: `ssh azold-test-server 'cd ~/da-sgp/v5 && python3 -c "import pandas as pd,os; dc=pd.read_parquet(\"catalog/dataset_catalog.parquet\"); print(sum(not os.path.exists(f\"{p}\") for p in dc.dataset))'`

## A3 — Observed retail rent · **Done (the right way)**

You asked to conserve `rent_retail_psf_med` to the observed URA locality medians. We tested literal
conservation and it **regresses the atlas**, so we delivered the same *intent* — defensible absolute
figures — without the damage.

**Why literal conservation was rejected** (measured on live data):
- URA publishes only a **blended locality median** (Orchard $8.59, Central-ex-Orchard $4.59,
  Outside-Central $5.15 psf/mo) — not prime ground-floor. At hex8 grain, "Orchard" is a **single
  cell**, so pinning it to the blended $8.59 erases the prime premium.
- Per-locality median-matching dropped the spread to **5.7×** (breaks V4 test A6 ≥8×), Orchard to
  **1.47×** heartland (breaks A6 ≥2×), and **inverted 160 suburban cells above Orchard**. That would
  regress exactly the V4 fixes you signed off on.

**What we shipped instead (v5.8.1)** — observed URA figures as **first-class anchor fields**, on hex8 + hex9:

| New column | Meaning |
|---|---|
| `rent_retail_locality_obs_psf` | **Observed** URA median retail rent for the cell's locality ($psf/mo): Orchard $8.59 · Central-ex $4.59 · Outside-Central $5.15 — the **defensible absolute** figure |
| `rent_retail_locality_obs_psm` | same in $psm/mo (×10.764) |
| `rent_retail_vacancy_pct` | **Observed** URA retail vacancy %: Orchard 6.5 · Central-ex 8.2 · Outside-Central 6.4 — a demand-side signal you didn't have |
| `rent_retail_n_obs` | URA records backing each locality (54 each) |

**Use this way:**
- **Absolute / defensible rent** → `rent_retail_locality_obs_psf` (observed, URA-sourced).
- **Within-grid ranking** → `rent_retail_psf_med` (modeled, unchanged — your tier-rent gate keeps working, V4 tests stay 30/30).

This gives you the observed truth where it exists (locality level) and keeps the modeled surface for
the per-cell ranking that locality medians can't provide. Bonus: vacancy is a new lever for demand.

---

## Status

- **Atlas v5.8.1** — hex8 `1191×855`, hex9 `7318×615`; manifest + catalog bumped; V4 acceptance
  **30/30** still green; 0 hex9 orphans. Backup `backups/v581_*`.
- **No blocking items.** A1 is a future procurement; A2 needs nothing from us; A3 is delivered.

---
*Atlas team · v5.8.1 · companion to `PLACES_FIX_RESPONSE_V4.md`.*
