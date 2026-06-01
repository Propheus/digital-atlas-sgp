"""
Plexis SGP v4 — Commercial Activity Index at hex8 (standalone layer).

A footfall-weighted economic-activity score distinct from the existing
`commercial_intensity` composite (which is supply/morphology only: place mix +
night-light + land-use). This index adds DEMAND signals — transit taps and OD
throughput — so it captures *where activity actually happens*, not just where
commercial supply sits.

Components (each min-max normalized on 1-99 pctile, then averaged):
  ca_nl        night-light intensity            nl_2024
  ca_spend     commercial spend proxy           nl_commercial_indicator
  ca_taps      transit boardings/alightings     daily_bus_taps + daily_train_taps
  ca_places    commercial place density         office+retail+f&b+services counts
  ca_footfall  OD journey throughput  (NEW)     od_throughput (in+out trips)

Output: hex/hex8_commercial_activity.parquet  -> merged into master.
"""
import json, time
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).parent


def minmax(s):
    s = pd.to_numeric(pd.Series(s), errors="coerce").fillna(0).astype(float)
    lo, hi = s.quantile(0.01), s.quantile(0.99)
    if hi <= lo:
        return pd.Series(np.zeros(len(s)), index=s.index)
    return ((s - lo) / (hi - lo)).clip(0, 1)


def main():
    t0 = time.time()
    df = pd.read_parquet(ROOT / "hex/hex8_all_features.parquet")
    od = pd.read_parquet(ROOT / "hex/hex8_od_features.parquet")[["hex8_id", "od_throughput"]]
    df = df.merge(od, on="hex8_id", how="left")
    df["od_throughput"] = df["od_throughput"].fillna(0)

    def col(c):
        return df[c].fillna(0) if c in df.columns else pd.Series(0.0, index=df.index)

    places = (col("pc_cat_business_office") + col("pc_cat_shopping_retail")
              + col("pc_cat_restaurant") + col("pc_cat_cafe_coffee") + col("pc_cat_services"))
    taps = col("daily_bus_taps") + col("daily_train_taps")

    out = pd.DataFrame({"hex8_id": df["hex8_id"]})
    out["ca_nl"]       = minmax(col("nl_2024")).round(4)
    out["ca_spend"]    = minmax(col("nl_commercial_indicator")).round(4)
    out["ca_taps"]     = minmax(taps).round(4)
    out["ca_places"]   = minmax(places).round(4)
    out["ca_footfall"] = minmax(col("od_throughput")).round(4)
    parts = ["ca_nl", "ca_spend", "ca_taps", "ca_places", "ca_footfall"]
    out["commercial_activity_index"] = out[parts].mean(axis=1).round(4)

    # distinctness vs existing commercial_intensity
    corr = float(np.corrcoef(out["commercial_activity_index"].values,
                             df["commercial_intensity"].fillna(0).values)[0, 1]) \
        if "commercial_intensity" in df.columns else None
    out.to_parquet(ROOT / "hex/hex8_commercial_activity.parquet", index=False)

    rep = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "components": parts,
        "corr_with_commercial_intensity": round(corr, 4) if corr is not None else None,
        "index_mean": round(float(out["commercial_activity_index"].mean()), 4),
        "index_p90": round(float(out["commercial_activity_index"].quantile(0.90)), 4),
        "hex8_nonzero": int((out["commercial_activity_index"] > 0).sum()),
        "wall_clock_s": round(time.time() - t0, 2),
    }
    json.dump(rep, open(ROOT / "hex/commercial_activity_report.json", "w"), indent=2)
    print(json.dumps(rep, indent=2))
    print("\nTop hex8 by commercial_activity_index:")
    top = out.nlargest(6, "commercial_activity_index")
    print(top.to_string(index=False))


if __name__ == "__main__":
    main()
