"""
Hex v10 — final feature table: merged v10 base + rings.

Inputs:
    data/hex_v10/hex_features_v10_merged.parquet  (base + place composition + micrograph)
    data/hex_v10/hex_rings.parquet                (k=1/k=2 neighbor aggregates)

Output:
    data/hex_v10/hex_features_v10.parquet         (full raw feature table)
    data/hex_v10/hex_features_v10_catalog.md      (pillar-organized catalog)

Plus a final broadcast scan — any feature with zero within-subzone variance that
isn't in the intentional bookkeeping set is flagged loudly.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
V10 = ROOT / "data" / "hex_v10"
MERGED = V10 / "hex_features_v10_merged.parquet"
RINGS = V10 / "hex_rings.parquet"
OUT = V10 / "hex_features_v10.parquet"
CATALOG = V10 / "hex_features_v10_catalog.md"

# Bookkeeping columns — kept in table for audit/debugging but not features
# (should be dropped at training time).
BOOKKEEPING = {
    "subzone_pop_total",
    "subzone_res_floor_area",
    "residential_floor_weight",
    "hex_area_sqm",  # constant up to rounding
}

IDENTITY = {
    "hex_id", "lat", "lng", "area_km2",
    "parent_subzone", "parent_subzone_name", "parent_pa", "parent_region",
}

PILLAR_RULES = [
    ("neighbor_nbr1_mean", lambda c: c.startswith("nbr1_mean_")),
    ("neighbor_nbr1_max",  lambda c: c.startswith("nbr1_max_")),
    ("neighbor_nbr2_mean", lambda c: c.startswith("nbr2_mean_")),
    ("neighbor_contrast",  lambda c: c.startswith("contrast_")),
    ("neighbor_rank",      lambda c: c.startswith("rank_")),
    ("identity",           lambda c: c in IDENTITY),
    ("bookkeeping",        lambda c: c in BOOKKEEPING),
    ("buildings",          lambda c: c.startswith("bldg_") or c in {"avg_floors", "max_floors", "avg_height", "max_height", "hdb_blocks", "total_floor_area_sqm", "residential_floor_area_sqm", "commercial_floor_area_sqm"}),
    ("population",         lambda c: c in {"population", "children_count", "elderly_count", "working_age_count", "walking_dependent_count"}),
    ("land_use",           lambda c: c.startswith("lu_") or c == "avg_gpr"),
    ("transit_points",     lambda c: c in {"mrt_stations", "lrt_stations", "bus_stops", "mrt_daily_taps", "bus_daily_taps", "transit_daily_taps", "mrt_hex_rings", "mrt_ring2"}),
    ("amenities_points",   lambda c: c in {"hawker_centres", "chas_clinics", "preschools_gov", "hotels", "tourist_attractions", "sfa_eating_establishments", "silver_zones", "school_zones", "park_facilities"}),
    ("walkability_v9",     lambda c: "walkability" in c or c == "amenity_types_nearby" or c.startswith("walk_") or (c.startswith("dist_") and c.endswith("_m"))),
    ("roads_signals_v9",   lambda c: c.startswith("road_cat_") or c.startswith("sig_") or c.startswith("ped_") or c == "bicycle_signal" or c.startswith("hex_") or c == "dist_nearest_mrt_m"),
    ("v9_rings",           lambda c: c.endswith("_ring1") or c.endswith("_ring2")),
    ("place_composition",  lambda c: c.startswith("pc_")),
    ("micrograph",         lambda c: c.startswith("mg_")),
]


def assign_pillar(col: str) -> str:
    for label, rule in PILLAR_RULES:
        if rule(col):
            return label
    return "other"


def main() -> None:
    merged = pd.read_parquet(MERGED)
    rings = pd.read_parquet(RINGS)
    final = merged.merge(rings, on="hex_id", how="left")
    assert len(final) == len(merged), "row count mismatch"
    print(f"Final shape: {final.shape}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    final.to_parquet(OUT, index=False)
    print(f"Wrote {OUT}")

    # Broadcast audit
    feat_cols = [c for c in final.columns if c not in IDENTITY and c not in BOOKKEEPING and final[c].dtype != object]
    broadcast = []
    for c in feat_cols:
        col_std = final[c].std(ddof=0)
        if not np.isfinite(col_std) or col_std < 1e-9:
            continue
        s = final.groupby("parent_subzone")[c].std(ddof=0)
        sizes = final.groupby("parent_subzone").size()
        s = s[sizes > 1]
        if len(s) == 0:
            continue
        max_within = s.max(skipna=True)
        if max_within is not None and max_within < 1e-9:
            broadcast.append(c)
    print(f"Unintentional subzone-broadcast feature columns: {len(broadcast)}")
    for c in broadcast:
        print(f"  {c}")

    # Pillars
    pillars: dict[str, list[str]] = {}
    for c in final.columns:
        p = assign_pillar(c)
        pillars.setdefault(p, []).append(c)
    print()
    print("Pillar breakdown:")
    for p, cols in sorted(pillars.items(), key=lambda kv: -len(kv[1])):
        print(f"  {p:24s} {len(cols):4d}")

    # Catalog
    lines: list[str] = []
    lines.append("# Hex Features v10 — Catalog")
    lines.append("")
    lines.append(f"**Rows:** {len(final):,} hexes (H3 res 9, complete Singapore admin subzones)  ")
    lines.append(f"**Columns:** {final.shape[1]}  ")
    lines.append(f"**File:** `{OUT.relative_to(ROOT)}`  ")
    lines.append("")
    lines.append("## What v10 fixes over v1 hex table")
    lines.append("")
    lines.append("1. **Hex universe extended** from 5,897 → 7,318 hexes. The previous V9 universe was missing 11 subzones including Siglap, Maritime Square (VivoCity/HarbourFront), Sentosa, Jurong Port, NE Islands, Southern Group. 5 sub-hex-size micro-subzones in Downtown/Rochor remain absent due to H3-9 resolution.")
    lines.append("2. **Persona leakage eliminated.** The 35 `p_*` persona features were subzone-broadcast from a file that itself held only 48 unique values across 318 subzones (personas are actually computed at the planning area level). Dropped at hex level. Will be included in the subzone representation with documented PA-level granularity.")
    lines.append("3. **Population & age counts recomputed dasymetrically** from Census 2025 subzone totals weighted by residential floor area per hex (from the fused building table). A hex with no residential floor area gets zero population, not a broadcast copy.")
    lines.append("4. **Land use / GPR recomputed** by area-weighted intersection of 113K URA zoning parcels against each hex polygon. `avg_gpr` now has real within-subzone variance (median std 0.34 across subzones).")
    lines.append("5. **`elderly_pct` and `walking_dependent_pct` dropped at hex level.** With a single dasymetric weight these ratios collapse to subzone constants. They belong at subzone level.")
    lines.append("6. **HDB resale prices dropped at hex level.** Without OneMap-style geocoding of (town, block, street_name) we can't place transactions in hexes. Will be first-class at subzone level where 227K transactions give clean per-subzone medians.")
    lines.append("7. **All buildings and amenity point counts recomputed from source geojsons** against the new universe. VivoCity / Sentosa / Maritime Square now carry their actual buildings and amenities.")
    lines.append("8. **Gap scores dropped entirely** (leakage from V7 / V8 models). Targets belong in a sibling table, not the feature matrix.")
    lines.append("")
    lines.append("## Known gaps")
    lines.append("")
    lines.append("- **5 micro-subzones** (DTSZ04 Phillip, DTSZ07 Maxwell, RCSZ04/06/08 Rochor Canal/Mackenzie/Selegie) are smaller than one H3-9 cell (0.039-0.12 km²). Their places fall into neighboring subzones' hexes. Total population loss: ~20 residents.")
    lines.append("- **Micrograph is v2 local** (66K generic universal + 2.9K cafe-specific). v3 per-category (174K places) is on rwm-server and will upgrade the 19 `mg_*` features when synced.")
    lines.append("- **HDB prices and personas are not present at hex level** (see above). They appear at subzone level in the subzone representation.")
    lines.append("- **LTA congestion, road/signal, walkability, walk-to-amenity distances** are COPY-THROUGH from V9 for overlapping hexes; the 1,421 new hexes have NaN for these columns until those V9-era pipelines are re-run. Flagged via mask in normalization step.")
    lines.append("")
    lines.append("## Pillar summary")
    lines.append("")
    lines.append("| Pillar | # features |")
    lines.append("|---|---|")
    for p, cols in sorted(pillars.items(), key=lambda kv: -len(kv[1])):
        lines.append(f"| `{p}` | {len(cols)} |")
    lines.append("")
    lines.append("## Columns by pillar")
    lines.append("")
    for p, cols in pillars.items():
        lines.append(f"### `{p}` ({len(cols)})")
        lines.append("")
        for c in cols:
            lines.append(f"- `{c}`")
        lines.append("")

    CATALOG.write_text("\n".join(lines))
    print(f"Wrote {CATALOG}")


if __name__ == "__main__":
    main()
