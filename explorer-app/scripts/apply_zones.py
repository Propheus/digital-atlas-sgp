"""Local post-process: borrow zone_type from the transport-adequacy app to
(1) mask hex8/subzone to displayable land (residential + industrial only —
drops airport, nature/water-catchment, restricted islands, future, empty), and
(2) reorganize layers.json metrics into clean categories for the top toggle.

Run from explorer-app/:  python3 scripts/apply_zones.py
"""
import json
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "public" / "data"
TRANSPORT = Path("/Users/sumanth/propheus-projs/da-apps-sgp-mobility/da-apps-sgp-mobility/transport-adequacy-app/public/data/hex8_adequacy.geojson")
KEEP = {"residential", "industrial"}

# metric id -> category (ordered)
CATS = [
  ("Population", ["pop_total", "nonres_share", "pop_dorm"]),
  ("Mobility",   ["od_throughput", "od_net", "transit", "walkability"]),
  ("Commercial", ["commercial_activity", "commercial_intensity", "nl_2024", "nl_change"]),
  ("Places",     ["place_density", "place_diversity", "magnets", "brands", "avg_rating", "reviews", "fnb", "retail"]),
  ("Living",     ["vibrancy", "livability", "density", "hdb_resale"]),
  ("People",     ["affluence", "median_age", "pct_univ"]),
  ("Emergent",   ["breathing", "latent_demand"]),
]
CAT_OF = {m: c for c, ms in CATS for m in ms}


def main():
    tj = json.load(open(TRANSPORT))
    zone = {f["properties"]["hex8_id"]: (f["properties"].get("zone_type"),
                                         f["properties"].get("zone_type_broad"))
            for f in tj["features"]}
    disp_hex = {h for h, (zt, zb) in zone.items() if zb in KEEP}

    # hex8: filter + attach zone_type
    hj = json.load(open(DATA / "hex8_explore.geojson"))
    kept = []
    for f in hj["features"]:
        hid = f["properties"]["hex8_id"]
        if hid in disp_hex:
            zt, zb = zone[hid]
            f["properties"]["zone_type"] = zt
            f["properties"]["zone_type_broad"] = zb
            kept.append(f)
    hj["features"] = kept
    json.dump(hj, open(DATA / "hex8_explore.geojson", "w"))
    print(f"hex8: kept {len(kept)} / displayable {len(disp_hex)}")

    # subzone: keep those that contain a displayable hex (consistent atlas naming)
    disp_sz = {(f["properties"].get("parent_subzone_name") or "").strip().upper()
               for f in kept}
    disp_sz.discard("")
    sj = json.load(open(DATA / "subzone_explore.geojson"))
    skept = [f for f in sj["features"]
             if (f["properties"].get("SUBZONE_N") or "").strip().upper() in disp_sz]
    sj["features"] = skept
    json.dump(sj, open(DATA / "subzone_explore.geojson", "w"))
    print(f"subzone: kept {len(skept)} / {len(disp_sz)} displayable names")

    # layers.json: reassign categories + order
    lj = json.load(open(DATA / "layers.json"))
    for m in lj["metrics"]:
        m["group"] = CAT_OF.get(m["id"], "Other")
    order = {c: i for i, (c, _) in enumerate(CATS)}
    lj["metrics"].sort(key=lambda m: (order.get(m["group"], 99),
                                      [x for _, ms in CATS for x in ms].index(m["id"]) if m["id"] in CAT_OF else 99))
    lj["categories"] = [c for c, _ in CATS]
    json.dump(lj, open(DATA / "layers.json", "w"), indent=2)
    print(f"layers.json: {len(lj['metrics'])} metrics across {len(CATS)} categories")


if __name__ == "__main__":
    main()
