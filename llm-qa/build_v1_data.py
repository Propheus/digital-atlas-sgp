#!/usr/bin/env python3
"""
Build the V1 continued-SFT corpus from the cross-layer + metric reasoning generators.

REASON-IN-CONTEXT: each example's prompt carries a Context block of the area's metrics
(same shape the server injects), so the answer's numbers TRACE to the context — we teach
the cross-layer CHAINS, not memorised facts. Plus a REPLAY sample of the original corpus
so continued training doesn't forget v0's behaviour/voice.

    ATLAS=/root/atlas python3 build_v1_data.py --gens cross_layer.jsonl metric_reasoning.jsonl \
        --replay /root/train.jsonl --out_train train_v1.jsonl --out_eval eval_v1.jsonl
"""
import os, json, argparse, random
import atlas_tools as A
A.ATLAS = os.environ.get("ATLAS", A.ATLAS)

SYS = ("You are Alchemy, a sharp local urban analyst for Singapore, grounded in the Plexis atlas. "
       "Reason across the data layers (people, housing, movement, places, demand-supply, activity) using the "
       "Context provided. Lead with a clear read, weave the figures in as evidence and say what they imply, and "
       "reason about gaps/demand correctly: anchor strength = demand the area generates (footfall, positive); "
       "gap = unmet provision (opportunity); saturation/competitors = crowding. Cite only figures from the "
       "Context; treat forward-looking siting calls as estimates, not facts; if the atlas doesn't track "
       "something, say so.")

def _num(v, nd=0):
    try:
        v = float(v)
        if v != v: return None
        return int(round(v)) if nd == 0 else round(v, nd)
    except Exception:
        return None

def _top_by(sz, r, prefix, suffix, n=3, thresh=None):
    items = []
    for c in sz.columns:
        if c.startswith(prefix) and c.endswith(suffix):
            cat = c[len(prefix):len(c) - len(suffix)] if suffix else c[len(prefix):]
            v = r[c]
            if v == v and (thresh is None or float(v) >= thresh):
                items.append((cat.replace("_", " "), float(v)))
    items.sort(key=lambda x: -x[1]); return items[:n]

def ctx_for(sz, name):
    """Rich context for one subzone — superset containing every metric the answers cite."""
    if name not in sz.index: return None
    r = sz.loc[name]; g = lambda c: r[c] if c in sz.columns else None
    bits = [f"{name} ({g('pa')}, {g('region')})"]
    def add(label, col, nd=0, suf=""):
        v = _num(g(col), nd)
        if v is not None: bits.append(f"{label} {v}{suf}")
    add("population", "pop_resident")
    dens = _num(g("pop_density"))
    if dens is not None and dens < 150000: bits.append(f"density {dens}/km²")
    for lab, col in [("children","child_share"),("elderly","elder_share"),("HDB-housed","pop_hdb_share")]:
        v = g(col)
        if v is not None and v == v: bits.append(f"{lab} {int(round(float(v)*100))}%")
    add("walkability (0-1)", "walkability_score", 2); add("transit score (0-1)", "max_transit_score", 2)
    add("MRT stations", "mrt_station_count"); add("metres to MRT", "dist_mrt_m"); add("bus stops", "bus_stop_count")
    add("daily bus taps", "daily_bus_taps"); add("amenities within 400m", "walk_amenities_400m")
    add("schools", "school_count_total"); add("primary schools within 1km", "primary_schools_within_1km")
    add("preschools", "preschool_count"); add("hawker eateries", "pc_cat_hawker"); add("hawker centres", "hawker_centre_count")
    add("vibrancy (0-1)", "vibrancy_index", 2); add("commercial intensity (0-1)", "commercial_intensity", 2)
    add("livability index (0-1)", "livability_index", 2); add("family index (0-1)", "family_index", 2)
    add("land-use diversity (0-1)", "lu_entropy", 2); add("local jobs", "wp_pop"); add("total places", "pc_total")
    rps = _num(g("hdb_resale_median_psm"))
    if rps: bits.append(f"HDB resale ~${rps:,}/m²")
    ctx = "; ".join(str(b) for b in bits) + "."
    try:
        o = A.od(name, "top_dest", 3).get("top_destinations") or []
        if o: ctx += " Top weekday destinations: " + ", ".join(f"{x['dest']} ({x['trips']:,})" for x in o) + "."
        sc = A.od(name, "self_containment").get("self_containment_pct")
        if sc is not None: ctx += f" Self-containment {sc}%."
    except Exception: pass
    # location-intelligence
    li = []
    anc = _top_by(sz, r, "mg_", "_anchor_strength", 3)
    if anc: li.append("demand generators (anchor strength): " + ", ".join(f"{c} ({int(v)})" for c, v in anc))
    gap = _top_by(sz, r, "gap_", "", 3, thresh=0.25)
    if gap: li.append("biggest provision gaps (+1=under-served): " + ", ".join(f"{c} ({v:.2f})" for c, v in gap))
    sat = _top_by(sz, r, "sat_", "_per_1k", 2)
    if sat: li.append("most provided per 1k: " + ", ".join(f"{c} ({v:.1f})" for c, v in sat))
    avga = _num(g("mg_avg_anchor_strength")); comp = _num(g("mg_avg_competitors_400m"))
    if avga is not None: li.append(f"avg anchor strength {avga}")
    if comp is not None: li.append(f"avg competitors/400m {comp}")
    if li: ctx += " Location-intelligence — " + "; ".join(li) + "."
    return ctx

def to_chat(sz, rec):
    """Generator record -> reason-in-context chat example. Returns None if context unavailable."""
    ent = rec.get("entity", "")
    if rec["kind"] == "tool_call":
        return {"messages": [{"role": "system", "content": SYS},
                             {"role": "user", "content": rec["question"]},
                             {"role": "assistant", "content": rec["reasoning"]}],
                "meta": {"kind": rec["kind"], "category": rec["category"]}}
    ents = [e.strip() for e in ent.split("&")] if ent else []
    ctxs = [c for c in (ctx_for(sz, e) for e in ents) if c]
    if not ctxs: return None
    context = "\n".join("Context: " + c for c in ctxs)
    user = f"{context}\n\nQuestion: {rec['question']}"
    assistant = (rec.get("reasoning", "").strip() + " " + rec.get("answer", "").strip()).strip()
    return {"messages": [{"role": "system", "content": SYS},
                         {"role": "user", "content": user},
                         {"role": "assistant", "content": assistant}],
            "meta": {"kind": rec["kind"], "category": rec["category"], "entity": ent}}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gens", nargs="+", required=True)
    ap.add_argument("--replay", default="")
    ap.add_argument("--replay_n", type=int, default=5000)
    ap.add_argument("--upsample", type=int, default=2)
    ap.add_argument("--out_train", default="train_v1.jsonl")
    ap.add_argument("--out_eval", default="eval_v1.jsonl")
    args = ap.parse_args()
    rnd = random.Random(42)

    sz, _ = A._load()
    new = []
    for path in args.gens:
        for l in open(path):
            try: r = json.loads(l)
            except: continue
            ex = to_chat(sz, r)
            if ex: new.append(ex)
    print(f"new reasoning examples: {len(new)}")

    # entity-holdout eval: hold a few well-known areas out of NEW data
    HOLD = {"Bedok North", "Tampines East", "Clementi Central", "Bishan East", "Jurong East"}
    train_new = [e for e in new if e["meta"].get("entity", "").split(" &")[0] not in HOLD]
    eval_new  = [e for e in new if e["meta"].get("entity", "").split(" &")[0] in HOLD]
    train_new = train_new * args.upsample
    rnd.shuffle(train_new)

    replay = []
    if args.replay and os.path.exists(args.replay):
        allr = [json.loads(l) for l in open(args.replay)]
        replay = rnd.sample(allr, min(args.replay_n, len(allr)))
        print(f"replay sample: {len(replay)}")

    train = train_new + replay
    rnd.shuffle(train)
    with open(args.out_train, "w") as f:
        for e in train: f.write(json.dumps(e) + "\n")
    with open(args.out_eval, "w") as f:
        for e in eval_new[:400]: f.write(json.dumps(e) + "\n")
    print(f"TRAIN {len(train)} (new x{args.upsample}={len(train_new)} + replay {len(replay)}) -> {args.out_train}")
    print(f"EVAL  {len(eval_new[:400])} held-out -> {args.out_eval}")

if __name__ == "__main__":
    main()
