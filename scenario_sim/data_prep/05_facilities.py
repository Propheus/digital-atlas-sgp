"""
Build facility_supply.parquet — per-subzone counts for CHAS clinics, FairPrice,
and background grocery competition.

CHAS clinics: parse HTML-embedded attributes from chas_clinics.geojson, filter to
clinics where CLINIC_PROGRAMME_CODE contains "CHAS", spatial-join to subzones.

FairPrice: filter sgp_places_v2.jsonl by brand string (NTUC FairPrice | FairPrice);
use the subzone_code already present on each record.

Background groceries: all non-FairPrice grocery/supermarket brands (Sheng Siong,
Giant, Cold Storage, Prime, etc.). Used for realistic t=0 competition in the gravity
model, but *not* scenario-mutable in v0.

Output schema:
  subzone_code, chas_clinics, fairprice, grocery_background
"""
import json
import re
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

BASE = "/home/azureuser/digital-atlas-sgp"
OUT = f"{BASE}/scenario_sim/cache/facility_supply.parquet"

# Brand matching
FAIRPRICE_BRANDS = {"NTUC FairPrice", "FairPrice"}
BG_GROCERY_BRANDS = {
    "Sheng Siong", "Giant", "GIANT", "Cold Storage", "Cold Storage Singapore",
    "Prime Supermarket", "U Stars", "Fortune Supermarket", "Mustafa",
}

def parse_clinic_html(desc: str) -> dict:
    """Extract key fields from the HTML blob in chas_clinics.geojson Description."""
    out = {}
    if not desc:
        return out
    # pattern: <th>KEY</th> <td>VALUE</td>
    for m in re.finditer(r"<th>([^<]+)</th>\s*<td>([^<]*)</td>", desc):
        out[m.group(1).strip()] = m.group(2).strip()
    return out

def main():
    # --- load subzones (for spatial joins)
    sz = gpd.read_file(f"{BASE}/data/boundaries/subzones.geojson").to_crs("EPSG:4326")
    sz = sz.rename(columns={"SUBZONE_C": "subzone_code"})[["subzone_code", "geometry"]]
    all_codes = sz["subzone_code"].tolist()
    print(f"[05] subzones: {len(sz)}")

    # ============================================================
    # CHAS clinics
    # ============================================================
    clinics_raw = gpd.read_file(f"{BASE}/data/amenities_updated/chas_clinics.geojson")
    if clinics_raw.crs is None:
        clinics_raw = clinics_raw.set_crs("EPSG:4326")
    else:
        clinics_raw = clinics_raw.to_crs("EPSG:4326")
    print(f"[05] total clinics in file: {len(clinics_raw)}")

    # Parse HTML to filter for CHAS programme
    clinics_raw["parsed"] = clinics_raw["Description"].apply(parse_clinic_html)
    clinics_raw["programme"] = clinics_raw["parsed"].apply(lambda d: d.get("CLINIC_PROGRAMME_CODE", ""))
    clinics_raw["hci_name"] = clinics_raw["parsed"].apply(lambda d: d.get("HCI_NAME", ""))

    chas = clinics_raw[clinics_raw["programme"].str.contains("CHAS", na=False)].copy()
    print(f"[05] CHAS clinics (filtered): {len(chas)}")

    # Spatial join
    chas_points = chas[["hci_name", "programme", "geometry"]].copy()
    chas_joined = gpd.sjoin(chas_points, sz, how="left", predicate="within")
    n_unjoined = chas_joined["subzone_code"].isna().sum()
    if n_unjoined:
        print(f"[05] WARN: {n_unjoined} CHAS clinics did not fall inside any subzone (edge cases)")
    chas_counts = (
        chas_joined.dropna(subset=["subzone_code"])
        .groupby("subzone_code")
        .size()
        .rename("chas_clinics")
    )

    # ============================================================
    # FairPrice + background groceries (from places jsonl)
    # ============================================================
    fp_counts = {}
    bg_counts = {}
    total_scanned = 0
    fp_total = 0
    bg_total = 0
    with open(f"{BASE}/data/places_consolidated/sgp_places_v2.jsonl") as f:
        for line in f:
            rec = json.loads(line)
            total_scanned += 1
            brand = rec.get("brand")
            code = rec.get("subzone_code")
            if not brand or not code:
                continue
            if brand in FAIRPRICE_BRANDS:
                fp_counts[code] = fp_counts.get(code, 0) + 1
                fp_total += 1
            elif brand in BG_GROCERY_BRANDS:
                bg_counts[code] = bg_counts.get(code, 0) + 1
                bg_total += 1
    print(f"[05] places scanned: {total_scanned}")
    print(f"[05] FairPrice total: {fp_total}  (expected ~280)")
    print(f"[05] background groceries total: {bg_total}")

    # ============================================================
    # Assemble supply table
    # ============================================================
    out = pd.DataFrame({"subzone_code": all_codes})
    out["chas_clinics"] = out["subzone_code"].map(chas_counts).fillna(0).astype(int)
    out["fairprice"] = out["subzone_code"].map(fp_counts).fillna(0).astype(int)
    out["grocery_background"] = out["subzone_code"].map(bg_counts).fillna(0).astype(int)
    out["total_grocery"] = out["fairprice"] + out["grocery_background"]

    out.to_parquet(OUT, index=False)
    print(f"[05] wrote {OUT}  shape={out.shape}")
    print(f"[05] totals:  CHAS={out['chas_clinics'].sum()}  FairPrice={out['fairprice'].sum()}  "
          f"bg_grocery={out['grocery_background'].sum()}")

    # Top subzones per category (sanity)
    print("\n[05] top 10 subzones by CHAS count:")
    print(out.nlargest(10, "chas_clinics")[["subzone_code", "chas_clinics"]].to_string(index=False))
    print("\n[05] top 10 subzones by FairPrice count:")
    print(out.nlargest(10, "fairprice")[["subzone_code", "fairprice"]].to_string(index=False))

if __name__ == "__main__":
    main()
