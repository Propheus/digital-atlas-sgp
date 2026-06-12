# Plexis SGP v5.1.0 — Feature Metadata Validation Report

**Generated:** 2026-06-11  
**Atlas path:** `/Users/sumanth/propheus-projs/da-sgp/digital-atlas-sgp/plexis-sgp-v5/`  
**Method:** Read-only inspection of catalog files, master parquets, manifests, and validation logs. No data mutations.

---

## Executive Summary

Plexis SGP v5.1.0 is a **well-structured, validation-gated geospatial atlas** with machine-readable feature metadata at scale. The catalog is **largely trustworthy for production use**, with a few metadata hygiene issues to fix before Nous upgrades from v4 → v5.

| Check | Result |
|---|---|
| Feature catalog row count | **2,518** — matches checkpoint + manifest |
| Descriptions present | **2,518 / 2,518 (100%)** |
| Curated vs pattern-derived | **1,347 curated + 1,171 pattern** |
| Dataset catalog file existence | **48 / 48 present** |
| Dataset shape accuracy | **48 / 48 match** (rows × cols) |
| Master parquet ↔ catalog column alignment | **PASS** — zero orphan columns in masters |
| Sample stats validation (null_pct) | **PASS** — 0 mismatches in 30-feature sample |
| Embedding files on disk | **2 / 10 present** locally |
| `atlas_manifest.json` freshness | **STALE** — reports v4.8.0 shapes |

**Bottom line:** The feature metadata is real, complete, and internally consistent for tabular features. The main gaps are (1) stale manifest, (2) place-level micrograph features not catalogued, (3) embedding catalog overstates local availability, and (4) site-selection layers S1–S9 are hex8-only while `cap_*` / `colo_*` also exist at hex9.

---

## 1. Atlas Overview

### Spatial scales

| Scale | Cells | Master cols | Join key | Master file |
|---|---|---|---|---|
| **hex9** (H3 res-9, ~0.10 km²) | 7,318 | **583** | `hex9_id` | `hex/hex9_all_features.parquet` |
| **hex8** (H3 res-8, ~0.74 km²) | 1,191 | **703** | `hex8_id` | `hex/hex8_all_features.parquet` |
| **subzone** (URA MP2019) | 326 | **389** | `subzone_c` | `hex/subzone_all_features.parquet` |
| **place** (POI) | 190,591 | **27** | `id` | `places/sgp_places_final.parquet` |

Population baseline: **6,036,900** (SingStat Jun-2024). Total indexed data: **~305 MB** across 250 files (per `CHECKPOINT_v5.1.0.json`).

### Version lineage

- **v5.0.0** = v4.10.0 content rebranded; adds site-selection layers **S1–S9** (85 hex8 cols)
- **v5.1.0** = adds **S10 context pack** (16 hex8 cols): conservation, carparks, polyclinics, wet markets, petrol, coworking, condos, female pop share, BTO pipeline

---

## 2. Metadata Artifacts

### Where metadata lives

| Artifact | Path | Format | Rows | Purpose |
|---|---|---|---|---|
| **Feature catalog** | `catalog/feature_catalog.parquet` | Parquet | 2,518 | Per-column definitions, stats, provenance |
| Feature catalog (human) | `catalog/feature_catalog.md` | Markdown | 2,518 | Same content, browsable |
| Feature catalog (apps) | `catalog/feature_catalog.json` | JSON | 2,518 | App consumption (symlinked from v4 extension, content matches parquet) |
| **Dataset catalog** | `catalog/dataset_catalog.parquet` | Parquet | 48 | Per-file inventory with shapes |
| Dataset catalog (human) | `catalog/dataset_catalog.md` | Markdown | 48 | Browsable index |
| **Embedding catalog** | `catalog/embedding_catalog.json` | JSON | 10 | Embedding specs + paths |
| **Atlas manifest** | `catalog/atlas_manifest.json` | JSON | — | High-level bundle summary |
| Data catalog (narrative) | `DATA_CATALOG.md` | Markdown | — | Human orientation doc |
| Site-selection spec | `SITE_SELECTION_METRICS.md` | Markdown | — | S1–S10 metric definitions |
| Site-selection validation | `SITE_SELECTION_VALIDATION.md` | Markdown | — | Per-layer gate results |
| Checkpoint | `CHECKPOINT_v5.1.0.{json,md}` | JSON+MD | — | Build manifest + validator summary |

### Feature catalog schema

Each of the 2,518 rows carries:

| Column | Coverage | Notes |
|---|---|---|
| `column` | 100% | Feature name |
| `scale` | 100% | hex9 / hex8 / subzone / place / matrix |
| `dataset` | 100% | Source parquet path |
| `dtype` | 100% | Arrow dtype |
| `description` | 100% | Human-readable definition |
| `desc_source` | 100% | `curated` (1,347) or `pattern` (1,171) |
| `null_pct` | ~94% | Validated against actual data (sample: 0 mismatches) |
| `min`, `max`, `mean`, `median` | ~94% | Distribution stats |
| `n_unique`, `sample` | ~94% | Cardinality + example values |
| `units` | 53% (1,347) | Present for curated entries |
| `source_stage` | 100% | Pipeline stage owner (e.g. `all`, `S1`, `S10`) |
| `derivation` | 1% (30) | Formula documentation — **sparse** |

### Description quality by scale

| Scale | Curated | Pattern | Total |
|---|---|---|---|
| hex8 | 571 | 467 | 1,038 |
| hex9 | 454 | 428 | 882 |
| subzone | 290 | 275 | 565 |
| place | 26 | 1 | 27 |
| matrix | 6 | 0 | 6 |

Pattern-derived descriptions follow templated text (e.g. `mg_cafe_coffee_pressure_400m` → "Magnet model: 400m distance-decayed SAME-category competitive pressure for cafe coffee"). These are consistent and machine-parseable but less specific than curated entries.

---

## 3. Catalog ↔ Data Validation Results

### 3.1 Master bundle alignment — PASS

Every feature column in the three master parquets is documented in `feature_catalog.parquet`. Zero orphan columns found.

| Master | Actual feature cols | Catalog `all_features` entries | Delta |
|---|---|---|---|
| hex9 | 577 | 583 | +6 join-key/parent cols counted as features in catalog |
| hex8 | 698 | 703 | +5 join-key/parent cols |
| subzone | 388 | 389 | +1 (`subzone_c`) |

The catalog intentionally includes join keys (`hex9_id`, `parent_pa`, etc.) as feature entries. Consumers filtering to "model features only" should exclude keys and parent hierarchy columns.

### 3.2 Dataset catalog — PASS

All 48 catalogued datasets exist on disk. All 48 reported `(n_rows, n_cols)` match actual parquet metadata exactly.

### 3.3 Places layer — PASS

All 27 columns in `places/sgp_places_final.parquet` are catalogued at `scale=place`. Perfect 1:1 match.

### 3.4 Place micrograph — GAP

`places/sgp_places_micrograph.parquet` has **19 feature columns** (plus `id`). **None are in the feature catalog.**

Missing columns include:
- `pmg_competitors_400m`, `pmg_competitors_800m`, `pmg_closest_competitor_m`
- `pmg_complements_400m`, `pmg_complements_800m`, `pmg_complement_diversity`
- `pmg_anchors_400m`, `pmg_anchors_800m`
- (and 11 more place-level micrograph fields)

These **are** represented at hex scale as `mg_*` rollup columns (75 in hex8 master, 225 catalog entries across all scales/datasets). The gap is place-level granularity only — relevant if Nous Scout or Alchemist needs per-place competition context.

### 3.5 Stats accuracy — PASS (sampled)

30 random hex8 features: `null_pct` in catalog matches actual parquet values within 0.5 percentage points for all samples.

### 3.6 Manifest drift — FAIL (stale)

`catalog/atlas_manifest.json` reports outdated shapes:

| Bundle | Manifest shape | Actual shape | Column delta |
|---|---|---|---|
| hex9_all_features | 7,318 × **558** | 7,318 × **583** | +25 |
| hex8_all_features | 1,191 × **548** | 1,191 × **703** | +155 |
| subzone_all_features | 326 × **388** | 326 × **389** | +1 |

Manifest version field says **4.8.0** while checkpoint says **5.1.0**. Feature count (2,518) is current; bundle shapes are not.

**Impact:** Any consumer reading `atlas_manifest.json` for column counts will undercount v5 features by 155 hex8 columns.

### 3.7 JSON symlink note

`catalog/feature_catalog.json` and `catalog/dataset_catalog.json` are symlinks to:
```
plexis-sgp-v4/extensions/20260505-235911/
```
Content was verified to match the v5 parquet catalogs (2,518 rows, v5 columns like `dt_pop`, `bto_pipeline_est` present). The symlink target name is misleading but content is current.

---

## 4. Feature Inventory by Family (hex8 master)

The hex8 master (`703` columns) decomposes into these families:

| Family | Cols | Key prefixes / examples | Site-selection relevance |
|---|---|---|---|
| **Site-selection S1–S10** | 96 | `dt_*`, `iso_*`, `cap_*`, `biz_*`, `colo_*`, `labor_*`, `vis_*`, `rent_*`, `roi_*`, `pipe_*`, `cons_*`, `carpark_*`, `bto_*`, `condo_*` | **Primary** — built for retail site selection |
| **Spatial rings / pop-weighted** | 142 | `ring1_*`, `ring2_*`, `pw1_*`, `pw2_*`, `max1_*`, `max2_*` | Neighbour context, emergent gap signals |
| **Place composition v1** | 85 | `pc_*` (24 categories) | Demand/supply category counts |
| **Place composition v2** | 59 | `pc2_*` (55 categories) | Finer taxonomy |
| **Micrograph rollup** | 75 | `mg_*_pressure_400m`, `mg_*_support_400m`, `mg_*_anchor_strength` | **Nous Scout supply dimension** |
| **Amenities & schools** | 67 | `school_*`, `chas_*`, `hawker_*`, `polyclinic_*`, `wet_market_*` | Anchor/gate signals |
| **Transit & GTFS** | 49 | `mrt_*`, `bus_*`, `gtfs_*`, `daily_train_taps` | Accessibility, daytime demand |
| **Walkability** | 41 | `walk_*`, `ped_*`, `dist_*` | Format-fit gates |
| **Buildings** | 31 | `bldg_*`, `hdb_*`, `est_far` | Feasibility, cost proxies |
| **Satellite / night lights** | 31 | `nl_*`, `wc_*` | Commercial vibrancy |
| **OD mobility** | 29 | `od_*` | Breathing / temporal mismatch |
| **NVIDIA personas** | 33 | `nvp_*` | Affluence, demographic segments |
| **Population** | 23 | `pop_*`, `nonres_*`, `pop_dorm` | Core demand drivers |
| **Composites** | 23 | `vibrancy_index`, `commercial_intensity`, `livability_index` | Scout anchor/demand |
| **Demand pull (gravity)** | 19 | `pull_cbd`, `pull_mall`, `pull_hospital` | Anchor proximity |
| **Land use** | 19 | `lu_*`, `dominant_use` | Feasibility guardrails |
| **HDB resale** | 15 | `hdb_resale_*` | Affluence / rent tier |
| **Roads / traffic** | 15 | `road_*`, `centr_*`, `vis_*` | Visibility, access |
| **Saturation / gap** | 9 | `gap_*` | Category-level supply gaps |
| **Synergy** | 8 | `syn_*` | Cross-feature interactions |
| **Commercial activity** | 6 | `ca_*`, `commercial_activity_index` | Daytime commercial intensity |
| **Other** | 50 | `avg_gpr`, `family_index`, `transit_score`, etc. | Mixed utility |

---

## 5. Site-Selection Layers (S1–S10) — Detailed Inventory

All layers validation-gated per `SITE_SELECTION_VALIDATION.md`. Status: **all PASS** as of 2026-06-11.

### Scale availability matrix

| Layer | Prefix | hex8 cols | hex9 cols | Primary use |
|---|---|---|---|---|
| **S1** Huff capture | `cap_*` | 13 | **13** | Outlet-equivalent capture potential (11 categories) |
| **S2a** Walk isochrone | `iso_walk10_*` | 12 | 0 | Network walk catchments |
| **S2b** Transit isochrone | `iso_transit15_*` | 5 | 0 | 15-min transit reach |
| **S3** Daytime population | `dt_*` | 8 | 0 | AM commuter headcount, lunch demand |
| **S4** ACRA business | `biz_*` | 10 | 0 | Formation/churn, live business density |
| **S5** Labor shed | `labor_*` | 4 | 0 | Jobs reach within 30/45-min transit |
| **S6** Co-location fit | `colo_*` | 11 | **11** | Mix-match vs 24×24 lift matrix |
| **S7** Visibility | `vis_*` | 6 | 0 | MRT exit footfall, traffic exposure |
| **S8** Rent surface | `rent_*`, `roi_*` | 8 | 0 | URA resi rent + capture-per-rent ROI |
| **S9** Future pipeline | `pipe_*` | 5 | 0 | New MRT + FAR dev capacity |
| **S10** Context pack | `cons_*`, `carpark_*`, etc. | 16 | 0 | Conservation, carparks, polyclinics, BTO |

**Key finding for Nous:** Site-selection metrics are **hex8-primary**. Only `cap_*` and `colo_*` are replicated at hex9. If Nous continues ranking at hex9 (current CRUCIBLE behaviour), it must either:
- Join hex8 site-selection features down to hex9 via parent mapping, or
- Shift ranking grain to hex8

### S10 context pack columns (new in v5.1.0)

| Column | Description | Source |
|---|---|---|
| `cons_bldg_count` | URA conserved building count | URA MP19 SDCP (7,235 buildings) |
| `cons_cluster_flag` | Heritage cluster flag (≥20 conserved bldgs) | Derived |
| `carpark_count_hdb` | HDB carpark count | HDB Carpark API |
| `carpark_capacity_lots` | Total car lot capacity | 696K lots |
| `polyclinic_count` / `dist_polyclinic_m` | Polyclinic proximity | OSM (27 clinics) |
| `wet_market_count` / `dist_wet_market_m` | Wet market proximity | NEA hawker layer (63 markets) |
| `petrol_station_count` / `dist_petrol_m` | Petrol station coverage | OSM (201 stations) |
| `coworking_count` | Coworking venue density | Atlas places match (171 venues) |
| `condo_project_count` / `condo_txn_units` | Condo project density | URA PMI transactions (2,384 projects) |
| `female_pop_share` | Female population share | SingStat 2025 (subzone-broadcast) |
| `bto_uc_units_town` | BTO under-construction units | HDB FY2024 (91,941 units) |
| `bto_pipeline_est` | FAR-headroom allocated pipeline estimate | Derived |

Raw point files delivered to Nous: `nous_export/` (10 files, all sanity-PASS per README).

---

## 6. Embeddings Metadata

`catalog/embedding_catalog.json` documents **10 embeddings**:

| Name | Dim | Scale | Method | Local file |
|---|---|---|---|---|
| `hex9_embedding_where_64d` | 64 | hex9 | PCA (84% var) | ✅ Present |
| `hex9_embedding_node2vec_64d` | 64 | hex9 | Node2Vec | ❌ Missing |
| `hex9_embedding_gcn_64d` | 64 | hex9 | 2-hop GCN + PCA | ❌ Missing |
| `hex9_embedding_combined_128d` | 128 | hex9 | PCA concat | ✅ Present |
| `hex9_embedding_super_128d` | 128 | hex9 | concat[node2vec, gcn] | ❌ Missing |
| `place_embedding_what_64d` | 64 | place | PCA | ❌ Missing |
| `place_embedding_place2vec_64d` | 64 | place | Word2Vec co-location | ❌ Missing |
| `place_embedding_combined_128d` | 128 | place | PCA concat | ❌ Missing |
| `place_embedding_super_128d` | 128 | place | concat | ❌ Missing |
| `place_embedding_mega_256d` | 256 | place | Full ensemble | ❌ Missing |

**Only 2 of 10 embedding parquets exist on this Mac copy.** `DATA_CATALOG.md` notes the 5 graph embeddings (node2vec, gcn, super, place2vec, mega) exist on canonical build host `atlas-1` but were not deployed locally. Nous Prism currently references `mega_256d` — **unavailable in this v5 tree**.

GNN embeddings (`plexis_v3/v6_embeddings.npz`) are referenced in docs but not present in the v5 root listing.

---

## 7. Validation Gate Summary

From `CHECKPOINT_v5.1.0.md` — core pipeline validators:

| Validator | Pass | Warn | Fail |
|---|---|---|---|
| transit | 6 | 0 | 0 |
| population | 6 | 0 | 0 |
| place_composition | 6 | 0 | 0 |
| embeddings | 5 | 0 | 0 |
| buildings_clean | 5 | 1 | 0 |
| schools | 6 | 0 | 0 |
| land_use | 6 | 0 | 0 |
| amenities_extra | 10 | 0 | 0 |
| composites | 5 | 1 | 0 |
| road_centrality | 4 | 1 | 0 |
| non_resident | 5 | 0 | 0 |
| satellite | 3 | 2 | 0 |
| buildings | 5 | 1 | 0 |
| roads | 6 | 2 | 0 |
| demand_pull | 7 | 0 | 0 |
| hdb_resale | 6 | 0 | 0 |

Site-selection layers S1–S10 each have dedicated validators with documented PASS results in `SITE_SELECTION_VALIDATION.md`. Notable quality finding: `breathing_idx` was redefined to AM-directional form after validation proved the old form was direction-blind (ρ=0.996 with full-day OD).

---

## 8. Implications for Nous (v4 → v5 upgrade)

### What Nous uses today (v4)

| Nous component | v4 features relied on |
|---|---|
| Scout demand | `pop_nonresident`, `daily_train_taps`, `pop_hdb`, `pop_resident` |
| Scout supply | `mg_<category>_pressure_400m` (75 mg_* rollups) |
| Scout anchor | `mall_count`, `commercial_intensity`, `near_mrt_400m` |
| Gap Analyzer | `pw1_pc_cat_*`, `od_*`, demand/supply from hex8 |
| Architect | Same Scout columns + synthetic revenue |
| Prism | `place_embedding_mega_256d`, `hex9_super_128d` |

### What v5 adds that Nous should adopt

| v5 feature family | Why it matters |
|---|---|
| `dt_*` (daytime pop) | Fixes office-hub demand undervaluation (PLQ-type cases) |
| `iso_*` (isochrones) | True network catchments vs H3 k-rings |
| `cap_*` (Huff capture) | Direct "what would a new outlet capture?" signal |
| `biz_*` (ACRA) | Business formation/churn — dynamic market vitality |
| `colo_*` (co-location) | Mix-match scoring with validated 24×24 lift matrix |
| `rent_*` / `roi_*` | Cost feasibility beyond PA tier heuristics |
| `pipe_*` (future supply) | Forward-looking whitespace |
| S10 context pack | Carparks, conservation, BTO pipeline — Nous gap analyzer wish-list |

### Upgrade blockers identified

1. **Grain mismatch:** v5 site-selection is hex8; Nous ranks hex9
2. **Embedding gap:** `mega_256d` not on disk in v5 Mac copy
3. **Manifest stale:** automated tooling may read wrong column counts
4. **Micrograph place-level:** 19 `pmg_*` cols undocumented (hex rollup exists)

---

## 9. Findings & Recommendations

### ✅ Strengths

1. **100% feature descriptions** — every column has text; rare at this scale
2. **Dual catalog format** — parquet for machines, markdown for humans
3. **Provenance tracking** — `desc_source`, `source_stage`, `dataset` per feature
4. **Distribution stats baked in** — null_pct, min/max/mean/median enable automated QA
5. **Validation-gated pipeline** — site-selection layers don't merge until gates pass
6. **Nous integration path** — `nous_export/` delivers raw points; S10 merged into hex8 master

### ⚠️ Issues found

| # | Issue | Severity | Recommendation |
|---|---|---|---|
| 1 | `atlas_manifest.json` stale (v4.8.0 shapes) | Medium | Regenerate from `build_catalog.py` on each release |
| 2 | 8/10 embedding files missing locally | High (for Nous) | Sync from atlas-1 or rebuild; update embedding catalog `exists` flag |
| 3 | Place micrograph (`pmg_*`) not in feature catalog | Low | Add 19 place-scale entries or document intentional omission |
| 4 | `derivation` field 99% empty | Low | Backfill for site-selection + mg_* pattern features |
| 5 | Site-selection S1–S9 hex8-only | Medium (for Nous) | Document join recipe hex8→hex9; or build hex9 rollups |
| 6 | JSON catalog symlinks point to v4 path | Low | Retarget symlinks to v5/catalog/ or copy files |
| 7 | `units` only on curated entries | Low | Acceptable; pattern entries infer units from dtype |

### Recommended next steps

1. **Regenerate `atlas_manifest.json`** to v5.1.0 with correct shapes (703/583/389)
2. **Sync missing embeddings** before Nous v5 cutover (especially `mega_256d`)
3. **Publish hex8→hex9 join recipe** for site-selection features in `DATA_CATALOG.md`
4. **Add place micrograph** to feature catalog (19 rows) for completeness
5. **Nous Scout v6 templates** — incorporate `dt_*`, `cap_*`, `colo_*`, `rent_*` into brand_format manifests

---

## 10. Quick Reference — Key Files

```
plexis-sgp-v5/
├── catalog/
│   ├── feature_catalog.parquet    ← 2,518 features (AUTHORITATIVE)
│   ├── feature_catalog.md         ← human-readable twin
│   ├── dataset_catalog.parquet    ← 48 datasets
│   ├── embedding_catalog.json     ← 10 embeddings (2 on disk)
│   └── atlas_manifest.json        ← STALE — do not trust shapes
├── hex/
│   ├── hex8_all_features.parquet  ← 1,191 × 703 (PRIMARY for site selection)
│   ├── hex9_all_features.parquet  ← 7,318 × 583
│   └── subzone_all_features.parquet
├── places/
│   ├── sgp_places_final.parquet   ← 190,591 × 27
│   └── sgp_places_micrograph.parquet ← 19 cols NOT in catalog
├── nous_export/                   ← S10 raw points for Nous gap analyzer
├── DATA_CATALOG.md                ← orientation
├── SITE_SELECTION_METRICS.md      ← S1–S10 specs
├── SITE_SELECTION_VALIDATION.md     ← gate evidence
└── CHECKPOINT_v5.1.0.json          ← build manifest
```

### Load recipe

```python
import pandas as pd

ROOT = "/Users/sumanth/propheus-projs/da-sgp/digital-atlas-sgp/plexis-sgp-v5"

# Masters
h8 = pd.read_parquet(f"{ROOT}/hex/hex8_all_features.parquet")   # 1191 × 703
h9 = pd.read_parquet(f"{ROOT}/hex/hex9_all_features.parquet")   # 7318 × 583

# Metadata
feat = pd.read_parquet(f"{ROOT}/catalog/feature_catalog.parquet")  # 2518 rows
ds   = pd.read_parquet(f"{ROOT}/catalog/dataset_catalog.parquet")  # 48 datasets

# Lookup a feature
row = feat[feat["column"] == "cap_cafe_coffee"].iloc[0]
print(row[["scale", "description", "null_pct", "mean", "desc_source"]])

# Site-selection cols only
ss_prefixes = ("dt_", "iso_", "cap_", "biz_", "colo_", "labor_", "vis_", "rent_", "roi_", "pipe_", "cons_", "carpark_", "bto_", "condo_")
ss_cols = [c for c in h8.columns if c.startswith(ss_prefixes)]
print(f"Site-selection features in hex8: {len(ss_cols)}")
```

---

*Report generated by automated catalog validation against on-disk parquets. No atlas data was modified.*