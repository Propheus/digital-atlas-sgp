# Atlas Team → nous Team — Consolidated Fixes Response

**Re:** `brand-analysis/ATLAS_TEAM_FIXES_CONSOLIDATED.md` (9 open items)
**Atlas:** Plexis SGP **v5.9.0** · Data: `azold-test-server:/home/azureuser/da-sgp/v5/`

Worked the whole residue list. **6 fixed, 1 confirmed-already-clean, 2 declined/deferred with reason.**
The category/brand fixes cascaded through `places → pc_cat → Huff demand → embeddings`, so the P0
Huff refit (#1) and the embedding refits (#8) are resolved as part of the same rebuild.

| # | Item | Verdict |
|---|---|---|
| **1** P0 | Refit Huff `cap_*`/`gap_*` on cleaned places | ✅ **Refit + confirmed** |
| **2** P1 | Pharmacy/H&B ≠ `health_medical` | ✅ **New `pharmacy_beauty` category** |
| **3** P1 | Gong Cha undercount + thin-brand sweep | ✅ **Swept** (Gong Cha = source gap) |
| **4** P1 | LAC + NTUC Healthcare Unity in `supermarket` | ✅ **Reclassified** |
| **5** P1 | Split NTUC subsidiaries | ✅ **Split** |
| **6** P2 | ~12 ATMs `is_storefront=true` | ✅ **Already 0** |
| **8** P2 | Confirm `plexis-p1` + packs refit | ✅ **p1 retrained; e1 retrained** |
| **7** P2 | Transient-hub demand feed | ⛔ **Declined** (no data) |
| **9** P2 | `first_seen` / `listing_age` | ⛔ **Deferred** (no source date) |

---

## 🔴 #1 — Huff demand (`cap_*`/`gap_*`) refit on cleaned places · **Done + confirmed**

Verified the supply was already clean (`pc_cat_convenience = 2,164`, the depolluted set), then
**regenerated the entire Huff layer** off it so there is no ambiguity:

- Re-ran `build_place_composition` → `build_huff_capture` → `build_saturation_gap` → `build_demand_pull`
  on the cleaned + recategorised places, and surgically merged the refreshed `pc_cat_*` / `cap_*` /
  `gap_*` / `sat_*` / `pull_*` into the master (V4/V5 fixes preserved).
- `cap_convenience` now computed off the **2,164** convenience set; **added `gap_convenience`**
  (it was previously absent from the saturation layer) so the depolluted convenience demand is
  explicit. `pull_hospital` is now clinic-only (retail pharmacies removed — see #2).
- **Acceptance met:** demand for re-bucketed categories tracks the clean supply.

## 🟠 #2 — Pharmacy / health-&-beauty ≠ `health_medical` · **New `pharmacy_beauty` category**

Created a **distinct `plexis_category = 'pharmacy_beauty'`** (27th category) and split the retail
chemists out of the clinic bucket so their demand is modeled on **retail footfall, not medical catchment**.

- **569 places** rerouted: Watsons (92), Guardian (128), Unity / NTUC Healthcare Unity, and all
  `primary_category='Pharmacy'` (515) — clinics/hospitals/TCM stay in `health_medical` (now 7,453 → 6,939).
- Wired into the Huff model (`lambda 700`, neighbourhood-retail) + saturation gap. **Demand now tracks
  shopping:** `corr(cap_pharmacy_beauty, retail_footfall_score) = 0.74` vs `corr(…, pull_hospital) = 0.22`.
- **Guardian brand_norm coverage 16 → 129** (the brand gap you flagged); Watsons consolidated to 92.
- **Acceptance met:** Guardian/Watsons demand tracks shopping catchment, not clinic catchment.

## 🟠 #3 — Gong Cha undercount + thin-brand sweep · **Swept; Gong Cha is a true source gap**

- **Swept the major chains:** KOI (91), CHICHA San Chen (35), Each-a-Cup (44), PlayMade (24),
  LiHO (53) already carry `brand_norm` — coverage is good. Filled the residual **R&B Tea (+5)**.
- **Gong Cha = 2 records is a genuine source gap** — only 2 exist in the underlying places data
  (no alternate spelling/venue filing found). We cannot manufacture stores that aren't ingested; a
  full Gong Cha footprint needs a new source pull, not a normalisation fix. Your `<5-store
  low-confidence` guard correctly flags it meanwhile.

## 🟠 #4 — LAC + NTUC Healthcare Unity out of `supermarket` · **Reclassified**

- **LAC Nutrition For Life (40 rows)** and **NTUC Healthcare Unity (1 row)** moved out of
  `plexis_category='supermarket'` → `pharmacy_beauty` (supplement / pharmacy retail). Supermarket 2,939 → 2,897.
- The separately-branded `Unity Pharmacy` rows were already correct and untouched.

## 🟠 #5 — Split NTUC subsidiaries · **Split**

- `brand_norm='NTUC FairPrice'` → split out **NTUC LearningHub (10)** and **NTUC Healthcare Unity
  (4)** into their own brands (the latter also recategorised to `pharmacy_beauty`, cross-ref #4).
  `NTUC Foodfare` had 0 rows still under the FairPrice brand_norm (already separate). Finest / Xpress /
  Cheers retained as legitimate FairPrice grocery formats.

## 🟡 #6 — Residual ATMs `is_storefront` · **Already 0**

Verified on v5.9.0: **0** records match `name ~ ATM` with `is_storefront=true`. Already resolved by
the prior storefront-classifier tightening.

## 🟡 #8 — `plexis-p1` + domain packs refit · **p1 retrained, e1 retrained**

- **plexis-p1 retrained.** The shipped p1 (2026-06-12) **predated** the v5.6 cleaned places — your
  #8(a) was correct. Retrained on the cleaned + recategorised places (`plexis_category` is a one-hot
  p1 input). **9/9 exam pass** — chain retrieval 0.814, category-kNN 0.997, geo-leak 0.077,
  forbidden-rating R² 0.094, 3-seed Procrustes 0.979–0.981. Re-shipped `place_embedding_plexis_p1_64d.parquet`.
- **plexis-e1 retrained** to absorb the new `pc_cat_pharmacy_beauty` input (e1 was already leak-free
  and on cleaned places per v5.8.0). Winner E1; **leak gate stays clean** — negative-control R²
  −0.001, known-twin panel 5/5, 3-seed Procrustes 0.918, probes honest (hdb 0.81 / od 0.87 / adq 0.95).
  Re-shipped `hex8_embedding_plexis_e1_256d.parquet`.
- **Domain packs:** the hero scores consume `cap_*`/footfall/industrial, all refreshed by this
  rebuild and re-merged into the master; packs remain excluded from embedding inputs (the v5.8.0 leak fix).

## 🟡 #7 — Transient-hub destination throughput · **Declined (no data)**

Airport pax / stadium events / campus footfall need a **destination-throughput feed** we do not have
licensed (same class as the declined V5/A1 measured-footfall layer). Your `SPECIAL_DEMAND` floor
remains the right mitigation until such a source is procured. No re-raise.

## 🟡 #9 — `first_seen` / `listing_age` · **Deferred (no source field)**

The source scrape carries **no listing-creation date**, so `first_seen` can't be derived without a
new dated ingest (or a longitudinal diff we'd have to start accumulating now). `zero_reviews` remains
the only available proxy. Flagged for a future dated pull.

---

## Status

- **Atlas v5.9.0** — hex8 `1191×861`, hex9 `7318×621`; `places/sgp_places_final.parquet` updated
  (new `pharmacy_beauty` category, brand splits). **V4 acceptance still 30/30**; 0 hex9 orphans.
- Backups: `backups/places_consol_*`, `backups/v581_*`; embedding `*.PRECONSOL.json`.
- Catalog + manifest bumped; new columns (`pc_cat_pharmacy_beauty`, `cap_/gap_pharmacy_beauty`,
  `gap_convenience`) documented.

---
*Atlas team · v5.9.0 · supersedes the per-round response files.*
