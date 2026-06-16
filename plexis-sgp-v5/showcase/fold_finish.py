"""Finish: subzone fold (key subzone_c == pack.parent_subzone) + catalog append.
hex8 master already folded to 840 on disk; feature_catalog still original."""
import pandas as pd
from pathlib import Path
import importlib.util
V5 = Path("/home/azureuser/da-sgp/v5")
spec = importlib.util.spec_from_file_location("fp", V5/"showcase/fold_packs_into_master.py")
# reuse DESC + PACKS + catalog_rows from the original module WITHOUT re-running its body:
DESC = {}  # rebuilt below to avoid executing module side-effects
exec(compile(open(V5/"showcase/fold_packs_into_master.py").read().split("# ---- HEX8")[0],
             "fold_defs", "exec"), globals())  # loads DESC, PACKS, catalog_rows, V5, etc.

# ---- SUBZONE fold ----
sz = pd.read_parquet(V5/"hex/subzone_all_features.parquet"); n0 = sz.shape[1]
added_sz = []
for pk in PACKS:
    pf = pd.read_parquet(V5/f"hex/subzone_{pk}_pack.parquet")
    sc = [c for c in pf.columns if c in DESC]
    sub = pf[["parent_subzone"]+sc].drop_duplicates("parent_subzone").rename(columns={"parent_subzone":"subzone_c"})
    sz = sz.merge(sub, on="subzone_c", how="left"); added_sz += sc
sz.to_parquet(V5/"hex/subzone_all_features.parquet", index=False)
matched = int(sz[added_sz[0]].notna().sum())
print(f"subzone: {n0} -> {sz.shape[1]}  ({matched}/{len(sz)} subzones matched a pack rollup)")

# ---- catalog append (hex8 read from the already-folded master) ----
import shutil, time
h = pd.read_parquet(V5/"hex/hex8_all_features.parquet")
addedH = [c for c in DESC if c in h.columns]
fc = pd.read_parquet(V5/"catalog/feature_catalog.parquet")
already = set(fc[fc.dataset=="hex/hex8_all_features.parquet"].column)
newH = catalog_rows(h, [c for c in addedH if c not in already], "hex/hex8_all_features.parquet", "hex8")
newS = catalog_rows(sz, [c for c in added_sz if c in sz.columns], "hex/subzone_all_features.parquet", "subzone")
fc2 = pd.concat([fc, newH, newS], ignore_index=True)
fc2.to_parquet(V5/"catalog/feature_catalog.parquet", index=False)
print(f"feature_catalog: {len(fc)} -> {len(fc2)} (+{len(newH)} hex8, +{len(newS)} subzone)")

# ---- known-answer validation ----
print("re_feasibility top3:", h.nlargest(3,"re_feasibility_score")["parent_subzone_name"].tolist())
print("transit-desert top3:", h.nlargest(3,"mobility_desert_priority")["parent_subzone_name"].tolist())
print("hex8 final:", h.shape, "| subzone final:", sz.shape)
print("DONE")
