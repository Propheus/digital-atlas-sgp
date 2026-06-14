"""Shared helpers for domain-pack builders (Phase 1). Real-column reconciled."""
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).parent
MASTER = ROOT / "hex/hex8_all_features.parquet"
PRIM = ROOT / "hex/hex8_domain_primitives.parquet"
ADMIN = ["parent_subzone", "parent_pa", "parent_region", "zone_type_broad"]


def load():
    """master joined with primitives on hex8_id; admin cols carried."""
    m = pd.read_parquet(MASTER)
    p = pd.read_parquet(PRIM)
    df = m.merge(p, on="hex8_id", how="left", suffixes=("", "_prim"))
    return df


def col(df, name, default=0.0):
    if name in df.columns:
        return pd.to_numeric(df[name], errors="coerce").fillna(default)
    return pd.Series(default, index=df.index, dtype=float)


def minmax(s):
    s = pd.Series(s, dtype=float).fillna(0)
    lo, hi = s.quantile(0.01), s.quantile(0.99)
    if hi <= lo:
        return pd.Series(np.zeros(len(s)), index=s.index)
    return ((s - lo) / (hi - lo)).clip(0, 1)


def inv_dist(s, half=400):
    return np.exp(-pd.Series(s, dtype=float).fillna(9999) / half).clip(0, 1)


def score100(x):
    return (minmax(x) * 100).round(0).astype(int)


def save(df, out_cols, name):
    """write hex8_<name>_pack.parquet (key + admin + new cols) + report."""
    import json
    import time
    keep = ["hex8_id"] + [c for c in ADMIN if c in df.columns] + out_cols
    sub = df[keep].copy()
    out = ROOT / f"hex/hex8_{name}_pack.parquet"
    sub.to_parquet(out, index=False)
    rep = {"pack": name, "n_hex": len(sub), "cols": out_cols,
           "scores": {c: {"min": int(sub[c].min()), "max": int(sub[c].max()),
                          "nonzero_pct": round((sub[c] != 0).mean() * 100, 1)}
                      for c in out_cols if c.endswith("_score") or c.endswith("_tier")}}
    json.dump(rep, open(ROOT / f"hex/{name}_pack_report.json", "w"), indent=1)
    print(f"hex8_{name}_pack: {sub.shape} | scores: "
          + ", ".join(f"{c}({rep['scores'][c]['nonzero_pct']:.0f}%nz)"
                      for c in rep["scores"]))
    return sub
