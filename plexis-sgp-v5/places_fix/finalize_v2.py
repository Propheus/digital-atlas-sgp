"""V2 finalize — promote sgp_places_v2 -> canonical, refresh place_composition
(pc_unique_brands etc.) into the masters, bump checkpoint, dump final V2 stats."""
import json, shutil, subprocess, time
from pathlib import Path
import pandas as pd
ROOT = Path("/home/azureuser/da-sgp/v5"); t0 = time.time()

before = pd.read_parquet(ROOT/"places/sgp_places_final.parquet")
v2 = pd.read_parquet(ROOT/"places/sgp_places_v2.parquet")
# promote
shutil.copy2(ROOT/"places/sgp_places_v2.parquet", ROOT/"places/sgp_places_final.parquet")
print(f"[1] promoted sgp_places_v2 -> sgp_places_final ({v2.shape})", flush=True)

# refresh place_composition (pc_unique_brands / pc_magnets reflect new brands+dedup)
r = subprocess.run(["python3","build_place_composition.py"], cwd=ROOT, capture_output=True, text=True)
print("[2] build_place_composition:", "OK" if r.returncode==0 else "FAIL "+r.stderr[-800:], flush=True)
for mp, cp, k in [("hex/hex8_all_features.parquet","hex/hex8_place_composition.parquet","hex8_id"),
                  ("hex/hex9_all_features.parquet","hex/hex9_place_composition.parquet","hex9_id"),
                  ("hex/subzone_all_features.parquet","hex/subzone_place_composition.parquet","subzone_c")]:
    m = pd.read_parquet(ROOT/mp); comp = pd.read_parquet(ROOT/cp)
    cols = [c for c in comp.columns if c != k]
    m = m.drop(columns=[c for c in cols if c in m.columns]).merge(comp, on=k, how="left")
    m.to_parquet(ROOT/mp, index=False)
print(f"[3] pc_ refreshed into masters", flush=True)

cp = {"version":"5.6.1","generated_at":time.strftime("%Y-%m-%dT%H:%M:%S"),
      "change":"places fixes V2: robust dedup + operator + brand resolution (dict+LLM)",
      "detail":{"dedup":f"{int(before.get('is_duplicate',pd.Series(False)).sum())}-> {int(v2['is_duplicate'].sum())} (60m spatial merge)",
                "brand_coverage":f"{int(before['brand_norm'].notna().sum())} -> {int(v2['brand_norm'].notna().sum())}",
                "operator":int((v2['operator']!='').sum()) if 'operator' in v2 else 0,
                "backup":"backups/places_v2_*"}}
json.dump(cp, open(ROOT/"CHECKPOINT_v5.6.1.json","w"), indent=2)
subprocess.run(["python3","build_catalog_json.py"], cwd=ROOT, capture_output=True, text=True)

cov_b = int(before["brand_norm"].notna().sum()); cov_a = int(v2["brand_norm"].notna().sum())
dup_b = int(before.get("is_duplicate", pd.Series(False, index=before.index)).sum()); dup_a = int(v2["is_duplicate"].sum())
print("\n================ PLACES V2 — FINAL STATS ================")
print(f"version -> 5.6.1 · {round(time.time()-t0)}s")
print(f"places: {len(v2):,} canonical {len(v2)-dup_a:,}")
print(f"brand_norm coverage: {cov_b:,} ({100*cov_b/len(v2):.1f}%) -> {cov_a:,} ({100*cov_a/len(v2):.1f}%)")
for c in ["shopping_retail","restaurant","health_medical","cafe_coffee"]:
    sub=v2[v2.plexis_category==c]; br=int(sub.brand_norm.notna().sum())
    print(f"  {c:16s}: {br:,}/{len(sub):,} branded ({100*br/max(len(sub),1):.0f}%)")
print(f"duplicates: {dup_b:,} -> {dup_a:,} ({len(v2)-dup_a:,} canonical)")
print(f"operator/parent_brand: {int((v2['operator']!='').sum()):,}")
print("masters refreshed (pc_unique_brands); CHECKPOINT_v5.6.1")
