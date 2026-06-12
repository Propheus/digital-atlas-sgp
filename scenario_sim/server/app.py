"""
FastAPI server for scenario_sim.

Endpoints:
  GET  /                      → UI (static HTML)
  GET  /api/state             → baseline adequacy + logsum A per subzone
  GET  /api/subzones.geojson  → subzone polygons (served once from cache)
  GET  /api/stations          → MRT station locations
  GET  /api/catalog           → dropdown catalog (subzones, categories)
  POST /api/scenario          → apply mutations, return state + delta + takeaways
  GET  /api/opportunity       → ranked top-K opportunities (no scenario mutation)

Run:
  python -m server.app           # from scenario_sim/
  or via screen: screen -dmS scenario-sim python3 -m server.app
"""
from __future__ import annotations
from pathlib import Path
import json
import sys

import numpy as np
import pandas as pd
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Allow running as `python -m server.app` or `python server/app.py`
HERE = Path(__file__).parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))

from engine.state import load_state, State, LARGE_MIN
from engine.gravity import Gravity, Category
from engine.scenarios import Scenario
from engine.opportunity import Opportunity

# ============================================================
# Startup: load state + calibrate gravity
# ============================================================
PORT = 18070
STATIC_DIR = HERE / "static"
DATA_DIR = ROOT.parent / "data" if (ROOT.parent / "data" / "boundaries" / "subzones.geojson").exists() else Path("/home/azureuser/digital-atlas-sgp/data")

print(f"[server] loading state from {ROOT / 'cache'}")
STATE: State = load_state()
GRAV = Gravity(STATE)
print("[server] calibrating β...")
BETAS = GRAV.calibrate_all()
print(f"[server] calibrated: {BETAS}")
OPP = Opportunity(STATE, GRAV)

# Baseline compute (once)
BASELINE = {cat: GRAV.compute(cat) for cat in ("clinic", "grocery")}

# Cache subzone geojson for reuse
SZ_GEOJSON_PATH = DATA_DIR / "boundaries" / "subzones.geojson"
print(f"[server] loading geometries from {SZ_GEOJSON_PATH}")
with open(SZ_GEOJSON_PATH) as f:
    SZ_GEOJSON = json.load(f)
# Normalize props: ensure subzone_code is the primary key
for feat in SZ_GEOJSON["features"]:
    p = feat["properties"]
    p["subzone_code"] = p.get("SUBZONE_C", "")
    p["subzone_name"] = p.get("SUBZONE_N", "").title()
    p["planning_area"] = p.get("PLN_AREA_N", "").title()
    p["region"] = p.get("REGION_N", "").title()
    # Drop huge unused props to minimize payload
    for k in list(p.keys()):
        if k not in ("subzone_code", "subzone_name", "planning_area", "region"):
            del p[k]

# Station catalog for display
STATIONS_DF = pd.read_parquet(ROOT / "cache" / "stations.parquet")

print(f"[server] ready: {STATE.n} subzones, {len(SZ_GEOJSON['features'])} polygons, {len(STATIONS_DF)} stations")

# ============================================================
# FastAPI
# ============================================================
app = FastAPI(title="SGP Scenario Sim", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _state_snapshot(result_by_cat) -> dict:
    """Pack per-subzone numbers for the frontend."""
    s = STATE
    out_rows = []
    for i in range(s.n):
        row = {
            "subzone_code": s.codes[i],
            "subzone_name": str(s.subzone_name[i]),
            "planning_area": str(s.planning_area[i]),
            "population": int(s.population[i]),
            "included": bool(s.included[i]),
            "home_lat": float(s.home_lat[i]),
            "home_lon": float(s.home_lon[i]),
            "elderly_share": float(s.elderly_share[i]),
            "supply": {
                "chas_clinics": int(s.supply["chas_clinics"][i]),
                "fairprice": int(s.supply["fairprice"][i]),
            },
        }
        for cat, res in result_by_cat.items():
            row[f"A_{cat}"] = float(res.A[i])
            row[f"L_{cat}"] = float(res.L[i])
        out_rows.append(row)
    return {"subzones": out_rows}


def _world_snapshot(result_by_cat) -> dict:
    s = STATE
    cats = {}
    for cat, res in result_by_cat.items():
        key = GRAV.params[cat].supply_key
        cats[cat] = {
            "label": "NTUC FairPrice" if cat == "grocery" else "CHAS Clinic",
            "facilities": int(s.supply[key].sum()),
            "monthly_visits": float(res.total_visits),
            "monthly_load_served": float(res.L.sum()),
            "mean_A_included": float(res.A[s.included].mean()),
        }
    return {
        "n_subzones": int(s.n),
        "n_active": int(s.included.sum()),
        "total_population": int(s.population[s.included].sum()),
        "categories": cats,
    }


@app.get("/api/world")
def world():
    """Global counts and aggregate agent activity under the baseline."""
    return _world_snapshot(BASELINE)


@app.get("/api/inspect")
def inspect(code: str, category: Category = "grocery", top_k: int = 5):
    """Per-subzone detail: demand generated, top destinations, top origins."""
    s = STATE
    g = GRAV
    if code not in s.code_to_idx:
        return JSONResponse({"error": f"unknown subzone {code}"}, status_code=404)
    j = s.idx(code)
    res = BASELINE[category]
    supply_key = g.params[category].supply_key

    prob_row = res.prob[j]  # (n,) — where resident-j's trips go
    # Per-capita × pop × included — monthly trips this subzone *generates*
    demand_j = float(s.population[j] * res.demand[j]) if s.included[j] else 0.0

    # Top destinations by probability
    order = np.argsort(-prob_row)
    destinations = []
    for i in order[:top_k]:
        share = float(prob_row[i])
        if share < 0.005:
            break
        destinations.append({
            "subzone_code": s.codes[int(i)],
            "subzone_name": str(s.subzone_name[int(i)]),
            "planning_area": str(s.planning_area[int(i)]),
            "share": share,
            "visits": share * demand_j,
            "supply": int(s.supply[supply_key][int(i)]),
            "travel_min": float(s.T_composite[j, int(i)]),
            "is_local": bool(i == j),
        })

    # Top origins if this subzone hosts facilities
    origins = []
    if s.supply[supply_key][j] > 0:
        # inflow to i=j from all origins o
        inflow_vec = res.prob[:, j] * (s.population.astype(np.float32) * res.demand * s.included.astype(np.float32))
        oorder = np.argsort(-inflow_vec)
        for o in oorder[:top_k]:
            v = float(inflow_vec[int(o)])
            if v < 50:
                break
            origins.append({
                "subzone_code": s.codes[int(o)],
                "subzone_name": str(s.subzone_name[int(o)]),
                "planning_area": str(s.planning_area[int(o)]),
                "visits": v,
                "share": float(v / res.L[j]) if res.L[j] > 0 else 0.0,
                "travel_min": float(s.T_composite[int(o), j]),
                "is_local": bool(o == j),
            })

    # Local capture rate: % of this subzone's generated trips that stay within j
    local_capture = float(prob_row[j]) if s.included[j] else 0.0

    adq = float(g.adequacy_index(category, res)[j])

    return {
        "subzone_code": code,
        "subzone_name": str(s.subzone_name[j]),
        "planning_area": str(s.planning_area[j]),
        "population": int(s.population[j]),
        "included": bool(s.included[j]),
        "category": category,
        "supply": int(s.supply[supply_key][j]),
        "elderly_share": float(s.elderly_share[j]),
        "monthly_demand_generated": demand_j,
        "monthly_load_served": float(res.L[j]),
        "local_capture_share": local_capture,
        "adequacy": adq,
        "accessibility_A": float(res.A[j]),
        "top_destinations": destinations,
        "top_origins": origins,
    }


@app.get("/api/catalog")
def catalog():
    s = STATE
    subzones = []
    for i in range(s.n):
        if not s.included[i]:
            continue
        subzones.append({
            "code": s.codes[i],
            "name": str(s.subzone_name[i]),
            "planning_area": str(s.planning_area[i]),
            "population": int(s.population[i]),
        })
    subzones.sort(key=lambda r: -r["population"])
    return {
        "subzones": subzones,
        "categories": [
            {"id": "clinic", "label": "CHAS clinic"},
            {"id": "grocery", "label": "NTUC FairPrice"},
        ],
        "calibrated_beta": BETAS,
        "total_subzones": s.n,
        "included_subzones": int(s.included.sum()),
    }


@app.get("/api/subzones.geojson")
def subzones_geojson():
    return JSONResponse(SZ_GEOJSON)


@app.get("/api/stations")
def stations():
    return JSONResponse(STATIONS_DF.to_dict(orient="records"))


@app.get("/api/state")
def get_state():
    """Baseline state snapshot with per-subzone A/L for each category."""
    adq_scores = {cat: GRAV.adequacy_index(cat, BASELINE[cat]).tolist() for cat in ("clinic", "grocery")}
    snap = _state_snapshot(BASELINE)
    # Also add adequacy per-subzone
    for i, row in enumerate(snap["subzones"]):
        for cat in ("clinic", "grocery"):
            row[f"adq_{cat}"] = float(adq_scores[cat][i])
    return snap


# --------------------- scenario ---------------------

class Mutation(BaseModel):
    kind: str                                # "transit_link" | "add_facility" | "remove_facility"
    corridor: list[str] | None = None
    corridor_speed_kmh: float | None = 35.0
    corridor_stop_min: float | None = 1.0
    subzone_code: str | None = None
    category: str | None = None
    count: int | None = 1


class ScenarioRequest(BaseModel):
    mutations: list[Mutation]
    category: Category = "grocery"           # which category we're focused on for outputs
    lam: float = 0.0                         # cannibalisation weight


@app.post("/api/scenario")
def run_scenario(req: ScenarioRequest):
    scen = Scenario(STATE)
    for m in req.mutations:
        if m.kind == "transit_link" and m.corridor:
            scen.add_transit_link(m.corridor, speed_kmh=m.corridor_speed_kmh or 35, stop_min=m.corridor_stop_min or 1)
        elif m.kind == "add_facility" and m.subzone_code and m.category:
            scen.add_facility(m.subzone_code, m.category, count=m.count or 1)
        elif m.kind == "remove_facility" and m.subzone_code and m.category:
            scen.remove_facility(m.subzone_code, m.category, count=m.count or 1)

    sr = scen.apply()
    # Recompute for both categories
    post = {}
    for cat in ("clinic", "grocery"):
        supply_key = GRAV.params[cat].supply_key
        post[cat] = GRAV.compute(cat, T_override=sr.T_composite, supply_override=sr.supply[supply_key])

    # Deltas (A) per subzone
    rows = []
    s = STATE
    cat_focus = req.category
    adq_base = GRAV.adequacy_index(cat_focus, BASELINE[cat_focus])
    adq_post = GRAV.adequacy_index(cat_focus, post[cat_focus])
    for i in range(s.n):
        rows.append({
            "subzone_code": s.codes[i],
            "A_base": float(BASELINE[cat_focus].A[i]),
            "A_post": float(post[cat_focus].A[i]),
            "dA": float(post[cat_focus].A[i] - BASELINE[cat_focus].A[i]),
            "adq_base": float(adq_base[i]),
            "adq_post": float(adq_post[i]),
            "dadq": float(adq_post[i] - adq_base[i]),
            "L_base": float(BASELINE[cat_focus].L[i]),
            "L_post": float(post[cat_focus].L[i]),
        })

    # Opportunity ranking under the mutated state
    supply_key = GRAV.params[cat_focus].supply_key
    opp_res = OPP.rank(
        cat_focus,
        T_override=sr.T_composite,
        supply_override=sr.supply[supply_key],
        lam=req.lam,
        top_k=10,
    )

    # Redundancy
    red_res = OPP.redundancy(cat_focus, BASELINE[cat_focus].L, post[cat_focus].L, top_k=5)

    # Takeaways
    tk = OPP.takeaways(
        cat_focus,
        baseline_A=BASELINE[cat_focus].A,
        scenario_A=post[cat_focus].A,
        opp_result=opp_res,
        redundancy_result=red_res,
    )

    # World-level before/after deltas
    world_before = _world_snapshot(BASELINE)
    world_after = _world_snapshot(post)
    world_delta = {
        "population": 0,  # doesn't change in v0
        "categories": {
            cat: {
                "facilities": world_after["categories"][cat]["facilities"] - world_before["categories"][cat]["facilities"],
                "mean_A_included": world_after["categories"][cat]["mean_A_included"] - world_before["categories"][cat]["mean_A_included"],
                "monthly_load_served": world_after["categories"][cat]["monthly_load_served"] - world_before["categories"][cat]["monthly_load_served"],
            }
            for cat in ("clinic", "grocery")
        },
    }

    return {
        "category": cat_focus,
        "notes": sr.notes,
        "rows": rows,
        "top_opportunities": opp_res.top_opportunities,
        "top_redundant": red_res.top_redundant,
        "takeaways": tk.narrative,
        "world_delta": world_delta,
    }


@app.get("/api/opportunity")
def opportunity(category: Category = "grocery", lam: float = 0.0, top_k: int = 10):
    r = OPP.rank(category, lam=lam, top_k=top_k)
    return {
        "category": category,
        "lam": lam,
        "top_opportunities": r.top_opportunities,
    }


# --------------------- static UI ---------------------

STATIC_DIR.mkdir(parents=True, exist_ok=True)


@app.get("/", response_class=HTMLResponse)
def index():
    return FileResponse(STATIC_DIR / "index.html")


app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="info")
