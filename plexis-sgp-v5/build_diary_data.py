"""
Atlas Diary app — precompute per-use-case payloads (docs/USE_CASE_DIARY.md).
Reuses SG Pulse data (hexes/twins/cards) + plexis-p1 for place-level entries.
Emits to apps/atlas-diary/public/data/.
"""
import json
import shutil
from pathlib import Path

import h3
import numpy as np
import pandas as pd

ROOT = Path(__file__).parent
PULSE = ROOT.parent / "apps/sg-pulse/public/data"
APP = ROOT.parent / "apps/atlas-diary/public/data"
APP.mkdir(parents=True, exist_ok=True)


def main():
    # ---- base layers straight from SG Pulse (same validated build) ----
    for f in ["hexes.geojson", "twins.json", "report_cards.json"]:
        shutil.copy(PULSE / f, APP / f)
    hexes = json.load(open(APP / "hexes.geojson"))
    twins = json.load(open(APP / "twins.json"))
    cards = json.load(open(APP / "report_cards.json"))
    hprop = {f["properties"]["id"]: f["properties"] for f in hexes["features"]}

    pl = pd.read_parquet(ROOT / "places/sgp_places_final.parquet",
                         columns=["id", "name", "plexis_category", "brand_norm",
                                  "latitude", "longitude", "hex8_id",
                                  "parent_subzone_name"])
    E = pd.read_parquet(ROOT / "places/place_embedding_plexis_p1_64d.parquet")
    Z = E.drop(columns=["id"]).to_numpy(np.float32)
    pl = E[["id"]].merge(pl, on="id", how="left")   # row-aligned with Z

    diary = {}

    # ---- e1 pilot/rollout: Toa Payoh anchor (twins drawn client-side) ----
    toa = next(h for h, p in hprop.items()
               if p["parent_subzone_name"] == "TOA PAYOH CENTRAL")
    diary["e1"] = {"anchor": toa}

    # ---- e2 rent benchmark: best demo hexes (big twin rent spread) ----
    demos = []
    for h, tws in twins.items():
        r0 = hprop.get(h, {}).get("rent_resi_psf_med")
        rs = [hprop.get(t["id"], {}).get("rent_resi_psf_med") for t in tws]
        rs = [r for r in rs if r]
        if r0 and len(rs) >= 4:
            ratio = r0 / np.mean(rs)
            demos.append((abs(np.log(ratio)), h, round(ratio, 2)))
    demos.sort(reverse=True)
    diary["e2"] = {"default": demos[0][1],
                   "examples": [{"hex": h, "ratio": r} for _, h, r in demos[:6]]}

    # ---- e3 grocery gap: numeric — self far BELOW its twins on open
    # supermarket capture (twins are alike, so a big shortfall is a signal;
    # band-level never disagrees — the embedding is too good for that filter)
    gaps = []
    for h, tws in twins.items():
        c0 = hprop.get(h, {}).get("cap_supermarket")
        cs = [hprop.get(t["id"], {}).get("cap_supermarket") for t in tws]
        cs = [c for c in cs if c is not None]
        if c0 is None or len(cs) < 4:
            continue
        tw_mean = float(np.mean(cs))
        if tw_mean >= 0.6 and c0 <= 0.55 * tw_mean:
            gaps.append({"hex": h, "name": hprop[h]["parent_subzone_name"],
                         "self": round(c0, 2), "twin_mean": round(tw_mean, 2),
                         "twins": [{"name": t["name"],
                                    "cap": hprop.get(t["id"], {}).get("cap_supermarket")}
                                   for t in tws]})
    gaps.sort(key=lambda g: g["self"] / max(g["twin_mean"], 1e-6))
    diary["e3"] = {"gaps": gaps[:8]}

    # ---- e4 Tengah trajectory: where do its hexes' twins live ----
    teng = [h for h, p in hprop.items() if p.get("parent_pa") == "TENGAH"
            and h in twins]
    counts = {}
    for h in teng:
        for t in twins[h]:
            pa = hprop.get(t["id"], {}).get("parent_pa") or "?"
            counts[pa] = counts.get(pa, 0) + 1
    diary["e4"] = {"hexes": teng,
                   "towns": sorted(counts.items(), key=lambda x: -x[1])[:8]}

    # ---- e6 expansion scout: 4 anchors + their 12 siblings via p1 ----
    def sibs(anchor_mask, label):
        rows = pl.index[anchor_mask]
        if not len(rows):
            print("MISS", label); return None
        r = rows[0]
        s = Z @ Z[r]; s[r] = -2
        top = np.argsort(-s)[:12]
        return {"label": label,
                "anchor": {"name": pl["name"].iloc[r], "lat": float(pl["latitude"].iloc[r]),
                           "lng": float(pl["longitude"].iloc[r]),
                           "cat": pl["plexis_category"].iloc[r]},
                "sibs": [{"name": pl["name"].iloc[i], "lat": float(pl["latitude"].iloc[i]),
                          "lng": float(pl["longitude"].iloc[i]),
                          "cat": pl["plexis_category"].iloc[i],
                          "sz": pl["parent_subzone_name"].iloc[i],
                          "rank": int(k + 1)} for k, i in enumerate(top)]}

    diary["e6"] = {"anchors": [a for a in [
        sibs(pl["name"].eq("Tiong Bahru Bakery"), "a beloved bakery chain"),
        sibs(pl["name"].str.startswith("Ya Kun Kaya Toast (One Holland", na=False), "a kopi institution"),
        sibs(pl["name"].eq("The Lions Den"), "a Chinatown shophouse bar"),
        sibs(pl["name"].eq("Seatrium Canteen"), "an industrial canteen"),
    ] if a]}

    # ---- e7 brand ghost map: FairPrice homes -> twin hexes without one ----
    fp = pl[pl["brand_norm"].eq("NTUC FairPrice")]
    fp_hex = set(fp["hex8_id"])
    ghost = {}
    for h in fp_hex:
        for t in twins.get(h, []):
            if t["id"] not in fp_hex:
                ghost[t["id"]] = ghost.get(t["id"], 0) + 1
    top_ghost = sorted(ghost.items(), key=lambda x: -x[1])[:14]
    diary["e7"] = {
        "brand": "NTUC FairPrice", "n_outlets": int(len(fp)),
        "outlets": [[round(r["longitude"], 5), round(r["latitude"], 5)]
                    for _, r in fp.iterrows()],
        "ghosts": [{"hex": h, "votes": v,
                    "name": hprop.get(h, {}).get("parent_subzone_name", "?")}
                   for h, v in top_ghost if h in hprop]}

    # ---- e8 cast this corner: archetypes its twins host, it lacks ----
    by_hex_cat = pl.groupby(["hex8_id", "plexis_category"]).size()
    def cast(h):
        own = set(by_hex_cat.get(h, pd.Series(dtype=int)).index
                  if isinstance(by_hex_cat.get(h), pd.Series) else
                  [c for (hh, c) in by_hex_cat.index if hh == h])
        own = {c for (hh, c) in by_hex_cat.index if hh == h}
        votes = {}
        for t in twins.get(h, []):
            tc = {c for (hh, c) in by_hex_cat.index if hh == t["id"]}
            for c in tc - own:
                votes[c] = votes.get(c, 0) + 1
        keep = sorted([(v, c) for c, v in votes.items() if v >= 3], reverse=True)
        return [{"cat": c, "votes": v} for v, c in keep[:6]]

    e8 = []
    for h, tws in list(twins.items()):
        cs = cast(h)
        if len(cs) >= 3:
            e8.append({"hex": h, "name": hprop[h]["parent_subzone_name"],
                       "wants": cs})
        if len(e8) == 6:
            break
    diary["e8"] = {"corners": e8}

    # ---- e9 misfits: place farthest from its hex's own crowd ----
    mis = []
    for h, g in pl.groupby("hex8_id"):
        if len(g) < 12 or h not in hprop:
            continue
        idx = g.index.to_numpy()
        c = Z[idx].mean(0); c /= np.linalg.norm(c)
        s = Z[idx] @ c
        k = int(np.argmin(s))
        r = g.iloc[k]
        if not str(r["name"]).strip():
            continue
        mis.append({"name": r["name"], "cat": r["plexis_category"],
                    "lat": round(float(r["latitude"]), 5),
                    "lng": round(float(r["longitude"]), 5),
                    "sz": r["parent_subzone_name"],
                    "fit": round(float(s[k]), 3),
                    "crowd": int(len(g))})
    mis.sort(key=lambda x: x["fit"])
    diary["e9"] = {"misfits": mis[:40]}

    # ---- e10 segments on the geo map: 25K sample colored by cluster ----
    arrays = json.load(open(ROOT.parent / "apps/place-graph/public/data/arrays.json"))
    meta = json.load(open(ROOT.parent / "apps/place-graph/public/data/meta.json"))
    n = meta["n"]
    step = max(1, n // 25000)
    cl_color = {i: meta["cat_colors"][meta["cats"].index(c["top_cat"])]
                for i, c in enumerate(meta["clusters"])}
    feats = [{"type": "Feature",
              "geometry": {"type": "Point",
                           "coordinates": [arrays["lng"][i], arrays["lat"][i]]},
              "properties": {"c": cl_color.get(arrays["cluster"][i], "#64748b")}}
             for i in range(0, n, step)]
    json.dump({"type": "FeatureCollection", "features": feats},
              open(APP / "segments.geojson", "w"))
    diary["e10"] = {"n_shown": len(feats), "n_clusters": len(meta["clusters"])}

    json.dump(diary, open(APP / "diary.json", "w"))
    print("diary.json done:", {k: (len(v) if isinstance(v, list) else "ok")
                               for k, v in diary.items()})
    print("e3 gaps:", [g["name"] for g in diary["e3"]["gaps"][:4]])
    print("e4 tengah:", diary["e4"]["towns"][:4])
    print("e7 ghosts:", [g["name"] for g in diary["e7"]["ghosts"][:5]])
    print("e9 worst misfits:", [(m["name"], m["sz"]) for m in mis[:4]])


if __name__ == "__main__":
    main()
