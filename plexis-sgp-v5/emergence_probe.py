"""Read-only: how do the ~600 hex8 layers combine? What emerges?"""
import numpy as np, pandas as pd, json
from numpy.linalg import svd

H = "/home/azureuser/da-sgp/v4/hex"
df = pd.read_parquet(f"{H}/hex8_all_features.parquet")
lab = df[["hex8_id","parent_pa","parent_subzone_name"]].copy() if "parent_subzone_name" in df else df[["hex8_id","parent_pa"]].copy()

# numeric matrix, active hexes only (some pop or some transit activity)
num = df.select_dtypes(include=[np.number]).copy()
active = (df.get("pop_total_all",0) > 50) | (df.get("od_throughput",0) > 0)
X = num[active].fillna(0.0)
labA = lab[active].reset_index(drop=True)
print(f"active hexes: {active.sum()} / {len(df)}  numeric features: {X.shape[1]}")

# ---------- 1. latent structure (PCA via SVD on z-scored, variance-bearing cols) ----------
sd = X.std(0); keep = sd[sd > 1e-9].index
Z = ((X[keep] - X[keep].mean(0)) / sd[keep]).values
U, S, Vt = svd(Z, full_matrices=False)
var = (S**2) / (S**2).sum()
cum = np.cumsum(var)
n80 = int(np.argmax(cum >= 0.80) + 1); n90 = int(np.argmax(cum >= 0.90) + 1)
print(f"\n=== LATENT STRUCTURE ===  {len(keep)} varying features")
print(f"PC1 {var[0]*100:.1f}%  PC1-3 {cum[2]*100:.1f}%  PC1-5 {cum[4]*100:.1f}%  | 80% needs {n80} PCs, 90% needs {n90}")
for pc in range(5):
    load = pd.Series(Vt[pc], index=keep)
    top = load.reindex(load.abs().sort_values(ascending=False).index)[:8]
    print(f"  PC{pc+1} ({var[pc]*100:.1f}%): " + ", ".join(f"{n}{'+' if v>0 else '-'}" for n,v in top.items()))

# ---------- 2. day-night "breathing": OD inflow vs residential pop ----------
def z(s): s=pd.to_numeric(s,errors="coerce").fillna(0); return (s-s.mean())/(s.std()+1e-9)
d = df[active].copy()
d["breathing"] = z(d["od_in_trips"]) - z(d["pop_resident"])   # >0 job center, <0 bedroom
d["lab"] = labA["parent_pa"].values
print("\n=== DAY-NIGHT BREATHING (od_in vs resident) ===")
print("Top JOB CENTERS (fill by day):")
print(d.nlargest(6,"breathing")[["lab","od_in_trips","pop_resident","commercial_activity_index","od_am_pm_out_ratio"]].to_string(index=False))
print("Top BEDROOM communities (empty by day):")
print(d.nsmallest(6,"breathing")[["lab","od_in_trips","pop_resident","od_out_am","od_am_pm_out_ratio"]].to_string(index=False))

# ---------- 3. coherence vs friction: activity vs supply ----------
d["act_minus_supply"] = z(d["commercial_activity_index"]) - z(d["commercial_intensity"])
print("\n=== ACTIVITY > SUPPLY (under-built vibrancy / hidden demand) ===")
print(d.nlargest(5,"act_minus_supply")[["lab","commercial_activity_index","commercial_intensity","od_throughput"]].to_string(index=False))
print("=== SUPPLY > ACTIVITY (over-built / quiet) ===")
print(d.nsmallest(5,"act_minus_supply")[["lab","commercial_activity_index","commercial_intensity","od_throughput"]].to_string(index=False))

# ---------- 4. persona-environment coupling ----------
cc = {}
for a,b in [("nvp_affluence_idx","hdb_resale_4r_median_psm"),
            ("nvp_affluence_idx","commercial_activity_index"),
            ("nvp_pct_age_55plus","od_throughput"),
            ("nvp_occ_manual","pop_dorm"),
            ("nvp_pct_univ","nl_2024")]:
    if a in d and b in d:
        m=d[[a,b]].dropna()
        if len(m)>20: cc[f"{a} ~ {b}"]=round(float(np.corrcoef(m[a],m[b])[0,1]),3)
print("\n=== PERSONA <-> ENVIRONMENT correlations ===")
for k,v in cc.items(): print(f"  {v:+.3f}  {k}")

# ---------- 5. dorm-worker service gap ----------
if "pop_dorm" in d:
    dorm = d[d["pop_dorm"]>500]
    print(f"\n=== DORM HEXES (n={len(dorm)}, pop_dorm>500) ===")
    print(f"  mean commercial_activity_index: dorm {dorm['commercial_activity_index'].mean():.3f} vs all {d['commercial_activity_index'].mean():.3f}")
    print(f"  mean od_throughput: dorm {dorm['od_throughput'].mean():,.0f} vs all {d['od_throughput'].mean():,.0f}")
    print(f"  mean walkability_score: dorm {dorm['walkability_score'].mean():.3f} vs all {d['walkability_score'].mean():.3f}")
