# Atlas places fixes V2 — DONE (response to nous ATLAS_TEAM_FIXES_V2)

**From:** Plexis Atlas team · **Date:** 2026-06-18 · **Atlas:** Plexis SGP **v5.6.1**
**Output:** `sgp_places_final.parquet` (190,591 × 36) · backup `backups/places_v2_*`

| # | Issue | Status | Result |
|---|---|---|---|
| 1 | Residual store-code / pin duplicates | ✅ | dedup **271 → 1,497** via 60m spatial + name-normalized merge (strips `CKN5`-style codes, "Car Park"/"Drop-off" suffixes); `is_duplicate` + `canonical_id`. 189,094 canonical. Filter `is_duplicate==False` for supply. |
| 2 | Sparse `brand` ⭐ | ✅ | **15,127 → 21,204 (7.9% → 11.1%)**. Per-category (nous-cited): shopping_retail **3%→14%**, restaurant **4%→13%**, health_medical **10%→14%**, cafe_coffee **17%→26%**. Method: 150-chain SG dictionary (+848) + conservative Haiku LLM (+5,229, null for independents). |
| 3 | Stall-level operator | ✅ | `operator`/`parent_brand` field added — 410 food-court/coffeeshop stalls (Koufu, Kopitiam, Foodfare, Food Republic…). |
| 4 | Demand feed (airport/stadium/campus) | ⏭ P2 | mobility-feed task, not places — separate. |
| 5 | place2vec degenerate | ⏭ note | shipped place embedding is **plexis-p1** (exam-gated), not the old place2vec. |
| 6 | 0-reviews ambiguity | ⚙ partial | `zero_reviews` flag present; true `first_seen` unavailable in source. |

**Downstream:** `pc_unique_brands` refreshed into hex8/hex9/subzone masters; manifest + feature_catalog regenerated; **CHECKPOINT_v5.6.1**. Non-destructive (backup retained).

**Note:** brand is now conservative (LLM returns null when unsure), so 11.1% is *high-precision* coverage — independents are correctly left unbranded rather than mislabelled.
