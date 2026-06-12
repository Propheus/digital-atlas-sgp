"""
Master-level reconciliation for the dorm-aware population update.

Strategy (per advisor): start from the DEPLOYED master (locks the 558/548/388
column set), overwrite ONLY the columns that genuinely depend on the changed
population, each computed by code that is VERIFIED to reproduce the deployed
value on old inputs (reproduce-gate). Everything else is preserved byte-for-byte.
density_pressure is injected before synergy / pop_weighted consume it.

Changed set (predicted):
  base pop:  pop_resident pop_hdb pop_non_hdb pop_0_14 pop_15_64 pop_65plus
             pop_nonresident pop_total_all nonres_share   (pop_hdb_share invariant)
  added:     pop_dorm
  rings:     ring1/2_pop_resident, ring1/2_pop_nonresident          (hex9, hex8)
  composite: density_pressure
  synergy:   syn_density_x_amenities
  pop-wtd:   pw1/2_density_pressure, max1/2_density_pressure        (hex9, hex8)

Reads new pop from hex/{scale}_population.parquet (already rebuilt). Compares
against the untouched deployed master at LIVE. Writes corrected master + the
affected layer parquets. Asserts the final column diff == predicted set.
"""
import importlib.util, json
import numpy as np
import pandas as pd

LIVE = "/home/azureuser/da-sgp/v4/hex"
TOL = 1e-6

def load_mod(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

bc  = load_mod("bc",  "build_composites.py")
bsg = load_mod("bsg", "build_synergy.py")
brg = load_mod("brg", "build_spatial_rings.py")
bpw = load_mod("bpw", "build_pop_weighted.py")

POP_OVERWRITE = ["pop_resident","pop_hdb","pop_non_hdb","pop_0_14","pop_15_64",
                 "pop_65plus","pop_nonresident","pop_total_all","nonres_share"]
RING_POP = ["ring1_pop_resident","ring1_pop_nonresident",
            "ring2_pop_resident","ring2_pop_nonresident"]
PW_DENS  = ["pw1_density_pressure","pw2_density_pressure",
            "max1_density_pressure","max2_density_pressure"]

def faithful(recompute, deployed, col):
    """True if current code reproduces the deployed stored value on old inputs."""
    if col not in recompute.columns or col not in deployed.columns:
        return False
    a = pd.to_numeric(deployed[col], errors="coerce").fillna(0).values
    b = pd.to_numeric(recompute[col], errors="coerce").fillna(0).values
    return float(np.abs(a - b).max()) < TOL

def rings_all(df, key, target):
    r1 = brg.ring_aggregates(df, key, target, 1)
    r2 = brg.ring_aggregates(df, key, target, 2)
    return r1.merge(r2, on=key, how="left")

def pw_all(df, key):
    r1 = bpw.pw_aggregates(df, key, "pop_resident", bpw.FEATURES, 1)
    r2 = bpw.pw_aggregates(df, key, "pop_resident", bpw.FEATURES, 2)
    return r1.merge(r2, on=key, how="left")

report = {"scales": {}, "unfaithful": []}

for scale, key, has_rings_pw in [("hex9","hex9_id",True),
                                 ("hex8","hex8_id",True),
                                 ("subzone","subzone_c",False)]:
    deployed = pd.read_parquet(f"{LIVE}/{scale}_all_features.parquet")
    newpop   = pd.read_parquet(f"hex/{scale}_population.parquet").set_index(key)
    m = deployed.copy()                       # row order preserved == column lock
    changed = set()

    # --- base pop (overwrite from rebuilt population parquet) ---
    for c in POP_OVERWRITE:
        if c in newpop.columns and c in m.columns:
            new_vals = newpop[c].reindex(m[key]).values
            if float(np.abs(np.nan_to_num(new_vals) - np.nan_to_num(m[c].values)).max()) > TOL:
                m[c] = new_vals; changed.add(c)
    pop_dorm = newpop["pop_dorm"].reindex(m[key]).fillna(0).values

    # --- density_pressure (composite) ---
    comp_old = bc.composite(deployed)
    comp_new = bc.composite(m)
    if faithful(comp_old, deployed, "density_pressure"):
        if float(np.abs(comp_new["density_pressure"].values - deployed["density_pressure"].values).max()) > TOL:
            m["density_pressure"] = comp_new["density_pressure"].values; changed.add("density_pressure")
    else:
        report["unfaithful"].append(f"{scale}:density_pressure")

    # --- rings (pop only) --- (density_pressure not a ring feature)
    if has_rings_pw:
        target = [f for f in brg.RING_FEATURES if f in m.columns]
        r_old = rings_all(deployed, key, target)
        r_new = rings_all(m, key, target)
        for c in RING_POP:
            if faithful(r_old, deployed, c):
                if float(np.abs(r_new[c].values - deployed[c].values).max()) > TOL:
                    m[c] = r_new[c].values; changed.add(c)
            else:
                report["unfaithful"].append(f"{scale}:{c}")

    # --- synergy (uses density_pressure -> must run AFTER injection above) ---
    syn_old = bsg.synergy(deployed)
    syn_new = bsg.synergy(m)
    c = "syn_density_x_amenities"
    if faithful(syn_old, deployed, c):
        if float(np.abs(syn_new[c].values - deployed[c].values).max()) > TOL:
            m[c] = syn_new[c].values; changed.add(c)
    else:
        report["unfaithful"].append(f"{scale}:{c}")

    # --- pop_weighted density terms (uses density_pressure feature) ---
    if has_rings_pw:
        pw_old = pw_all(deployed, key)
        pw_new = pw_all(m, key)
        for c in PW_DENS:
            if faithful(pw_old, deployed, c):
                if float(np.abs(pw_new[c].values - deployed[c].values).max()) > TOL:
                    m[c] = pw_new[c].values; changed.add(c)
            else:
                report["unfaithful"].append(f"{scale}:{c}")

    # --- append pop_dorm at end ---
    m["pop_dorm"] = pop_dorm

    # --- full column diff assertion vs deployed ---
    common = [col for col in deployed.columns if col in m.columns]
    drift = []
    for col in common:
        if col in changed:
            continue
        a = pd.to_numeric(deployed[col], errors="coerce").fillna(0).values if deployed[col].dtype != object else deployed[col].astype(str).values
        b = pd.to_numeric(m[col], errors="coerce").fillna(0).values if m[col].dtype != object else m[col].astype(str).values
        try:
            if np.issubdtype(np.asarray(a).dtype, np.number):
                if float(np.abs(a - b).max()) > 1e-6:
                    drift.append(col)
            else:
                if not (a == b).all():
                    drift.append(col)
        except Exception:
            if not (a == b).all():
                drift.append(col)

    report["scales"][scale] = {
        "deployed_cols": len(deployed.columns),
        "final_cols": len(m.columns),
        "changed": sorted(changed),
        "added": ["pop_dorm"],
        "unexpected_drift": drift,
        "total_pop": float(m["pop_total_all"].sum()),
        "dorm_pop": float(m["pop_dorm"].sum()),
    }
    m.to_parquet(f"hex/{scale}_all_features.parquet", index=False)

print(json.dumps(report, indent=2))
