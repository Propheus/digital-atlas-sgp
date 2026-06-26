import pandas as pd
ROOT="/home/azureuser/da-sgp/v5"
for scale,key in [("hex8","hex8_id"),("hex9","hex9_id")]:
    m=pd.read_parquet(f"{ROOT}/hex/{scale}_all_features.parquet"); n0=m.shape
    for tag in ["place_composition","huff_capture"]:
        src=pd.read_parquet(f"{ROOT}/hex/{scale}_{tag}.parquet")
        newcols=[c for c in src.columns if c!=key and not c.startswith(("subzone_","parent_"))]
        m=m.drop(columns=[c for c in newcols if c in m.columns])
        m=m.merge(src[[key]+newcols].drop_duplicates(key),on=key,how="left")
    m.to_parquet(f"{ROOT}/hex/{scale}_all_features.parquet",index=False)
    print(f"{scale}: {n0}->{m.shape} | pc_cat_pharmacy_beauty={'pc_cat_pharmacy_beauty' in m.columns} cap_pharmacy_beauty={'cap_pharmacy_beauty' in m.columns} | pc_cat_convenience_sum={int(m['pc_cat_convenience'].sum())} pc_cat_pharmacy_beauty_sum={int(m['pc_cat_pharmacy_beauty'].sum())} pc_cat_health_medical_sum={int(m['pc_cat_health_medical'].sum())}")
