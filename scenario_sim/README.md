# Scenario Sim — Subzone-level connectivity & adequacy simulation

Subzone-agent simulation for Singapore. 332 subzones as agents. Three scenario knobs:

1. **New transit link** (BRT / MRT extension / express bus corridor)
2. **Add/remove CHAS clinic**
3. **Add/remove NTUC FairPrice store**

Output: accessibility deltas, adequacy maps, opportunity rankings, redundancy flags, "three takeaways" narrative.

## Layout

```
scenario_sim/
├── data_prep/        # One-time scripts that build the cache
│   ├── 01_subzone_state.py
│   ├── 02_centroids.py
│   ├── 03_rail_graph.py
│   ├── 04_travel_matrix.py
│   ├── 05_facilities.py
│   └── run_all.sh
├── engine/           # Pure-python sim engine
│   ├── state.py          # Load cached parquets into a State object
│   ├── gravity.py        # Huff model + logsum accessibility
│   ├── scenarios.py      # Knob mutations
│   └── opportunity.py    # Marginal welfare gain + cannibalization + feasibility
├── server/
│   ├── app.py            # FastAPI
│   └── static/           # HTML + JS UI
└── cache/            # Pre-computed parquets (<10 MB total)
    ├── subzone_state.parquet
    ├── centroids.parquet
    ├── rail_graph.pkl
    ├── travel_matrix.parquet
    └── facility_supply.parquet
```

## Running

**Data prep** (one-time, run on rwm-server where the source data lives):
```
cd scenario_sim/data_prep && bash run_all.sh
```

**Local engine dev** (uses cached parquets):
```
python -m engine.state    # verify cache loads
```

**Server** (rwm-server, screen `scenario-sim`, port 18070):
```
cd scenario_sim && python -m server.app
```

## Design reference

See upstream design conversation. Key decisions:

- **Agents:** 332 subzones (minus ~20 excluded non-populated zones)
- **Categories modeled:** connectivity, CHAS clinics, FairPrice groceries
- **Core model:** Huff / multinomial logit gravity with logsum welfare output
- **Parameters:** ~15 total; only β_clinic, β_grocery are fit to median catchment priors
- **Validation gates:** Yunnan grocery desert + Yishun East transit deficit must appear
- **Tick:** instant before/after; optional 5-year playback (v0.5)

## Deployment

- Server: rwm-server
- Port: 18070
- Screen: scenario-sim
- Path: /home/azureuser/digital-atlas-sgp/scenario_sim/
- Disk budget: cache <10 MB; code <500 KB
