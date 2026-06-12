# Hex Features v10 — Catalog

**Rows:** 7,318 hexes (H3 res 9, all 327 Singapore admin subzones with ≥1 hex)
**Columns:** 322 (raw) / 319 (normalized, bookkeeping excluded)
**File:** `data/hex_v10/hex_features_v10.parquet`
**Normalized:** `data/hex_v10/hex_features_v10_normalized.parquet`

## Pillar summary

| # | Pillar | Cols | Source | What it captures |
|---|---|---|---|---|
| 1 | `identity` | 8 | hex_universe | hex_id, lat/lng, area, parent_subzone/pa/region |
| 2 | `buildings` | 19 | Overture+HDB+OSM fused (377K) | Counts by 9 types, floor areas, avg/max floors & height |
| 3 | `population` | 5 | Census 2025 dasymetric | population, children, elderly, working age, walking dependent |
| 4 | `land_use` | 12 | URA 113K parcels area-weighted | 9 zoning-bucket shares, entropy, avg_gpr |
| 5 | `transit` | 7 | MRT/bus geojsons + LTA PV | Station/stop counts, daily tap volumes |
| 6 | `amenities` | 9 | data.gov.sg geojsons | hawkers, clinics, preschools, hotels, attractions, etc. |
| 7 | `roads_signals` | 22 | V9 copy-through (LTA + OSM) | 6 road categories, signals, ped crossings, jam/flow |
| 8 | `walkability` | 24 | V9 copy-through (OSM) | Walk-times, walk-scores, dist-to-amenity |
| 9 | `place_composition` | 66 | 174K v2 places | 24 cats counts+shares, 5 tiers, brands, HHI, entropy |
| 10 | `micrograph` | 20 | v2 66K + 2.9K cafe | T1-T4 context means, anchor counts, density bands |
| 11 | `influence_spatial_max` | 31 | H3 k=5 ring | Densest commercial hex within ~875m walk |
| 12 | `influence_spatial_pw` | 30 | H3 k=5 ring | Place-weighted mean of walking neighborhood |
| 13 | `influence_transit_max` | 30 | MRT graph (209 stations, 3,716 edges) | Densest hex reachable by MRT |
| 14 | `influence_transit_pw` | 30 | MRT graph | Place-weighted mean of transit reach |
| 15 | `influence_scalars` | 2 | Derived | MRT distance, transit reachable count |
| 16 | `development_gaps` | 4 | URA zoning vs building footprint | Plan-vs-reality: residential, commercial, industrial sub-gaps |
| 17 | `bookkeeping` | 3 | Dasymetric denominators | Excluded from normalized matrix |

## Why influence features replaced k-ring

Original v10 had 150 k-ring features (5 aggregates × 30 basis). Testing showed:
- `contrast_*`: **-1.2%** (hurts — local deviation is noise for similarity)
- `rank_*`: **-2.9%** (hurts — ordinal within 6 neighbors doesn't encode context)
- `nbr2_mean_*`: +4.5% (only useful one, but drowned by contrast/rank)
- **Net k-ring lift: +2.0%**

Replacement influence features (4 views × 30 basis = 124):
- **Net influence lift: +29.9%** (119% relative improvement)
- Key insight: spatial neighbors (walking) + transit neighbors (MRT) capture complementary context that k-ring averages miss

## Influence basis (30 features)

| Group | Features |
|---|---|
| Demographics (5) | population, elderly_count, children_count, walking_dependent_count, residential_floor_area_sqm |
| Buildings (3) | bldg_count, hdb_blocks, bldg_footprint_sqm |
| Transit (2) | mrt_stations, bus_stops |
| Commercial (11) | pc_total, pc_cat_{restaurant, cafe, shopping, hawker, health, education, office, bar}, pc_unique_brands, pc_cat_entropy |
| Land use (4) | lu_residential_pct, lu_commercial_pct, lu_business_pct, avg_gpr |
| Micrograph (5) | mg_mean_{transit, competitor, complementary, demand, anchor_count} |

## Normalization

| Rule | Formula | Applied to |
|---|---|---|
| `sqrt` | √(max(x,0)) | Counts, floor areas, influence features |
| `passthrough` | x → x | Shares, entropies, micrograph means, walk scores |
| `distance_decay` | exp(-d/500m) | walk_*_m, dist_*_m |

Post-transform: z-score (μ=0, σ=1). NaN → 0 with mask preserved. Stats in `_normalization_stats.json`.

## What's NOT at hex level

| Feature | Why | Where it lives |
|---|---|---|
| Personas (35) | PA-broadcast (48 unique across 318 subzones) | Subzone / PA |
| HDB prices | No geocoding (town+block+street → no lat/lng) | Subzone |
| Private prices | Same | Subzone |
| elderly_pct | Collapses to subzone constant under dasymetric | Subzone |
| Gap scores | V7/V8 model outputs — leakage | Targets table |

## Development gap features (4 columns) — satellite-inspired

Derived from URA zoning vs actual building footprint. Captures plan-vs-reality mismatch without satellite rasters.

| Feature | Formula | What it identifies |
|---|---|---|
| `ura_development_gap` | (lu_res + lu_com + lu_bus + lu_inst) − total_footprint_ratio | Overall: is this hex built to plan, underdeveloped, or overbuilt? |
| `gap_residential` | lu_residential_pct − residential_footprint_ratio | Zoned residential but not built → future HDB/condo sites |
| `gap_commercial` | (lu_commercial + lu_mixed_use) − commercial_footprint_ratio | Zoned commercial but not built → retail/office opportunity |
| `gap_industrial` | lu_business_pct − industrial_footprint_ratio | Zoned business but not built → industrial expansion room |

All 4 are mutually low-correlated (max r = 0.637 between ura_gap and gap_industrial; gap_res vs gap_com = 0.024).

**Archetype validation:**

| Archetype | ura_gap | gap_res | gap_com | gap_ind |
|---|---|---|---|---|
| CBD | +0.00 | +0.05 | **+0.30** | +0.00 |
| HDB heartland | +0.34 | **+0.32** | +0.02 | +0.12 |
| Industrial belt | +0.43 | +0.01 | -0.00 | **+0.64** |
| New towns | +0.36 | **+0.31** | +0.02 | +0.08 |

CBD has commercial gaps, heartlands have residential gaps, industrial belt has industrial gaps. Each sub-gap tells a different story.

## Satellite features — what was evaluated and decided

### Tested and ADDED (derived, no rasters needed)

The 4 gap features above. Evidence: `ura_development_gap` has max |r| = 0.631 with any existing feature — carries independent signal.

### Tested and DROPPED

| Feature | Why dropped |
|---|---|
| `nightlife_intensity` (bars + 0.5×hotels + 0.2×restaurants / total) | r = 0.915 with `pc_pct_cat_bar_nightlife` already in the table — redundant |

### Evaluated and NOT ADDED (data not locally available)

| Feature | Value assessment | What's needed |
|---|---|---|
| **Night light temporal change (2022→2024)** | **HIGH** — UNIQUE signal. Zero temporal features in v10. Cannot be approximated from any current source. | VIIRS annual composites (.tif), free download ~100MB |
| **Tree canopy cover (ESA WorldCover 10m)** | **MODERATE** — actual greenery vs "open space" zoning. Genuinely different from lu_open_space_pct. | ESA WorldCover download, ~100MB for SG tile |
| Night light radiance (absolute) | **LOW** — r ~0.95 with pc_total. Mostly redundant. | VIIRS 2024 .tif |
| Satellite-derived population | **LOW** — Census 2025 dasymetric is authoritative. | WorldPop .tif |
| Water body / bare soil extent | **LOW** — partially derivable from building absence + URA zoning. | ESA WorldCover |
| sat_dev_index composite | **LOW** — opaque composite, no clear added value. | Satellite report data |

### Why night light radiance (absolute) is redundant with pc_total

Tested via synthetic proxy: commercial activity proxy (pc_total × 10 + commercial_floor_area / 100 + sfa_eating × 5 + hotels × 50 + bars × 20) correlates r = 0.948 with pc_total. Night light radiance is fundamentally a proxy for the same commercial density signal our place count already captures. The marginal signal (actual illumination patterns, signage brightness) adds ~5% information.

## Known gaps

1. Micrograph is v2 local only. v3 on server covers 174K per-category.
2. Roads/signals/walkability NaN for 1,421 new hexes (V9 copy-through only).
3. 5 micro-subzones are sub-hex-size (combined pop ~20).
4. Transit graph is MRT-only. Adding bus routes would extend reach.
5. **Night light temporal change** — the single most valuable satellite upgrade. Requires VIIRS .tif download.
6. **Tree canopy cover** — second most valuable satellite upgrade. Requires ESA WorldCover download.
