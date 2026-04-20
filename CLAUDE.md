# Digital Atlas Singapore — Project Context

## Working Directory
`/Users/sumanth/propheus-projs/da-sgp/digital-atlas-sgp`

## Full snapshot
See [`CONTEXT.md`](./CONTEXT.md) for the complete server + data catalog (5.7 GB across 14 sources, all paths, ports, models, findings, restart commands, project launchpad).

## What This Is
Mathematical representation of Singapore's urban structure. **174,713 places** across 332 subzones and 5,897 H3-9 hexagons with per-place micrographs, deployed as an interactive map app.

## Deployment

### Hex Adequacy Explorer (PRIMARY public app)
- **URL:** https://sgp-sim.alchemy-propheus.ai/
- **Server:** `rwm-server` | **Port:** 16789 | **Screen:** `hex-adequacy`
- **Path:** `/home/azureuser/hex-adequacy-app/`
- **GitHub:** github.com/Propheus/da-sgp-simulation-app

### SGP Atlas App (subzone explorer)
- **Server:** `rwm-server` | **Port:** 18067 | **Screen:** `sgp-atlas`
- **Path:** `/home/azureuser/digital-atlas-sgp/sgp-atlas-app/app/dist/`

### Scenario Sim (subzone-level connectivity + clinics + FairPrice)
- **Server:** `rwm-server` | **Port:** 18070 | **Screen:** `scenario-sim`
- **Path:** `/home/azureuser/digital-atlas-sgp/scenario_sim/` (code + cache + UI)
- **What:** 332 subzone agents, Huff gravity + logsum welfare, 3 scenario knobs: new transit link / add CHAS clinic / add FairPrice. Rebuild from source (no minified patching).

### NYC Atlas App (SEPARATE, DO NOT TOUCH)
- **Server:** `rwm-server` | **Port:** 20990 | **Screen:** `digital-atlas-v2`
- **Path:** `/home/azureuser/digital-atlas-v2/`
- **URL:** `https://digital-atlas-v2.alchemy-propheus.ai/`

### Server Data
- **Full data:** `/home/azureuser/digital-atlas-sgp/data/` (1.9 GB, 15 layers)
- **Micrographs:** `/home/azureuser/digital-atlas-sgp/micrograph_output/`
- **Pipeline:** `/home/azureuser/digital-atlas-sgp/micrograph_pipeline/`
- **Scripts:** `/home/azureuser/digital-atlas-sgp/scripts/`

## Git
- **Repo:** `github.com/paperclip369/digital-atlas-sgp`
- **LFS:** Tracks *.geojson, *.csv, *.parquet, *.jsonl, app/dist/data/**/*.json, micrograph_output/**
- **3 commits:** v1.0, app plan, v1.1 (LLM-classified + v2 micrographs)

## Local Structure
```
data/                    Raw data layers (boundaries, demographics, roads, etc.)
model/                   Feature matrices (332×202) + gap analysis
micrograph_output/       12 category micrographs (per-place star-graphs)
micrograph_pipeline/     Pipeline code (config + run_cafe_v2.py)
app/
  dist/                  Running app (static HTML/JS/CSS + data JSONs)
  compose_data.py        Transforms raw data → frontend JSONs
  public/data/           Composed frontend data (9.5 MB)
scripts/                 Processing pipeline (19 steps + models v1-v5)
docs/                    Architecture, reports, ideation
```

## Key Numbers
- **174,713 places** (master: `data/places_consolidated/sgp_places_v2.jsonl`) | 24 categories | 233 brands
- 332 subzones × 243 V8 features | 5,897 H3-9 hexes × 154 V9 features
- 12 category micrographs (V2) + V3 pipeline covering 174K places
- V7 gap model: R²=0.755 | V8 population model: R²=0.816

## App Tech
- NYC Digital Atlas v2 codebase adapted for SGP
- React + Vite + Mapbox GL + Deck.gl + Framer Motion + Zustand + Tailwind
- Built JS at `app/dist/assets/index-BCz-A6kC.js` (patched via string replacement)
- Data served as static JSON files from `app/dist/data/`

## Key Files
- `app/dist/assets/index-BCz-A6kC.js` — The built app JS (all UI logic)
- `app/dist/data/tract_profiles.json` — 332 subzone profiles
- `app/dist/data/cafes_slim.json` — Place scatter data (tuples)
- `app/dist/data/cafe_details/` — Per-subzone micrograph details
- `micrograph_pipeline/run_cafe_v2.py` — Quality micrograph pipeline
- `data/places/sgp_places.jsonl` — Source of truth for all places
- `STATUS.html` — Full build report

## Servers (SSH Aliases)
- `rwm-server` — Main server (digital atlas, micrograph processing, app hosting)
- `az-gojek-server` — Data storage (Overture Maps, /datanew)
- `az-gojek-infra-proc-{1,2,3,4,6,7,10,13,14,15,16,17}` — 12-server fleet for scraping

## API Keys
- OpenRouter: `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`
- data.gov.sg: `v2:1640185d0e5ac09bdf935dec249bdd589c3a0ad87a7542a9e939fc56bfbcd805:FxDrTgyu3b2Ohjw-JAubYddVjNcxnHMg`
- Mapbox: `MAPBOX_TOKEN_PLACEHOLDER`

## Recent Changes (v1.1)
- All 66K places LLM-classified via Gemini 2.0 Flash (660 reclassified)
- Micrograph v2: quality anchors (MRT only for T1, 10+ review competitors, 30+ review demand magnets)
- App fully customized for SGP (zero NYC references)
- DRIVE NETWORK STATS panel removed
- Deployed on rwm-server:18067
