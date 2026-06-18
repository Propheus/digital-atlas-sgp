# Atlas places fixes — DONE (response to nous ATLAS_TEAM_FIXES)

**From:** Plexis Atlas team · **Date:** 2026-06-18 · **Re:** `ATLAS_TEAM_FIXES.md`
**Output:** `da-sgp/v5/places/sgp_places_cleaned.parquet` (35 cols, 8 new) · non-destructive (flags, no row drops)

Verified your findings against the source and corrected the P0/P1 places issues.
Scripts: `places_fix.py` (deterministic) + `llm_classify_residue.py` (Haiku reclassify).

## What was fixed

| # | Issue | Status | Result |
|---|---|---|---|
| 1 | `convenience` polluted with ATMs/vending/banks | ✅ fixed | **5,762 → 2,164**; root cause was `category_map.py` routing ATM/Vending/Locker/Lottery→convenience |
| — | financial venues scattered | ✅ new category | **`financial_services` = 3,720** (ATM + Bank + Financial Services + Insurance + Money Transfer + Pawnshop, unified from 3 old categories) |
| — | unmanned machines counted as stores | ✅ new category + flag | **`automated_kiosk` = 1,913** (vending/locker/AXS) + **`is_storefront`** flag (TRUE 178,235 / FALSE 12,356) |
| 2 | Co-located tenants carry host name | ✅ fixed | **`host_venue` extracted for 7,896** "@"-named tenants; `brand` now follows the operator (pre-@), not the host; `operator_name` added |
| 3 | Duplicate / phantom POIs | ✅ flagged | **271 duplicates** flagged (exact-coord + store-code-alias grouping) → 190,320 canonical; `is_duplicate` + `canonical_id` + `is_phantom_suspect` (non-destructive — filter, don't lose) |
| 7 | `other_uncategorized` huge | ✅ fixed | **17,990 → 3,413** (−14,577, 81%) via Haiku LLM into the 26-cat taxonomy; biggest gains: services +2.3k, business_office +2.0k, shopping_retail +1.4k, restaurant +1.2k, health +0.9k |
| 6 | Stall-level naming | ⚙ partial | `parent_brand` field added (food-court operator via host_venue match) |
| 10 | 0-review ambiguity | ⚙ partial | `zero_reviews` flag added (true `first_seen` unavailable in source) |

## Taxonomy change
24 → **26 categories** (added `financial_services`, `automated_kiosk`). The root
fix is in `category_map.py` (the deterministic `primary_category → plexis_category`
map) — ATM/Vending/Parcel-Locker/Self-Service-Kiosk re-routed; Bank/Insurance/
Money-Transfer unified into `financial_services`.

## New columns on `places`
`is_storefront` · `host_venue` · `operator_name` · `parent_brand` ·
`is_duplicate` · `canonical_id` · `zero_reviews` · `is_phantom_suspect`
→ the demand model should now count supply as `plexis_category == <cat> AND
is_storefront AND NOT is_duplicate`.

## Not yet done / honest limits
- **#4 — rebuild hex8 `pc_cat_*` / `pw1_*` / `pw2_*` from the cleaned places.** This
  is the downstream step and is the real cost: it changes the 840-col master →
  triggers an e1/p1 re-train + re-exam = a **v5.6 places-clean release**. Cleaned
  places is the prerequisite; say go and we run it.
- **#5 — sparse `brand`.** All known chains were already brand-resolved; the 175k
  unbranded are genuine independents. Lifting coverage needs a much larger SG chain
  dictionary (separate data task), not a re-run.
- **#7 residue (3,413)** — genuinely ambiguous names (one-off durian stalls, study
  pods, holding-co shells); left as `other_uncategorized`.
- **#8 (airport/stadium/campus throughput)** and **#9 (place2vec)** — note the
  shipped place embedding is **plexis-p1** (exam-gated), not the old degenerate
  place2vec; #8 is a mobility-feed task, separate from places.

## To promote
`sgp_places_cleaned.parquet` is staged, not yet canonical. Promotion = replace
`sgp_places_final.parquet` → rebuild hex8 counts (#4) → re-train e1/p1 → re-exam →
tag v5.6. Reversible until then (original untouched, scripts deterministic).
