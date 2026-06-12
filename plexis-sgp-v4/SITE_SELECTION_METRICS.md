# Plexis SGP v4 — Site-Selection Metrics: Spec & Build Plan

**Date:** 2026-06-10
**Status:** Spec approved-pending — build one metric at a time, validation gate between each.
**Motivation:** The atlas (hex8: 1,191 × 601) describes *what a hex is* but not *what a new
outlet there would capture*. Nothing today models choice (competition), true catchments
(network distance), cost (rent), or time (daypart, pipeline). These 9 metrics close that gap.

**Primary scale:** hex8 (~0.74 km², the site-selection grain; matches OD/personas layers).
hex9 only where micro-scale matters (S7). Each metric ships as its own layer following the
v4 convention: `build_<name>.py` + `validate_<name>.py` + `hex/hex8_<name>.parquet` +
validation report, merged into the master only after its gate passes.

---

## Metric inventory

| # | Metric | Prefix | Cols | Tier | Depends on | New ingestion |
|---|---|---|---|---|---|---|
| S3 | Daytime population | `dt_` | ~5 | 1 | — (cols exist) | none |
| S2 | Isochrone catchments | `iso_` | ~10 | 1 | walk graph | none |
| S1 | Huff capture potential | `cap_` | ~14 | 1 | S2 distances | none |
| S4 | Business formation & churn (ACRA) | `biz_` | ~7 | 1 | OneMap geocode | none (API calls) |
| S6 | Co-location lift | `colo_` | ~13 + matrix | 1 | — | none |
| S5 | Labor-shed / jobs-reach | `labor_` | ~4 | 1 | GTFS graph | none |
| S7 | Micro visibility (MRT exits, traffic-pass) | `vis_` | ~5 | 1.5 | — | MRT exits geojson (tiny) |
| S8 | Commercial rent | `rent_` | ~5 | 2 | S1 (for ratio) | URA API / data.gov.sg |
| S9 | Future supply pipeline | `pipe_` | ~6 | 2 | — | BTO + GLS + future MRT |

~70 new columns total. Naming follows existing per-family prefixes (`od_`, `ca_`, `nvp_`).

---

## S3 — Daytime population  (build first: trivial, validates the harness)

**What:** Absolute headcount present in the hex during working hours. `breathing_idx`
(z-score) already exists; operators need the absolute number and the day/night ratio.

**Formula:**
```
trips_to_persons = od_*_am_monthly / 22 weekdays / 1.0 trips-per-person-per-AM-window
dt_pop      = pop_resident − persons_out_am + persons_in_am      (clip at 0, report clips)
dt_ratio    = dt_pop / max(pop_resident, 1)
dt_class    = {job_center, balanced, bedroom} by dt_ratio thresholds (>1.5, 0.67–1.5, <0.67)
dt_lunch_demand = dt_pop weighted by pc_cat_business_office share   (lunch-driven F&B signal)
```
Transit-only caveat: OD covers bus+train only — car/walk commuters invisible. Document as
known undercount; calibrate the trips→persons factor (see validation).

**Inputs (verified):** `od_in_am`, `od_out_am`, `pop_resident` in hex8 master.

**Validation gate:**
1. Conservation: Σ dt_pop ≈ Σ pop_resident nationally (OD nets to ~0) — tolerance ±5%.
2. Archetypes: CBD hexes (Raffles Place, Tanjong Pagar) dt_ratio ≫ 1; Toa Payoh/Yishun
   residential hexes < 1; industrial dorm hexes (Tuas) behave sanely with pop_dorm.
3. No hex with dt_pop > 5× its (pop + od_in persons) — formula bug guard.
4. ~~corr(dt_ratio, breathing_idx) > 0.8~~ **AMENDED 2026-06-10:** breathing_idx turned
   out to be direction-blind (full-day in≈out, ρ=0.996; breathing ≈ throughput-vs-pop,
   ρ=0.999) and mis-scores interchange town centres as job centers. Replaced with a
   discriminant test: dt_net must predict office presence better than breathing_idx
   (it does: 0.31 vs 0.20 on pc2 office counts). Follow-up at Phase 8: redefine the
   explorer's breathing_idx to the AM-directional form.
5. Calibration: published LTA/SingStat daytime-pop figures for CBD if findable; else
   plausibility band (CBD daytime ~10–20× resident).

---

## S2 — Isochrone catchments  (the foundation layer)

**What:** Population / spend / places reachable within a 10-min walk and 15-min transit of
each hex8 centroid, computed on the real network instead of fixed k-rings. Rings treat an
expressway and a park connector identically; isochrones capture severance.

**Method (amended during S2a build — see SITE_SELECTION_VALIDATION.md):**
- Pedestrian graph from `data/roads/roads.geojson` (550,991 edges, already topologized
  u/v). Walkable = everything except motorway/trunk(+links). Walk speed 4.8 km/h →
  10 min = 800 m network distance. **Origin = activity centroid** (places mean →
  pop-weighted → geometric), **k=4 multi-source Dijkstra** (single-node centroid snap
  proved enclave-fragile). **Demand = node-field**: hex9 population distributed onto
  the network nodes inside each hex9 (centroid snapping quantizes too hard at 800 m).
- Transit: 15-min budget = walk to stop + wait (headway/2 from GTFS) + in-vehicle + walk out.
  GTFS: `data/gtfs/singapore-gtfs.zip` (8M stop_times already parsed by build_gtfs_windows.py).
- Demand at reached hex9s allocated by network-distance share (hex9 grain for precision,
  output at hex8).

**Outputs:**
```
iso_walk10_pop, iso_walk10_spend (pop × nvp_affluence_idx), iso_walk10_places,
iso_walk10_competitor_free_pop_{cafe,supermarket}   (pop reached minus pop already
                                                     within 800m of an existing outlet)
iso_transit15_pop, iso_transit15_places
iso_severance_ratio = iso_walk10_pop / ring-equivalent pop   (low = barriers nearby)
```

**Validation gate:**
1. Upper bound: iso_walk10_pop ≤ population within 800 m euclidean ring, for every hex.
2. Severance spot-checks: hexes abutting AYE/PIE/MRT depots show iso_severance_ratio
   well below 1; open HDB estates ≈ 0.85–1.0.
3. Compare vs existing `walk_*` / `dist_*` columns — expect correlated but not redundant
   (flag any |r| > 0.9 → reconsider, per the v10 nightlife_intensity precedent).
4. Graph QA: connected-component count of walk graph; % of centroids snapping > 150 m
   to nearest node (must be < 2%).
5. Manual: pick 5 hexes, draw the isochrone polygon, eyeball on map vs Google Maps
   walking times.

---

## S1 — Huff capture potential  (the headline metric)

**What:** Expected demand a *new* outlet at hex h would capture, per category — competition-
adjusted. Turns `latent_demand` (a z-score heuristic) into expected customers. Reuses the
Huff machinery already built for scenario_sim (subzone) at hex8 grain.

**Formula (per category c):**
```
A_j  = attractiveness of existing supply in hex j = pc_cat_c_j × (1 + log1p(reviews_share_j))
f(d) = exp(−d / λ_c)                      d = S2 network walk distance (transit-blend for
                                          destination categories: shopping, attractions)
P(i chooses h) = A_h·f(d_ih) / (Σ_j A_j·f(d_ij) + A_h·f(d_ih))     A_h = 1 outlet
cap_c(h) = Σ_i D_i,c · P(i→h)
D_i,c = demand at hex i = (dt_pop or pop_resident, category-dependent) × national
        per-capita demand for c (total category demand / 6.04M, in outlet-equivalents)
```
~~λ_c calibrated per category~~ **AMENDED 2026-06-10: λ is ASSUMED, not calibrated.**
Finding: λ is not empirically identifiable from cross-sectional outlet data — the
placement test drives λ→100 m (overfits zoning adjacency), and the allocation test
never beats its degenerate λ→∞ baseline ρ(counts, reviews). Mitigation: capture
*rankings* are λ-robust (ρ≥0.91 across 400–1200 m), so behavioral priors carry it:
500 m walk-daily / 700 m neighborhood / 1000 m restaurant / 1500 m destination retail.
Also: **cap_bar_nightlife dropped** (ρ≈0 on both tests — bars follow culture, not
spatial demand; consistent with v7 finding #3). 11 categories ship.

**Outputs:** `cap_{cafe,restaurant,hawker,fast_food,supermarket,convenience,gym,clinic,
beauty,retail,education,bar}` (12 categories), `cap_total`, `cap_best_category`.

**Validation gate:**
1. Reproduction test: model-implied demand at existing-outlet hexes must rank-correlate
   with actual outlet counts per category (Spearman ≥ 0.6 on held-out subzones).
2. Marginality: inserting a synthetic competitor 200 m away must reduce cap_c — test on
   20 random hexes (monotonicity check).
3. Conservation: Σ over hexes of demand assigned ≤ national demand per category.
4. Archetypes: Orchard tops retail capture per-outlet? No — Orchard is saturated, so
   *capture for a new outlet* should be mid-pack there and high in underserved growth
   areas (Tengah, Punggol edges, Yunnan for supermarket — matches the known FairPrice
   desert finding). This inversion is the whole point; verify it happens.
5. Cross-check vs `gap_*` saturation features: directionally aligned (r > 0.3) but capture
   must add information (r < 0.85).

---

## S4 — Business formation & churn (ACRA)

**What:** Vitality and risk: where businesses form, survive, and die. No current layer
captures commercial mortality.

**Inputs (verified):** `data/business/acra_entities.csv` — 2,076,438 rows:
`uen, uen_status_desc, entity_type_desc, uen_issue_date, reg_street_name, reg_postal_code`.
~~Geocode via OneMap free API~~ **AMENDED 2026-06-10:** OneMap live API now requires an
auth token (unauthenticated → ~18/min + HTTP-200 error bodies). Used the offline dump
`xkjyeah/singapore-postal-codes` (141,726 buildings, 2026-04) instead — 94.24% entity
coverage, zero API calls.

**Known limitation:** no cessation *date* — only current status. So we get lifetime
dead-share and formation-rate cohorts, not a recent churn window. Documented, not fixable
from this file.

**Outputs:**
```
biz_live_count, biz_density_per_km2
biz_formation_5y   = entities issued 2021-06..2026-06 (count, live or not)
biz_dead_share     = deregistered / total ever registered        (lifetime mortality)
biz_recent_dead_share = deregistered among 2018+ cohorts          (closer to churn)
biz_median_age_yrs = median(today − uen_issue_date) of live entities
biz_entity_mix     = share local-company vs sole-prop (formality signal)
```

**Validation gate:**
1. Geocode coverage ≥ 93% of entities with non-null postal (report failures by reason).
2. corr(biz_live_count, pc_total): expect 0.5–0.85 — high is fine, 1.0 means we built
   nothing new; ACRA covers offices/holding cos invisible to POI data.
3. Spot-check 10 postal codes by hand (known buildings: Suntec, a HDB block, a Tuas factory).
4. National sums match file totals; no hex absorbs > 3% of all entities (a default-postal-code
   artifact would do this — e.g. virtual-office buildings; flag and report top-10 hexes).
5. Archetypes: CBD highest density; biz_dead_share elevated in older industrial estates.

---

## S6 — Co-location lift matrix

**What:** Learned synergy weights from 190K places: which categories actually thrive near
which. Replaces the 4 hand-built `syn_*` products with empirical PMI-style statistics.

**Formula:**
```
lift(A,B) = P(≥1 B-place within 400 m of an A-place) / P(≥1 B-place within 400 m of a
            random place location)            (null = category-blind location distribution)
colo_fit_c(h) = Σ_B log(lift(c,B)) · 1[count_B(h, 400m) > 0]     per candidate category c
```
Min support: pairs with < 200 A-places get NaN (no degenerate lifts). Bootstrap 95% CI
(200 resamples); only lifts whose CI excludes 1.0 enter colo_fit.

**Inputs (verified):** `places/sgp_places_final.parquet` (190,591 × 27, 24 categories).

**Outputs:** 24×24 lift matrix (`catalog/colo_lift_matrix.parquet`) + per-hex
`colo_fit_{12 major categories}` + `colo_anchor_score` (lift-weighted magnet proximity).

**Validation gate:**
1. Face validity: cafe↔office lift > 1, bar↔bar > 1 (known clustering), supermarket↔
   supermarket < 1 (spacing), gym↔residential > 1 (known finding #8: gyms follow families).
2. Stability: split places 50/50, recompute — lift estimates correlate r > 0.9.
3. colo_fit must not collapse to pc_total (|r| < 0.85).
4. Asymmetries are real, not artifacts: hawker→office vs office→hawker reviewed by hand.

---

## S5 — Labor-shed & jobs-reach

**What:** For office/industrial/large-format site selection (currently unserved): how many
workers can reach this hex within 45-min transit, and how many jobs can a resident here reach.

**Method:** Transit graph from GTFS (stops, headway-aware transfer costs — reuse S2 transit
machinery, just a bigger time budget) + first/last-mile walk. Working-age supply at residence
from `pop_15_64`-equivalent (pop − pop_65plus − pop_0_14). Jobs proxy at destination:
`biz_live_count` (S4) blended with `pc_cat_business_office` + dorm/industrial worker counts.

**Outputs:** `labor_pool_45m`, `labor_pool_30m`, `jobs_reach_45m`,
`labor_accessibility_pct = labor_pool_45m / national workforce`.

**Validation gate:**
1. Archetypes: CBD + Jurong East top labor_pool; Tuas low despite jobs (known transit gap);
   Changi mid.
2. Monotonic with transit_score (ρ > 0.5) but adds reach information rings can't see.
3. National anchor: from any central hex, labor_pool_45m should be a plausible share of
   the ~3.6M workforce (sanity band 30–60%, cross-check vs LTA reach statistics).
4. Symmetry audit: labor_pool (who can come here) vs jobs_reach (where I can go) diverge
   exactly at job-rich/transit-poor hexes — list top divergences, eyeball.

---

## S7 — Micro visibility (Tier 1.5 — narrowed)

ROADS_IDEATION.md §9–10 already specs expressway exits, frontage classes, parking; road
centrality + `dist_*` are in the master. Only what's missing:

```
vis_dist_mrt_exit_m      — LTA "MRT Station Exit" geojson (data.gov.sg, ~600 pts, tiny dl)
                           ≠ dist to station centroid: exits define real foot-traffic points
vis_exit_footfall        — taps at the parent station, split across its exits
vis_traffic_pass_proxy   — Σ (speed-band volume class × lane_km) on primary/secondary in hex
vis_corner_premium       — signalized intersections on main-road frontage (hex9 grain)
```
**Validation:** exits join 100% to the 231 stations; Orchard/Raffles exits top footfall;
vis_traffic_pass corr with known AADT corridors (PIE/CTE adjacency).

---

## S8 — Commercial rent (Tier 2 — ingestion)

**What:** The missing denominator. `cap_c / rent` = ROI layer; nothing in 601 cols prices a hex.

**Source:** URA Space API (free token) — retail + office median rentals $psf/mo by
locality/street, quarterly; fallback data.gov.sg URA rental-contract datasets. Broadcast:
locality → hex8 by containment, gap-fill by nearest-3 localities IDW. Resolution honestly
labeled (like `nvp_` PA-broadcast precedent).

**Outputs:** `rent_retail_psf_med`, `rent_office_psf_med`, `rent_resolution_flag`,
`rent_yoy_pct`, and after S1: `roi_capture_per_rent_{cat}`.

**Validation gate:** Orchard top-decile retail rent; Raffles top office; coverage ≥ 80% of
commercial hexes at locality resolution (report broadcast share); cross-check 5 localities
against published URA quarterly release numbers.

## S9 — Future supply pipeline (Tier 2 — ingestion)

**What:** Demand in 3 years. `nl_change_pct` sees the past; this sees the announced future.

**Sources:** HDB upcoming BTO launches (data.gov.sg, units + est completion), URA GLS site
list, future MRT stations (CRL ph2, JRL remaining, TEL ext — hand-curated static geojson
with opening years; ~50 stations).

**Outputs:** `pipe_new_dwellings_3y` (within 1 km), `pipe_pop_uplift_est` (units × 3.1
avg household), `pipe_new_mrt_within_800m`, `pipe_mrt_year`, `pipe_gls_commercial_gfa`.

**Validation gate:** Tengah/Bidadari/Punggol-north top dwelling uplift; national pipeline
total matches announced BTO supply figures at ingestion date; every future-MRT point
verified against LTA published alignment maps.

---

## Build order & gates

```
Phase 0  this doc + agree on gates                              ← you are here
Phase 1  S3 daytime pop          (hours; proves the harness)
Phase 2  S2 isochrones           (the foundation; walk+transit graphs built once)
Phase 3  S1 Huff capture         (consumes S2; headline deliverable)
Phase 4  S4 ACRA churn  ∥  S6 co-location   (independent of each other; S4 needs
                                             overnight geocode run — start cache early)
Phase 5  S5 labor-shed           (reuses S2 transit graph)
Phase 6  S7 visibility           (tiny ingestion)
Phase 7  S8 rent  ∥  S9 pipeline (Tier-2 ingestion)
Phase 8  merge → hex8 master, explorer "Opportunity" metric group, final HTML report
```

Gate protocol per metric (no metric merges without all five):
1. `validate_<name>.py` passes its numbered checks above (machine-checkable ones).
2. Correlation audit vs all existing master cols — any |r| > 0.9 with an existing feature
   is grounds to drop/redefine (v10 nightlife_intensity precedent).
3. Archetype spot-table (CBD / mature HDB / new town / industrial / saturated-prime)
   reviewed by hand.
4. Coverage + NaN accounting (which hexes are NaN and why — zone_type rules apply:
   non-residential PAs stay Not-Applicable, never silently 0).
5. One-page validation report appended to `SITE_SELECTION_VALIDATION.md`, sign-off,
   then merge + checkpoint.

## Cross-cutting decisions (locked unless overridden)

- hex8 is the canonical output scale; hex9 only for S7. Subzone rollups derived, not rebuilt.
- All distances network-based (S2 machinery), EPSG:3414 for metric ops.
- Demand uses dt_pop (S3) for daytime categories (cafe, fast food, office-lunch) and
  pop_resident for residential categories (supermarket, clinic, education) — per-category
  flag in config.
- NaN ≠ 0 everywhere; masks preserved like v10 normalization.
- Every layer gets its own parquet + validator; master merge only at Phase 8 (single
  re-export to explorer, not nine).
