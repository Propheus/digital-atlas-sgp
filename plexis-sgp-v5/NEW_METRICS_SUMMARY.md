# Digital Atlas v5 — the new derived metrics, in plain language

**What this is:** the inventory of metrics we *invented or derived* in v5 (not raw data we
imported). One line on what each means and the decision it serves. Everything here is
validation-gated (`SITE_SELECTION_VALIDATION.md`) and catalogued
(`catalog/feature_catalog.parquet`). 2026-06-12.

---

## 1 · "What would a NEW outlet capture here?" — the opportunity family

| Metric | Meaning | Why it matters |
|---|---|---|
| **`cap_<category>` (11) + `cap_total`, `cap_best_category`** | Huff gravity model: demand (in *outlet-equivalents*) a new outlet at this hex would win against every existing competitor. cap=1.0 ⇒ enough winnable demand to support one average outlet | THE site-selection number. Re-derived the known FairPrice desert (Yunnan p96) blind; refuses to score bars (culture, not demand — deliberately deleted) |
| **`roi_cap_per_rent_<cat>` (5)** | capture ÷ local rent | Opportunity per dollar of occupancy cost — turns a heat-map into an investment ranking |
| `latent_demand` *(explorer)* | z(activity) − z(commercial supply) | Footfall that supply hasn't caught up with — "hungry corners" |

## 2 · "Who can actually reach this spot?" — the catchment family

| Metric | Meaning | Why it matters |
|---|---|---|
| **`iso_walk10_pop / _spend / _places / _magnets`** | People, spending power, venues within a TRUE 800 m network walk (not a circle) — multi-source from the hex's activity centre | Kills the "800-metre lie"; severance-aware |
| **`iso_walk10_unserved_pop_<cat>` (4)** ⭐ | Catchment residents with NO outlet of that category near home | **The single most novel column in the atlas** (max correlation 0.14 with all 800 prior features) — pure underserved demand |
| `iso_walk10_competitors_<cat>` (4) | Existing outlets inside the walk catchment | The denominator of any pitch |
| **`iso_severance_ratio`** | Network-reached pop ÷ straight-line pop (healthy grid ≈ 0.55) | Quantifies how much expressways/rivers amputate a location's true reach |
| `iso_transit15_pop / _places` | Door-to-door 15-min weekday-AM transit reach (GTFS graph, waits included) | Yishun interchange reaches 250K — the bus city made visible |

## 3 · "Who is HERE, and when?" — the temporal population family

| Metric | Meaning | Why it matters |
|---|---|---|
| **`dt_pop`** | Daytime headcount: residents − AM commuters out + commuters in | The first time the atlas distinguishes the day city from the night city |
| `dt_net_am_persons`, `dt_ratio`, `dt_class` | Net AM inflow; day/night ratio; job-centre / balanced / bedroom label | Replaced the old `breathing_idx`, which we proved was direction-blind (it was just throughput) |

## 4 · "Is this place commercially alive or dying?" — the vitality family (ACRA, 2.07M entities)

| Metric | Meaning | Why it matters |
|---|---|---|
| **`biz_recent_dead_share`** ⭐ | Share of 2018+ registered businesses now deregistered | A churn/risk signal nothing else in the atlas carried (max prior corr 0.39). 46% in parts of Yunnan — sobering and true |
| `biz_dead_share`, `biz_median_age_yrs`, `biz_formation_5y` | Lifetime mortality, incumbent age, recent formation | Vitality vs entrenchment at a glance |
| **`biz_live_robust`** | Live entities with any single address capped at 100 | Honest density — Paya Lebar Square alone held 19K paper registrations |
| **`biz_per_address`** | Live entities per unique postal | *Detects* virtual-office/registered-agent buildings (City Hall: 109–131 per address) |

## 5 · "Who thrives next to whom?" — the empirically learned synergy family

| Metric | Meaning | Why it matters |
|---|---|---|
| **24×24 co-location lift matrix** | How much category B over-concentrates near A, beyond generic clustering (bootstrap-significant only) | The city's hidden social contract: bars seek bars (3.0×), industry repels homes (0.5×), and **cafés do NOT follow offices (0.87×)** — a stereotype, killed |
| **`colo_fit_<cat>` (11)** | Does this hex's surrounding *mix* match what category c empirically thrives in (share-weighted, volume-independent) | Mix-match, not amenity-count — survived the redundancy gate only after we redesigned it twice |

## 6 · "Can a workforce / can workers get there?" — the labour family

| Metric | Meaning | Why it matters |
|---|---|---|
| `labor_pool_30m / _45m` | Working-age people who can reach the hex by transit | CBD: 1.68M (59.6% of the workforce). Tuas: bottom of the island — its labour problem, quantified |
| **`labor_jobs_balance_45m`** ⭐ | Jobs reachable ÷ workers reachable | Novel (max prior corr 0.27); flags job-rich/transit-poor fringes instantly |

## 7 · Micro-location & cost derivatives

| Metric | Meaning | Why it matters |
|---|---|---|
| **`vis_exit_footfall`** | Weekday taps at the nearest MRT *exit*, station volume split per exit | The per-door number an outlet actually experiences — one Punggol-concourse exit out-foots any single Orchard exit |
| `vis_traffic_pass_proxy`, `vis_corner_premium` | Drive-past exposure; signalised main-road corners | Roadside-format siting |
| **`rent_resi_psf_med`** (+ resolution flag) | IDW rent surface from 913 URA projects | The atlas's first spatial price signal (commercial rent is paywalled island-wide — documented) |
| **`pipe_dev_capacity_res/com`** | FAR headroom: allowed GPR − built FAR, × zoning share | Where growth CAN physically go (Matilda 0.50, Bidadari 0.34, built-out Toa Payoh exactly 0) — the footprint version was wrong and we proved it |
| `pipe_new_mrt_within_800m / dist / name` | Proximity to the 37 FUTURE rail stations (MP2019 minus existing) | "Demand in three years" — full JRL recovered automatically |
| `bto_pipeline_est` | Town-level under-construction HDB units allocated within town by FAR headroom | Estate-growth estimate despite BTO locations no longer being published |
| `linkway_per_road_km` (+ lengths) | Covered-walkway metres per road km | Sheltered-walk density — the most Singapore metric in existence (245 km quantified) |
| `pr_share`, `low_income_share` | PR ratio; low-income ratio | Rescued as *ratios* after their level versions were (correctly) auto-deduped |
| **per-place `pmg_*` (19)** | Each of 190,591 venues' own 400/800 m fingerprint: rivals, complements, anchors, transit | Now drawn live on the SG Pulse map — click any venue |

## 8 · The similarity space

| Asset | Meaning | Why it matters |
|---|---|---|
| **`plexis-e1` 256-d hex embedding** | Hybrid 160 PCA + 96 contrastive dims over all 801 features; distance = functional similarity | Powers twin-finding ("which places are like Tiong Bahru?"); passed a 13-check exam locked before training; the pure neural version *failed* the exam and was rejected — use it RAW, never re-normalised |

---

### The ⭐ rule of thumb
Stars mark metrics with essentially **no correlation to anything that existed before**
(`iso_walk10_unserved_pop_*` 0.14 · `labor_jobs_balance` 0.27 · `biz_recent_dead_share`
0.39) — genuinely new information about Singapore, not recombinations.

### Where to touch them
Live hex8 view (1,191 × 801) · `catalog/feature_catalog.parquet` for every definition ·
SG Pulse (http://10.0.2.25:16095) to *see* them · ATLAS_V5_REPORT.html for validations.
