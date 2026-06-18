# Plexis SGP Atlas — Release Notes v5.6 (places-clean)

**Date:** 2026-06-18 · **Versions:** v5.6.0 (places clean) + v5.6.1 (dedup/brand/operator)
**Scope:** `places` table + the places-derived `hex8` features. Non-destructive; backups retained.

## TL;DR
The places table was cleaned, brand-resolved, de-duplicated, and re-categorised; the
demand-relevant hex counts (`pc_cat_*`, pop-weighted rings) were rebuilt from it.
**Action for consumers:** count supply as `is_storefront AND NOT is_duplicate`.

## What changed
- **Taxonomy 24 → 26 categories** — added `financial_services` (3,720: ATM+bank+insurance+remittance)
  and `automated_kiosk` (1,913: vending/locker/AXS). `convenience` depolluted **5,762 → 2,164**
  (ATMs/vending no longer counted as stores).
- **`other_uncategorized` 17,990 → 3,413** — reclassified into real categories (LLM).
- **Co-located tenants** — `brand` now = the operator, not the host ("Singapore Pools @ FairPrice"
  → brand `Singapore Pools`); new `host_venue` field.
- **De-duplication** — 1,497 store-code aliases / pin-duplicates flagged (`is_duplicate`,
  `canonical_id`); 189,094 canonical stores.
- **Brand coverage 7.9% → 11.1%** (high-precision; independents left null on purpose).
  Per category: shopping_retail 3→14%, restaurant 4→13%, health_medical 10→14%, cafe_coffee 17→26%.
- **`operator`/`parent_brand`** — food-court/coffeeshop operator (Koufu, Kopitiam, …).
- **hex8/hex9/subzone masters** — `pc_cat_*` rebuilt at 26 cats; `pw1/pw2/max1/max2` pop-weighted
  refreshed; `pc_unique_brands` refreshed. hex8 master 801 → **842 cols**.

## New columns on `places`
`is_storefront` · `host_venue` · `operator` / `parent_brand` · `is_duplicate` · `canonical_id`
· `zero_reviews` · `is_phantom_suspect`

## How to consume
- **Supply / competition counts:** filter `is_storefront == True AND is_duplicate == False`.
- **Category counts per hex:** `pc_cat_<cat>` (now incl. `pc_cat_financial_services`,
  `pc_cat_automated_kiosk`); convenience/business_office are now clean.
- **Brand analytics:** `brand_norm` (null = independent or unresolved, *not* an error).
- **Keys unchanged:** `id` (place), `hex8_id`, `subzone_c`. No row IDs changed.

## Not changed in this release (known)
- **`cap_*` / `gap_*` (Huff demand)**, **domain packs**, **plexis-e1/p1 embeddings** still reflect
  the pre-clean composition (partial refit pending). `cap_convenience` may over-count.
- **Brand** is precision-first — many true independents remain null by design.
- **Airport/stadium/campus throughput** still absent from the mobility/demand feed.
- No `first_seen`; `zero_reviews` is the only new/no-traffic signal.

## Where to get it (server location)
**Host:** `azold-test-server` · **Root:** `/home/azureuser/da-sgp/v5/`
(Git mirror: `github.com/Propheus/digital-atlas-sgp` → `plexis-sgp-v5/`, parquets via LFS.)

| Artifact | Path (under `/home/azureuser/da-sgp/v5/`) |
|---|---|
| Places (cleaned) | `places/sgp_places_final.parquet` (190,591 × 36) |
| Hex8 master | `hex/hex8_all_features.parquet` (1,191 × 842) |
| Hex9 / Subzone masters | `hex/hex9_all_features.parquet` · `hex/subzone_all_features.parquet` |
| Place composition (`pc_cat_*`) | `hex/hex8_place_composition.parquet` |
| Manifest / feature catalog | `catalog/atlas_manifest.json` · `catalog/feature_catalog.json` (v5.6.1) |
| Checkpoint | `CHECKPOINT_v5.6.1.json` |
| Backups (pre-change) | `backups/places_promote_*` · `backups/places_v2_*` |

**Pull example:** `scp azold-test-server:/home/azureuser/da-sgp/v5/places/sgp_places_final.parquet .`
