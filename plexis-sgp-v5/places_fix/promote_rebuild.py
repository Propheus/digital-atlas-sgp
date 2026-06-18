"""
Promote cleaned places to canonical + rebuild the places-derived hex features
(nous #4) — bounded & fold-preserving. Backup already taken.
  1 promote sgp_places_cleaned -> sgp_places_final
  2 rebuild pc_cat_* (26 cats) via build_place_composition  [CATS pre-patched to 26]
  3 patch pc_* into hex9/hex8/subzone masters (preserve the 840 pack-fold)
  4 refresh pop_weighted (pw1/pw2/max1/max2) from the patched master, patch back
  5 catalog + manifest -> v5.6.0 ; dump stats
"""
import json, shutil, subprocess, time
from pathlib import Path
import pandas as pd
ROOT = Path("/home/azureuser/da-sgp/v5")
t0 = time.time()

# ---- 1. promote ----
src = ROOT / "places/sgp_places_cleaned.parquet"
dst = ROOT / "places/sgp_places_final.parquet"
before_master_pc = [c for c in pd.read_parquet(ROOT/"hex/hex8_all_features.parquet").columns if c.startswith("pc_")]
shutil.copy2(src, dst)
print(f"[1] promoted cleaned -> sgp_places_final.parquet ({pd.read_parquet(dst).shape})", flush=True)

# ---- 2. rebuild composition (CATS already patched to 26 in the script) ----
r = subprocess.run(["python3", "build_place_composition.py"], cwd=ROOT, capture_output=True, text=True)
print("[2] build_place_composition:", "OK" if r.returncode == 0 else "FAIL\n"+r.stderr[-1500:], flush=True)
assert r.returncode == 0

# ---- 3. patch pc_* into the 3 masters ----
def patch_pc(master_path, comp_path, key):
    m = pd.read_parquet(master_path)
    comp = pd.read_parquet(comp_path)
    pc_cols = [c for c in comp.columns if c != key]
    m = m.drop(columns=[c for c in pc_cols if c in m.columns])         # drop stale pc_*
    m = m.merge(comp, on=key, how="left")
    m.to_parquet(master_path, index=False)
    return m.shape, len([c for c in pc_cols if c.startswith("pc_cat_")])

for mp, cp, k in [("hex/hex8_all_features.parquet","hex/hex8_place_composition.parquet","hex8_id"),
                  ("hex/hex9_all_features.parquet","hex/hex9_place_composition.parquet","hex9_id"),
                  ("hex/subzone_all_features.parquet","hex/subzone_place_composition.parquet","subzone_c")]:
    sh, ncat = patch_pc(ROOT/mp, ROOT/cp, k)
    print(f"[3] patched {mp}: {sh}  ({ncat} pc_cat cols)", flush=True)

# ---- 4. refresh pop_weighted from patched master, patch pw/max back ----
r = subprocess.run(["python3", "build_pop_weighted.py"], cwd=ROOT, capture_output=True, text=True)
print("[4] build_pop_weighted:", "OK" if r.returncode == 0 else "FAIL\n"+r.stderr[-1200:], flush=True)
if r.returncode == 0:
    for mp, pw, k in [("hex/hex8_all_features.parquet","hex/hex8_pop_weighted.parquet","hex8_id"),
                      ("hex/hex9_all_features.parquet","hex/hex9_pop_weighted.parquet","hex9_id")]:
        m = pd.read_parquet(ROOT/mp); pwdf = pd.read_parquet(ROOT/pw)
        cols = [c for c in pwdf.columns if c != k]
        m = m.drop(columns=[c for c in cols if c in m.columns]).merge(pwdf, on=k, how="left")
        m.to_parquet(ROOT/mp, index=False)
        print(f"[4] patched pop_weighted into {mp}: {m.shape}", flush=True)

# ---- 5. catalog + manifest + checkpoint ----
subprocess.run(["python3", "build_catalog_json.py"], cwd=ROOT, capture_output=True, text=True)
mani = json.load(open(ROOT/"catalog/atlas_manifest.json"))
cp56 = {"version": "5.6.0", "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "change": "places cleaned + promoted; pc_cat_ (24->26) + pop_weighted rebuilt from clean places",
        "detail": {"places": "sgp_places_cleaned -> sgp_places_final (35 cols, 8 new flags)",
                   "new_categories": ["financial_services", "automated_kiosk"],
                   "rebuilt": ["pc_cat_*", "pc_total/diversity/dominant", "pw1/pw2/max1/max2 pop_weighted"],
                   "backup": "backups/places_promote_*",
                   "not_refit": ["cap_/gap_ (saturation stage 14)", "domain packs", "plexis-e1/p1 embeddings"]}}
json.dump(cp56, open(ROOT/"CHECKPOINT_v5.6.0.json", "w"), indent=2)
subprocess.run(["python3", "build_catalog_json.py"], cwd=ROOT, capture_output=True, text=True)

# ---- stats ----
m8 = pd.read_parquet(ROOT/"hex/hex8_all_features.parquet")
after_pc = [c for c in m8.columns if c.startswith("pc_")]
mani2 = json.load(open(ROOT/"catalog/atlas_manifest.json"))
print("\n================ PROMOTE + REBUILD — STATS ================")
print(f"version -> {mani2['version']}  ·  {round(time.time()-t0)}s")
print(f"hex8 master: {m8.shape}  (was 1191x840)")
print(f"pc_ cols in master: {len(before_master_pc)} -> {len(after_pc)}  (+{len(after_pc)-len(before_master_pc)})")
print(f"new pc_cat cols: pc_cat_financial_services={int(m8.get('pc_cat_financial_services',pd.Series([0])).sum())}, "
      f"pc_cat_automated_kiosk={int(m8.get('pc_cat_automated_kiosk',pd.Series([0])).sum())}")
print(f"pc_cat_convenience total now: {int(m8.get('pc_cat_convenience',pd.Series([0])).sum())} (was inflated by ATMs)")
print(f"pc_cat_business_office total now: {int(m8.get('pc_cat_business_office',pd.Series([0])).sum())} (banks/insurance moved out)")
print(f"manifest hex8 shape: {mani2['master_bundles']['hex8_all_features']['shape']}")
print("places_final is now the CLEANED table; pc_cat_/pop_weighted rebuilt from it.")
print("NOT re-fit (flagged): cap_/gap_ saturation · domain packs · plexis-e1/p1 embeddings")
