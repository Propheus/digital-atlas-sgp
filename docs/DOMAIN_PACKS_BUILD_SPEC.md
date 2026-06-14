# Singapore Digital Atlas — Domain Packs Build Spec

**Audience:** Builder implementing on `plexis-sgp-v5` (Atlas v5.4.0)  
**Goal:** Ship **five domain packs** as curated hex8 parquets + subzone rollups + pack catalogs — without re-building foundation layers.  
**Status:** Ready to build · 2026-06-14  
**Supersedes:** ideation-only sections of `DOMAIN_PACKS_IDEATION.md` (keep that file as product narrative; **this doc is the build order**)

**Related:** `FEATURE_CATALOG.md` · `CONTEXT.md` · `build_mobility_pack.py` (pattern) · `catalog/embedding_catalog.json` · `JAKARTA_REPLICATION_PLAYBOOK.md`

---

## 0. Scope & geometry

| Layer | Units | Key | Master file |
|-------|-------|-----|-------------|
| **Hex8 (product grid)** | 1,191 cells | `hex8_id` | `hex/hex8_all_features.parquet` (801 cols) |
| **Subzone (planning/report)** | ~332 zones | `subzone_code` | `hex/subzone_all_features.parquet` (rollup) |
| **Place (site dossier)** | ~190K venues | `id` | `places/*` + `plexis-p1` |

**Rule:** Packs are built at **hex8**, then **area-weighted or pop-weighted rollup** to subzone for URA/LTA/PUB reporting. Site-specific dossiers join **place** + parent hex8 pack cols.

**Embeddings (do not re-train in v1 pack build):**

- `hex/hex8_embedding_plexis_e1_256d.parquet` — twins, comps, accumulation clustering  
- `places/place_embedding_plexis_p1_64d.parquet` — brand-DNA, misfit, venue comps  

---

## 1. Pack model (builder view)

Each pack ships four artifacts:

| Artifact | Path pattern |
|----------|--------------|
| Feature parquet | `hex/hex8_{pack}_pack.parquet` |
| Column catalog | `catalog/pack_{pack}_catalog.json` |
| QA report | `hex/{pack}_pack_report.json` |
| Subzone rollup | `hex/subzone_{pack}_pack.parquet` |

**Pack =** curated subset of existing 801 cols **+** new derived cols **+** 3–6 hero scores (0–100).

Helper functions (reuse from `build_composites.py`):

```python
def minmax(s): ...      # 1–99 percentile → [0,1]
def inv_dist(s, half=400): return np.exp(-s/half)  # distance → score
def score100(x): return (minmax(x) * 100).round(0).astype(int)
```

---

## 2. Build phases (execute in order)

```
PHASE 0 — Shared primitives (unlocks 4 packs)
  build_domain_primitives_sgp.py

PHASE 1 — 🟢 Pack composites (derivable now, no new downloads)
  build_retail_pack_sgp.py
  build_realestate_pack_sgp.py
  build_utilities_pack_sgp.py
  build_transport_pack_sgp.py
  build_insurance_pack_sgp.py

PHASE 2 — Merge + catalog + validate
  merge_domain_packs_sgp.py      → optional cols into hex8_all_features OR sidecars only
  build_domain_pack_catalogs.py
  validate_domain_packs_sgp.py
  rollup_domain_packs_subzone.py

PHASE 3 — 🟡 Cross-cutting (parallel tracks, not blocking Phase 1 ship)
  build_daypart_od_sgp.py
  build_climate_risk_sgp.py      (PUB flood + heat)
  build_spend_surface_sgp.py
```

**Recommendation:** Ship Phase 0+1+2 first (~1 week). Phase 3 is separate PRs.

---

## 3. Phase 0 — Shared primitives

**Script:** `plexis-sgp-v5/build_domain_primitives_sgp.py`  
**Input:** `hex/hex8_all_features.parquet`  
**Output:** `hex/hex8_domain_primitives.parquet`

| Column | Formula / method | Packs |
|--------|------------------|-------|
| `cannibalization_pressure` | Mean `cap_{cat}` overlap vs nearest same-brand outlet (place-level Huff overlap rolled to hex) — **v1 proxy:** `sat_{cat}_per_1k` × `cap_{cat}` for default cat=cafe_coffee | Retail |
| `delivery_demand_density` | `minmax(iso_walk10_pop) × minmax(pc_cat_restaurant) × (1 - sat_restaurant_per_1k)` | Retail |
| `spend_proxy_index` | `minmax(rwi or income proxy) × minmax(affluence) × minmax(rent_resi_psf_med)` — use existing wealth cols | Retail, RE, Transport, Insurance |
| `diurnal_load_am` | `dt_pop` (day) | Utilities |
| `diurnal_load_pm` | `pop_resident` (night) | Utilities |
| `diurnal_swing` | `(dt_pop - pop_resident) / max(pop_resident, 1)` | Utilities |
| `water_demand_proxy` | `pop_resident × 0.15 + est_total_floor_area × lu_commercial_pct × 0.02` (document coeffs) | Utilities |
| `waste_gen_proxy` | `pop_resident × 0.45 + commercial_poi_density × 0.1` kg/day proxy | Utilities |
| `ev_demand_proxy` | `parking_lot_count × car_ownership_proxy × dt_pop` — car proxy from `hdb_mscp` + affluence | Utilities |
| `ev_charging_gap` | `ev_demand_proxy - n_charger_pois` (or charger POI count col) | Utilities |
| `first_last_mile_gap` | `iso_transit15_unserved_pop × inv_dist(dist_mrt_m, 800)` | Transport |
| `transit_desert_score` | `pop_resident × inv_dist(dist_mrt_m, 1200) × (1 - minmax(transit_score))` | Transport |
| `crowding_stress` | `vis_exit_footfall / max(gtfs_headway_am, 1)` — capacity-normalised | Transport |
| `ridehail_demand_proxy` | `first_last_mile_gap × dt_pop × spend_proxy_index` | Transport, Retail |
| `fire_risk_score` | `minmax(bldg_density) × minmax(hdb_avg_age_years) × lu_industrial_pct × (1 - inv_dist(dist_fire_station, 1000))` | Insurance |
| `auto_exposure_score` | `minmax(intersection_density) × inv_dist(dist_expressway_m, 500) × minmax(od_throughput)` | Insurance |
| `industrial_hazard_buffer` | `lu_industrial_pct × inv_dist(dist_expressway_m, 300)` | Insurance, RE |
| `pop_health_risk` | `minmax(pop_65plus) × (1 - minmax(min15_health)) × minmax(vulnerability_share)` | Insurance, Utilities |
| `collateral_value_proxy` | `hdb_resale_4r_median_psm × est_total_floor_area × 0.3` — HDB-biased v1 | RE, Insurance |
| `nuisance_penalty` | `minmax(expressway_severance) + minmax(lu_industrial_pct) + inv_dist(dist_airport, 1)` | RE |
| `enbloc_upside_score` | `minmax(hdb_avg_age_years) × minmax(pipe_dev_capacity_res) × minmax(nl_change_pct)` | RE |
| `lease_decay_penalty` | `1 - minmax(avg_lease_remaining_yrs)` | RE |

**QA:** No all-null cols; `transit_desert_score` high in fringe (Punggol/Woodlands spot-check); `crowding_stress` high at Orchard/CBD MRT exits.

---

## 4. Pack 1 — Retail

**Buyers:** F&B, FMCG, mall operators, QSR, franchise, grocers, pharmacy, retail REITs  
**Core question:** *Where should this format go — and where should it not?*  
**Honest limit:** **Placement & demand tier, not store revenue forecast.** `cap_*` is outlet-equivalent demand, not SGD sales.

### Use cases → workflow → output

| ID | Workflow | Key inputs | Output |
|----|----------|------------|--------|
| R1 | Filter `gap_{cat}` + `cap_{cat}` → flood veto → rank | gap, cap, iso | Ranked hex CSV |
| R2 | Report `cap_{cat}` + iso catchment pop | cap, iso_walk10 | Site demand brief |
| R3 | Candidate vs network → `cannibalization_index` | primitives + p1 | Network-safe flag |
| R4 | Map `gap_{cat}` by subzone | gap | Whitespace map |
| R5 | `format_fit_score` thresholds | format_fit | kiosk / store / flagship |
| R6 | **Demand tier vs rent tier** (not ROI) | cap + rent_resi_psf_med | affordable / stretch / premium |
| R7 | e1 twin-vote absent hexes | e1 + brands_index | Ghost expansion list |
| R8 | `nvp_*` + `pc_*` profile | personas | Assortment note |
| R9 | p1 misfit > threshold | p1 | Closure-risk flag |
| R10 | `delivery_demand_density` rank | primitives | Dark-store shortlist |
| R11 | Phase 3 `daypart_footfall_*` | 🟡 later | Lunch/dinner curve |

### Existing columns (curate into pack — do not rebuild)

`cap_*`, `gap_*`, `demand_ready_gap_*`, `iso_walk10_*`, `iso_transit15_*`, `colo_fit_*`, `sat_*_per_1k`, `mg_*`, `pc_*`, `dt_pop`, `dt_class`, `vis_exit_footfall`, `od_throughput`, `walk_food_400m`, `nvp_*`, `rent_resi_psf_med`, `chain_visibility` cols if present, `plexis-p1` (sidecar).

### New columns (this pack)

| Column | Formula |
|--------|---------|
| `retail_whitespace_score` | `score100(gap_{cat} × cap_{cat} × (1 - flood_proxy))` — default cat from param |
| `retail_competition_pressure` | `score100(sat_{cat}_per_1k + mg_{cat}_pressure)` |
| `format_fit_score` | `score100(walkability × vis_exit_footfall × inv_dist(dist_arterial) × colo_fit_{cat})` |
| `cannibalization_index` | from primitives (place roll-up v1.1) |
| `retail_delivery_score` | `score100(delivery_demand_density)` |
| `retail_ghost_rank` | External: twin-vote script output column `ghost_votes` |
| `rent_demand_tier` | categorical: `{value, mid, premium}` from cap percentile × rent_resi percentile |

### Script

`build_retail_pack_sgp.py` — TAKE list + compute 6 new cols → `hex/hex8_retail_pack.parquet`

### Place-level (optional v1.1)

`places/retail_site_features.parquet`: `on_main_road`, `mg_rivals_400`, `cannibalization_dist_m`, p1 misfit — for site dossier, not hex map.

---

## 5. Pack 2 — Real Estate

**Buyers:** developers, REITs, valuers, mortgage, GLS, PropTech  
**Core question:** *What is this micro-market like — and what are true comps?*  
**Honest limit:** **v1 = HDB resale + residential rent + comps + feasibility.** Private condo AVM is **v2** (🔴 paywalled).

### v1 vs v2

| Tier | Ships | Does not ship |
|------|-------|---------------|
| **v1 (this build)** | HDB resale/rent, `pipe_dev_capacity_*`, e1 comps, livability/family, en-bloc score, nuisance | Private PSF, transaction momentum |
| **v2** | Hedonic $ model, private scrape, view premium sightline | — |

### Use cases → workflow → output

| ID | Workflow | Output |
|----|----------|--------|
| E1 | HDB comps + e1 NN + resale psf | Valuation **support** dossier (not certified AVM) |
| E2 | `pipe_dev_capacity_res/com` + `avg_gpr` | GFA headroom brief |
| E3 | `rent_resi_psf_med / hdb_resale_4r_median_psm` | Yield **proxy** band |
| E4 | `nl_change_pct` + `biz_formation_5y` + en-bloc | Momentum tier |
| E5 | `livability_index` + `family_index` + `min15_score` | Liveability brief |
| E6 | `pull_school_premium` + `time_to_cbd_min` + `dist_mrt_m` | Amenity premium **flags** (not $ until v2) |
| E7 | e1 top-20 NN + feature deltas | Comp table |
| E8 | `nl_change_pct` rank + low `biz_recent_dead_share` | Gentrification watchlist |
| E9 | `enbloc_upside_score` top decile | Redevelopment candidates |
| E10 | `pipe_new_mrt_*` × growth × family_index | New-launch demand proxy |
| E11 | collateral_proxy + livability − nuisance | Lender location tier |

### New columns

| Column | Formula |
|--------|---------|
| `re_feasibility_score` | `score100(pipe_dev_capacity_res + pipe_dev_capacity_com)` |
| `re_livability_score` | `score100(livability_index + family_index + min15_score)` |
| `re_momentum_score` | `score100(nl_change_pct + biz_formation_5y)` |
| `re_amenity_premium_flags` | JSON or cols: `near_mrt`, `school_belt`, `park_400m` from existing dist cols |
| `re_collateral_tier` | `score100(collateral_value_proxy × livability − nuisance_penalty)` |
| `re_enbloc_score` | `score100(enbloc_upside_score)` |
| `re_yield_proxy` | `rent_resi_psf_med / max(hdb_resale_4r_median_psm, 1)` |

### Script

`build_realestate_pack_sgp.py`

---

## 6. Pack 3 — Public Utilities

**Buyers:** PUB, SP Group, telcos, district cooling, NEA waste, solar installers  
**Core question:** *Where is load growing and where is infrastructure stressed?*  
**Honest limit:** **Modelled kWh/m³ proxies** — not SCADA or feeder-level capacity.

### Use cases → workflow → output

| ID | Workflow | Output |
|----|----------|--------|
| U1 | `electricity_load_proxy` rank | Load growth heatmap |
| U2 | load growth × low grid proxy | Upgrade priority hex |
| U3 | `diurnal_swing` + hourly profile (🟡) | Day/night shape chart |
| U4 | rooftop solar (🟡 Phase 3) | Solar suitability map |
| U5 | `ev_charging_gap` | Charger siting gap |
| U6 | commercial FAR × heat (🟡) | DC viability shortlist |
| U7 | `dt_pop` × venues | Telco small-cell demand |
| U8 | `waste_gen_proxy` | Collection volume tier |
| U9 | `pop_65plus` × `vulnerability` × outage proxy | Critical customer map |
| U10 | `min15_*` gaps vs peers | Equity brief |

### New columns (Phase 1)

| Column | Formula |
|--------|---------|
| `utility_load_proxy` | `nl_2024 × est_total_floor_area × (0.6×lu_residential + 1.0×lu_commercial)` |
| `utility_load_growth` | `utility_load_proxy × (1 + nl_change_pct)` |
| `utility_water_proxy` | from primitives |
| `utility_waste_proxy` | from primitives |
| `utility_ev_gap_score` | `score100(ev_charging_gap)` |
| `utility_equity_score` | `score100(1 - min15_score) × vulnerability_share` |
| `utility_resilience_score` | `score100(min15_health + inv_dist(hospital))` |

### Script

`build_utilities_pack_sgp.py` — reuse SG-Pulse diurnal math when Phase 3 lands.

---

## 7. Pack 4 — Transport

**Buyers:** LTA, operators, Grab, logistics, TOD planners  
**Core question:** *Where is mobility inadequate or stressed?*  
**Note:** Strongest existing pack — **curate `od_*`, mobility pack, iso_*`**; daypart OD is Phase 3 upgrade.

### Use cases → workflow → output

| ID | Workflow | Output |
|----|----------|--------|
| T1 | `od_throughput` + daypart OD (🟡) | Ridership forecast band |
| T2 | `transit_desert_score` + pop | New route candidates |
| T3 | `first_last_mile_gap` | Feeder priority |
| T4 | `ridehail_demand_proxy` | Hotspot map |
| T5 | short-trip OD + cycling paths (🟡) | Micromobility corridors |
| T6 | parking supply vs `dt_pop` dwell | Parking stress |
| T7 | resi density × arterial | Logistics hub rank |
| T8 | `modal_split_proxy` | Car vs transit propensity |
| T9 | `transit_desert_score` top decile | Desert report |
| T10 | `pipe_new_mrt_*` × `pipe_dev_capacity` | TOD opportunity map |
| T11 | `crowding_stress` at exits | Capacity stress rank |

### Existing columns (TAKE — see also `hex8_mobility_pack.parquet`)

`od_*`, `od_throughput`, `vis_exit_footfall`, `gtfs_headway_*`, `iso_transit15_*`, `iso_walk10_*`, `labor_*`, `time_to_*`, `mrt_reach_*`, `min15_*`, `adq_*`, `walkability_score`, `pipe_new_mrt_*`, `road_centrality`, `linkway_*`, `cycling_*`.

### New columns

| Column | Formula |
|--------|---------|
| `mobility_access_score` | `score100(transit_score + walkability + multimodal_score)` |
| `mobility_desert_priority` | `score100(transit_desert_score × pop_resident)` |
| `mobility_crowding_stress` | `score100(crowding_stress)` |
| `mobility_tod_score` | `score100(inv_dist(pipe_new_mrt_dist) × pipe_dev_capacity × od_throughput)` |
| `mobility_ridehail_score` | `score100(ridehail_demand_proxy)` |
| `mobility_parking_stress` | `score100(dt_pop / max(parking_lot_count, 1))` |
| `modal_split_proxy` | `minmax(parking) × (1-minmax(transit_score))` — document as proxy |

### Script

`build_transport_pack_sgp.py` — join mobility pack + master + primitives; dedupe at |r|>0.98 vs master (same pattern as `build_mobility_pack.py`).

---

## 8. Pack 5 — Insurance & Risk

**Buyers:** GI insurers, reinsurers, banks, corporate risk  
**Core question:** *What perils apply and how concentrated is exposure?*  
**Honest limit:** **Hazard stratification, not actuarial pricing.** No crime/theft ground truth in SG open data.

### Use cases → workflow → output

| ID | Workflow | Output |
|----|----------|--------|
| I1 | `fire_risk` + `flood_risk` composite | Property peril tier |
| I2 | flood + heat + coastal | Cat peril map |
| I3 | `auto_exposure_score` | Motor pricing zone |
| I4 | `pop_health_risk` + dengue (🟡) | Life/health zone |
| I5 | `biz_recent_dead_share` × p1 misfit | BI / commercial failure proxy |
| I6 | `collateral_value_proxy` − perils | Collateral tier |
| I7 | e1 cluster + peril overlay | Accumulation report |
| I8 | weighted peril scores | Single `insurance_risk_score` |
| I9 | Micro-tier from I8 | Premium band suggestion (internal) |
| I10 | Client claims vs peer band | Anomaly flag (needs client data) |

### New columns (Phase 1)

| Column | Formula |
|--------|---------|
| `risk_fire_score` | `score100(fire_risk_score)` |
| `risk_auto_score` | `score100(auto_exposure_score)` |
| `risk_health_score` | `score100(pop_health_risk)` |
| `risk_bi_failure` | `score100(biz_recent_dead_share × (1 + p1_misfit_hex_mean))` |
| `risk_collateral_score` | `score100(collateral_value_proxy)` |
| `risk_nuisance_score` | `score100(nuisance_penalty + industrial_hazard_buffer)` |
| `insurance_risk_score` | `0.3×flood + 0.25×fire + 0.2×bi + 0.15×auto + 0.1×health` — flood Phase 3; v1 omit flood weight or use `lu_water_pct` proxy |
| `insurance_accumulation_band` | quintile of `insurance_risk_score` × `collateral_value_proxy` |

### Phase 3 additions

| Column | Source |
|--------|--------|
| `risk_flood_score` | PUB flood raster + DEM |
| `risk_heat_score` | LST + green cover |
| `risk_dengue_score` | NEA cluster feed |

### Script

`build_insurance_pack_sgp.py`

---

## 9. Phase 2 — Merge, catalog, validate

### `merge_domain_packs_sgp.py`

**Policy:** Pack cols live in **sidecar parquets** by default (keeps master 801 stable). Optional `--merge-hero-scores` adds only `*_score` cols (≤30) to `hex8_all_features.parquet`.

Join key: `hex8_id`, left join from master.

### `build_domain_pack_catalogs.py`

Emit `catalog/pack_{retail,realestate,utilities,transport,insurance}_catalog.json`:

```json
{
  "pack": "retail",
  "version": "1.0.0",
  "hex8_key": "hex8_id",
  "hero_scores": ["retail_whitespace_score", "format_fit_score"],
  "use_cases": ["R1", "R2", "..."],
  "limits": ["No revenue forecast", "cap_* is Huff outlet-equivalent"],
  "path": "hex/hex8_retail_pack.parquet"
}
```

### `rollup_domain_packs_subzone.py`

For each numeric pack col: `subzone_value = Σ(hex_value × pop_resident_hex) / Σ(pop_resident_hex)` within subzone polygon mapping (use existing hex→subzone lookup).

### `validate_domain_packs_sgp.py`

| Gate | Expect |
|------|--------|
| Row count | 1,191 hex8 per pack |
| Hero scores | ∈ [0, 100], not constant |
| Retail whitespace | Correlates with `gap_cafe_coffee` (ρ > 0.4) |
| RE feasibility | High in areas with known `pipe_dev_capacity` |
| Transport desert | Higher in Tuas / far fringe than Orchard |
| Insurance BI | Correlates with `biz_recent_dead_share` (ρ > 0.5) |
| Dedup | No new col with \|r\| > 0.98 vs master unless documented |
| Subzone rollup | 320–335 subzones, no null `subzone_code` |

**Spot-check hex8_ids** (hardcode in validator):

- Orchard / Somerset — high crowding, retail vibrancy  
- Punggol / Sengkang — transit desert moderate, family score high  
- Jurong Industrial — high industrial hazard, low residential  
- Sentosa / coastal — collateral high, flood TBD Phase 3  

---

## 10. Phase 3 — Cross-cutting (parallel)

| Script | Columns | Packs unlocked |
|--------|---------|----------------|
| `build_daypart_od_sgp.py` | `od_am`, `od_pm`, `od_offpeak`, `daypart_footfall_lunch`, `daypart_footfall_evening` | Retail, Transport, Utilities, Insurance |
| `build_climate_risk_sgp.py` | `risk_flood_score`, `risk_heat_score`, `coastal_exposure` | RE, Insurance, Utilities |
| `build_spend_surface_sgp.py` | `spend_fnb_proxy`, `spend_retail_proxy` | Retail, RE, Transport |
| `build_rooftop_solar_sgp.py` | `solar_kwh_potential` | Utilities, RE |
| `build_commercial_rent_scrape_sgp.py` | `rent_com_psf_med` | Retail, RE (🔴 partnership) |

---

## 11. Embeddings & agent tools (no re-train)

| Tool name | Pack | Implementation |
|-----------|------|----------------|
| `hex_twins` | All | e1 cosine NN — exists in `plexis-embeddings/kit.py` |
| `brand_ghost_map` | Retail | e1 vote over brand hexes |
| `valuation_comps` | RE | e1 NN + `re_*` delta table |
| `peril_peers` | Insurance | e1 NN filtered by `insurance_risk_score` band |
| `transit_similar` | Transport | e1 NN + `mobility_*` deltas |
| `load_peers` | Utilities | e1 NN on `utility_load_proxy` |

Wire in Plexis-Reasoner as tool definitions pointing at pack parquets + kit.py.

---

## 12. Deliverables checklist

| File | Description |
|------|-------------|
| `hex/hex8_domain_primitives.parquet` | Phase 0 shared |
| `hex/hex8_retail_pack.parquet` | Pack 1 |
| `hex/hex8_realestate_pack.parquet` | Pack 2 |
| `hex/hex8_utilities_pack.parquet` | Pack 3 |
| `hex/hex8_transport_pack.parquet` | Pack 4 |
| `hex/hex8_insurance_pack.parquet` | Pack 5 |
| `hex/subzone_*_pack.parquet` | ×5 rollups |
| `catalog/pack_*_catalog.json` | ×5 |
| `hex/domain_packs_report.json` | Combined QA |
| `docs/DOMAIN_PACKS_BUILD_SPEC.md` | This file |

---

## 13. Smoke test (post-build)

```bash
cd plexis-sgp-v5/build-scripts   # or plexis-sgp-v5/ if scripts live at root
python3 build_domain_primitives_sgp.py
python3 build_retail_pack_sgp.py
python3 build_realestate_pack_sgp.py
python3 build_utilities_pack_sgp.py
python3 build_transport_pack_sgp.py
python3 build_insurance_pack_sgp.py
python3 rollup_domain_packs_subzone.py
python3 build_domain_pack_catalogs.py
python3 validate_domain_packs_sgp.py

python3 -c "
import pandas as pd
r = pd.read_parquet('hex/hex8_retail_pack.parquet')
print(r.nlargest(5,'retail_whitespace_score')[['hex8_id','retail_whitespace_score','format_fit_score']])
"
```

---

## 14. One-line summary for builder

**Phase 0 primitives → five pack parquets (curate 801 existing + ~6 hero scores each) → subzone rollup → catalog JSON → validate. Do not re-train e1/p1. Ship 🟢 now; daypart OD + PUB flood in Phase 3.**

---

*Atlas v5.4.0 · hex8 1,191×801 · plexis-e1/p1 exam-gated · pattern: `build_mobility_pack.py`*