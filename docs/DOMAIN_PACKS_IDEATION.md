# Digital Atlas — Domain Packs Ideation

*Five vertical feature packs (Retail · Real Estate · Public Utilities · Transport ·
Insurance & Risk). Product narrative + feature mapping.*

> **Builder handoff:** see **[DOMAIN_PACKS_BUILD_SPEC.md](./DOMAIN_PACKS_BUILD_SPEC.md)** for scripts, formulas, hero scores, QA gates, and build order. Start there.

*Updated 2026-06-14.*

---

## 0. The pack model

**Scales:** hex8 (1,191 cells, product grid) + subzone rollup (~332, planning reports) + place dossiers (190K + p1).

A **domain pack** is three layers:

1. **Re-framed existing features** — the atlas already has ~801 hex8 features +
   190K place micrographs + two embeddings. Most domain value is *re-labelling
   and bundling* what exists into the language of that vertical's decision.
2. **New domain features** — the gaps that a vertical genuinely needs and the
   atlas doesn't yet have. Each flagged with its likely source + difficulty.
3. **The reasoning layer** — the e1/p1 embeddings (twins, brand-DNA, comps) and
   the in-progress Plexis-Reasoner agent turn a feature table into answers.

A few **cross-cutting new features** (rent/price surfaces, spend/wealth, climate
risk, daypart footfall, energy load) serve 3–5 domains at once — those are the
highest-leverage builds and are called out in §6.

**Atlas feature families to reference** (existing): `pop_*`/`dt_pop` (people &
day-night), `cap_*`/`gap_*` (Huff demand & unmet demand), `iso_*` (true
catchments), `mg_*`/`colo_*`/`sat_*`/`syn_*` (micro-context, fit, saturation,
synergy), `biz_*` (ACRA vitality/churn), `rent_resi_*`/`hdb_resale_*` (price),
`pipe_*` (FAR headroom + future rail), `od_*`/`labor_*`/`time_to_*`/`gtfs_*`
(mobility & OD), `min15_*`/`adq_*`/`walkability` (access/livability), `nl_*`
(night lights), `lu_*`/`bldg_*`/`hdb_*` (form & stock), `vis_*` (per-exit
footfall), `nvp_*` (personas), `vulnerability`/`silver`/`low_income_share`
(equity), plus `livability/family/vibrancy_index` and **plexis-e1 / plexis-p1**.

---

## 1. RETAIL PACK 🛍️

**For:** F&B chains, FMCG, mall operators, QSR, franchise developers, grocers,
pharmacy/health-&-beauty, retail REITs, pop-up/dark-store operators.

### Use cases
| # | Decision | Question |
|---|---|---|
| R1 | Site selection | Where do I open the next outlet? |
| R2 | Catchment & demand | How many customers can this site win? |
| R3 | Cannibalisation | Will a new store eat my existing ones? |
| R4 | White-space / competitor map | Where is the category under-supplied? |
| R5 | Format fit | Kiosk vs full-store vs flagship here? |
| R6 | Demand vs occupancy cost tier | Is catchment demand in the right **tier** for likely rent? (not revenue ROI) |
| R7 | Brand expansion plan | Rank all of SG for our siting DNA |
| R8 | Assortment localisation | What mix to stock for this demographic? |
| R9 | Underperformer / closure risk | Which outlets are mis-sited? |
| R10 | Dark-store / delivery siting | Where's the delivery-demand density? |
| R11 | Daypart strategy | Lunch vs dinner vs weekend trade here? |

### Existing features that already serve it
- **R1/R2/R4:** `cap_<cat>` (Huff capture — *the* site number), `gap_<cat>`,
  `iso_walk10_*` + `iso_transit15_*` catchments, `iso_walk10_unserved_pop_<cat>`.
- **R3/R7/R9:** **plexis-p1** (place twins = real competitors; brand-DNA =
  expansion ghost map; misfit = closure risk), **plexis-e1** (hex twins).
- **R4/R5:** `mg_<cat>_pressure/support/anchor_strength`, `colo_fit_<cat>`,
  `sat_<cat>_per_1k`, `pc_*` place composition.
- **R2/R11:** `dt_pop` + `dt_class` (workday vs residential trade),
  `vis_exit_footfall`, `od_throughput`, `walk_food_400m`.
- **R8:** `nvp_*` personas, `pop_*` age splits, `pop_hdb_share`, `pr_share`.
- **R6 (partial):** `cap_<cat>` (demand) vs `rent_resi_psf_med` (occupancy cost **proxy**) — residential rent only; label *tier match*, not P&L. Commercial rent 🔴.

### New features to build
| Feature | What it adds | Source / difficulty |
|---|---|---|
| **Commercial rent surface** | true R6 ROI — residential rent ≠ shop rent | scrape listings / JTC / mall data · 🔴 hard (no open feed) |
| **Daypart footfall** (hourly) | R11 — lunch vs evening vs weekend curves | model from OD + GTFS + place opening-hours · 🟡 |
| **Spend / wallet surface** (per category) | R2 quality — demand $ not just heads | income proxy × category propensity (HES) · 🟡 |
| **Cannibalisation index** | R3 — demand overlap between a candidate & existing outlets | Huff + p1 overlap · 🟢 (derivable now) |
| **Tourist / transient demand** | R2 — hotel & attraction-driven trade | hotel POIs + attraction OD · 🟡 |
| **Delivery-demand density** | R10 — dark-store siting | resi density × food-delivery propensity × kitchen supply · 🟡 |
| **Format-fit score** | R5 — kiosk/store/flagship suitability | built form + footfall + frontage + rent · 🟢 |
| **Vacancy / lease-availability** | R1 — which units are actually available | hard to source openly · 🔴 |

### The Retail Pack = `cap_*` + `gap_*` + `iso_*` + `mg_*`/`colo_*`/`sat_*` + p1
(twins/brand-DNA/misfit) + `dt_pop`/`vis_*` footfall + personas — **plus** the
commercial-rent surface and daypart footfall as the two highest-value new builds.

---

## 2. REAL ESTATE PACK 🏢

**For:** developers, REITs, property investors, valuers/AVMs, mortgage lenders,
agents, GLS bidders, PropTech, planners.

### Use cases
| # | Decision | Question |
|---|---|---|
| E1 | Valuation / AVM | What is this unit worth? |
| E2 | Development feasibility | What & how much can I build here? |
| E3 | Rental yield | Rent ÷ price by area & type? |
| E4 | Appreciation forecast | Where will prices rise? |
| E5 | Neighbourhood quality | Is this a good place to live/invest? |
| E6 | Amenity-premium pricing | What's the MRT / school / sea premium? |
| E7 | Comparable selection | What are the true comps? |
| E8 | Emergence / gentrification | Which areas are on the up? |
| E9 | GLS / en-bloc potential | Which sites have redevelopment upside? |
| E10 | New-launch demand | Will units here sell/lease? |
| E11 | Mortgage collateral risk | How good is the location backing this loan? |

### Existing features that already serve it
- **E1/E7:** `hdb_resale_4r_median_psm`, `rent_resi_psf_med`, **plexis-e1**
  (functional comps — "places like this for valuation"), `bldg_*`/`hdb_*` stock.
- **E2/E9:** `pipe_dev_capacity_res/com` (FAR headroom — *the* feasibility
  number), `avg_gpr`/`max_gpr`, `lu_*`, `bto_pipeline_est`, `hdb_avg_age_years`.
- **E4/E8:** `nl_change_pct` + `nl_2024` (growth signal), `pipe_new_mrt_*`
  (future-rail uplift), `biz_formation_5y` (commercial vitality).
- **E5:** `livability_index`, `family_index`, `min15_score`, `walkability_score`,
  `adq_*`, `pull_school_premium`.
- **E6:** `dist_mrt_m`, `time_to_cbd_min`, `pull_school_premium`, `walk_park_400m`.
- **E11:** `plexis-e1` + livability + `biz_recent_dead_share` (area health).

### New features to build
| Feature | What it adds | Source / difficulty |
|---|---|---|
| **Private property price surface** | E1/E3 — atlas has HDB resale, NOT private (condo/landed) | URA/EPRC paywalled → scrape (Centaline/Rumah-equiv) · 🔴 |
| **Price momentum (12/36-mo Δ)** | E4 — actual appreciation, not just night-lights | historical transactions time-series · 🔴 |
| **Hedonic amenity-premium model** | E6 — $ attributed to each amenity | regression on prices × atlas features · 🟡 (inputs exist) |
| **View / frontage premium** | E6 — sea/park/reservoir view, water frontage | DEM + coastline + park polygons + building height · 🟡 |
| **Lease-decay surface (HDB)** | E1 — remaining-lease value erosion | lease data × resale model · 🟢 |
| **En-bloc / redevelopment score** | E9 — old stock × FAR headroom × land uplift | `bldg_age` × `pipe_dev_capacity` × price · 🟢 |
| **School-catchment pressure** | E6/E5 — 1km/2km zones, balloting oversubscription | MOE school locations + admissions · 🟡 |
| **Nuisance proximity** | E1 down-weight — expressway, industrial, flight path | `dist_expressway` + `lu_industrial` + airport · 🟢 |
| **Construction-activity index** | E8/E10 — visible development pace | satellite change-detection · 🟡 |

### The Real Estate Pack = `pipe_*` (feasibility) + `hdb_resale`/`rent` + e1
(comps) + livability/family/min15 + `nl_change`/future-rail (momentum).

**v1 ships:** HDB + comps + feasibility + momentum tiers. **v2 unlock:** private-price surface + hedonic $ model (🔴 paywalled).

---

## 3. PUBLIC UTILITIES PACK ⚡

**For:** PUB (water), SP Group (power/grid/gas), telcos, district-cooling, waste,
solar/green-energy, gov infrastructure planning.

### Use cases
| # | Decision | Question |
|---|---|---|
| U1 | Demand forecast (power/water/gas) | How much load per area? |
| U2 | Network / capacity planning | Where to add substations, mains, cells? |
| U3 | Diurnal load shape | How does demand swing day↔night? |
| U4 | Rooftop solar potential | Where's the generation upside? |
| U5 | EV-charging siting & gap | Where do we need chargers? |
| U6 | District-cooling viability | Which dense clusters justify DC? |
| U7 | Telco / 5G small-cell siting | Where is data demand concentrated? |
| U8 | Waste-generation estimate | Collection volume & routing by area? |
| U9 | Outage criticality | Who's affected; who's vulnerable? |
| U10 | Infrastructure equity | Which areas are under-provisioned? |

### Existing features that already serve it
- **U1/U3:** `pop_resident` (night load) + `dt_pop` (day load) + `dt_class`/
  `dt_ratio` (the swing) + `nl_2024` (electricity proxy, calibratable),
  `est_total_floor_area`, `bldg_density`, `n_highrise_bldgs`, `est_built_far`.
- **U1 by use-type:** `lu_residential/commercial/industrial_pct`,
  `biz_live_robust` (commercial load), `hdb_dwelling_units`.
- **U2:** `road_density`/centrality (network corridors), `pipe_dev_capacity`
  (future demand growth), `bldg_*` clusters.
- **U5:** existing **charger POIs** + `parking_lot_count`/`hdb_mscp_count` +
  car-ownership proxy + `dt_pop` dwell → demand-vs-supply gap.
- **U9:** `pop_65plus`/`silver`, `vulnerability`, hospital/CHAS POIs.
- **U10:** `min15_*`/`adq_*` (the same under-provision logic as amenities).

### New features to build
| Feature | What it adds | Source / difficulty |
|---|---|---|
| **Rooftop solar potential** | U4 — usable roof area × orientation × shading | building footprints + DEM + satellite · 🟡 (high value) |
| **Modelled electricity load (kWh)** | U1 — calibrated load, not just a proxy | floor-area × use × occupancy, calibrated to `nl_2024` · 🟡 |
| **Modelled water demand** | U1 — per-capita + commercial/industrial multipliers | population × use-type · 🟢 |
| **Diurnal load profile (hourly)** | U3 — full day shape | blend `pop_resident`/`dt_pop`/`nl` by hour (the SG-Pulse "breathing" math, re-used for load) · 🟢 |
| **EV-charging demand & gap** | U5 — siting + gap vs existing | car proxy × dwell × parking − chargers · 🟢 |
| **District-cooling viability** | U6 — clustered cooling load | commercial floor-area density + heat · 🟡 |
| **Telco data-demand surface** | U7 — small-cell siting | `dt_pop` × device density × event venues · 🟡 |
| **Waste-generation estimate** | U8 — tonnage & routing | population + commercial-type coefficients · 🟢 |
| **Urban-heat / cooling-need layer** | U6/U4 — heat island | satellite LST + green cover + `bldg_density` · 🟡 |

### The Utilities Pack = `pop`/`dt_pop`/`nl` (load drivers) + `lu_*`/`bldg_*`
(stock & use) + charger/parking POIs + `pipe_dev_capacity` (growth) — **plus**
rooftop-solar + modelled load + diurnal profile as the new core. (The SG-Pulse
day-night blend code is directly reusable as a load-shape engine.)

---

## 4. TRANSPORT PACK 🚇

**For:** LTA, SBS/SMRT, ride-hail/MaaS (Grab/Gojek), micromobility, logistics &
last-mile, AV pilots, TOD planners, fleet-electrification.

*(Transport is the atlas's strongest existing area — the pack is mostly
re-framing, with daypart OD as the key new build.)*

### Use cases
| # | Decision | Question |
|---|---|---|
| T1 | Ridership / transit demand | How many trips will this route/stop serve? |
| T2 | Network & route planning | Where to add bus/feeder/rail? |
| T3 | First/last-mile gap | Who can't reach transit easily? |
| T4 | Ride-hail demand hotspots | Where & when is demand high? |
| T5 | Micromobility siting & rebalancing | Where do bikes/scooters go? |
| T6 | Parking demand & pricing | Where is parking stressed? |
| T7 | Logistics / hub siting | Where to place delivery depots? |
| T8 | Modal split | Who drives vs takes transit here? |
| T9 | Accessibility equity | Where are the transit deserts? |
| T10 | TOD opportunity | Where does future rail meet build capacity? |
| T11 | Crowding / capacity stress | Which stations/links are over-stressed? |

### Existing features that already serve it
- **T1/T2/T11:** **full `od_*` matrix** + `od_throughput`, `vis_exit_footfall`
  (per-exit ridership), `gtfs_headway_*`, `bus_taps_in_am`, `daily_train`.
- **T3/T9:** `iso_transit15_*` + `iso_walk10_*`, `iso_severance_ratio`,
  `dist_mrt_m`/`_exit_m`/`bus_m`, `min15_score`, `mrt_reach_*`.
- **T8:** `labor_pool_45m`, `labor_jobs_balance_45m`, `time_to_cbd/orchard/*`,
  `dt_net_am` (commute direction).
- **T6:** `parking_lot_count`, `hdb_mscp_count`, `dt_pop` dwell.
- **T10:** `pipe_new_mrt_*` × `pipe_dev_capacity` (future-rail × build headroom).
- **T2/T5:** `road_centrality`/`centr_betweenness`, `walkability`,
  `linkway_per_road_km`, `ped_path_density`, `signalized_crossing_count`.

### New features to build
| Feature | What it adds | Source / difficulty |
|---|---|---|
| **Time-varying OD (daypart)** | T1/T4/T11 — AM/PM/off-peak/weekend flows | expand the OD matrix by time-band · 🟡 (data exists) |
| **Ride-hail demand surface** | T4 — transit-gap × pop × spend, by hour | derived from gap + daypart OD · 🟢 |
| **First/last-mile gap index** | T3 — residents far from transit, ranked | home→stop distance × unserved pop · 🟢 |
| **Micromobility demand & corridors** | T5 — short-trip (1–3 km) OD + cycling infra | short-trip OD + path network · 🟡 |
| **Modal-split estimate** | T8 — car vs transit propensity | income × parking × transit quality · 🟡 |
| **Parking utilisation** | T6 — supply vs demand, dynamic | carpark capacity feeds (HDB/URA) · 🟡 |
| **Freight / delivery demand** | T7 — e-commerce + industrial OD | resi delivery density + industrial OD · 🟡 |
| **Crowding / capacity stress** | T11 — ridership ÷ capacity | `vis_exit_footfall` ÷ `gtfs` capacity · 🟢 |
| **Curb-demand index** | T4/T7 — pickup/dropoff intensity | ride-hail + delivery + frontage · 🟡 |

### The Transport Pack = `od_*` + `iso_transit/walk` + `vis_exit_footfall` +
`labor_*` + `pipe_new_mrt` + centrality/walkability — **plus** daypart OD as the
single highest-value upgrade (unlocks ride-hail, crowding, and dynamic planning).

---

## 5. INSURANCE & RISK MANAGEMENT PACK 🛡️

**For:** property/auto/health/life insurers, reinsurers, actuaries, underwriters,
risk managers, banks (collateral/credit risk).

### Use cases
| # | Decision | Question |
|---|---|---|
| I1 | Property risk pricing | Fire / structural / theft risk here? |
| I2 | Catastrophe / climate risk | Flood / heat / coastal exposure? |
| I3 | Auto risk | Accident exposure by area? |
| I4 | Health / life actuarial | Morbidity & longevity drivers? |
| I5 | Commercial / BI risk | Will this business fail or be interrupted? |
| I6 | Collateral / credit risk | How good is the property backing this loan? |
| I7 | Accumulation / concentration | How exposed is the portfolio in one peril zone? |
| I8 | Underwriting automation | A single location-risk score |
| I9 | Premium personalisation | Micro-location pricing |
| I10 | Claims / fraud anomaly | Unusual claim patterns by area |

### Existing features that already serve it
- **I5/I6 (the standout):** `biz_recent_dead_share` + `biz_*` (business-failure
  signal — directly an underwriting input for commercial & BI), `plexis-p1`
  misfit (mis-sited → higher failure odds).
- **I1/I6:** `rent_resi_*`/`hdb_resale_*` (sum-insured / collateral value),
  `bldg_*` (age, height, count), `lu_industrial_pct` (hazard proximity),
  `plexis-e1` (risk-similar areas for portfolio clustering / I7).
- **I3:** `dist_expressway_m`, `road_density`, `signalized_crossing_count`,
  `centr_betweenness` (traffic exposure), `dt_pop`/`nl` (activity = exposure).
- **I4:** `pop_65plus`/`silver`, `pop_0_14`, `vulnerability`, `walking_dependent`,
  `min15_health`, CHAS/polyclinic access, `low_income_share`.
- **I2 (partial):** `dist_to_coast` (where present), `lu_water_pct`, DEM (JKT
  build already has flood/elevation — SG can add).
- **I7:** `plexis-e1` clusters peril-similar hexes for accumulation analysis.

### New features to build
| Feature | What it adds | Source / difficulty |
|---|---|---|
| **Flood / inundation risk** | I1/I2 — *the* property cat-risk layer | PUB flood maps + DEM + drainage · 🟡 (DEM exists for JKT) |
| **Fire-risk surface** | I1 — density × age × use × hawker/industrial × hydrant | composite of existing form features · 🟢 |
| **Road-accident risk** | I3 — actuarial auto pricing | intersections × expressway × ped-crossings × volume · 🟢 |
| **Heat / climate-exposure** | I2/I4 — urban heat island, growing peril | satellite LST + green cover + density · 🟡 |
| **Industrial-hazard proximity** | I1/I5 — chemical/petrol/gas/Jurong-Island | `lu_industrial` + petrol/POI + buffers · 🟢 |
| **Population-health composite** | I4 — life/health risk by micro-area | age × density × healthcare adequacy × walkability · 🟢 |
| **Dengue / vector risk** | I4 — health peril (open NEA clusters) | NEA dengue-cluster feed · 🟢 |
| **Accumulation / aggregation index** | I7 — reinsurer concentration in a peril | policies × peril-zone overlap (uses e1 + flood) · 🟡 |
| **Building-vulnerability** | I1 — construction era, façade, height | satellite + footprint + age · 🟡 |
| **Private-property value surface** | I1/I6 — accurate sum-insured / collateral | shared with Real-Estate pack · 🔴 |

> **Honest gap:** crime/theft data is *not in the atlas and not openly available*
> in SG — flagged for I1/theft. A churn/vacancy/night-activity proxy is possible
> but must be labelled a proxy, not ground truth.

### The Insurance Pack = `biz_recent_dead_share` (BI/commercial) + `bldg_*`/`lu_*`
(property) + `pop_65plus`/`vulnerability`/health-access (life/health) + road/
expressway (auto) + e1 (accumulation) — **plus** flood + fire + heat + a
population-health composite as the new core (turns the atlas into an underwriting
risk-score engine).

---

## 6. Cross-cutting new features (build these first — they serve 3–5 packs)

| New feature | Retail | Real Estate | Utilities | Transport | Insurance |
|---|:--:|:--:|:--:|:--:|:--:|
| **Commercial rent surface** | ✅ | ✅ | | | |
| **Private property price surface** | | ✅ | | | ✅ |
| **Spend / income / wealth surface** | ✅ | ✅ | | ✅ | ✅ |
| **Daypart footfall / time-varying OD** | ✅ | | ✅ | ✅ | ✅ |
| **Flood / heat / climate-risk layer** | | ✅ | ✅ | | ✅ |
| **Rooftop solar / energy-load** | | ✅ | ✅ | | |
| **Satellite change-detection** | ✅ | ✅ | ✅ | | ✅ |
| **Population-health composite** | | | ✅ | | ✅ |

The four with the widest reach — **wealth/spend surface**, **daypart
footfall/OD**, **climate-risk**, and **satellite change-detection** — each unlock
4–5 packs. Build order should follow reach × feasibility, not domain by domain.

---

## 7. How the embeddings & reasoning layer amplify every pack

- **plexis-e1 (hex):** comps/twins for valuation (RE), rollout transfer (Retail),
  peril-accumulation clustering (Insurance), demand-similar corridors (Transport),
  load-similar areas (Utilities). One primitive, five verticals.
- **plexis-p1 (place):** real competitor sets & brand-DNA (Retail), misfit /
  business-failure risk (Insurance/Retail), venue-level comps.
- **Plexis-Reasoner agent:** each pack ships as *tools the agent can chain* —
  "score this site for a clinic" (Retail+RE), "rank flood-exposed high-value
  collateral" (Insurance+RE), "where do future rail + build capacity + demand
  align" (Transport+RE). The packs are the agent's domain vocabularies.

---

## 8. Build prioritisation (a thinking, not a commitment)

| Tier | Builds | Why |
|---|---|---|
| **Now (derivable from existing data, 🟢)** | cannibalisation index, format-fit, EV-charging gap, fire-risk, road-accident risk, first/last-mile gap, en-bloc score, diurnal load, water/waste estimate, population-health composite | no new data — pure derivation; ship in days |
| **Near (need modelling / open data, 🟡)** | daypart footfall/OD, hedonic premium model, rooftop solar, modelled electricity load, flood/heat layer, school-catchment, satellite change-detection, dengue | known sources, real modelling |
| **Hard (paywalled / unavailable, 🔴)** | commercial rent, private property prices, price momentum, vacancy, crime/theft | needs scraping or partnerships; flag honestly |

The 🟢 tier is striking: a large fraction of all five packs is **already
derivable from the 801 features we have** — the packs are mostly an act of
*curation and re-framing*, with a focused set of new surfaces (wealth, rent,
climate, daypart, solar) doing the heavy lifting across domains.

---

*Grounded in the live v5.4.0 atlas (801 hex8 features, 190K place micrographs,
plexis-e1/p1). Cross-city note: the same pack definitions transfer to the HK and
Jakarta atlases once their feature bases reach parity — Jakarta's flood/informal
layers are in fact a head-start for the Insurance and Utilities packs.*
