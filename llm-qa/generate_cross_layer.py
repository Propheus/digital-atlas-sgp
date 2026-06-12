#!/usr/bin/env python3
"""
Alchemy V1 — cross-layer reasoning generator.

Builds the reasoning that spans the six urban layers (see docs/ALCHEMY_URBAN_REASONING_MODEL.md).
The keystone family is INDEX-DECOMPOSITION: reproduce the atlas's own outcome index
(livability / family / vibrancy / walkability) — a VERIFIABLE gold — AND narrate the real
drivers (data-grounded by global correlation + this area's percentile on each driver).

Families:
  index_value_why   reproduce index + decompose drivers            (verifiable)
  index_rank        most/least <index> in region/PA                (verifiable)
  demo_gap          demographic need x provision gap               (verifiable)
  behavioural_role  bedroom / employment / balanced (OD + jobs)    (verifiable)
  opportunity       demand-generation x gap x saturation           (CAVEATED estimate)
  tool_call         emit an atlas tool call, use the result        (teaches tool use)

Run:  ATLAS=/root/atlas python3 generate_cross_layer.py --out cross_layer.jsonl
"""
import os, json, argparse
import atlas_tools as A
A.ATLAS = os.environ.get("ATLAS", A.ATLAS)
MIN_POP = 2000

INDICES = ["livability_index", "family_index", "vibrancy_index", "walkability_score"]
LABEL = {"livability_index": "livability", "family_index": "family-friendliness",
         "vibrancy_index": "vibrancy", "walkability_score": "walkability"}
DRIVERS = ["walkability_score","max_transit_score","dist_mrt_m","bus_stop_count","mrt_station_count",
 "daily_bus_taps","pop_density","density_pressure","pop_hdb_share","child_share","elder_share",
 "school_count_total","primary_schools_within_1km","preschool_count","pc_total","walk_amenities_400m",
 "vibrancy_index","commercial_intensity","lu_entropy","nl_commercial_indicator","hdb_resale_median_psm",
 "wp_pop","mg_avg_competitors_400m","pull_composite"]
DNAME = {"walkability_score":"walkability","max_transit_score":"transit access","dist_mrt_m":"distance to MRT",
 "bus_stop_count":"bus coverage","mrt_station_count":"MRT presence","daily_bus_taps":"bus ridership",
 "pop_density":"population density","density_pressure":"density pressure","pop_hdb_share":"HDB share",
 "child_share":"share of children","elder_share":"elderly share","school_count_total":"schools",
 "primary_schools_within_1km":"primary schools within 1km","preschool_count":"preschools",
 "pc_total":"amenity count","walk_amenities_400m":"walkable amenities","vibrancy_index":"vibrancy",
 "commercial_intensity":"commercial intensity","lu_entropy":"land-use mix","nl_commercial_indicator":"night-light activity",
 "hdb_resale_median_psm":"housing prices","wp_pop":"local jobs","mg_avg_competitors_400m":"retail competition",
 "pull_composite":"central accessibility"}

def rec(kind, entity, q, reasoning, answer, fact, prov, verdict=False):
    return {"category":"cross_layer","kind":kind,"scale":"subzone","entity":entity,"question":q,
            "reasoning":reasoning,"answer":answer,"fact":fact,"provenance":prov,"verdict":verdict}

def main():
    import numpy as np
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default="cross_layer.jsonl"); args = ap.parse_args()
    sz, g = A._load()
    # keep only complete-data subzones (drop missing-area/missing-metric rows: absurd density, 0 walkability)
    sz = sz[(sz.pop_resident >= MIN_POP) & (sz.walkability_score > 0.05) &
            (sz.pop_density < 150000) & (sz.max_transit_score > 0)].copy()
    drivers = [d for d in DRIVERS if d in sz.columns]
    idxs = [i for i in INDICES if i in sz.columns]

    # global driver correlations per index (sign tells us lift vs drag) + percentile ranks per driver
    def corr(a, b):
        x = sz[a].astype(float); y = sz[b].astype(float); m = x.notna() & y.notna()
        return float(np.corrcoef(x[m], y[m])[0, 1]) if m.sum() > 20 else 0.0
    idx_drivers = {i: sorted(((d, corr(i, d)) for d in drivers if d != i), key=lambda x: -abs(x[1]))[:7] for i in idxs}
    pct = {d: sz[d].rank(pct=True) for d in drivers}

    out = []
    names = list(sz.index)
    gap_cols = [c for c in sz.columns if c.startswith("gap_")]
    anchor_cols = [c for c in sz.columns if c.startswith("mg_") and c.endswith("_anchor_strength")]

    for name in names:
        r = sz.loc[name]; reg = r["region"]

        # ---- index_value_why : reproduce the index + decompose drivers (VERIFIABLE) ----
        for idx in idxs:
            v = r[idx]
            if v != v: continue
            v = float(v)
            lifts, drags = [], []
            for d, c in idx_drivers[idx]:
                if d not in pct or name not in pct[d].index: continue
                p = float(pct[d].loc[name])
                # positive corr: high percentile lifts, low drags; negative corr: high drags, low lifts
                if c > 0.15:
                    (lifts if p >= 0.6 else (drags if p <= 0.4 else []) ).append(DNAME.get(d, d))
                elif c < -0.15:
                    (drags if p >= 0.6 else (lifts if p <= 0.4 else []) ).append(DNAME.get(d, d))
            lifts, drags = lifts[:3], drags[:2]
            band = "high" if v >= 0.66 else ("moderate" if v >= 0.4 else "low")
            chain = (f"{LABEL[idx]} index here is {v:.2f} ({band}). Across Singapore it tracks most with "
                     f"{', '.join(DNAME.get(d,d) for d,_ in idx_drivers[idx][:3])}. ")
            if lifts: chain += f"This area scores well on {', '.join(lifts)}, lifting it. "
            if drags: chain += f"It is held back by {', '.join(drags)}. "
            ans = f"{name}'s {LABEL[idx]} is {v:.2f} ({band})"
            if lifts: ans += f", driven by its {', '.join(lifts)}"
            if drags: ans += f", though {', '.join(drags)} hold{'s' if len(drags)==1 else ''} it back"
            ans += "."
            out.append(rec("index_value_why", name,
                f"What is {name}'s {LABEL[idx]} like, and what drives it?",
                chain, ans, f"{idx}={v:.3f}",
                {"metric": idx, "value": round(v, 3), "lifts": lifts, "drags": drags}))

        # ---- behavioural_role : OD self-containment + jobs (VERIFIABLE) ----
        try:
            sc = A.od(name, "self_containment").get("self_containment_pct")
        except Exception:
            sc = None
        wp = r["wp_pop"] if "wp_pop" in sz.columns else None
        if sc is not None:
            role = ("a self-contained, balanced town" if sc >= 35 else
                    "a mostly residential 'bedroom' area — people commute out" if sc < 20 else
                    "a partly self-contained area")
            wtxt = f" It holds about {int(wp):,} local jobs." if (wp == wp and wp is not None) else ""
            out.append(rec("behavioural_role", name,
                f"Is {name} a place people both live and work, or do they commute out?",
                f"Self-containment {sc}% (share of weekday trips staying within the area). "
                f"{sc}% ⇒ {role}.{wtxt}",
                f"{name} is {role} (self-containment {sc}%).",
                f"self_containment={sc}",
                {"metric": "self_containment", "value": sc}))

        # ---- demo_gap : demographic need x provision gap (VERIFIABLE) ----
        es = float(r["elder_share"]) if "elder_share" in sz.columns and r["elder_share"]==r["elder_share"] else None
        if es is not None and es > 0.18 and "gap_health_medical" in sz.columns and r["gap_health_medical"]==r["gap_health_medical"]:
            ghm = float(r["gap_health_medical"])
            verdict = "an under-served gap for an older population" if ghm > 0.15 else "adequately covered for healthcare"
            out.append(rec("demo_gap", name,
                f"With its older residents, is {name} well-covered for healthcare?",
                f"Elderly share is {es*100:.0f}% (above the ~18% typical), so healthcare need is elevated. "
                f"gap_health_medical = {ghm:.2f} ({'positive=under-served' if ghm>0 else 'negative=over-served'}). "
                f"High need + that gap ⇒ {verdict}.",
                f"{name}: {es*100:.0f}% elderly with healthcare gap {ghm:.2f} — {verdict}.",
                f"elder_share={es:.3f}; gap_health_medical={ghm:.3f}",
                {"elder_share": round(es,3), "gap_health_medical": round(ghm,3)}))

        # ---- opportunity : demand-generation (anchor) x gap x saturation (CAVEATED) ----
        if gap_cols and anchor_cols:
            gv = [(c[4:].replace("_"," "), float(r[c])) for c in gap_cols if r[c]==r[c]]
            gv = [x for x in gv if x[1] > 0.3]; gv.sort(key=lambda x:-x[1])
            avg_anchor = float(r["mg_avg_anchor_strength"]) if "mg_avg_anchor_strength" in sz.columns and r["mg_avg_anchor_strength"]==r["mg_avg_anchor_strength"] else None
            if gv:
                best = gv[0]
                dem = (f"The area is a strong demand generator (avg anchor strength {int(avg_anchor)}, i.e. it already "
                       f"pulls in footfall). " if avg_anchor else "")
                out.append(rec("opportunity", name,
                    f"Where's the F&B opportunity in {name}?",
                    f"{dem}On the provision side the biggest unmet gaps are "
                    f"{', '.join(f'{c} ({v:.2f})' for c,v in gv[:3])}. Combining footfall (demand generation) with the "
                    f"largest gap points to {best[0]}: ride the existing demand into the under-served category. "
                    f"This is a directional estimate from the signals, not a guarantee — rent, exact site and "
                    f"competition still decide it.",
                    f"{best[0]} looks most promising — strong area footfall meeting the largest provision gap "
                    f"({best[1]:.2f}). A directional estimate, not a forecast.",
                    f"avg_anchor={avg_anchor}; gap argmax {best[0]}={best[1]:.3f}",
                    {"argmax": best[0], "gap": round(best[1],3), "avg_anchor": avg_anchor}, verdict=True))

    # ---- index_rank : most <index> in region (VERIFIABLE) ----
    for idx in idxs:
        for reg in sorted(sz["region"].dropna().unique()):
            sub = sz[sz.region == reg].dropna(subset=[idx])
            if len(sub) < 3: continue
            top = sub.sort_values(idx, ascending=False).iloc[0]
            out.append(rec("index_rank", top["name"],
                f"Which subzone in the {reg} scores highest on {LABEL[idx]}?",
                f"Ranking {LABEL[idx]} across {reg} subzones, the top is {top['name']} at {float(top[idx]):.2f}.",
                f"{top['name']} has the highest {LABEL[idx]} in the {reg} ({float(top[idx]):.2f}).",
                f"rank {idx} in {reg} -> {top['name']}",
                {"metric": idx, "scope": reg, "argmax": top["name"], "value": round(float(top[idx]),3)}))

    # ---- tool_call traces : teach the model to CALL the atlas (a handful of templates) ----
    tool_examples = [
        ("Which East-region subzone is most under-served for cafes?",
         'rank(metric="gap_cafe_coffee", scope="East Region", direction="desc", n=1)',
         "The tool returns the ranked area; I report it as the answer."),
        ("How family-friendly is Bishan compared to Toa Payoh?",
         'compare(entities=["Bishan","Toa Payoh"], metric="family_index")',
         "The tool returns both index values; I state which is higher and by how much."),
        ("What is Tampines East a strong demand draw for?",
         'anchor_top(entity="Tampines East")',
         "The tool returns the top anchor categories; I name the strongest."),
    ]
    for q, call, note in tool_examples:
        out.append(rec("tool_call", "",
            q,
            f"This needs an exact atlas figure, so I call a tool.\nTOOL: {call}\n{note}",
            f"[calls {call.split('(')[0]} → answers from the returned value]",
            "tool-use exemplar", {"tool": call}))

    import collections
    kc = collections.Counter(r["kind"] for r in out)
    with open(args.out, "w") as f:
        for r in out: f.write(json.dumps(r) + "\n")
    print(f"subzones={len(names)} indices={idxs}")
    print(f"wrote {len(out)} rows -> {args.out}")
    print("by kind:", dict(kc)); print("verdicts (caveated):", sum(1 for r in out if r.get('verdict')))

if __name__ == "__main__":
    main()
