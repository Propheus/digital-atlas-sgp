# Singapore Digital Atlas — Full Context Snapshot

**Last updated:** 2026-04-11
**Purpose:** Single-source-of-truth for launching new projects on top of the SGP data lake.

---

## 1. Servers

### rwm-server (Primary — data, models, app hosting)
- **SSH alias:** `rwm-server`
- **Internal IP:** 10.0.2.23  |  **Public IP:** 52.179.10.198
- **Hostname:** DE-data-processor
- **Specs:** Azure VM, 16 vCPU AMD EPYC 9V74, 62 GB RAM, 96 GB disk (~80% used)
- **OS:** Ubuntu 24.04, Python 3.12.3

### evamlabs-deploy (Nginx reverse proxy + frontend)
- **SSH alias:** `evamlabs-deploy`
- **Internal IP:** 10.0.2.50  |  **Public IP:** 52.179.10.198
- **Nginx configs:** `/etc/nginx/sites-available/evamlabs`, `/etc/nginx/sites-available/sgp-sim`

### Other SSH-reachable servers
- `az-gojek-server` — Data storage (Overture Maps, `/datanew`)
- `az-gojek-infra-proc-{1,2,3,4,6,7,10,13,14,15,16,17}` — 12-server scraping fleet

### Public Domains
| Domain | Routes to | App |
|--------|-----------|-----|
| `https://sgp-sim.alchemy-propheus.ai/` | App Gateway → evamlabs nginx → rwm-server:16789 | Hex Adequacy Explorer |
| `https://sgp-digital-atlas-v2.alchemy-propheus.ai/` | rwm-server:18067 | SGP Subzone Explorer |
| `https://digital-atlas-v2.alchemy-propheus.ai/` | rwm-server:20990 | NYC Digital Atlas (separate) |

---

## 2. Running Services on rwm-server

| Screen | Port | Path | Purpose |
|--------|------|------|---------|
| **hex-adequacy** | **16789** | `/home/azureuser/hex-adequacy-app/` | Hex Adequacy Explorer (PRIMARY public app) |
| sgp-atlas | 18067 | `/home/azureuser/digital-atlas-sgp/sgp-atlas-app/app/dist/` | SGP subzone explorer |
| sim-api | 18068 | `/home/azureuser/digital-atlas-sgp/sim-ui/` | Store birth/death ABM (branded places × top 50 subzones) |
| **scenario-sim** | **18070** | `/home/azureuser/digital-atlas-sgp/scenario_sim/` | Subzone-level scenario simulator (connectivity + clinics + FairPrice) |
| digital-atlas-v2 | 20990 | `/home/azureuser/digital-atlas-v2/` | NYC Digital Atlas (DO NOT TOUCH) |
| alchemy, retail, health, services, food_bev, graphapi, atlas-search, da-insights-v2, reaosning-run | various | — | Other workers |

### Nginx Routes (evamlabs-deploy)
| Path | Target | App |
|------|--------|-----|
| `/hex/` | rwm-server:16789 | Hex Adequacy Explorer |
| `/sgp/` | 127.0.0.1:14090 | SGP Subzone Explorer |
| `/blr/` | 127.0.0.1:13090 | Bangalore Atlas |
| `/` | 127.0.0.1:3000 | Main EvamLabs (Next.js) |
| `sgp-sim.alchemy-propheus.ai` (vhost) | rwm-server:16789 | DA-Simulation custom domain |

---

## 3. Data Catalog — `/home/azureuser/digital-atlas-sgp/` (5.7 GB)

### Places (763 MB)
| File | Size | Records |
|------|------|---------|
| `data/places_consolidated/sgp_places_v2.jsonl` | 83 MB | **174,713 places (MASTER)** |
| `data/places/sgp_places.jsonl` | 33 MB | 66,851 places (v1, original) |
| `data/overture_places_2025/sgp_places.parquet` | 26 MB | 147,501 Overture raw |
| `data/places_consolidated/llm_classified.jsonl` | 5 MB | 53,584 LLM classifications |
| `data/places/sgp_brands.jsonl` | 32 KB | 233 brands |

### Boundaries
- `data/boundaries/subzones.geojson` — 332 subzone polygons
- `data/boundaries/planning_areas.geojson` — 55 planning areas

### Buildings (Fused: Overture + OSM + HDB)
- `data/buildings_overture/sgp_buildings.parquet` — 377,331 Overture (37 MB)
- `data/buildings_overture/sgp_buildings_fused.parquet` — Fused HDB+OSM (23 MB)
- `data/buildings_overture/subzone_buildings_fused.parquet` — Per-subzone aggregated
- `data/housing/hdb_existing_buildings.geojson` — 13,386 authoritative HDB blocks (54 MB)
- `data/buildings/buildings.geojson` — 125,973 OSM buildings (82 MB)

### Demographics & Housing
- `data/demographics/pop_age_sex_tod_2025.csv` — Census 2025
- `data/demographics/dwellings_subzone_2025.csv` — Dwelling by floor area
- `data/property/hdb_resale_prices.csv` — 227,207 HDB transactions (21 MB)
- `data/property/private_resi_transactions.csv` — 287,196 private transactions (22 MB)

### Roads & Land Use
- `data/roads/roads.geojson` — 550,991 OSM road edges (220 MB)
- `data/land_use/master_plan_land_use.geojson` — 113,212 URA zoning parcels (166 MB)

### Transit
- `data/transit_updated/train_stations_mar2026.geojson` — 231 MRT/LRT stations
- `data/transit_updated/bus_stops_mar2026.geojson` — 5,177 bus stops
- `data/transit/rail_lines.geojson` — 1,366 rail segments (22 MB)
- `data/transit/traffic_signals.geojson` — 44,922 signals (16 MB)

### LTA Live (`data/lta_live/`)
- `transport_node_train_202601.csv` — MRT PV Jan 2026 (88.6M monthly taps)
- `transport_node_bus_202512.csv` — Bus PV Dec 2025
- `traffic_speed_bands_full.json` — 15,500 road segments
- `traffic_incidents.json` — Live incidents
- `est_travel_times_full.json` — 192 expressway segments
- `bus_services.json` — 788 bus services
- `congestion_features.parquet` — Per-subzone congestion
- `od_train_202512.zip` — OD train matrix
- `carpark_availability.json`, `taxi_availability.json` — Live snapshots

### Amenities
- `data/amenities_updated/eating_establishments_sfa.geojson` — 34,378 SFA licensed (36 MB)
- `data/amenities_updated/chas_clinics.geojson` — 1,193 CHAS clinics
- `data/amenities_updated/preschools.geojson` — 2,290 preschools
- `data/amenities_updated/hawker_centres.geojson` — 129 hawker centres
- `data/amenities_updated/silver_zones.geojson` — 42 elderly zones
- `data/amenities_updated/school_zones.geojson` — 211 school zones
- `data/amenities_updated/tourist_attractions.geojson` — 109 attractions
- `data/amenities/parks_nature_reserves.geojson` — 450 parks
- `data/amenities/park_connector.geojson` — 883 PCN segments (340 km)
- `data/amenities/hotels.geojson` — 468 hotels
- `data/amenities/supermarkets.geojson` — 526 supermarkets
- `data/amenities/schools.csv` — 337 schools

### Business
- `data/business/acra_entities.csv` — 2,076,437 ACRA entities (218 MB)
- `data/business/graduate_employment.csv` — 1,550 records

### NVIDIA Personas
- `data/personas/train-00000-of-00002.parquet` + `train-00001-of-00002.parquet` — 148,000 personas (262 MB)
- `data/personas/persona_features_by_subzone.parquet` — 35 features × 318 subzones

### Satellite
- `data/satellite/satellite_features.json` — 18 features per subzone
- `data/satellite/night_light_temporal.json` — 2022→2024 change

### Hex Grid V9
- `data/hex_v9/hex_features_v2.parquet` — **5,897 hexes × 154 features**
- `data/hex_v9/hex_features.geojson` — Polygon GeoJSON
- `data/hex_v9/HEX_V9_REPORT.html` — Validation report

### Feature Tables
- `model/v8_subzone_table.parquet` — **332 subzones × 243 features (MAIN TABLE)**
- `model/v8_adequacy_table.parquet` — 332 × 70 adequacy features
- `data/features/subzone_features_raw.parquet` — 332 × 205 raw features
- `data/features/hdb_derived_features.parquet` — 332 × 24 HDB derived features

### Embeddings
- `model/embeddings_v5/feature_matrix.parquet` — 332 × 431
- `model/embeddings_v5/ae_embeddings.parquet` — 332 × 32 (AE 32-dim)
- `model/embeddings_v6/feature_matrix_v6.parquet` — 332 × 465 (V5 + personas)

### Micrographs
- `micrograph_output/` — 650 MB, 12 categories × ~66K places (V2)
- `micrograph_output_v3/` — 1.6 GB, V3 pipeline (174K places)
- `micrograph_pipeline/` — Pipeline code

### Reports & Analysis (`model/results/`)
- `gap_analysis_v7.parquet` — 4th-root gap model output
- `report_v7.json` — Model report
- `category_drivers_v7.json` — Per-category drivers
- `CATEGORY_INTELLIGENCE.html` — 24-category R² and drivers
- `V8_FEATURE_REPORT.html` — 142 subzone features documented
- `HEX_V9_REPORT.html` — Hex validation
- `FEATURE_INVENTORY.html` — 484-feature inventory
- `FAIRPRICE_ADEQUACY.html` — FairPrice adequacy report
- `model/DEEP_ANOMALIES.html` — Satellite anomaly detection
- `model/NIGHT_LIGHT_GROWTH.html` — VIIRS temporal analysis

### Misc
- `data/osm/singapore-latest.osm.pbf` — Raw OSM (231 MB)
- `data/osm_pois/` — 28K amenities, 12K leisure
- `data/graphs/transit_connectivity.json` — 139 nodes, 914 edges
- `model/simulation_phase0_v2.json` — Agent simulation results

---

## 4. Hex Adequacy App — Live Deployment

- **URL:** https://sgp-sim.alchemy-propheus.ai/
- **Direct:** http://10.0.2.23:16789/
- **Server path:** `/home/azureuser/hex-adequacy-app/`
- **GitHub:** github.com/Propheus/da-sgp-simulation-app

```
hex-adequacy-app/
├── index.html, neighbourhood.html
├── assets/
│   ├── main-CvKP35NM.js (30 KB, PATCHED)
│   ├── main-IwBNiBo1.css (14 KB)
│   ├── mapbox-gl-DTwc483t.js (1.9 MB)
│   ├── neighbourhood-ClRoke_a.js (58 KB)
├── data/
│   ├── hex.geojson (22 MB, 5,897 hexes × 92 features)
│   ├── subzones_profiles.geojson (4.9 MB)
│   └── region_interactions.json (26 KB)
├── transit_gap_report.html, transit_congestion_experiment.html
└── server.py (with /hex/ prefix stripping)
```

**Tabs (after patching):**
1. Adequacy Analysis — hex map with 10 metrics
2. Neighbourhood Profiles — 332 subzone profiles
3. Insights & Reports — Transit gap report iframe

**Patches on rwm-server `/tmp/`:** `patch_all.py`, `patch_branding.py`, `patch_tabs.py`, `server_fix.py`, `patch_labels.py`

Re-apply after redeploy:
```bash
ssh rwm-server 'python3 /tmp/patch_all.py && python3 /tmp/patch_branding.py'
```

---

## 5. Source Code Locations

| Location | What |
|----------|------|
| `/Users/sumanth/propheus-projs/da-sgp/digital-atlas-sgp/` | Main atlas repo (data, models, scripts) |
| `/Users/sumanth/propheus-projs/da-sgp-simulation-app/` | Hex app source (GitHub-tracked) |
| `/Users/sumanth/propheus-projs/da-sgp/digital-atlas-sgp/apps/hex-adequacy/` | Local hex app dev copy |
| `/home/azureuser/da-sgp-simulation-app/` (rwm-server) | Source mirror on server |
| `/home/azureuser/hex-adequacy-app/` (rwm-server) | Deployed build |

---

## 6. Key Numbers

| Metric | Value |
|--------|-------|
| Total places | 174,713 |
| Subzones | 332 |
| H3-9 hexagons | 5,897 (175m edge, ~0.12 km²) |
| V8 subzone features | 243 |
| V9 hex features | 154 |
| Data sources | 14 |
| Overture buildings | 377,331 |
| HDB blocks (authoritative) | 13,386 |
| OSM road edges | 550,991 |
| URA zoning parcels | 113,212 |
| MRT stations | 231 |
| Bus stops | 5,177 |
| Traffic signals | 44,922 |
| ACRA entities | 2,076,437 |
| NVIDIA personas | 148,000 |
| HDB resale transactions | 227,207 |
| Monthly MRT taps (Jan 2026) | 88.6M |
| Total SGP data | 5.7 GB |

---

## 7. Models

### V7 Gap Model (Current)
- **Transform:** 4th root (R²=0.755, std=0.129)
- **Stage 1:** 56 structural features → total places (R²=0.742)
- **Stage 2:** Per-category prediction (mean R²=0.607)
- **Gap bands:** Percentile-based (top/bottom 15% = signal)

### V5/V6 Embeddings
- V5: 431 features → 32-dim AE (separation 0.720)
- V6: 465 features → 32-dim AE (V5 + personas, +9.5% lift)

### V8 City Model — Population
- Physical structure → population: R²=0.816
- Top drivers: gov preschools (46%), residential zoning (38%)

---

## 8. Key Findings

1. **995,613 residents (24%)** live >800m from MRT
2. **Government infrastructure predicts private markets** — SFA licensing #1 for F&B (55%)
3. **Bar districts emerge from culture, not zoning** (R²=0.44)
4. **Built-up ratio** (r=0.45) predicts congestion better than transit absence
5. **More MRT = more jam** — dense cores attract visitors
6. **Model identifies 9/12 known congestion spots** (75%)
7. **CHAS clinic coverage excellent** — no populated hex lacks clinic <500m
8. **Gyms follow families, not fitness culture**
9. **Condo % is Singapore's stealth income proxy**
10. **Industrial zoning is a secret office market signal**
11. **Yishun East** most transit-deficient (70K affected, 13 deficit hexes)
12. **FairPrice deserts:** 802,685 residents (19.3%) >800m; Yunnan biggest gap (60K, 1.4km)

---

## 9. API Keys

- **LTA DataMall:** `aaoMYVkcRUCheVpACtoykQ==`
- **Mapbox:** `MAPBOX_TOKEN_PLACEHOLDER`
- **OpenRouter:** `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`
- **data.gov.sg:** `v2:1640185d0e5ac09bdf935dec249bdd589c3a0ad87a7542a9e939fc56bfbcd805:FxDrTgyu3b2Ohjw-JAubYddVjNcxnHMg`

---

## 10. Restart Commands

```bash
# Hex adequacy app (port 16789) — PRIMARY
ssh rwm-server 'screen -X -S hex-adequacy quit; screen -dmS hex-adequacy bash -c "cd /home/azureuser/hex-adequacy-app && python3 server.py"'

# SGP atlas explorer (port 18067)
ssh rwm-server 'screen -X -S sgp-atlas quit; screen -dmS sgp-atlas bash -c "cd /home/azureuser/digital-atlas-sgp/sgp-atlas-app/app/dist && python3 -m http.server 18067 --bind 0.0.0.0"'

# Simulation API (port 18068)
ssh rwm-server 'screen -X -S sim-api quit; screen -dmS sim-api bash -c "cd /home/azureuser/digital-atlas-sgp/sim-ui && python3 sim_api.py"'

# Scenario sim (port 18070) — subzone-level connectivity + clinics + FairPrice
ssh rwm-server 'screen -X -S scenario-sim quit; screen -dmS scenario-sim bash -c "cd /home/azureuser/digital-atlas-sgp/scenario_sim && python3 -u -m server.app > /tmp/scenario_sim.log 2>&1"'
```

---

## 11. Git Repos

- **Main atlas:** github.com/paperclip369/digital-atlas-sgp (LFS: geojson, csv, parquet, jsonl)
- **Simulation app:** github.com/Propheus/da-sgp-simulation-app

---

## 12. Project Launchpad — What's Buildable on Top of This Data

The data lake supports many directions. Pick a thread:

### A. Spatial / urban-planning analytics
- Adequacy/gap analysis for any category (FairPrice template extends to any brand or service type)
- Catchment + accessibility studies (transit, walking, driving isochrones via roads.geojson)
- Land-use change detection (master plan vs Overture buildings vs satellite)
- HDB resale price modelling (227K transactions × 243 V8 features)
- Private resi pricing (287K transactions, segment by district/property type)

### B. Movement / activity intelligence
- OD train flow analysis (`od_train_202512.zip`)
- Congestion modelling (V8 model already at 75% recall on known hotspots)
- Bus PV vs MRT PV substitution
- Live carpark / taxi availability dashboards

### C. Subzone / hex embedding products
- Similar-neighbourhood search (V6 32-dim AE embedding)
- "Twin city" scoring across subzones
- Cluster-based persona segmentation (NVIDIA personas × subzones)

### D. Place / business intelligence
- Brand expansion recommender (where should X open next?)
- Competitor density heatmaps per category
- ACRA entity → places linkage (2M entities × 174K places)
- Micrograph-based site scoring (V3 pipeline covers 174K places)

### E. App / product surfaces
- New tabs / views in hex-adequacy-app (single source, single deploy)
- Standalone reports (HTML, like FAIRPRICE_ADEQUACY.html template)
- API endpoints via sim-api FastAPI (port 18068)

To start a new project: pick a thread, name it, and we scope a v0 against the existing data files. No new ingestion needed for most directions.
