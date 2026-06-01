"""
Plexis SGP v4 — Stage 16: per-hex influence summary.

Real OD-flow data isn't available, so influence is approximated as the
*outbound gravity-influence sum* + *inbound gravity-influence sum* per hex.

For each ordered pair (i, j), influence(i→j) = vibrancy(j) · exp(-d_ij / L)
  outbound_influence(i)  = Σ_j j≠i  influence(i→j)         (how much pull i exerts on others)
  inbound_influence(i)   = Σ_j j≠i  influence(j→i)         (how much pull i receives from others)
  net_influence(i)       = outbound - inbound (normalized)

Computed on hex9 only. Heavy compute (~7K × 7K × 8 bytes = 400MB matrix).

Outputs:
  hex/hex9_influence.parquet
"""
import json, time
from pathlib import Path
import numpy as np
import pandas as pd
import geopandas as gpd
import h3

ROOT = Path(__file__).parent

L = 3000.0  # decay scale (m) — interaction "feel-able" range


def main():
    t0 = time.time()
    print("Loading...")
    h9_uni = pd.read_parquet(ROOT / "hex/hex9_universe.parquet")
    h9 = pd.read_parquet(ROOT / "hex/hex9_all_features.parquet")

    # Get vibrancy as the "attraction" score; fallback to pc_total if missing
    if "vibrancy_index" in h9.columns:
        attr = h9["vibrancy_index"].fillna(0).values.astype(float)
    elif "pc_total" in h9.columns:
        attr = h9["pc_total"].fillna(0).values.astype(float)
        if attr.max() > 0: attr = attr / attr.max()
    else:
        raise SystemExit("Neither vibrancy_index nor pc_total found")
    print(f"  attraction values: shape {attr.shape}, max {attr.max():.3f}")

    # Centroids in EPSG:3414
    cents = np.array([h3.cell_to_latlng(c) for c in h9_uni["hex9_id"]])
    g = gpd.GeoDataFrame(geometry=gpd.points_from_xy(cents[:, 1], cents[:, 0]),
                         crs="EPSG:4326").to_crs(3414)
    xy = np.column_stack([g.geometry.x.values, g.geometry.y.values])
    n = len(xy)
    print(f"  hex9: {n}")

    # Compute pairwise distances + decays in chunks (memory safe)
    print("Computing pairwise gravity-decay matrix...")
    out_inf = np.zeros(n, dtype=np.float64)
    in_inf  = np.zeros(n, dtype=np.float64)
    CHUNK = 256
    for s in range(0, n, CHUNK):
        e = min(s + CHUNK, n)
        dx = xy[s:e, 0:1] - xy[:, 0]
        dy = xy[s:e, 1:2] - xy[:, 1]
        d = np.sqrt(dx * dx + dy * dy)
        decay = np.exp(-d / L)
        np.fill_diagonal(decay[:, s:e], 0)  # i→i excluded
        # outbound_inf[i] = Σ_j attr[j] * decay[i,j]
        out_inf[s:e] = (decay * attr[None, :]).sum(axis=1)
        # inbound_inf[j] = Σ_i attr[i] * decay[i,j] — same matrix, swap weights
        in_inf[s:e]  = (decay * attr[s:e][:, None]).sum(axis=1)

    # Normalize 0..1
    out_n = (out_inf - out_inf.min()) / (out_inf.max() - out_inf.min() + 1e-9)
    in_n  = (in_inf  - in_inf.min())  / (in_inf.max()  - in_inf.min()  + 1e-9)
    net = (out_n - in_n)
    net = (net - net.min()) / (net.max() - net.min() + 1e-9)

    out = pd.DataFrame({
        "hex9_id": h9["hex9_id"].values,
        "outbound_influence": out_n.round(3),
        "inbound_influence":  in_n.round(3),
        "net_influence":      net.round(3),
    })
    out.to_parquet(ROOT / "hex/hex9_influence.parquet", index=False)
    print(f"  hex9_influence: {out.shape}")
    print(f"  outbound: median {np.median(out_n):.3f}, p90 {np.quantile(out_n, 0.9):.3f}")
    print(f"  inbound:  median {np.median(in_n):.3f},  p90 {np.quantile(in_n,  0.9):.3f}")

    summary = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "wall_clock_s": round(time.time() - t0, 2),
        "decay_L_m": L,
        "attraction": "vibrancy_index" if "vibrancy_index" in h9.columns else "pc_total",
        "shape": list(out.shape),
    }
    with open(ROOT / "hex/influence_report.json", "w") as f:
        json.dump(summary, f, indent=2)


if __name__ == "__main__":
    main()
