# S11 — Mobility pack: curating the best of the mobility-v2 model into v5

**Date:** 2026-06-11 · **Status:** ideation — curation locked pending approval
**Source:** `azold:~/sgp-mobility-v2/dist/data/hex8_adequacy.geojson` (1,191 hexes ×
208 props, same hex8_id grid → direct join) + 12 overlay geojsons.
**Principle:** not a bulk import. Every column earns its place with a stated USE;
duplicates, display bands, and legacy fields stay out.

## Verdict counts

| Bucket | Count | |
|---|---|---|
| TAKE | ~88 | new signal, joins as-is (some renamed) |
| DERIVE | 3 | aggregated from overlay geometries |
| SKIP | ~117 | duplicate of v5 / display-only / legacy / bookkeeping |

---

## TAKE — by family, with the use case

### T1 · Travel-time anchors (12) — the functional-position signature
`time_to_{cbd, orchard, jurong_east, one_north, changi_business, tampines_hub,
nus, ntu, sgh, cgh, kkh, ttsh}_min`
- **Embedding:** the FLOW view's backbone — a 12-dim "where am I in the functional
  city" vector no training trick can synthesize. Likely replaces the OD-role
  loss term (E3) entirely.
- **Showcase:** "45 minutes of Singapore" story; report-card Access row.
- **nous:** office/clinic segment anchors (time_to_sgh for medical clusters).

### T2 · Destination reach (6)
`n_dest_reachable, n_dest_within_45min, pct_dest_within_45min,
pct_dest_within_60min, n_lines_to_cbd, n_stations_walking`
- Network centrality, precomputed. Complements labor_pool_45m (people-reach)
  with place-reach.

### T3 · MRT effective-reach model (8)
`mrt_reach_eff_min, mrt_reach_walk_min, mrt_reach_bus_min, mrt_reach_bus_wait_min,
mrt_reach_crowd, mrt_reach_index, mrt_reach_n_feeders, mrt_reach_mode` (categorical)
- Multi-leg effective MRT access (walk vs feeder-bus vs none) — strictly richer
  than dist_mrt_m. nous P8 (morning commute) upgrade.

### T4 · Service quality (4)
`peak_wait_min, peak_wait_bus_only_min, peak_wait_mrt_only_min, crowding_load_factor`
- Frequency + crowding — the quality axis taps don't capture. Embedding FLOW view;
  showcase "what the map doesn't show: waiting" beat.

### T5 · Adequacy v3 suite (rename to `adq_*`, 14)
`adq_default, adq_core, adq_v2, adq_default_{elderly,family,workers},
adq_core_{elderly,family,workers}, adq_gap_default, adq_gap_core, adq_gap_equity_max,
adq_availability_v2, adq_worst_factor_value` + categorical `adq_worst_factor`,
`adq_primary_factor`, `adq_primary_gap_reason`
- The validated per-profile adequacy model (Telok Blangah −24pts calibration).
- **Rename rationale:** raw names collide semantically with v5's saturation `gap_*`.
- Showcase report-card "Access verdict"; Govern-lens stories; nous equity guard.

### T6 · Factor scores (rename `adq_f_*`, 12)
`adq_f_{accessibility, connectivity, distance, last_mile, line_pressure,
low_frequency, reach_gap, children_gap, elderly_gap, dorm_gap, fdw_gap, low_income_gap}`
- The WHY behind adequacy. Per-profile demand legs for nous (P4 senior ← elderly_gap,
  P10 blue-collar ← dorm_gap). Skip their *_band twins (display).

### T7 · 15-minute city (14)
`min15_score, min15_{essentials,health,retail,school},
min15_count_{essentials,health,retail,school},
min15_nearest_{clinic,hawker,park,school,super}_m`
- Calibrated (Toa Payoh 100 / LCK 13). Replication Lab tile (Moreno) gets its
  columns into the master at last. Embedding WHERE view.

### T8 · Population fine-splits (8)
`pop_resident_citizen, pop_resident_pr, pop_nr_ep, pop_nr_fdw, pop_nr_sp,
pop_nr_wp_other, low_income_pop, walking_dependent_count`
- Pass-type breakdown v5 lacks (has only aggregate + dorm). WHO view; nous
  segment demand (FDW → services, EP → premium F&B); equity stories.
- Skip pop_nr_dorm (≡ pop_dorm).

### T9 · Vulnerability & equity (7)
`vulnerability_share, vulnerability_penalty, access_vuln_share,
access_vuln_penalty, crowd_sensitive_share, crowd_equity_penalty` + the 3
per-profile vulnerability penalties folded into T5 profiles? → keep base 6 only;
profile penalties are internal to adq scores (skip).

### T10 · Micro transit/walk infrastructure (13)
`ped_crossings_count, ped_greenman_count, lrt_stations, lrt_stations_in_500m,
dist_to_nearest_lrt_m, bus_stops_in_400m, bus_stops_in_800m, mrt_stations_in_500m,
mrt_stations_in_1km, nearest_mrt_st_peak_taps, last_mile_friction,
multimodal_score, transit_mode_count`
- Last-mile texture. nous transit_hub formats; embedding WHERE view.

### T11 · Context one-offs (3)
`industrial_adjacency_score` (novel guard signal), `zone_type`, `zone_type_broad`
- zone_type FINALLY lands in the master (today it exists only in the explorer
  export mask). Feasibility mask for nous; NA-handling everywhere.

## DERIVE from overlays (3)
| New column | From | Method |
|---|---|---|
| `linkway_len_m` | covered_linkway.geojson (7,012 segs) | clip-to-hex length sum — sheltered-walk density, the most Singapore feature there is |
| `cycling_path_len_m` | cycling_paths.geojson (5,257) | same |
| `linkway_per_road_km` | derived | linkway_len / road_length_total — shelter coverage ratio |

## SKIP — and why (so nobody re-litigates)
- **Duplicates of v5 (≈45):** pop_resident/total/density, elderly/children/working_age
  counts (≡ pop_65plus/0_14/15_64), lu_*, lat/lng/parent_*, bldg_*, dist_{bus,clinic,
  hawker,park,school,super,nearest_mrt}, bus/mrt/transit_daily_taps, bus_routes_count,
  mrt_stations, silver_zones_count, poi_*, hdb_pop_share, walk_mrt_score, land_use_entropy,
  bus/mrt_taps_per_capita (recomputable), cbd_km + cbd_proximity_score (inferior to
  time_to_cbd_min).
- **Display/presentation (≈35):** every `*_band`, `primary_text_*`, `pop_callout_*`.
- **Legacy (5):** `*_legacy` fields.
- **Bookkeeping (6):** `_od_done, is_data_shown, is_scored, cell_active_flag,
  mrt_reach_validated, mrt_reach_band, mrt_reach_dist_m (≡ dist_mrt)`.
- **Internal compound gaps (≈10):** availability/quality/frequency/crowding/reach/
  resilience `*_adequacy_gap` + per-profile variants — components already inside
  adq_* scores; keep the suite lean (revisit on demand).

## Build & gates (standard protocol)
1. `build_mobility_pack.py`: fetch geojson from azold app dir (deployed = validated
   truth) → select TAKE set → renames (`adq_` family) → overlay derivations →
   `hex/hex8_mobility_pack.parquet` (~91 cols).
2. `validate_mobility_pack.py`:
   - M1 join integrity: 1,191/1,191 hex8_id match, zero NaN introduced by join
   - M2 dedupe audit: every TAKE col |r| < 0.98 vs all 703 v5 cols (else move to SKIP)
   - M3 archetype anchors: Telok Blangah adq penalty visible; time_to_cbd ~5min CBD
     / >60min Lim Chu Kang; min15 Toa Payoh≈100; linkway density peaks in mature HDB
   - M4 zone_type: non-residential PAs flagged NA per the established rule
   - M5 redundancy + NaN semantics accounting
3. Merge as S11 → master ~794 cols → catalogs (curated descriptions all ~91) →
   explorer detail group → checkpoint v5.2.0 → push v5 → verify.

## What this buys the embedding (the reason we paused for it)
FLOW view: +30 cols incl. the 12-dim anchor signature (probably deletes the E3
OD-role loss term). WHERE view: +linkways/last-mile. WHO view: +pass-type splits.
Plus zone_type as the training mask (exclude non-scored hexes from contrastive
negatives — industrial vs nature confusion is noise we no longer have to learn).
