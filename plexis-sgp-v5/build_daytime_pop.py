"""
Plexis SGP v4 — S3 Daytime population (dt_*) per hex8.

Spec: SITE_SELECTION_METRICS.md §S3.

Estimates the headcount present in each hex8 during working hours from the
LTA OD matrix AM window (Apr-2026, monthly weekday totals) anchored on
resident population:

    persons_x_am = (od_x_am / WEEKDAYS) / PT_MODE_SHARE
    dt_pop       = max(pop_resident + persons_in_am - persons_out_am, 0)

Known limitations (documented, not silently absorbed):
  - OD sees transit journeys only; car/walk/private-bus commuters are scaled
    in via PT_MODE_SHARE, a single national constant (no spatial variation).
  - Bus OD is per service leg, so transfers inflate gross in/out counts;
    the inflation largely cancels in the NET term (transfer hex gets +1 in
    and +1 out) but gross dt_inflow/outflow are upper bounds.
  - Dorm workers on private dorm buses are invisible (Tuas-type hexes
    underestimate daytime pop).
  - AM-window-only: midday arrivals (shoppers, lunch crowds) not counted —
    this is a *commuter* daytime population.

Output: hex/hex8_daytime_pop.parquet + hex/daytime_pop_report.json
"""
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).parent

WEEKDAYS = 22          # April 2026 weekday count (OD basis = monthly weekday totals)
PT_MODE_SHARE = 0.62   # assumed peak-period public-transport mode share
                       # (plausible range 0.50-0.75; validator D6 checks rank
                       #  stability across the band)
TRIPS_PER_PERSON_AM = 1.0  # one AM journey per commuter

RATIO_MIN_POP = 50     # dt_ratio is meaningless below this resident base
JOB_CENTER_RATIO = 1.5
BEDROOM_RATIO = 0.67


def main():
    t0 = time.time()
    pop = pd.read_parquet(ROOT / "hex/hex8_population.parquet")
    od = pd.read_parquet(ROOT / "hex/hex8_od_features.parquet")

    df = pop[["hex8_id", "pop_resident"]].merge(od, on="hex8_id", how="left")
    for c in ["od_in_am", "od_out_am", "od_throughput"]:
        df[c] = df[c].fillna(0.0)

    scale = 1.0 / (WEEKDAYS * PT_MODE_SHARE * TRIPS_PER_PERSON_AM)
    df["dt_inflow_am_persons"] = df["od_in_am"] * scale
    df["dt_outflow_am_persons"] = df["od_out_am"] * scale
    df["dt_net_am_persons"] = df["dt_inflow_am_persons"] - df["dt_outflow_am_persons"]

    raw = df["pop_resident"] + df["dt_net_am_persons"]
    df["dt_clipped"] = raw < 0
    df["dt_pop"] = raw.clip(lower=0)

    # transit-observed variant, no mode-share scale-up (for sensitivity work)
    df["dt_pop_unadj"] = (
        df["pop_resident"] + (df["od_in_am"] - df["od_out_am"]) / WEEKDAYS
    ).clip(lower=0)

    has_signal = (df["pop_resident"] >= RATIO_MIN_POP) | (df["od_throughput"] > 0)
    df["dt_ratio"] = np.where(
        has_signal & (df["pop_resident"] >= RATIO_MIN_POP),
        df["dt_pop"] / df["pop_resident"].clip(lower=1),
        np.nan,
    )
    # job-center hexes often have pop < RATIO_MIN_POP but huge inflow: give
    # them a ratio against the floor so dt_class still classifies them
    cbd_like = has_signal & (df["pop_resident"] < RATIO_MIN_POP) & (df["dt_pop"] > 1000)
    df.loc[cbd_like, "dt_ratio"] = df.loc[cbd_like, "dt_pop"] / RATIO_MIN_POP

    conds = [
        ~has_signal,
        df["dt_ratio"].isna(),
        df["dt_ratio"] > JOB_CENTER_RATIO,
        df["dt_ratio"] < BEDROOM_RATIO,
    ]
    df["dt_class"] = np.select(conds, ["no_data", "no_data", "job_center", "bedroom"],
                               default="balanced")

    out_cols = ["hex8_id", "dt_pop", "dt_pop_unadj", "dt_ratio",
                "dt_inflow_am_persons", "dt_outflow_am_persons",
                "dt_net_am_persons", "dt_clipped", "dt_class"]
    out = df[out_cols].copy()
    for c in out.columns:
        if out[c].dtype == float:
            out[c] = out[c].round(2)
    out.to_parquet(ROOT / "hex/hex8_daytime_pop.parquet", index=False)

    rep = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "spec": "SITE_SELECTION_METRICS.md S3",
        "od_basis": "2026-04 monthly weekday totals, AM window",
        "weekdays": WEEKDAYS,
        "pt_mode_share": PT_MODE_SHARE,
        "rows": int(len(out)),
        "hex_with_od": int((df["od_throughput"] > 0).sum()),
        "clipped_hexes": int(df["dt_clipped"].sum()),
        "clipped_persons": float((raw.clip(upper=0)).abs().sum()),
        "national_pop_resident": float(df["pop_resident"].sum()),
        "national_dt_pop": float(df["dt_pop"].sum()),
        "class_counts": df["dt_class"].value_counts().to_dict(),
        "feature_cols": out_cols[1:],
        "wall_clock_s": round(time.time() - t0, 2),
    }
    json.dump(rep, open(ROOT / "hex/daytime_pop_report.json", "w"), indent=2)
    print(json.dumps(rep, indent=2))

    names = pop[["hex8_id", "parent_subzone_name"]]
    show = out.merge(names, on="hex8_id")
    print("\nTop 8 daytime gainers (dt_net_am_persons):")
    print(show.nlargest(8, "dt_net_am_persons")[
        ["hex8_id", "parent_subzone_name", "dt_pop", "dt_net_am_persons", "dt_class"]
    ].to_string(index=False))
    print("\nTop 8 daytime losers:")
    print(show.nsmallest(8, "dt_net_am_persons")[
        ["hex8_id", "parent_subzone_name", "dt_pop", "dt_net_am_persons", "dt_class"]
    ].to_string(index=False))


if __name__ == "__main__":
    main()
