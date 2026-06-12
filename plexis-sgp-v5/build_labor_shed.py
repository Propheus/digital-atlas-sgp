"""
Plexis SGP v4 — S5 Labor-shed & jobs-reach (labor_*) per hex8.

Spec: SITE_SELECTION_METRICS.md §S5. Reuses the S2b cached transit minute
matrix (hex8 origins x hex9, weekday-AM, 50-min horizon).

  labor_pool_45m(h8)  = sum working-age pop (pop_15_64) of hex9s with
                        t(h8 -> hex9) <= 45 min     [30-min variant too]
  jobs_reach_45m(h8)  = sum job-proxy of hex9s within 45 min
  labor_accessibility_pct = labor_pool_45m / national working-age pop

Approximations (documented):
  - Direction symmetry: matrix is h8->h9; workers travel h9->h8. Bus/MRT run
    both directions at similar AM headways, so t is treated as symmetric.
  - Jobs proxy v0 = places count of business_office + industrial_mfg +
    services per hex9, scaled to 2.4M jobs. Refine with ACRA biz_live_count
    when S4 completes (geocode in progress).

Output: hex/hex8_labor_shed.parquet + hex/labor_shed_report.json
"""
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).parent
JOB_CATS = ["business_office", "industrial_mfg", "services"]
NATIONAL_JOBS = 2_400_000.0


def main():
    t0 = time.time()
    npz = np.load(ROOT / "hex/hex8_hex9_transit_min.npz", allow_pickle=True)
    tm = npz["minutes"]                       # (1191, 7318)
    hex8_ids = npz["hex8_id"]
    hex9_ids = npz["hex9_id"]

    h9 = pd.read_parquet(ROOT / "hex/hex9_population.parquet").set_index("hex9_id")
    h9 = h9.reindex(hex9_ids)
    work = h9["pop_15_64"].fillna(0).to_numpy()

    pl = pd.read_parquet(ROOT / "places/sgp_places_final.parquet",
                         columns=["hex9_id", "plexis_category"])
    jobs = pl[pl["plexis_category"].isin(JOB_CATS)].groupby("hex9_id").size()
    jobs = jobs.reindex(hex9_ids).fillna(0).to_numpy(dtype=float)
    jobs = jobs / jobs.sum() * NATIONAL_JOBS

    m30, m45 = tm <= 30, tm <= 45
    out = pd.DataFrame({
        "hex8_id": hex8_ids,
        "labor_pool_30m": (m30 @ work).round(0),
        "labor_pool_45m": (m45 @ work).round(0),
        "jobs_reach_45m": (m45 @ jobs).round(0),
        "labor_accessibility_pct": ((m45 @ work) / work.sum()).round(4),
    })
    out["labor_jobs_balance_45m"] = (
        out["jobs_reach_45m"] / out["labor_pool_45m"].clip(lower=1)).round(3)
    out.to_parquet(ROOT / "hex/hex8_labor_shed.parquet", index=False)

    rep = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "spec": "SITE_SELECTION_METRICS.md S5",
        "national_working_age": float(work.sum()),
        "jobs_proxy": f"places {JOB_CATS} scaled to {NATIONAL_JOBS:,.0f}",
        "median_labor_pool_45m": float(out["labor_pool_45m"].median()),
        "max_labor_pool_45m": float(out["labor_pool_45m"].max()),
        "wall_clock_s": round(time.time() - t0, 2),
    }
    json.dump(rep, open(ROOT / "hex/labor_shed_report.json", "w"), indent=2)
    print(json.dumps(rep, indent=2))


if __name__ == "__main__":
    main()
