"""
Plexis Reasoner — the tool layer (the model's action space).

Every function is deterministic Python over the v5 atlas. The LLM learns to
CHOOSE and CHAIN these; the facts always come from here, never the weights.

Grain note: the atlas master is hex8 (1,191 cells x 801 cols). Most questions
are subzone-level, so we build a SUBZONE view by aggregating hex8 -> subzone
(sums for counts, pop-weighted means for rates). Tools accept scale in
{"subzone","pa","region","hex8"}.

Design rules:
- typed, JSON-serialisable returns (the harness feeds these back to the model)
- never raise on bad input -> return {"error": "..."} so the model can recover
- one atlas operation per tool (granularity = the skill is in the chaining)
"""
import functools
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2] / "plexis-sgp-v5"

CATEGORIES = ["beauty_personal", "cafe_coffee", "convenience", "education",
              "fast_food", "fitness_recreation", "hawker", "health_medical",
              "restaurant", "shopping_retail", "supermarket"]

REGIONS = ["CENTRAL REGION", "EAST REGION", "NORTH REGION",
           "NORTH-EAST REGION", "WEST REGION"]

# topics the atlas does NOT cover -> the model must abstain, not invent
UNCOVERED = ["crime", "weather", "income", "salary", "politics", "election",
             "school ranking", "exam", "covid", "stock", "religion race",
             "future price", "prediction next year", "forecast price"]

# human-friendly field aliases -> real columns (the model can use either)
ALIAS = {
    "population": "pop_resident", "residents": "pop_resident",
    "children": "pop_0_14", "elderly": "pop_65plus",
    "daytime_population": "dt_pop", "rent": "rent_resi_psf_med",
    "business_mortality": "biz_recent_dead_share", "walkability": "walkability_score",
    "mrt_distance": "dist_mrt_m", "time_to_cbd": "time_to_cbd_min",
    "15min_score": "min15_score", "catchment": "iso_walk10_pop",
}

# count-like columns are SUMMED to subzone; everything else is pop-weighted mean
SUM_PREFIXES = ("pop", "bldg", "hdb_block", "hdb_dwelling", "biz_live", "biz_total",
                "pc_", "pc2_", "mrt_station", "mrt_exit", "bus_stop", "od_out",
                "iso_walk10_pop", "iso_walk10_spend", "lu_total", "lu_parcel")


# --------------------------------------------------------------------------- #
#  data loading (once, cached)                                                 #
# --------------------------------------------------------------------------- #
@functools.lru_cache(maxsize=1)
def _hex():
    return pd.read_parquet(ROOT / "hex/hex8_all_features.parquet").set_index("hex8_id")


@functools.lru_cache(maxsize=1)
def _agg(scale):
    """hex8 -> subzone/pa/region aggregate view, computed once."""
    if scale == "hex8":
        return _hex().reset_index()
    key = {"subzone": "parent_subzone_name", "pa": "parent_pa",
           "region": "parent_region"}[scale]
    m = _hex()
    num = m.select_dtypes("number")
    sums = num[[c for c in num.columns if c.startswith(SUM_PREFIXES)]]
    rest = num[[c for c in num.columns if not c.startswith(SUM_PREFIXES)]]
    w = m["pop_resident"].clip(lower=1)
    g = m.groupby(key)
    out = g[sums.columns].sum()
    # pop-weighted means for rate-like columns
    wm = (rest.mul(w, axis=0)).groupby(m[key]).sum().div(w.groupby(m[key]).sum(), axis=0)
    out = out.join(wm)
    out["n_hex"] = g.size()
    out = out.reset_index().rename(columns={key: "name"})
    # carry parent labels (mode per group) WITHOUT clashing with the key
    def mode(col):
        return g[col].agg(lambda s: s.mode().iloc[0] if len(s.mode()) else None)
    labels = {}
    for col in ("parent_pa", "parent_region", "zone_type_broad"):
        if col in m.columns and col != key:
            labels[col] = mode(col).reset_index(drop=True)
    for col, ser in labels.items():
        # align by the grouped order (reset_index above preserves group order)
        out[col] = mode(col).values
    return out


@functools.lru_cache(maxsize=1)
def _places():
    return pd.read_parquet(ROOT / "places/sgp_places_final.parquet")


@functools.lru_cache(maxsize=1)
def _emb_hex():
    e = pd.read_parquet(ROOT / "hex/hex8_embedding_plexis_e1_256d.parquet").set_index("hex8_id")
    return e, e.to_numpy(np.float32)


@functools.lru_cache(maxsize=1)
def _emb_place():
    e = pd.read_parquet(ROOT / "places/place_embedding_plexis_p1_64d.parquet").set_index("id")
    Z = e.to_numpy(np.float32)
    pl = _places().set_index("id")
    # align places metadata to embedding row order
    meta = pl.reindex(e.index)[["name", "plexis_category", "brand_norm",
                                 "parent_subzone_name", "parent_pa"]]
    return e, Z, meta


@functools.lru_cache(maxsize=1)
def _brands():
    return pd.read_parquet(ROOT / "places/brand_rollup.parquet")


def _col(field):
    """resolve an alias or pass through a real column name."""
    return ALIAS.get(field, field)


# --------------------------------------------------------------------------- #
#  the tools                                                                   #
# --------------------------------------------------------------------------- #
def list_categories():
    """The 11 place categories the capture/gap/saturation tools understand."""
    return {"categories": CATEGORIES}


def can_answer(topic: str):
    """True if the atlas could answer about this topic; False -> abstain."""
    t = (topic or "").lower()
    blocked = [u for u in UNCOVERED if any(w in t for w in u.split())]
    return {"covered": len(blocked) == 0,
            "reason": None if not blocked else f"atlas has no {blocked[0]} data"}


def _norm_scope(s):
    """Map a loose scope name to a real region/PA (e.g. 'North'->'NORTH REGION')."""
    if not s or s.lower() == "all":
        return s
    sl = s.strip().lower()
    regions = [r.lower() for r in REGIONS]
    # 'north' / 'north region' -> 'NORTH REGION'
    for r in REGIONS:
        if sl == r.lower() or r.lower().startswith(sl) or sl + " region" == r.lower():
            return r
    return s  # leave PA/exact names as-is


def resolve(name: str):
    """Match a place name to an atlas entity. Region words win over subzones
    (so 'North' -> NORTH REGION, not BEDOK NORTH)."""
    n = (name or "").strip().lower()
    # region first (handles bare 'North', 'East', 'North-East' + ' region')
    rs = _norm_scope(n)
    if rs in REGIONS:
        return {"name": rs, "scale": "region"}
    for scale in ("region", "pa", "subzone"):       # exact, broadest first
        df = _agg(scale)
        exact = df[df["name"].astype(str).str.lower() == n]
        if len(exact):
            return {"name": exact.iloc[0]["name"], "scale": scale}
    for scale in ("region", "pa", "subzone"):        # contains fallback
        df = _agg(scale)
        hit = df[df["name"].astype(str).str.lower().str.contains(n, na=False, regex=False)]
        if len(hit):
            return {"name": hit.iloc[0]["name"], "scale": scale, "note": "fuzzy match"}
    return {"error": f"'{name}' not found in the atlas"}


def lookup(entity: str, fields, scale: str = "subzone"):
    """Get atlas values for one entity. fields = list of column names/aliases."""
    df = _agg(scale)
    row = df[df["name"].astype(str).str.lower() == str(entity).strip().lower()]
    if not len(row):
        return {"error": f"{scale} '{entity}' not found"}
    row = row.iloc[0]
    if isinstance(fields, str):
        fields = [fields]
    out = {}
    for f in fields:
        c = _col(f)
        if c not in df.columns:
            out[f] = None
            continue
        v = row[c]
        out[f] = None if pd.isna(v) else (round(float(v), 4) if isinstance(v, (int, float, np.number)) else str(v))
    return {"entity": row["name"], "scale": scale, "values": out}


def filter(scope: str = "all", scale: str = "subzone", where: str = None,
           return_fields=None, limit: int = 50):
    """Filter entities. scope = a region/PA name or 'all'; where = a pandas
    expression like 'pop_resident > 20000 and time_to_cbd_min < 30'."""
    df = _agg(scale).copy()
    if scope and scope.lower() != "all":
        sc = _norm_scope(scope)
        mask = (df.get("parent_region", "").astype(str).str.lower() == sc.lower()) \
            | (df.get("parent_pa", "").astype(str).str.lower() == sc.lower())
        df = df[mask]
        if not len(df):
            return {"error": f"scope '{scope}' matched no {scale}s "
                    f"(regions: {[r.title() for r in REGIONS]})"}
    if where:
        try:
            df = df.query(where.replace(" and ", " & ").replace(" or ", " | "),
                          local_dict={c: df[c] for c in df.columns})
        except Exception:
            try:
                df = df.query(where)
            except Exception as e:
                return {"error": f"bad filter '{where}': {e}"}
    flds, seen = [], set()
    for f in ["name"] + [_col(x) for x in (return_fields or [])]:
        if f in df.columns and f not in seen:
            flds.append(f); seen.add(f)
    rows = df.loc[:, ~df.columns.duplicated()][flds].head(limit)
    return {"scale": scale, "n": len(df),
            "results": json.loads(rows.to_json(orient="records"))}


def rank(metric: str, scope: str = "all", scale: str = "subzone",
         where: str = None, order: str = "desc", k: int = 5):
    """Filter (optional) then rank by a metric. The filter-then-rank skill."""
    df = _agg(scale).copy()
    c = _col(metric)
    if c not in df.columns:
        return {"error": f"unknown metric '{metric}'"}
    if scope and scope.lower() != "all":
        sc = _norm_scope(scope)
        mask = (df.get("parent_region", "").astype(str).str.lower() == sc.lower()) \
            | (df.get("parent_pa", "").astype(str).str.lower() == sc.lower())
        df = df[mask]
    if where:
        try:
            df = df.query(where)
        except Exception as e:
            return {"error": f"bad filter '{where}': {e}"}
    df = df.dropna(subset=[c]).sort_values(c, ascending=(order == "asc")).head(k)
    return {"metric": metric, "scale": scale, "order": order,
            "results": [{"name": r["name"], metric: round(float(r[c]), 4)}
                        for _, r in df.iterrows()]}


def compare(a: str, b: str, dims, scale: str = "subzone"):
    """Side-by-side of two entities on the given dimensions."""
    la, lb = lookup(a, dims, scale), lookup(b, dims, scale)
    if "error" in la:
        return la
    if "error" in lb:
        return lb
    return {"a": la["entity"], "b": lb["entity"],
            "compare": {d: {"a": la["values"][d], "b": lb["values"][d]} for d in
                        ([dims] if isinstance(dims, str) else dims)}}


def capture(category: str, entity: str, scale: str = "subzone"):
    """Huff capture: demand (in outlet-equivalents) a NEW outlet here would win."""
    if category not in CATEGORIES:
        return {"error": f"category must be one of {CATEGORIES}"}
    return lookup(entity, [f"cap_{category}"], scale)


def gap(category: str, entities=None, scale: str = "subzone"):
    """Demand-supply gap for a category (higher = more underserved). One or many."""
    if category not in CATEGORIES:
        return {"error": f"category must be one of {CATEGORIES}"}
    col = f"gap_{category}"
    df = _agg(scale)
    if col not in df.columns:
        ok = sorted(c[4:] for c in df.columns if c.startswith("gap_"))
        return {"error": f"no gap metric for '{category}'. categories with a gap: {ok}"}
    if entities is None:
        return {"error": "give entities=[...] (or use rank on gap_<cat>)"}
    if isinstance(entities, str):
        entities = [entities]
    out = []
    for e in entities:
        row = df[df["name"].astype(str).str.lower() == str(e).strip().lower()]
        if len(row):
            v = row.iloc[0][col]
            out.append({"name": row.iloc[0]["name"],
                        f"gap_{category}": None if pd.isna(v) else round(float(v), 4)})
    return {"category": category, "results": out}


def find_twins(entity: str, k: int = 5, scale: str = "subzone"):
    """Functional twins via the plexis-e1 embedding. Returns most-similar entities."""
    e, Z = _emb_hex()
    m = _hex()
    # map entity -> its hexes -> mean embedding -> nearest distinct subzones
    if scale == "hex8":
        if entity not in e.index:
            return {"error": f"hex '{entity}' not in embedding"}
        q = e.loc[entity].to_numpy(np.float32)
        names = m["parent_subzone_name"]
    else:
        col = {"subzone": "parent_subzone_name", "pa": "parent_pa",
               "region": "parent_region"}[scale]
        hexes = m.index[m[col].astype(str).str.lower() == str(entity).strip().lower()]
        if not len(hexes):
            return {"error": f"{scale} '{entity}' not found"}
        q = e.loc[[h for h in hexes if h in e.index]].to_numpy(np.float32).mean(0)
        names = m[col]
    d = np.linalg.norm(Z - q, axis=1)
    order = np.argsort(d)
    own = str(entity).strip().lower()
    seen, out = {own}, []
    for i in order:
        nm = str(names.get(e.index[i], ""))
        if nm.lower() in seen or not nm:
            continue
        seen.add(nm.lower())
        out.append({"name": nm, "distance": round(float(d[i]), 3)})
        if len(out) == k:
            break
    return {"entity": entity, "scale": scale, "twins": out}


def places_in(entity: str, category: str = None, scale: str = "subzone",
              limit: int = 20):
    """List/count places in an entity, optionally filtered by category."""
    pl = _places()
    col = {"subzone": "parent_subzone_name", "pa": "parent_pa",
           "region": "parent_region"}[scale]
    sub = pl[pl[col].astype(str).str.lower() == str(entity).strip().lower()]
    if category:
        sub = sub[sub["plexis_category"] == category]
    return {"entity": entity, "category": category, "count": int(len(sub)),
            "sample": sub["name"].dropna().head(limit).tolist()}


def od_flow(entity: str, scale: str = "subzone"):
    """Outbound commuting profile (origin-destination) for an entity."""
    return lookup(entity, ["od_out_trips", "od_out_am", "od_out_pm",
                           "od_n_dest_hex", "dt_pop", "pop_resident"], scale)


def isochrone(entity: str, scale: str = "subzone"):
    """10-min walk catchment stats for an entity."""
    return lookup(entity, ["iso_walk10_pop", "iso_walk10_spend",
                           "iso_walk10_places", "iso_transit15_pop"], scale)


# ---- emergent-property wrappers (reachable via lookup too, friendly here) -- #
def colocation(category: str, entity: str, scale: str = "subzone"):
    """How well this place's surrounding MIX fits where category c thrives
    (co-location lift, share-weighted). >1 = a good neighbourhood for it."""
    if category not in CATEGORIES:
        return {"error": f"category must be one of {CATEGORIES}"}
    return lookup(entity, [f"colo_fit_{category}"], scale)


def saturation(category: str, entity: str, scale: str = "subzone"):
    """Existing outlets of a category per 1,000 residents (crowding)."""
    if category not in CATEGORIES:
        return {"error": f"category must be one of {CATEGORIES}"}
    return lookup(entity, [f"sat_{category}_per_1k"], scale)


def micrograph(category: str, entity: str, scale: str = "subzone"):
    """Per-category micro-environment: demand pressure, supply support, and
    anchor strength within 400 m (the per-place world, rolled to the entity)."""
    cat = category if category in CATEGORIES else None
    if cat is None:
        return {"error": f"category must be one of {CATEGORIES}"}
    return lookup(entity, [f"mg_{cat}_pressure_400m", f"mg_{cat}_support_400m",
                           f"mg_{cat}_anchor_strength"], scale)


SYN = ["syn_pop_x_walk", "syn_pop_x_transit", "syn_office_x_transit",
       "syn_retail_x_anchors", "syn_density_x_amenities"]


def synergy(entity: str, scale: str = "subzone"):
    """Interaction signals (population x walkability, office x transit, etc.)."""
    return lookup(entity, SYN, scale)


# ---- place-level tools (plexis-p1 embedding) ------------------------------- #
def place_resolve(name: str):
    """Find a specific venue by name -> its id + basics."""
    pl = _places()
    hit = pl[pl["name"].astype(str).str.lower() == str(name).strip().lower()]
    if not len(hit):
        hit = pl[pl["name"].astype(str).str.lower().str.contains(
            str(name).strip().lower(), na=False)]
    if not len(hit):
        return {"error": f"no place named '{name}'"}
    r = hit.iloc[0]
    return {"id": r["id"], "name": r["name"], "category": r["plexis_category"],
            "brand": r["brand_norm"], "subzone": r["parent_subzone_name"]}


def place_twins(place_id: str = None, name: str = None, k: int = 8):
    """Functional siblings of a venue via the plexis-p1 64-d embedding
    (no rating signals — purely structural: what it is + its 400 m world)."""
    e, Z, meta = _emb_place()
    if place_id is None and name:
        r = place_resolve(name)
        if "error" in r:
            return r
        place_id = r["id"]
    if place_id not in e.index:
        return {"error": f"place '{place_id}' has no embedding"}
    q = e.loc[place_id].to_numpy(np.float32)
    d = np.linalg.norm(Z - q, axis=1)
    order = np.argsort(d)[1:k + 1]
    return {"place_id": place_id, "name": meta.loc[place_id, "name"],
            "twins": [{"name": meta.iloc[i]["name"],
                       "category": meta.iloc[i]["plexis_category"],
                       "subzone": meta.iloc[i]["parent_subzone_name"],
                       "distance": round(float(d[i]), 3)} for i in order]}


def brand_dna(brand: str, k: int = 10):
    """A chain's 'siting DNA' = the centroid of its outlets' fingerprints,
    then the subzones whose hexes best match it (expansion ghost map)."""
    e, Z, meta = _emb_place()
    rows = meta.index[meta["brand_norm"].astype(str).str.lower() == str(brand).strip().lower()]
    if not len(rows):
        return {"error": f"no outlets for brand '{brand}'"}
    c = e.loc[rows].to_numpy(np.float32).mean(0)
    c /= (np.linalg.norm(c) + 1e-9)
    # nearest places to the brand centroid that are NOT this brand -> lookalike sites
    d = Z @ c
    order = np.argsort(-d)
    own = str(brand).strip().lower()
    out, seen = [], set()
    for i in order:
        b = str(meta.iloc[i]["brand_norm"]).lower()
        sz = meta.iloc[i]["parent_subzone_name"]
        if b == own or sz in seen or pd.isna(sz):
            continue
        seen.add(sz)
        out.append({"subzone": sz, "example": meta.iloc[i]["name"],
                    "fit": round(float(d[i]), 3)})
        if len(out) == k:
            break
    return {"brand": brand, "n_outlets": int(len(rows)),
            "expansion_candidates": out}


def brand_info(brand: str):
    """Where a chain operates: outlet count, category, region spread."""
    b = _brands()
    hit = b[b["brand_norm"].astype(str).str.lower() == str(brand).strip().lower()]
    if not len(hit):
        return {"error": f"brand '{brand}' not found"}
    r = hit.iloc[0]
    return {"brand": r["brand_norm"], "n_locations": int(r["n_locations"]),
            "category": r["primary_category"], "top_pa": r.get("top_pa")}


# registry the harness exposes to the model (name -> callable)
TOOLS = {
    "list_categories": list_categories, "can_answer": can_answer,
    "resolve": resolve, "lookup": lookup, "filter": filter, "rank": rank,
    "compare": compare, "capture": capture, "gap": gap,
    "colocation": colocation, "saturation": saturation,
    "micrograph": micrograph, "synergy": synergy,
    "find_twins": find_twins, "isochrone": isochrone, "od_flow": od_flow,
    "places_in": places_in,
    "place_resolve": place_resolve, "place_twins": place_twins,
    "brand_dna": brand_dna, "brand_info": brand_info,
}


def call(tool, **kwargs):
    """Dispatch a tool call by name (what the harness invokes).
    NEVER raises — any failure becomes an error dict the model can recover from.
    That robustness is what keeps an unattended generation run alive."""
    if tool not in TOOLS:
        return {"error": f"no tool '{tool}'. available: {list(TOOLS)}"}
    try:
        return TOOLS[tool](**kwargs)
    except TypeError as e:
        return {"error": f"bad args for {tool}: {e}"}
    except Exception as e:  # missing column, bad value, anything
        return {"error": f"{tool} failed: {type(e).__name__}: {str(e)[:160]}"}
