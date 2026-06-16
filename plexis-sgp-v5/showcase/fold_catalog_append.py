"""Append the 39 (+subzone) pack catalog rows. hex8(840)+subzone(428) already on disk."""
import pandas as pd
from pathlib import Path
V5 = Path("/home/azureuser/da-sgp/v5")
# load DESC, PACKS, catalog_rows from the original module's defs (before HEX8 section)
exec(compile(open(V5/"showcase/fold_packs_into_master.py").read().split("# ---- HEX8")[0],
             "defs", "exec"), globals())
# populate PACK_OF from the pack files (this was the missing piece)
for pk in PACKS:
    for c in pd.read_parquet(V5/f"hex/hex8_{pk}_pack.parquet").columns:
        if c in DESC: PACK_OF[c] = pk

h  = pd.read_parquet(V5/"hex/hex8_all_features.parquet")
sz = pd.read_parquet(V5/"hex/subzone_all_features.parquet")
fc = pd.read_parquet(V5/"catalog/feature_catalog.parquet")
addedH  = [c for c in DESC if c in h.columns]
addedSZ = [c for c in DESC if c in sz.columns]
newH = catalog_rows(h,  addedH,  "hex/hex8_all_features.parquet", "hex8")
newS = catalog_rows(sz, addedSZ, "hex/subzone_all_features.parquet", "subzone")
fc2 = pd.concat([fc, newH, newS], ignore_index=True)
fc2.to_parquet(V5/"catalog/feature_catalog.parquet", index=False)
print(f"feature_catalog: {len(fc)} -> {len(fc2)} (+{len(newH)} hex8, +{len(newS)} subzone)")
print("hex8 pack rows now:", int((fc2.column=='retail_whitespace_score').sum()))
