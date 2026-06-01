"""
Plexis SGP v4 — composites validator.

C1 all 6 indices in [0, 1]
C2 vibrancy: top hexes are CBD/Orchard/MBS
C3 commercial_intensity: top hexes in Cecil / Raffles / Marina South / Tanjong Pagar
C4 family_index: top hexes in HDB towns (Bishan / Punggol / Sengkang)
C5 livability: top hexes in mature residential (Bishan / Toa Payoh / Bukit Merah)
C6 density_pressure: top hexes in CBD or HDB-dense (Toa Payoh / Bukit Merah / Geylang)
"""
import json, time
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).parent
report = {"checks": []}


def add(name, status, detail=""):
    report["checks"].append({"check": name, "status": status, "detail": detail})
    print(f"  [{status}] {name} — {detail}")


print("Loading...")
h9 = pd.read_parquet(ROOT / "hex/hex9_composites.parquet")
h9_uni = pd.read_parquet(ROOT / "hex/hex9_universe.parquet")
h9_pa = h9.merge(h9_uni[["hex9_id","parent_pa","parent_subzone_name"]], on="hex9_id")

# C1 bounds
indices = ["vibrancy_index","livability_index","commercial_intensity","family_index",
            "density_pressure","accessibility_composite"]
ok = all((h9[c].between(0, 1)).all() for c in indices)
if ok:
    add("C1_bounds", "PASS", "all 6 indices in [0,1]")
else:
    bad = [c for c in indices if not h9[c].between(0,1).all()]
    add("C1_bounds", "FAIL", f"out of bounds: {bad}")

# Helper
def top_pa_overlap(col, expected, n=20):
    top = h9_pa.nlargest(n, col)
    hits = top["parent_pa"].isin(expected).sum()
    return hits, set(top["parent_pa"].unique()[:8])

# C2 vibrancy
exp = {"DOWNTOWN CORE","ORCHARD","MARINA SOUTH","ROCHOR","OUTRAM","SINGAPORE RIVER","MUSEUM"}
hits, top_pas = top_pa_overlap("vibrancy_index", exp)
if hits >= 12:
    add("C2_vibrancy_top_in_cbd", "PASS", f"{hits}/20 top vibrancy hexes in CBD-cluster (top PAs: {top_pas})")
else:
    add("C2_vibrancy_top_in_cbd", "WARN", f"{hits}/20 (top: {top_pas})")

# C3 commercial_intensity
exp = {"DOWNTOWN CORE","ORCHARD","MARINA SOUTH","OUTRAM","SINGAPORE RIVER","TANGLIN","MUSEUM","ROCHOR"}
hits, top_pas = top_pa_overlap("commercial_intensity", exp)
if hits >= 10:
    add("C3_commercial_top_in_cbd_cluster", "PASS", f"{hits}/20 top commercial hexes in CBD cluster")
else:
    add("C3_commercial_top_in_cbd_cluster", "WARN", f"{hits}/20")

# C4 family
exp = {"BISHAN","PUNGGOL","SENGKANG","ANG MO KIO","TAMPINES","TOA PAYOH","BEDOK","HOUGANG",
        "QUEENSTOWN","BUKIT MERAH","CLEMENTI","SERANGOON","PASIR RIS","KALLANG"}
hits, top_pas = top_pa_overlap("family_index", exp)
if hits >= 12:
    add("C4_family_top_in_hdb_pas", "PASS", f"{hits}/20 top family hexes in HDB PAs")
else:
    add("C4_family_top_in_hdb_pas", "WARN", f"{hits}/20")

# C5 livability
exp = {"BISHAN","TOA PAYOH","BUKIT MERAH","QUEENSTOWN","KALLANG","ANG MO KIO","TAMPINES",
        "BEDOK","CLEMENTI","SERANGOON","NOVENA","TANGLIN","PUNGGOL","SENGKANG"}
hits, top_pas = top_pa_overlap("livability_index", exp)
if hits >= 8:
    add("C5_livability_top_in_residential", "PASS", f"{hits}/20 top livable hexes in residential PAs")
else:
    add("C5_livability_top_in_residential", "WARN", f"{hits}/20")

# C6 density_pressure
exp = {"DOWNTOWN CORE","TOA PAYOH","BUKIT MERAH","GEYLANG","KALLANG","TAMPINES","BEDOK",
        "ANG MO KIO","BISHAN","CHOA CHU KANG","HOUGANG","ROCHOR","CENTRAL AREA"}
hits, top_pas = top_pa_overlap("density_pressure", exp)
if hits >= 10:
    add("C6_density_top_in_dense_pas", "PASS", f"{hits}/20 top density hexes in dense PAs")
else:
    add("C6_density_top_in_dense_pas", "WARN", f"{hits}/20")

passes = sum(1 for c in report["checks"] if c["status"] == "PASS")
print(f"\n{passes}/{len(report['checks'])} checks passed")

report["generated_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
with open(ROOT / "hex/composites_validation.json", "w") as f:
    json.dump(report, f, indent=2)
