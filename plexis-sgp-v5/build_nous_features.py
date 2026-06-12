"""
Plexis SGP — external feature pack for the nous gap analyzer.

Builds every section-A feature from nous/agents/FEATURES_TO_BUILD.md that is
buildable from public/owned sources today, in the delivery shapes that doc
specifies (point list / area table / hex8-keyed). Output goes to
nous_export/ and is copied to nous context/external/ by the caller.

Deliverables (one sanity assertion each, per the nous wiring checklist):
  shophouse_conserved_buildings.parquet  points (7,235 URA conserved bldgs)
  hex8_shophouse_density.parquet         hex8-keyed count + flag
  carparks.parquet                       points + total_lots capacity
  polyclinics.csv                        points (public primary care)
  female_pop_share.csv                   subzone table (SingStat 2025)
  wet_markets.csv                        points (markets & food centres)
  petrol_stations.csv                    points (OSM amenity=fuel)
  coworking_spaces.csv                   points (places name-match)
  condo_projects.parquet                 points + units weight (URA txns)
  hdb_completion_by_town.csv             town table (under-construction units)
  README.md                              manifest + provenance + sanity log
"""
import json
import re
import time
from pathlib import Path

import numpy as np
import pandas as pd
from pyproj import Transformer

ROOT = Path(__file__).parent
EXT = ROOT.parent / "data/external"
OUT = ROOT / "nous_export"
OUT.mkdir(exist_ok=True)

TR = Transformer.from_crs(3414, 4326, always_xy=True)
SANITY = []


def note(name, ok, detail):
    SANITY.append((name, "PASS" if ok else "CHECK", detail))
    print(f"  [{'PASS' if ok else 'CHECK'}] {name} — {detail}")


def centroid_lonlat(geom):
    import shapely.geometry as gg
    c = gg.shape(geom).centroid
    return c.x, c.y


def main():
    t0 = time.time()

    # ---- 1. shophouse / conservation -----------------------------------
    cb = json.load(open(EXT / "ura_conserved_buildings.geojson"))
    rows = []
    for f in cb["features"]:
        lon, lat = centroid_lonlat(f["geometry"])
        rows.append({"lat": lat, "lon": lon})
    sh = pd.DataFrame(rows)
    import h3
    sh["hex8_id"] = [h3.latlng_to_cell(a, o, 8) for a, o in zip(sh["lat"], sh["lon"])]
    sh.to_parquet(OUT / "shophouse_conserved_buildings.parquet", index=False)
    hx = sh.groupby("hex8_id").size().rename("conserved_bldg_count").reset_index()
    hx["is_conservation_cluster"] = hx["conserved_bldg_count"] >= 20
    hx.to_parquet(OUT / "hex8_shophouse_density.parquet", index=False)
    m = pd.read_parquet(ROOT / "hex/hex8_universe.parquet")[["hex8_id", "parent_subzone_name"]]
    top = hx.merge(m, on="hex8_id").nlargest(6, "conserved_bldg_count")
    heritage = {"CHINATOWN", "KAMPONG GLAM", "LITTLE INDIA", "JOO CHIAT",
                "BOAT QUAY", "CLARKE QUAY", "EMERALD HILL", "BUKIT PASOH",
                "TANJONG PAGAR", "MAXWELL", "CITY HALL", "BENCOOLEN",
                "VICTORIA", "SULTAN", "MACKENZIE", "FARRER PARK",
                # Jalan Besar conservation area spans these subzones
                "LAVENDER", "CRAWFORD", "JALAN BESAR", "KALLANG BAHRU"}
    hits = sum(any(h in sz for h in heritage) for sz in top["parent_subzone_name"])
    note("shophouse", hits >= 4,
         f"{len(sh):,} conserved bldgs; top hexes: "
         + ", ".join(top['parent_subzone_name'].head(4)) + f" ({hits}/6 heritage)")

    # ---- 2. carparks + capacity ----------------------------------------
    cp = pd.read_csv(EXT / "hdb_carpark_info.csv")
    lon, lat = TR.transform(cp["x_coord"].to_numpy(), cp["y_coord"].to_numpy())
    cp["lon"], cp["lat"] = lon, lat
    av = json.load(open(EXT / "carpark_availability_snapshot.json"))
    lots = {}
    for c in av["items"][0]["carpark_data"]:
        tot = sum(int(i["total_lots"]) for i in c["carpark_info"]
                  if i["lot_type"] == "C")
        lots[c["carpark_number"]] = tot
    cp["total_lots"] = cp["car_park_no"].map(lots)
    keep = ["car_park_no", "address", "lat", "lon", "car_park_type",
            "car_park_decks", "total_lots"]
    cp[keep].to_parquet(OUT / "carparks.parquet", index=False)
    cov = cp["total_lots"].notna().mean()
    note("carparks", cov > 0.8 and len(cp) > 2000,
         f"{len(cp):,} HDB carparks, capacity joined for {cov:.0%}, "
         f"{cp['total_lots'].sum():,.0f} car lots total")

    # ---- 3. polyclinics --------------------------------------------------
    am = json.load(open(ROOT.parent / "data/osm_pois/amenities.geojson"))
    rows = []
    for f in am["features"]:
        nm = str(f["properties"].get("name", ""))
        if "polyclinic" not in nm.lower():
            continue
        g = f["geometry"]
        lon, lat = (g["coordinates"] if g["type"] == "Point"
                    else centroid_lonlat(g))
        rows.append({"name": nm, "lat": lat, "lon": lon})
    pc = pd.DataFrame(rows).drop_duplicates(subset="name").reset_index(drop=True)
    pc.to_csv(OUT / "polyclinics.csv", index=False)
    known = sum(any(k in n for n in pc["name"])
                for k in ["Toa Payoh", "Bedok", "Yishun", "Tampines", "Jurong"])
    note("polyclinics", 20 <= len(pc) <= 35 and known >= 4,
         f"{len(pc)} polyclinics; known-name hits {known}/5")

    # ---- 4. female pop share (subzone) ----------------------------------
    d = pd.read_csv(ROOT.parent / "data/demographics/pop_age_sex_tod_2025.csv")
    g = d.groupby(["SZ", "Sex"])["Pop"].sum().unstack(fill_value=0)
    fs = pd.DataFrame({
        "subzone": g.index,
        "pop_female": g.get("Females", 0).to_numpy(),
        "pop_male": g.get("Males", 0).to_numpy(),
    })
    fs["female_pop_share"] = fs["pop_female"] / (fs["pop_female"] + fs["pop_male"]).replace(0, np.nan)
    fs.to_csv(OUT / "female_pop_share.csv", index=False)
    nat = fs["pop_female"].sum() / (fs["pop_female"].sum() + fs["pop_male"].sum())
    note("female_pop_share", 0.48 <= nat <= 0.54,
         f"{len(fs)} subzones, national female share {nat:.3f}")

    # ---- 5. wet markets --------------------------------------------------
    hk = json.load(open(ROOT.parent / "data/amenities_updated/hawker_centres.geojson"))
    rows = []
    for f in hk["features"]:
        props = f["properties"]
        blob = str(props.get("Description", "")) + " " + str(props.get("NAME", ""))
        mname = re.search(r"<th>NAME</th>\s*<td>([^<]+)</td>", blob)
        nm = (mname.group(1) if mname else props.get("NAME") or "").strip()
        g = f["geometry"]
        lon, lat = (g["coordinates"][:2] if g["type"] == "Point"
                    else centroid_lonlat(g))
        rows.append({"name": nm, "lat": lat, "lon": lon,
                     "is_wet_market": bool(re.search(r"\bmarket\b", nm, re.I))})
    wm = pd.DataFrame(rows)
    wm.to_csv(OUT / "wet_markets.csv", index=False)
    wets = wm[wm["is_wet_market"]]
    landmark = sum(any(k.lower() in n.lower() for n in wets["name"])
                   for k in ["Tekka", "Tiong Bahru", "Chinatown", "Geylang Serai"])
    note("wet_markets", len(wets) >= 30 and landmark >= 3,
         f"{len(wm)} centres, {len(wets)} flagged markets; landmarks {landmark}/4")

    # ---- 6. petrol stations ---------------------------------------------
    rows = []
    for f in am["features"]:
        if f["properties"].get("amenity") != "fuel":
            continue
        g = f["geometry"]
        lon, lat = (g["coordinates"] if g["type"] == "Point" else centroid_lonlat(g))
        rows.append({"name": f["properties"].get("name") or
                     f["properties"].get("brand") or "unnamed",
                     "brand": f["properties"].get("brand", ""),
                     "lat": lat, "lon": lon})
    pf = pd.DataFrame(rows)
    pf.to_csv(OUT / "petrol_stations.csv", index=False)
    brands = pf["name"].str.contains("Shell|Esso|SPC|Caltex|Sinopec", case=False,
                                     na=False).sum()
    note("petrol", 150 <= len(pf) <= 260 and brands > 80,
         f"{len(pf)} stations, {brands} major-brand named")

    # ---- 7. coworking -----------------------------------------------------
    pl = pd.read_parquet(ROOT / "places/sgp_places_final.parquet",
                         columns=["name", "latitude", "longitude",
                                  "plexis_category", "parent_subzone_name"])
    PAT = (r"\b(wework|justco|the great room|the work project|the working capitol"
           r"|spaces\b|regus|distrii|found8|common ground|workcentral|csuites"
           r"|the executive centre|ceo suite|servcorp|arcc spaces|crane\b"
           r"|trehaus|o2work|workbuddy|coworking|co-working|cospace)")
    cw = pl[pl["name"].str.contains(PAT, case=False, regex=True, na=False)].copy()
    cw = cw.rename(columns={"latitude": "lat", "longitude": "lon"})
    cw[["name", "lat", "lon", "parent_subzone_name"]].to_csv(
        OUT / "coworking_spaces.csv", index=False)
    central = cw["parent_subzone_name"].isin(
        ["CECIL", "RAFFLES PLACE", "ANSON", "TANJONG PAGAR", "CITY HALL",
         "CENTRAL SUBZONE", "CLIFFORD PIER", "PHILLIP", "MAXWELL", "BUGIS",
         "CHINATOWN", "ROBINSON"]).mean() if len(cw) else 0
    note("coworking", 60 <= len(cw) <= 400 and central > 0.25,
         f"{len(cw)} venues matched, {central:.0%} in CBD-core subzones")

    # ---- 8. condo projects (URA transactions) ----------------------------
    rows = []
    for b in [1, 2, 3, 4]:
        # URA JSON carries stray latin-1 bytes in street names
        t = json.loads(open(EXT / f"ura_resi_txn_b{b}.json",
                            encoding="utf-8", errors="replace").read())
        for p in t.get("Result", []):
            if "x" not in p or not p.get("x"):
                continue
            tx = p.get("transaction", [])
            strata = [x for x in tx if x.get("propertyType") in
                      ("Condominium", "Apartment", "Executive Condominium")]
            if not strata:
                continue
            units = sum(int(x.get("noOfUnits", 1)) for x in strata)
            last = max(x.get("contractDate", "0") for x in strata)
            rows.append({"project": p["project"], "street": p.get("street"),
                         "x": float(p["x"]), "y": float(p["y"]),
                         "units_sold": units, "n_txns": len(strata),
                         "last_txn": last,
                         "market_segment": p.get("marketSegment")})
    cd = pd.DataFrame(rows).drop_duplicates(subset=["project", "street"])
    lon, lat = TR.transform(cd["x"].to_numpy(), cd["y"].to_numpy())
    cd["lon"], cd["lat"] = lon, lat
    cd = cd.drop(columns=["x", "y"])
    cd.to_parquet(OUT / "condo_projects.parquet", index=False)
    ccr = (cd["market_segment"] == "CCR").mean()
    note("condo_projects", len(cd) > 2000 and 0.1 < ccr < 0.5,
         f"{len(cd):,} strata projects (txn-derived; units_sold = txn volume "
         f"weight, NOT total units), CCR share {ccr:.0%}")

    # ---- 9. HDB completion by town (BTO pipeline proxy) -------------------
    # file fetched once via data.gov.sg poll-download (curl); read local copy
    src = EXT / "hdb_completion_by_town.csv"
    if src.exists() and src.stat().st_size > 200:
        ct = pd.read_csv(src)
        ct.to_csv(OUT / "hdb_completion_by_town.csv", index=False)
        fy = ct["financial_year"].max()
        uc = ct[(ct["financial_year"] == fy)
                & (ct["status"] == "Under Construction")]["no_of_units"].sum()
        note("hdb_completion_by_town", len(ct) > 50 and uc > 10_000,
             f"{len(ct)} rows to FY{fy}; {uc:,.0f} units under construction")
    else:
        note("hdb_completion_by_town", False,
             "source CSV missing — re-run the poll-download curl")

    # ---- README manifest --------------------------------------------------
    md = ["# Atlas external feature pack for nous — " + time.strftime("%Y-%m-%d"),
          "",
          "Built by the Digital Atlas pipeline (plexis v5; script "
          "`plexis-sgp-v4/build_nous_features.py`). Shapes per "
          "FEATURES_TO_BUILD.md; H3 wiring stays on the nous side.",
          "",
          "| File | Shape | Maps to 🔨 | Source | Sanity |",
          "|---|---|---|---|---|"]
    meta = {
        "shophouse_conserved_buildings.parquet": ("points", "shophouse_density", "URA MP19 SDCP Conserved Building layer (data.gov.sg)"),
        "hex8_shophouse_density.parquet": ("hex8-keyed", "shophouse_density", "derived: conserved bldg count + cluster flag (≥20)"),
        "carparks.parquet": ("points+capacity", "carpark_accessibility", "HDB Carpark Information + live availability total_lots (C)"),
        "polyclinics.csv": ("points", "polyclinic_distance", "OSM (name match), deduped"),
        "female_pop_share.csv": ("subzone table", "female_pop_share", "SingStat 2025 pop by SZ × age × sex (local atlas copy)"),
        "wet_markets.csv": ("points+flag", "wet_market_adjacency", "NEA hawker-centres layer, 'market' name flag"),
        "petrol_stations.csv": ("points", "petrol_station_coverage", "OSM amenity=fuel"),
        "coworking_spaces.csv": ("points", "coworking_density", "Atlas places (190K) brand/name match"),
        "condo_projects.parquet": ("points+weight", "condo_density", "URA PMI_Resi_Transaction (strata only); units_sold = transaction volume, NOT stock"),
        "hdb_completion_by_town.csv": ("town table", "new_estate_growth", "HDB completion status by town/estate (under-construction units)"),
    }
    for f, (shape, maps, src) in meta.items():
        s = next((f"{st}: {d}" for n, st, d in SANITY if n in f or n in maps), "")
        md.append(f"| `{f}` | {shape} | `{maps}` | {src} | {s[:90]} |")
    md += ["",
           "## Not deliverable (so you don't wait for it)",
           "- **`rental_affordability` (shop rent)** — URA exposes NO commercial rental via API/data.gov.sg (probed 2026-06-10; Realis-only). The live hex8 view already carries `rent_resi_psf_med` + `rent_resolution` (913-project URA resi medians, IDW) — the best available rent *gradient*; treat as proxy with the same null-trap rule as HDB psm.",
           "- **BTO project-level locations** — no longer openly published (HDB geojson on data.gov.sg is 2018-stale). Town-level under-construction units above + the live `pipe_dev_capacity_res` / `pipe_new_mrt_within_800m` hex8 columns are the workable combination.",
           "",
           "## Sanity log", ""]
    md += [f"- [{st}] **{n}** — {d}" for n, st, d in SANITY]
    open(OUT / "README.md", "w").write("\n".join(md))
    print(f"\n{len(meta)} deliverables -> {OUT}  ({time.time()-t0:.1f}s)")


if __name__ == "__main__":
    main()
