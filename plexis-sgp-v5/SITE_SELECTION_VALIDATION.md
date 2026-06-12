# Site-Selection Metrics — Validation Log

## S11 — Mobility pack (time_to_/adq_/min15_/mrt_reach_/linkway…) — **PASS** (2026-06-11)

**Layer:** `hex/hex8_mobility_pack.parquet` (98 cols) · build `build_mobility_pack.py`
(ran ON azold) · validator `validate_mobility_pack.py` (5/5 PASS) · curation spec
`S11_MOBILITY_PACK.md` (TAKE ~88 + 2 derived ratios + 3 overlay / SKIP ~117).

**Source:** the deployed mobility-v2 adequacy model (`sgp-mobility-v2/dist/data/`,
same 1,191-hex8 grid — direct join) + covered-linkway (7,012 segs → 245 km) and
cycling-path (897 km) overlays; ribbon-polygon centerline ≈ perimeter/2.

**Curation enforcement:** builder auto-drops any column with |r| ≥ 0.98 vs the
existing master — 10 dropped (mrt_reach_walk_min≈dist_mrt_exit_m r=.999, four
min15_nearest_*≈existing nearest-dists, citizen/PR/low-income LEVELS≈pop cols,
ped_crossings≈sig_pedestrian). Lost ratio signals re-derived as `pr_share` and
`low_income_share`, which survive on their own merit.

**Zone-type NA rule enforced at the data layer:** the source app masks
non-residential adequacy at DISPLAY time; the master now carries NaN for all
normative `adq_*`/vulnerability scores on 497 industrial/airport/nature/islands/
future hexes (factual metrics — time_to_*, min15, reach — stay: measurements).
M4 asserts 100% NA.

**Gate results:** join 1,191/1,191; dedupe held (max residual |r|=0.977);
archetypes — CBD 9 min, national max 66 min, Lim Chu Kang correctly NA
(non-scored), Toa Payoh min15=100, Telok Blangah elderly vulnerability penalty
present (small in this deployed build — the −24pt calibration was a profile-app
configuration; noted), linkway top-10 7/10 mature towns; ranges clean.

**Effect:** hex8 master 703 → **801 cols**; catalog 2,735 rows (196 S11-curated),
100% described; checkpoint **v5.2.0**; manifest 5.2.0; artifacts synced both
ways. The embedding FLOW view now has its 12-anchor signature — E3 (OD-role
loss term) likely unnecessary.

---

## S10 — Context pack (cons_/carpark_/polyclinic/wet_market/petrol/coworking/condo/female/bto_*) — **PASS** (2026-06-11)

**Layer:** `hex/hex8_context_pack.parquet` (16 cols) · build `build_context_pack.py` ·
validator `validate_context_pack.py` (4/4 PASS) · sources = the externally-built nous
feature pack (`build_nous_features.py`, 10 sanity-passed deliverables).

**Columns:** URA conserved-building count + cluster flag (7,235 bldgs); HDB carpark
count + car-lot capacity (696K lots, live-availability join); polyclinic count/distance
(27); wet-market count/distance (63 markets); petrol stations (201); coworking venues
(171); condo project count + transacted-units weight (2,384 URA projects); female pop
share (SingStat 2025, subzone-broadcast, NaN = zero-pop subzone — exact 1.0 agreement);
BTO town under-construction units (FY2024, 91,941) + FAR-headroom within-town allocation.

**Gate results:** X1 national sums match the delivered pack exactly; X2 archetypes —
conservation top-5 = heritage subzones, wet-market distance in mature estates 483 m vs
1,380 m populated median, BTO top-8 hexes all in launch towns (Kallang/Whampoa, Tengah,
Queenstown…); X3 invariants hold (female band gated at pop≥1000 — tiny subzones skew
*genuinely*: Yio Chu Kang 76% male institutional quarters, kept as real data); X4
redundancy clean (dist_wet_market ~ hawker-centre distance is definitional: markets are
a subset of that source layer).

**Effect:** hex8 master 687 → **703 cols**; the nous gap analyzer's 🔨 wish-list items
(shophouse, carpark, polyclinic, female share, condo, estate growth) are now live
hex8 columns.

---

One page per gated layer. Spec: `SITE_SELECTION_METRICS.md`. Machine reports in `logs/`.

---

## S3 — Daytime population (dt_*) — **PASS** (2026-06-10)

**Layer:** `hex/hex8_daytime_pop.parquet` (1,191 × 9) · build `build_daytime_pop.py` ·
validator `validate_daytime_pop.py` (8/8 PASS) · report `logs/validate_daytime_pop.json`

**Definition:** `dt_pop = max(pop_resident + (od_in_am − od_out_am)/22/0.62, 0)` —
commuter daytime headcount from the Apr-2026 OD AM window, scaled by an assumed 0.62
peak public-transport mode share. Plus `dt_pop_unadj`, `dt_ratio`, gross in/out persons,
`dt_net_am_persons`, `dt_clipped`, `dt_class` ∈ {job_center 98, balanced 328, bedroom 61,
no_data 704}.

**Gate results:**

| Check | Result |
|---|---|
| D1 conservation | dt_pop 4,188,323 vs pop 4,179,800 → **+0.20%** (limit ±5%) |
| D2 clip accounting | 12 hexes (1.0%), 7,868 persons (0.19%) clipped to 0 |
| D3 archetypes | top-10 gainers 8/10 in CBD/job set (Central Subzone, Chinatown, City Hall, Boulevard, Moulmein, Toh Guan); top-10 losers 10/10 bedroom (Sembawang, Woodlands, Rivervale, Sengkang, Jurong West…) |
| D4 discriminant | dt_net predicts office presence better than breathing_idx: 0.309 vs 0.195 (pc2 offices), 0.214 vs 0.130 (pc) |
| D5 formula guard | 0 violations |
| D6 mode-share sensitivity | rank stability ρ=0.9925 across PT share 0.50→0.75 |
| D7 coverage | 644 no-OD hexes: dt_pop ≡ pop_resident (max dev 0.005) |
| D8 redundancy audit | no \|r\|>0.9 vs any non-source master column; max is dt_pop~pc2_cat_transport_ev_count 0.85 |

**Finding (material, feeds Phase 8):** the explorer's `breathing_idx` =
z(od_in_trips)−z(pop) is **direction-blind**. Full-day inbound≈outbound everywhere
(ρ=0.996, evening returns cancel direction), so breathing collapses to
throughput-vs-pop (ρ=0.999) and mis-labels interchange town centres (Yishun Central,
Woodgrove, Tampines East, Clementi Central, Sengkang TC) as "fills by day". The
AM-directional `dt_net_am_persons` is the correct form. **Action: redefine
breathing_idx in the explorer export at Phase 8.** Spec gate D4 amended accordingly.

**Known limitations (documented in builder docstring):** transit-only OD scaled by a
single national mode-share constant; bus-leg transfer inflation (cancels in net term);
private dorm-bus flows invisible (Tuas-type underestimate); AM-commuter definition —
midday shopper inflows not counted.

**Sign-off:** merged at Phase 8 (not yet in master, per single-merge protocol).

---

## S2a — Walk isochrone catchments (iso_*) — **PASS** (2026-06-10)

**Layer:** `hex/hex8_iso_walk.parquet` (1,191 × 17) · build `build_iso_walk.py` ·
validator `validate_iso_walk.py` (6/6 PASS) · report `logs/validate_iso_walk.json`

**Definition:** 10-min (800 m network) walk catchment per hex8 over the OSM walk graph
(546,340 edges, 213,979 nodes, giant component 99.9%). Demand = hex9 dasymetric population
distributed onto network nodes (node-weighted field); supply = 190,591 exact place points.
Origin = hex8 *activity centroid* (places mean → pop-weighted → geometric), k=4
multi-source Dijkstra. Columns: pop / spend / places / magnets reached, competitor counts
and competitor-free population for cafe, supermarket, restaurant, fitness, euclid-800m
baseline, severance ratio, snap QA.

**Design iterations the validation forced (kept honest, all in builder docstring):**
1. v1 hex9-centroid all-or-nothing snapping undercounted ~2.5× (Toa Payoh Central reached
   4 of ~10 contributing cells) → replaced with node-field demand distribution.
2. v2 geometric-centroid single-node snap was hostage to enclave pockets (Lorong 8
   Toa Payoh: 56 of 870 nearby nodes reachable, iso_pop 741) → activity centroid +
   k=4 multi-source (Lorong 8 → 8,016).
3. Chin Bee is NOT a zero-pop industrial archetype (8K residents, borders Taman Jurong)
   → Gul Circle used as the industrial anchor.

**Gate results:** I1 upper bound (0 material violations; 2 immaterial ~10-person rural
artifacts); I2 severance signal (expressway-adjacent populated hexes 0.250 vs far 0.295);
I3 redundancy (no |r|>0.9 outside source families; **iso_walk10_unserved_pop_supermarket
max |r| = 0.14 — the most novel column added so far**, network-precise FairPrice-desert
signal); I4 snap QA (populated-hex snap>150m = 0.55%, orphan pop 0.24%); I5 archetypes
(CBD 3,618 places / Tampines East 17.9K pop / Gul Circle 0 pop / Lim Chu Kang 1);
I6 invariants hold.

**Interpretation note:** severance_ratio ~0.55 is the ideal-grid ceiling (detour²),
not 1.0; populated median is 0.30. Visual isochrone eyeball deferred to the explorer
"Opportunity" tab at Phase 8 (numeric detour ratios 1.08–1.35 validated in lieu).

**Scope note:** transit-15min catchments are S2b (separate build on the GTFS graph).

---

## S2b — Transit isochrone catchments (iso_transit15_*) — **PASS** (2026-06-10)

**Layer:** `hex/hex8_iso_transit.parquet` (1,191 × 5) + cached minute matrix
`hex/hex8_hex9_transit_min.npz` (1,191 × 7,318, 50-min horizon — S5 reuses at 30/45) ·
build `build_iso_transit.py` · validator `validate_iso_transit.py` (7/7 PASS)

**Definition:** weekday-AM door-to-door 15-min reach over a directed route-dir-stop GTFS
graph (5,305 stops, 24,158 route-dir-stops, 90K edges; wait = headway/2 capped 30 min,
median AM ride times, 200 m transfer walks, 600 m access / 700 m egress at 80 m/min ×1.3
detour, pure-walk arm included). MRT AM headways verified realistic (1.7 min median).
Demand at hex9 grain (documented vs S2a's node field — fine at multi-km reach).

**Gate results:** T1 floor vs walk reach (1 immaterial violator); T2 archetypes
(Yishun Central 251K / Tampines East 243K / Woodlands East 203K all ≥ p90; CBD 73K;
Lim Chu Kang 10); T3 stratified mechanics (within density terciles, Spearman(reach,
stops) = 0.70/0.74/0.74); T4 plausibility (populated median 73K, max 312K); T5 MRT
lift ×1.22; T6 redundancy clean (max ring1_pop 0.91, a source-family col); T7 CBD
45-min reach 2.54M (plausible half-of-SG).

## S7 — Micro visibility (vis_*) — **PASS** (2026-06-10)

**Layer:** `hex/hex8_visibility.parquet` (6 cols) · build `build_visibility.py` ·
validator `validate_visibility.py` (4/4 PASS) · new ingestion: LTA MRT Station Exit
geojson (597 exits, data.gov.sg d_b39d3a0871985372d7e1637193335da5).

**Columns:** `vis_exit_footfall` (weekday taps at nearest exit ≤400 m, per-exit split
from real per-station PV), `vis_exit_station`, `vis_dist_exit_origin_m`,
`vis_main_road_m` + `vis_traffic_pass_proxy` (LTA speed-band cat-weights),
`vis_corner_premium` (signals × main-road presence).

**Design iterations the validation forced:** (1) hex-aggregated `daily_train_taps`
credited single-exit LRT stations with their interchange's whole hex (Petir LRT "saw"
Bukit Panjang's 160K) → switched to real per-station PV (`transport_node_train_202601`);
(2) sg-rail.geojson exit-label points (named "1","A"…) first accumulated phantom taps
and then overwrote the code→name map → ≥3-char name filter; (3) PV merges interchange
codes ("EW24/NS1", 15% of rows) → component-code resolution. (4) V2's "Orchard tops"
expectation was wrong for a per-EXIT measure — volume splits 13 ways at Orchard; the
correct check (top per-exit hexes ⊂ top-30 total-taps stations) passes 6/8, led by the
Punggol concourse, Novena, Newton, Simei.

---

## S9 — Future supply pipeline (pipe_*) — **PASS** (2026-06-10)

**Layer:** `hex/hex8_pipeline.parquet` (6 cols) · build `build_pipeline.py` ·
validator `validate_pipeline.py` (4/4 PASS) · new ingestion: MP2019 rail-station layer
(d_8d886e3a…).

**Source audit results:** HDB "Under-Construction" geojson is 2018-stale → dropped;
project-level BTO locations no longer openly published (FY2024 national total 31,452
awarded units recorded as context only).

**What ships:** (1) **future rail** = 37 MP19 stations with no existing Mar-2026 station
within 400 m — recovers the full committed JRL family (Tengah Park, Hong Kah,
Corporation, Bahar Junction, Gek Poh, Enterprise…) + Keppel CCL6; 66 hexes flagged
within 800 m. (2) **development capacity** = FAR headroom (avg_gpr − est_built_far,
clipped) × zoned share. The footprint-share v1 inverted archetypes (towers cover little
ground → built-out Toa Payoh read as "capacity") — FAR headroom ranks Matilda 0.50 /
Bidadari 0.34 top-decile and Toa Payoh Central exactly 0.

---

## S8 — Rent surface (rent_*) — **PASS** (2026-06-10)

**Layer:** `hex/hex8_rent_surface.parquet` (9 cols) · build `build_rent_surface.py` ·
validator `validate_rent_surface.py` (5/5 PASS) · source: URA Data Service
`PMI_Resi_Rental_Median` via user-provided access key (fetched 2026-06-10).

**Scope amendment:** URA's API exposes **no commercial rental services** (probed all
plausible names → "Invalid service") and office/retail medians are Realis-only. Shipped
layer = **residential** rent surface, honestly labeled: 913 private projects (building-
precise SVY21 coords, median of last 4 quarterly medians) → IDW k=5 within 2.5 km onto
hex8 activity points, with `rent_resolution` flag (local ≤800m / idw / none) +
`roi_cap_per_rent_*` ranking heuristics (S1 capture ÷ rent). Commercial rent remains an
open gap — would need Realis or manual quarterly-release transcription.

**Gate results:** coverage 99.7% of populated hexes ('none' hexes median pop 0); range
$2.02–8.17 psf/mo, Central 5.30 > North 4.02; corr with HDB resale psm 0.616 (same
construct, different segment — adds private-market variation); redundancy clean (max
0.68 vs pull_cbd). **Archetype note:** psf rents peak at *new-build* CBD (City Hall —
Midtown era) and prime D9/10 (Nassim, Leedon Park) — the older large-format Orchard
stock rents lower psf; original gate list amended accordingly (8/10 top hexes in
prime-CCR set).

---

## S4 — Business formation & churn, ACRA (biz_*) — **PASS** (2026-06-10)

**Layer:** `hex/hex8_acra_biz.parquet` (10 cols) · build `build_acra_biz.py` ·
validator `validate_acra_biz.py` (6/6 PASS)

**Geocoding pivot:** the OneMap live API now requires an auth token and throttles
unauthenticated callers to ~18/min with HTTP-200 *error bodies* (which read as
not-found — silent corruption risk). Replaced the planned 7-hour API run with the
offline OneMap dump `xkjyeah/singapore-postal-codes` (141,726 buildings, 2026-04)
→ `data/external/sg_postal_buildings.json`. 1,951,842 of 2,071,218 entities geocoded
(94.24%), building-precise, in 6 seconds.

**Artifact handled:** registered-agent buildings (Paya Lebar Square 19.1K entities,
ACRA building 14.0K, SBF Center 8.7K at single postals) — raw counts kept, plus
`biz_live_robust` (per-postal winsorized at 100) and `biz_per_address` (which itself
*detects* corporate-secretary buildings, City Hall hexes at 109–131 entities/address).

**Gate results:** coverage 94.2%; novelty 5/5 churn-family columns max |r| < 0.7
(dead_share 0.38, recent_dead_share 0.39, median_age 0.52, per_address 0.64,
company_share 0.56 — all new signal); 3/3 building spot-checks within 1 km;
concentration after winsorizing 3.07% = the Chinatown/Telok Ayer shophouse
registration belt (genuine, documented; raw 7.8% was the agent artifact); top-5
robust density all central commercial (Chinatown, Lavender, Little India, City Hall);
redundancy clean. National lifetime dead-share 68.1% (no cessation dates in source —
documented limit).

---

## S6 — Co-location lift (colo_*) — **PASS** (2026-06-10)

**Layer:** `catalog/colo_lift_matrix.parquet` (576 pairs, 518 significant at 95% CI) +
`hex/hex9_colo_fit.parquet` / `hex/hex8_colo_fit.parquet` (11 fit columns) ·
build `build_colo_lift.py` · validator `validate_colo_lift.py` (5/5 PASS)

**Definition:** count-based lift(A,B) = mean count of B within 400 m of A-places ÷
category-blind base over all 190K place locations; bootstrap CI ×200, min support 200.
colo_fit_c = Σ_B log lift(c,B) × *share*_B of the surrounding 400 m place mix.

**Design iterations the validation forced:** (1) presence-based lift saturated —
P(office within 400m of any place)≈1 capped lifts at ~1 → switched to counts;
(2) presence-weighted fit collapsed into amenity breadth (r=0.95 with walk_score_avg)
→ switched to share-weighted mix-match (max |r| vs walkability = 0.45, vs pc_total 0.24).

**Gate results:** 7/7 directional priors hold (bar→bar 3.0, fitness→residential 1.22,
industrial→residential 0.50, hotel→entertainment 2.27…); split-half stability r=0.988;
anti-collapse clean; asymmetries sensible (bars seek parks 1.10, parks don't seek bars
0.30). **Empirical surprise recorded:** cafe→office lift = 0.87 — SG cafes do NOT
over-index near offices relative to commercial fabric; they are mall/heartland creatures.

---

## S5 — Labor-shed & jobs-reach (labor_*) — **PASS** (2026-06-10)

**Layer:** `hex/hex8_labor_shed.parquet` (5 cols) · build `build_labor_shed.py` ·
validator `validate_labor_shed.py` (5/5 PASS) · input = S2b cached minute matrix.

**Definition:** working-age population (pop_15_64) reachable within 30/45-min weekday-AM
transit; jobs_reach via places-based job proxy (office+industrial+services, scaled 2.4M
— to be refined with ACRA biz_live_count when S4 lands); labor_jobs_balance ratio.
Direction symmetry assumed (documented).

**Gate results:** CBD pool 1.68M (p90+, 59.6% of working-age); Jurong East 851K at p70
(correct for a peripheral hub — 45-min reach mechanically peaks centrally: top pools are
Little India/Bendemeer 1.9–2.1M); Tuas at p0 (the known jobs-without-transit gap, now
quantified); monotone 30m≤45m everywhere; redundancy clean (labor_jobs_balance max
|r|=0.27 — novel signal).

---

## S1 — Huff capture potential (cap_*) — **PASS** (2026-06-10)

**Layer:** `hex/hex9_huff_capture.parquet` (7,318 × 14) + `hex/hex8_huff_capture.parquet`
(max-over-children rollup) · build `build_huff_capture.py` · validator
`validate_huff_capture.py` (5/5 PASS) · pair cache `hex/huff_pairs.npz`

**Definition:** demand (outlet-equivalents) a single new outlet would capture per
category against existing competition: exp-decay Huff with quality-weighted
attractiveness (1+log1p reviews), demand = hex9 pop (dt-adjusted for daytime
categories via S3) scaled to national outlet counts. 11 categories;
**cap_bar_nightlife dropped** — ρ≈0 on both validity tests (bars follow culture, not
spatial demand; consistent with v7 finding #3). cap=1.0 ⇒ enough winnable demand to
support one average outlet.

**Material finding — λ is not identifiable from this data:** placement calibration
collapses to λ=100 m (zoning-adjacency overfit, behaviorally absurd); the behavioral
allocation test never beats its degenerate λ→∞ baseline ρ(counts, reviews). λ is
therefore ASSUMED from behavioral priors (500/700/1000/1500 m by category class) and
defended by rank-stability: capture rankings move little across λ∈[400,1200]
(ρ 0.83–0.92 per category, reported per-category in `huff_capture_report.json`).

**Gate results:** H1 placement-ρ>0.2 for 11/11 (0.23–0.58, median 0.42) + rank-stability
min 0.83; H2 marginality — synthetic competitor 150–450 m away strictly reduces capture
in 40/40 cases; H3 conservation exact (alloc/demand=1.0000 all categories); **H4
saturation inversion — Yunnan ranks p96 for cap_supermarket (independently re-derives
the FairPrice-desert finding) while the Orchard corridor ranks p03 for cap_cafe
(saturated)**; H5 redundancy clean, gap_* alignment correctly negative (−0.57…−0.67:
high capture ⟺ undersupplied).

**Known limitations:** euclid distances (λ absorbs detour scale); fitness alloc-ρ weak
(0.14 — boutique-studio review concentration); education demand uses total pop, not
school-age weighting (future refinement).

---

**Finding (material):** `iso_transit15_pop` deliberately diverges from `transit_score`
(raw ρ=0.16). High-score/low-reach = MRT stations amid landed estates (Hillview, Swiss
Club, Toh Tuck). Low-score/high-reach = bus-dense HDB corridors without MRT — Yishun
East scores 0.54 yet reaches **190K** on buses alone, a counterpoint to the adequacy
work's "Yishun East most transit-deficient" framing: deficient in *rail proximity*,
rich in *bus reach*. Reach×density vs proximity are different axes; the atlas now has both.
