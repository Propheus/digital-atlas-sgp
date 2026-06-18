"""
v5.6-full Phase 1 — rebuild every places-derived feature layer from the CLEAN
places and patch into the hex8/hex9/subzone masters (preserving the pack-fold).
Order matters: places-direct builders first, patch, then master-derived.
"""
import subprocess, time
from pathlib import Path
import pandas as pd
ROOT = Path("/home/azureuser/da-sgp/v5")
t0 = time.time()

def run(script):
    r = subprocess.run(["python3", script], cwd=ROOT, capture_output=True, text=True)
    print(f"  {script}: {'OK' if r.returncode==0 else 'FAIL'}", flush=True)
    if r.returncode != 0:
        print(r.stderr[-1500:], flush=True); raise SystemExit(1)

def patch(parq, key):
    """Drop master cols present in `parq` (except key), merge fresh."""
    pq = ROOT / parq
    if not pq.exists(): print(f"   (skip {parq} — not written)", flush=True); return
    fresh = pd.read_parquet(pq)
    cols = [c for c in fresh.columns if c != key]
    mp = ROOT / f"hex/{key.replace('_id','').replace('subzone_c','subzone')}_all_features.parquet"
    # map key -> master path
    mp = {"hex8_id":"hex/hex8_all_features.parquet","hex9_id":"hex/hex9_all_features.parquet",
          "subzone_c":"hex/subzone_all_features.parquet"}[key]
    m = pd.read_parquet(ROOT/mp)
    n0 = m.shape[1]
    m = m.drop(columns=[c for c in cols if c in m.columns]).merge(fresh, on=key, how="left")
    m.to_parquet(ROOT/mp, index=False)
    print(f"   patched {mp.split('/')[-1]}: {n0} -> {m.shape[1]} cols (+{m.shape[1]-n0} net, {len(cols)} from {parq.split('/')[-1]})", flush=True)

print("=== Phase 1a: places-direct builders ===", flush=True)
for s in ["build_huff_capture.py", "build_place_composition_v2.py",
          "build_micrograph_hex_rollup.py", "build_colo_lift.py"]:
    run(s)
print("=== patch places-direct outputs into masters ===", flush=True)
for parq, key in [("hex/hex8_huff_capture.parquet","hex8_id"), ("hex/hex9_huff_capture.parquet","hex9_id"),
                  ("hex/hex8_place_composition_v2.parquet","hex8_id"), ("hex/hex9_place_composition_v2.parquet","hex9_id"), ("hex/subzone_place_composition_v2.parquet","subzone_c"),
                  ("hex/hex8_micrograph_rollup.parquet","hex8_id"), ("hex/hex9_micrograph_rollup.parquet","hex9_id"), ("hex/subzone_micrograph_rollup.parquet","subzone_c"),
                  ("hex/hex8_colo_fit.parquet","hex8_id"), ("hex/hex9_colo_fit.parquet","hex9_id")]:
    patch(parq, key)

print("=== Phase 1b: master-derived builders (need fresh master) ===", flush=True)
for s in ["build_commercial_activity_hex8.py", "build_saturation_gap.py"]:
    run(s)
for parq, key in [("hex/hex8_commercial_activity.parquet","hex8_id"),
                  ("hex/hex8_saturation_gap.parquet","hex8_id"), ("hex/hex9_saturation_gap.parquet","hex9_id"), ("hex/subzone_saturation_gap.parquet","subzone_c")]:
    patch(parq, key)

print("=== Phase 1c: synergy + composites (need cap/gap fresh) ===", flush=True)
for s in ["build_synergy.py", "build_composites.py"]:
    run(s)
for parq, key in [("hex/hex8_synergy.parquet","hex8_id"), ("hex/hex9_synergy.parquet","hex9_id"), ("hex/subzone_synergy.parquet","subzone_c"),
                  ("hex/hex8_composites.parquet","hex8_id"), ("hex/hex9_composites.parquet","hex9_id"), ("hex/subzone_composites.parquet","subzone_c")]:
    patch(parq, key)

m8 = pd.read_parquet(ROOT/"hex/hex8_all_features.parquet")
print(f"\n=== Phase 1 DONE {round(time.time()-t0)}s · hex8 master {m8.shape} ===", flush=True)
for fam in ["cap_","gap_","sat_","ca_","pc2_","mg_","syn_"]:
    print(f"  {fam}: {sum(c.startswith(fam) for c in m8.columns)} cols", flush=True)
