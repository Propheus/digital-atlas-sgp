"""
Plexis SGP v4 — S7 Micro visibility (vis_*) per hex8.

Spec: SITE_SELECTION_METRICS.md §S7, narrowed twice: dist_mrt_exit_m already
exists in the master, so this ships only the genuinely-new micro signals:

  vis_exit_footfall      weekday daily train taps at the nearest station exit
                         within 400 m of the hex activity origin, split evenly
                         across that station's exits. Station taps come from
                         the REAL per-station PV (transport_node_train_202601,
                         PT_CODE level, mapped to names via sg-rail.geojson) —
                         a v1 used hex-aggregated daily_train_taps and
                         credited single-exit LRT stations with their entire
                         interchange hex (Petir LRT "saw" Bukit Panjang's
                         160K). 0 if no exit within 400 m.
  vis_main_road_m        total length of LTA speed-band cat A/B (expressway/
                         major arterial) segments whose midpoint falls in hex
  vis_traffic_pass_proxy sum of road-category weights (A=5 B=4 C=3 D=2 E=1.5
                         F=1) over speed-band segments in hex — drive-past
                         exposure proxy
  vis_corner_premium     signalized intersections x main-road presence
                         (signal count if cat A/B present in hex, else 0)

Output: hex/hex8_visibility.parquet + hex/visibility_report.json
"""
import json
import time
from pathlib import Path

import h3
import numpy as np
import pandas as pd
from pyproj import Transformer
from scipy.spatial import cKDTree

ROOT = Path(__file__).parent
CAT_W = {"A": 5.0, "B": 4.0, "C": 3.0, "D": 2.0, "E": 1.5, "F": 1.0}
EXIT_RADIUS = 400.0


def main():
    t0 = time.time()
    tr = Transformer.from_crs(4326, 3414, always_xy=True)

    # ---- exits + station taps ----------------------------------------------
    ex = json.load(open(ROOT.parent / "data/external/lta_mrt_station_exits.geojson"))
    rows = [(f["properties"]["STATION_NA"], *f["geometry"]["coordinates"][:2])
            for f in ex["features"]]
    exits = pd.DataFrame(rows, columns=["station", "lng", "lat"])
    # real per-station PV: PT_CODE weekday taps -> station name via sg-rail
    pv = pd.read_csv(ROOT.parent / "data/lta_live/transport_node_train_202601.csv")
    pv = pv[pv["DAY_TYPE"] == "WEEKDAY"]
    code_taps = ((pv["TOTAL_TAP_IN_VOLUME"] + pv["TOTAL_TAP_OUT_VOLUME"])
                 .groupby(pv["PT_CODE"]).sum() / 22.0)   # monthly wd -> daily
    rail = json.load(open(ROOT / "data/lta_od/sg-rail.geojson"))
    import re
    code2name = {}
    for f in rail["features"]:
        if f["geometry"]["type"] != "Point":
            continue
        p = f["properties"]
        nm = p.get("name", "").upper()
        # sg-rail also holds exit-label points named "1", "2", "A", "B"...
        # that carry the parent station's codes — they accumulated phantom
        # taps (161K at Hume) and later overwrote code2name wholesale.
        # Real station names are >= 3 chars.
        if not nm or len(nm) < 3:
            continue
        for c in re.findall(r"[A-Z]{2}\d+", str(p.get("station_codes", ""))):
            code2name[c] = nm
    # PV PT_CODE is merged for interchanges ("EW24/NS1", 15% of rows):
    # resolve each PV entry to its station name(s) via any component code
    name_taps = {}
    for pt_code, taps in code_taps.items():
        names = {code2name.get(c)
                 for c in re.findall(r"[A-Z]{2}\d+", str(pt_code))} - {None}
        for nm in names:
            name_taps[nm] = name_taps.get(nm, 0) + float(taps) / max(len(names), 1)

    def station_name(raw):
        nm = re.sub(r"\s+(MRT|LRT)\s+STATION$", "", raw.strip().upper())
        if nm in name_taps:
            return nm
        m = re.fullmatch(r"[A-Z]{2}\d+", nm)          # code-only entries (DT18)
        if m and nm in code2name:
            return code2name[nm]
        return None

    exits["st_name"] = exits["station"].map(station_name)
    exits["n_exits"] = exits.groupby("station")["station"].transform("size")
    exits["exit_taps"] = (exits["st_name"].map(name_taps).fillna(0)
                          / exits["n_exits"])
    matched = exits["st_name"].notna().mean()
    print(f"exits: {len(exits)}, name-matched: {matched:.1%}, "
          f"stations with taps: {(exits.groupby('station')['exit_taps'].max() > 0).mean():.1%}")

    # hex8 activity origins
    h8 = pd.read_parquet(ROOT / "hex/hex8_universe.parquet")
    pl = pd.read_parquet(ROOT / "places/sgp_places_final.parquet",
                         columns=["hex8_id", "latitude", "longitude"])
    act = pl.groupby("hex8_id")[["longitude", "latitude"]].mean()
    h8 = h8.set_index("hex8_id")
    h8["o_lng"] = act["longitude"].reindex(h8.index).fillna(h8["lng"])
    h8["o_lat"] = act["latitude"].reindex(h8.index).fillna(h8["lat"])
    h8 = h8.reset_index()
    ox, oy = tr.transform(h8["o_lng"].to_numpy(), h8["o_lat"].to_numpy())
    exx, exy = tr.transform(exits["lng"].to_numpy(), exits["lat"].to_numpy())
    d, k = cKDTree(np.column_stack([exx, exy])).query(np.column_stack([ox, oy]))
    h8["vis_exit_footfall"] = np.where(d <= EXIT_RADIUS,
                                       exits["exit_taps"].to_numpy()[k], 0.0)
    h8["vis_exit_station"] = np.where(d <= EXIT_RADIUS,
                                      exits["station"].to_numpy()[k], None)
    h8["vis_dist_exit_origin_m"] = d.round(1)

    # ---- speed bands --------------------------------------------------------
    sb = json.load(open(ROOT.parent / "data/lta_live/traffic_speed_bands_full.json"))
    sb = sb if isinstance(sb, list) else sb.get("value", [])
    s = pd.DataFrame(sb)
    for c in ["StartLon", "StartLat", "EndLon", "EndLat"]:
        s[c] = pd.to_numeric(s[c], errors="coerce")
    s = s.dropna(subset=["StartLon", "EndLon"])
    s["mid_lat"] = (s["StartLat"] + s["EndLat"]) / 2
    s["mid_lng"] = (s["StartLon"] + s["EndLon"]) / 2
    s["hex8_id"] = [h3.latlng_to_cell(la, ln, 8)
                    for la, ln in zip(s["mid_lat"], s["mid_lng"])]
    x1, y1 = tr.transform(s["StartLon"].to_numpy(), s["StartLat"].to_numpy())
    x2, y2 = tr.transform(s["EndLon"].to_numpy(), s["EndLat"].to_numpy())
    s["len_m"] = np.hypot(x2 - x1, y2 - y1)
    s["w"] = s["RoadCategory"].map(CAT_W).fillna(1.0)
    s["is_major"] = s["RoadCategory"].isin(["A", "B"])
    g = s.groupby("hex8_id")
    agg = pd.DataFrame({
        "vis_main_road_m": g.apply(lambda x: x.loc[x["is_major"], "len_m"].sum()),
        "vis_traffic_pass_proxy": g["w"].sum(),
    }).reset_index()
    h8 = h8.merge(agg, on="hex8_id", how="left")
    h8[["vis_main_road_m", "vis_traffic_pass_proxy"]] = \
        h8[["vis_main_road_m", "vis_traffic_pass_proxy"]].fillna(0)

    m = pd.read_parquet(ROOT / "hex/hex8_all_features.parquet")
    sig_col = next((c for c in m.columns
                    if c.startswith("sig") and "count" in c), None)
    sigs = m.set_index("hex8_id")[sig_col] if sig_col else pd.Series(dtype=float)
    h8["vis_corner_premium"] = (h8["hex8_id"].map(sigs).fillna(0)
                                * (h8["vis_main_road_m"] > 0)).round(1)

    out = h8[["hex8_id", "vis_exit_footfall", "vis_exit_station",
              "vis_dist_exit_origin_m", "vis_main_road_m",
              "vis_traffic_pass_proxy", "vis_corner_premium"]]
    out = out.round(2)
    out.to_parquet(ROOT / "hex/hex8_visibility.parquet", index=False)

    rep = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "spec": "SITE_SELECTION_METRICS.md S7 (narrowed)",
        "exits": int(len(exits)),
        "stations": int(exits["station"].nunique()),
        "exit_name_match": round(float(matched), 3),
        "stations_with_taps": round(float(
            (exits.groupby("station")["exit_taps"].max() > 0).mean()), 3),
        "signal_col_used": sig_col,
        "speed_band_segments": int(len(s)),
        "hex_with_exit_footfall": int((out["vis_exit_footfall"] > 0).sum()),
        "wall_clock_s": round(time.time() - t0, 2),
    }
    json.dump(rep, open(ROOT / "hex/visibility_report.json", "w"), indent=2)
    print(json.dumps(rep, indent=2))


if __name__ == "__main__":
    main()
