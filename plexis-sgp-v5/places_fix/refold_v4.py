import pandas as pd, numpy as np, pathlib, re, json
ROOT=pathlib.Path("/home/azureuser/da-sgp/v5")

# (1) source-fix build_retail_pack_sgp.py: format_fit + footfall must use V4 footfall, not vis_exit
p=ROOT/"build_retail_pack_sgp.py"; s=p.read_text()
s=s.replace(
'''    o["format_fit_score"] = score100(minmax(col(df, "walkability_score"))
                                     * minmax(col(df, "vis_exit_footfall"))
                                     * minmax(col(df, f"colo_fit_{CAT}")).clip(lower=0.05))''',
'''    # V4: footfall component = the decontaminated retail_footfall_score (NOT vis_exit point-source)
    o["format_fit_score"] = score100(minmax(col(df, "walkability_score"))
                                     * minmax(col(df, "retail_footfall_score"))
                                     * minmax(col(df, f"colo_fit_{CAT}")).clip(lower=0.05))''')
s=s.replace(
'''    o["retail_footfall_score"] = score100(0.6 * minmax(col(df, "vis_exit_footfall"))
                                          + 0.4 * minmax(col(df, "dt_pop")))''',
'''    # V4: retail_footfall_score is OWNED upstream by the base feature fix (dt-mostly + hub
    # decile + dead-port NA). Pass it through unchanged so a re-fold never reverts it.
    o["retail_footfall_score"] = col(df, "retail_footfall_score")''')
assert "retail_footfall_score\"))" in s and "vis_exit_footfall" not in s.split("rent_demand_tier")[0].split("format_fit")[1], "retail patch check"
p.write_text(s); print("(1) build_retail_pack_sgp.py source-fixed (format_fit + footfall use V4)")

# (2) re-apply zone-type NA rule to normative adequacy/vuln/crowd scores using V4 zone_type_broad
m=pd.read_parquet(ROOT/"hex/hex8_all_features.parquet")
NA_ZONES={"industrial","airport","nature","islands","future"}   # NOT islands_resort/transport/institutional
namask=m["zone_type_broad"].isin(NA_ZONES)
norm=[c for c in m.columns if c.startswith(("adq_","vulnerability_","access_vuln","crowd_"))
      and pd.api.types.is_numeric_dtype(m[c])]
before=int((namask & m[norm].notna().any(axis=1)).sum())
m.loc[namask, norm]=np.nan
after=int((namask & m[norm].notna().any(axis=1)).sum())
m.to_parquet(ROOT/"hex/hex8_all_features.parquet",index=False)
print(f"(2) zone-NA re-applied to {len(norm)} normative cols | NA-zone cells cleared: {before}->{after} (target 0)")
json.dump({"na_zones":sorted(NA_ZONES),"norm_cols":len(norm),"cleared":before},open(ROOT/"hex/v4_refold_report.json","w"),indent=1)
