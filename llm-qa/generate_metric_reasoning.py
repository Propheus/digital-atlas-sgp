#!/usr/bin/env python3
"""
Alchemy — deterministic metric-reasoning generator.

Builds VERIFIABLE Q&A over the proprietary location-intelligence metrics that vanilla
Gemma has no model for (anchor strength · demand support · provision gap · saturation ·
demand pull). Every answer is computed from the parquet; the reasoning chain is the
canonical one from docs/ALCHEMY_METRIC_ONTOLOGY.md. Deterministic families end in a
checkable fact; the one forward-looking family (opportunity) is emitted as a CAVEATED
estimate, never as fact.

Run on a box with the atlas:
    ATLAS=/root/atlas python3 generate_metric_reasoning.py --out metric_reasoning.jsonl
Each line: {category, kind, scale, entity, question, reasoning, answer, fact, provenance, verdict?}
"""
import os, json, argparse, itertools
import atlas_tools as A
A.ATLAS = os.environ.get("ATLAS", A.ATLAS)

MIN_POP = 2000
ANCHOR_SUF = "_anchor_strength"
SAT_SUF = "_per_1k"

def load():
    sz, g = A._load()
    sz = sz[(sz.pop_resident >= MIN_POP) & (sz.walkability_score > 0.05) &
            (sz.pop_density < 150000) & (sz.max_transit_score > 0)].copy()
    anchor_cols = [c for c in sz.columns if c.startswith("mg_") and c.endswith(ANCHOR_SUF)]
    gap_cols    = [c for c in sz.columns if c.startswith("gap_")]
    sat_cols    = [c for c in sz.columns if c.startswith("sat_") and c.endswith(SAT_SUF)]
    return sz, anchor_cols, gap_cols, sat_cols

def _cat(col, prefix, suffix=""):
    c = col[len(prefix):]
    if suffix and c.endswith(suffix): c = c[:-len(suffix)]
    return c.replace("_", " ")

def rec(kind, entity, q, reasoning, answer, fact, prov, verdict=False):
    return {"category": "metric_reasoning", "kind": kind, "scale": "subzone", "entity": entity,
            "question": q, "reasoning": reasoning, "answer": answer, "fact": fact,
            "provenance": prov, "verdict": verdict}

def gen(sz, anchor_cols, gap_cols, sat_cols, seed_pairs=600):
    out = []
    names = list(sz.index)

    for name in names:
        r = sz.loc[name]
        reg = r["region"]

        # 1) which-draw (argmax anchor) — deterministic
        if anchor_cols:
            vals = [(c, float(r[c])) for c in anchor_cols if r[c] == r[c]]
            if vals:
                vals.sort(key=lambda x: -x[1])
                top = _cat(vals[0][0], "mg_", ANCHOR_SUF)
                top3 = ", ".join(f"{_cat(c,'mg_',ANCHOR_SUF)} ({int(v)})" for c, v in vals[:3])
                out.append(rec("draw_argmax", name,
                    f"What is {name} most of a regional draw for?",
                    f"Anchor strength = how strongly a category already pulls people to the area. "
                    f"Top anchors here: {top3}. The maximum is {top}.",
                    f"{name} is most a regional draw for {top}.",
                    f"anchors[{name}] top3: {top3}",
                    {"metric": "anchor_strength", "argmax": vals[0][0], "value": round(vals[0][1], 2)}))

        # 2) biggest gap (argmax gap) — deterministic, atlas verdict
        if gap_cols:
            gv = [(c, float(r[c])) for c in gap_cols if r[c] == r[c]]
            if gv:
                gv.sort(key=lambda x: -x[1])
                under = [(_cat(c, "gap_"), v) for c, v in gv if v > 0.25][:3]
                if under:
                    lst = ", ".join(f"{c} ({v:.2f})" for c, v in under)
                    out.append(rec("gap_argmax", name,
                        f"What is {name} most under-served for?",
                        f"gap_C runs -1 (over-served) to +1 (under-served). The highest gaps here are: {lst}. "
                        f"The biggest is {under[0][0]}.",
                        f"{name} is most under-served for {under[0][0]} (gap {under[0][1]:.2f}).",
                        f"gaps[{name}]: {lst}",
                        {"metric": "gap", "argmax": under[0][0], "value": round(under[0][1], 3)}))

        # 3) under-served yes/no for a specific category — deterministic
        for c in gap_cols[:4]:
            if r[c] != r[c]: continue
            cat = _cat(c, "gap_"); v = float(r[c])
            verdict = "under-served" if v > 0.15 else ("over-served" if v < -0.15 else "adequately served")
            out.append(rec("gap_yesno", name,
                f"Is {name} under-served for {cat}?",
                f"gap_{cat} = {v:.2f} (positive = under-served, negative = over-served). "
                f"{v:.2f} ⇒ {verdict}.",
                f"{name} is {verdict} for {cat} (gap {v:.2f}).",
                f"gap_{cat}={v:.3f}",
                {"metric": f"gap_{cat}", "value": round(v, 3)}))

        # 4) saturation — deterministic
        if sat_cols:
            svals = [(c, float(r[c])) for c in sat_cols if r[c] == r[c]]
            if svals:
                svals.sort(key=lambda x: -x[1])
                cat = _cat(svals[0][0], "sat_", SAT_SUF)
                out.append(rec("saturation_top", name,
                    f"Which everyday category is {name} most saturated with, per resident?",
                    f"sat_C = provision per 1,000 residents. Highest: {cat} at {svals[0][1]:.1f} per 1k — "
                    f"the most provided, i.e. least room for a new entrant.",
                    f"{name} is most saturated with {cat} ({svals[0][1]:.1f} per 1,000 residents).",
                    f"sat top: {cat}={svals[0][1]:.2f}",
                    {"metric": "sat_per_1k", "argmax": cat, "value": round(svals[0][1], 2)}))

        # 5) opportunity — CAVEATED estimate (judgment, grounded in gap)
        if gap_cols:
            gv = [( _cat(c,"gap_"), float(r[c])) for c in gap_cols if r[c] == r[c]]
            gv = [x for x in gv if x[1] > 0.3]; gv.sort(key=lambda x:-x[1])
            if gv:
                best = gv[0]
                out.append(rec("opportunity_estimate", name,
                    f"If someone wanted to open a new F&B business in {name}, what category looks most promising?",
                    f"Reading the provision gaps (higher = more unmet demand): {', '.join(f'{c} ({v:.2f})' for c,v in gv[:3])}. "
                    f"The largest gap is {best[0]}, so demand there is least met. This points to {best[0]} as the "
                    f"strongest opportunity — but it is a directional estimate from provision signals, not a guarantee; "
                    f"footfall, rent and competition still decide it.",
                    f"{best[0]} looks most promising (largest provision gap, {best[1]:.2f}) — a directional estimate, not a forecast.",
                    f"gap argmax {best[0]}={best[1]:.3f}",
                    {"metric": "gap", "argmax": best[0], "value": round(best[1], 3)}, verdict=True))

    # 6) cross-entity: which subzone in region R has the biggest gap for C — deterministic rank
    seen = set()
    regions = sorted(sz["region"].dropna().unique())
    for c in gap_cols:
        cat = _cat(c, "gap_")
        for reg in regions:
            sub = sz[sz.region == reg].dropna(subset=[c])
            if len(sub) < 3: continue
            top = sub.sort_values(c, ascending=False).iloc[0]
            key = (c, reg)
            if key in seen: continue
            seen.add(key)
            out.append(rec("gap_rank_region", top["name"],
                f"Which subzone in the {reg} is most under-served for {cat}?",
                f"Ranking gap_{cat} across {reg} subzones (higher = more under-served), the top is "
                f"{top['name']} at {float(top[c]):.2f}.",
                f"{top['name']} is the most under-served for {cat} in the {reg} (gap {float(top[c]):.2f}).",
                f"rank gap_{cat} in {reg} -> {top['name']}",
                {"metric": f"gap_{cat}", "scope": reg, "argmax": top["name"], "value": round(float(top[c]), 3)}))

    # 7) compare two areas on a gap — deterministic (stride sampling, no RNG)
    pairs = []
    step = max(1, len(names) // 40)
    for i in range(0, len(names) - 1, step):
        pairs.append((names[i], names[i + 1]))
    for (a, b) in pairs[:seed_pairs]:
        for c in gap_cols[:3]:
            va, vb = sz.loc[a, c], sz.loc[b, c]
            if va != va or vb != vb: continue
            cat = _cat(c, "gap_"); va, vb = float(va), float(vb)
            more = a if va > vb else b
            out.append(rec("gap_compare", f"{a} & {b}",
                f"Between {a} and {b}, which is more under-served for {cat}?",
                f"gap_{cat}: {a} = {va:.2f}, {b} = {vb:.2f}. Higher = more under-served, so {more} is.",
                f"{more} is more under-served for {cat} ({a} {va:.2f} vs {b} {vb:.2f}).",
                f"gap_{cat}: {a}={va:.3f} {b}={vb:.3f}",
                {"metric": f"gap_{cat}", "a": a, "b": b, "winner": more}))
    return out

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="metric_reasoning.jsonl")
    args = ap.parse_args()
    sz, anchor_cols, gap_cols, sat_cols = load()
    print(f"subzones={len(sz)} anchors={len(anchor_cols)} gaps={len(gap_cols)} sats={len(sat_cols)}")
    rows = gen(sz, anchor_cols, gap_cols, sat_cols)
    import collections
    kc = collections.Counter(r["kind"] for r in rows)
    with open(args.out, "w") as f:
        for r in rows: f.write(json.dumps(r) + "\n")
    print(f"wrote {len(rows)} rows -> {args.out}")
    print("by kind:", dict(kc))
    print("verdicts (caveated):", sum(1 for r in rows if r.get('verdict')))
