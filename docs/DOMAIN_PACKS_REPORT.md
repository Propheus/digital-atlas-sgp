# Digital Atlas — Domain Packs v1 · Final Report

*Five vertical feature packs built, validated, and shipped on Atlas v5.4.0.
2026-06-14. Build spec: [DOMAIN_PACKS_BUILD_SPEC.md](./DOMAIN_PACKS_BUILD_SPEC.md) ·
ideation: [DOMAIN_PACKS_IDEATION.md](./DOMAIN_PACKS_IDEATION.md).*

---

## Executive summary

Five domain packs — **Retail, Real Estate, Public Utilities, Transport,
Insurance & Risk** — now sit on top of the 1,191×801 hex8 atlas. Each turns the
existing validated features into the **one number a buyer pays for**, plus
sub-scores and a subzone rollup.

| | |
|---|---|
| **Packs** | 5 (retail / realestate / utilities / transport / insurance) |
| **New columns** | 22 shared primitives + **39 pack scores** = 61 derived features |
| **Scales** | hex8 (1,191) + pop-weighted subzone rollup (270) |
| **New data needed** | **none** — pure derivation from the existing 801 features |
| **Validation** | **ALL GATES PASS** (range · dedup audit · known-answer) |
| **Where** | built on `azold:/home/azureuser/da-sgp/v5/`, synced local, pushed to git |
| **Cost / time** | $0 compute, ~1 session — the value was curation, not collection |

The headline finding: **the five verticals are ~95% derivable from features the
atlas already has.** Packs are an act of *re-composition and re-framing*, not new
data collection. The only genuinely-new builds (climate risk, daypart OD, spend
surface, commercial rent) are scoped as Phase 3.

---

## The five packs

### 🛍️ Retail — *"Score this site for my brand"*
**Buyers:** F&B, FMCG, malls, QSR, franchise, grocers, pharmacy, retail REITs.
**Hero:** `retail_whitespace_score` + `format_fit_score`.
**Delivered (7):** whitespace · competition_pressure · format_fit · cannibalization · delivery · footfall · rent_demand_tier.
**Answers:** where to open, catchment demand, cannibalisation, white-space, format (kiosk/store/flagship), demand-vs-rent tier, dark-store siting.
**Built from:** `cap/gap/sat/mg/colo_cafe_coffee`, `iso_walk10_unserved_pop_*`, `vis_exit_footfall`, `dt_pop`, `walkability_score`, `rent_resi_psf_med`, plexis-p1.
**Honest limit:** placement & demand **tier**, not store-revenue forecast (`cap_*` is Huff outlet-equivalent demand). Commercial rent is residential-proxy until the 🔴 commercial-rent surface lands.

### 🏢 Real Estate — *"Value + what I can build"*
**Buyers:** developers, REITs, valuers/AVMs, mortgage, GLS bidders, PropTech.
**Hero:** `re_feasibility_score` + `re_livability_score` + `re_momentum_score`.
**Delivered (7):** feasibility · livability · momentum · enbloc · collateral · yield_proxy · lease_decay.
**Answers:** development feasibility (FAR headroom), neighbourhood quality, momentum/gentrification, en-bloc upside, collateral tier, yield proxy, lease decay.
**Built from:** `pipe_dev_capacity_res/com`, `livability/family_index`, `min15_score`, `nl_change_pct`, `biz_formation_5y`, `hdb_resale_*`, plexis-e1 comps.
**Honest limit:** v1 = HDB resale + residential rent + feasibility; **private-unit AVM is v2** (🔴 paywalled private prices + hedonic $ model).

### ⚡ Public Utilities — *"Load + green upside here"*
**Buyers:** PUB, SP Group, telcos, district-cooling, NEA waste, solar.
**Hero:** `utility_load_score` + `utility_ev_gap_score`.
**Delivered (8):** load · load_growth · water · waste · ev_gap · diurnal_swing · equity · resilience.
**Answers:** load demand & growth, day/night swing, EV-charger gap, water/waste estimates, infrastructure equity, critical-customer resilience.
**Built from:** `nl_2024`, `est_total_floor_area_m2`, `lu_residential/commercial/business_pct`, `pc2_cat_transport_ev_count` (EV chargers), `pop_65plus`, `vulnerability_share`.
**Honest limit:** modelled **relative** load, not SCADA/kWh — calibrate to SP if shared. (The SG-Pulse day-night engine is the diurnal-shape source.)

### 🚇 Transport — *"Demand + access + gap"*
**Buyers:** LTA, operators, ride-hail/MaaS, logistics, TOD planners.
**Hero:** `mobility_access_score` + `mobility_desert_priority`.
**Delivered (8):** access · desert_priority · crowding · tod · ridehail · firstlast_gap · parking_stress · modal_split.
**Answers:** access scoring, transit deserts, crowding stress, TOD opportunity, ride-hail hotspots, first/last-mile gaps, parking stress, modal split.
**Built from:** `transit_score`, `multimodal_score`, `od_throughput`, `pipe_mrt_dist_m`, `pipe_dev_capacity_res`, `parking_lot_count`, `pop_resident`.
**Honest limit:** OD is aggregate in v1 — **daypart OD is Phase 3** (unlocks time-of-day ride-hail & crowding).

### 🛡️ Insurance & Risk — *"Risk score for this address"*
**Buyers:** GI insurers, reinsurers, banks (collateral), corporate risk.
**Hero:** `insurance_risk_score` (peril blend).
**Delivered (9):** fire · auto · health · bi_failure · collateral · nuisance · coastal_proxy · **insurance_risk_score** · accumulation_band.
**Answers:** property (fire), motor (auto), life/health, business-interruption, collateral, accumulation/concentration, a single underwriting score.
**Built from:** `biz_recent_dead_share` (the unique BI asset), `bldg_density_per_km2`, `lu_business_pct`+`industrial_adjacency_score`, `road_intersection_density_per_km2`, `pop_65plus`, `vulnerability_share`, plexis-e1 (accumulation).
**Honest limit:** **hazard stratification, not actuarial pricing.** **No crime/theft data** in SG open data — that peril is *omitted, not proxied*. Flood/heat are Phase 3 (`lu_water_pct` is a weak coastal proxy).

---

## Phase 0 — the 22 shared primitives

Cross-pack derived columns (each reused by ≥1 pack): cannibalization_pressure ·
delivery_demand_density · spend_proxy_index · diurnal_load_am/pm · diurnal_swing ·
water_demand_proxy · waste_gen_proxy · ev_demand_proxy · ev_charging_gap ·
first_last_mile_gap · transit_desert_score · crowding_stress ·
ridehail_demand_proxy · fire_risk_score · auto_exposure_score ·
industrial_hazard_buffer · pop_health_risk · collateral_value_proxy ·
nuisance_penalty · enbloc_upside_score · lease_decay_penalty.

---

## Validation — ALL GATES PASS

| Gate | Result |
|---|---|
| Row count | 1,191 hex8 per pack ✅ |
| Score range / not-constant | every score in sane range, varies ✅ |
| Subzone rollup | 270 subzones each (atlas has 270 populated) ✅ |
| **Known-answer** | RE feasibility tops **Tengah**; transit-desert tops **Jurong West / Choa Chu Kang**; retail whitespace tops **Jurong West** (the Yunnan story); insurance-BI ρ=**0.99** vs `biz_recent_dead_share`; retail whitespace tracks unserved (0.42) + winnable (0.93) ✅ |
| Dedup audit | 3 expected re-framings flagged & documented (below) |

**Documented re-framings (|r|>0.98 with an existing column — by design):**
- `utility_waste_score` ≈ `pop_resident` (waste genuinely ∝ population; the value is the tonnage unit for the utility buyer)
- `risk_bi_failure_score` ≈ `biz_recent_dead_share` (the insurance-framed view of the validated churn metric)
- `mobility_access_score` ≈ `adq_gap_core` (the transport-framed view of the atlas's adequacy)

These are honest re-presentations of atlas signal in domain language, not new
information — flagged in each pack's catalog `limits`.

---

## Build provenance — two findings worth recording

1. **Column reconciliation was essential.** The draft formulas referenced
   column names that don't exist on the real master (e.g. `bldg_density`,
   `intersection_density`, `lu_industrial_pct`, `n_ev_charger`,
   `est_total_floor_area`). With the defensive `col()` fallback these would have
   **silently resolved to zero**, quietly breaking six primitives. The audit
   mapped them to the real names — `bldg_density_per_km2`,
   `road_intersection_density_per_km2`, `lu_business_pct`+`industrial_adjacency_score`,
   `pc2_cat_transport_ev_count`, `est_total_floor_area_m2` — restoring real signal.
2. **`gap_<cat>` has no variance.** It reads ~0.84 everywhere (std 0.40), so
   "underserved" is true almost city-wide and a `gap × cap` whitespace product
   collapsed to just `cap` (ρ=0.97 with cap, 0.00 with gap). Fix: use
   `iso_walk10_unserved_pop_<cat>` (real variance) + `cap` as an **additive**
   blend (products collapse when a factor is flat) — whitespace now tracks both
   unserved demand and winnability.

---

## Design note — packs are sidecars

Each pack parquet holds **only its new scores + admin keys** (`hex8_id`,
`parent_subzone/pa/region`, `zone_type_broad`) — it does **not** copy the
existing 801 master columns it's built from. Those are joined from
`hex8_all_features.parquet` on `hex8_id` at use-time. This keeps the master
stable. (Optional enhancement: fold each pack's curated "TAKE" columns into its
parquet to make it self-contained for external delivery.)

---

## Deliverables

| File | Contents |
|---|---|
| `hex/hex8_domain_primitives.parquet` | 22 shared primitives |
| `hex/hex8_{retail,realestate,utilities,transport,insurance}_pack.parquet` | the 5 packs (39 scores) |
| `hex/subzone_{...}_pack.parquet` ×5 | pop-weighted subzone rollups (270) |
| `catalog/pack_{...}_catalog.json` ×5 | columns, heroes, use-cases, honest limits |
| `hex/{...}_pack_report.json` ×6 | per-build QA reports |
| `build_domain_primitives_sgp.py`, `pack_util.py`, `build_{pack}_pack_sgp.py` ×5 | builders |
| `rollup_domain_packs_subzone.py`, `build_domain_pack_catalogs.py`, `validate_domain_packs_sgp.py` | Phase 2 |

All committed (`github.com/Propheus/digital-atlas-sgp`, commit `3b44c29`).

---

## What's next

| Track | Items |
|---|---|
| **Phase 3 — cross-cutting** (each unlocks 4–5 packs) | spend/wealth surface · daypart OD/footfall · climate-risk (PUB flood + heat) · rooftop solar |
| **🔴 partnership/scrape** | commercial rent surface (Retail/RE) · private property prices (RE/Insurance) |
| **Agent integration** | tool wrappers `site_score(cat, hex)`, `risk_score(hex)`, `load_peers`… so **Plexis-Reasoner** can call the packs — they become its domain vocabularies |
| **Self-contained packs** | fold curated existing columns into each pack parquet for external delivery |
| **Cross-city** | the pack definitions transfer to HK & Jakarta atlases at parity — Jakarta's flood/informal layers are a head-start for its Insurance & Utilities packs |

---

*Built on Atlas v5.4.0 (1,191×801 hex8, plexis-e1/p1 exam-gated). Zero new data,
five sellable verticals, validated to the same discipline as the S1–S11 layers.*
