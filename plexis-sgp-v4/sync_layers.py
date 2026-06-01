"""
Sync the reconciled master's changed columns back into the intermediate layer
parquets, so a future build_all_features reproduces the fix (no latent revert).
population parquets are already rebuilt; here we patch composites/rings/synergy/
pop_weighted with the master's corrected values.
"""
import pandas as pd

RING_POP = ["ring1_pop_resident","ring1_pop_nonresident",
            "ring2_pop_resident","ring2_pop_nonresident"]
PW_DENS  = ["pw1_density_pressure","pw2_density_pressure",
            "max1_density_pressure","max2_density_pressure"]

LAYERS = {  # parquet suffix -> (cols to sync, scales)
    "composites":   (["density_pressure"],        ["hex9","hex8","subzone"]),
    "spatial_rings":(RING_POP,                     ["hex9","hex8"]),
    "synergy":      (["syn_density_x_amenities"],  ["hex9","hex8","subzone"]),
    "pop_weighted": (PW_DENS,                      ["hex9","hex8"]),
}
KEY = {"hex9":"hex9_id","hex8":"hex8_id","subzone":"subzone_c"}

for scale in ["hex9","hex8","subzone"]:
    master = pd.read_parquet(f"hex/{scale}_all_features.parquet")
    k = KEY[scale]
    msel = master.set_index(k)
    for layer,(cols,scales) in LAYERS.items():
        if scale not in scales: continue
        path = f"hex/{scale}_{layer}.parquet"
        try:
            lp = pd.read_parquet(path)
        except FileNotFoundError:
            print(f"  skip {path} (absent)"); continue
        lpi = lp.set_index(k)
        synced = []
        for c in cols:
            if c in lpi.columns and c in msel.columns:
                lpi[c] = msel[c].reindex(lpi.index).values; synced.append(c)
        lpi.reset_index().to_parquet(path, index=False)
        print(f"  {path}: synced {synced}")
print("done")
