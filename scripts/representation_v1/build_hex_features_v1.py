"""
Representation v1 — final hex feature table (raw, unnormalized).

Merges:
    hex_base_merged.parquet   = V9 survivors (150) + place composition (66) + micrograph (20)
    hex_rings.parquet         = k-ring neighbor aggregates (140 features)

Writes:
    model/representation_v1/hex_features_v1.parquet     (5,897 × ~376 columns)
    model/representation_v1/hex_features_v1_catalog.md  (pillar-organized catalog)

No normalization applied here — raw features only. Downstream scripts apply sqrt
normalization to build the model-ready matrix.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "model" / "representation_v1" / "hex_base_merged.parquet"
RINGS = ROOT / "model" / "representation_v1" / "hex_rings.parquet"
OUT_PARQUET = ROOT / "model" / "representation_v1" / "hex_features_v1.parquet"
OUT_CATALOG = ROOT / "model" / "representation_v1" / "hex_features_v1_catalog.md"


# Pillar assignment rules — prefix or explicit name -> pillar label.
# Applied in order; first match wins.
PILLAR_RULES = [
    # Neighbor prefixes FIRST — they're the most specific and every ring column must
    # be bucketed under a neighbor pillar regardless of what base feature it wraps.
    ("neighbor_nbr1_mean", lambda c: c.startswith("nbr1_mean_")),
    ("neighbor_nbr1_max",  lambda c: c.startswith("nbr1_max_")),
    ("neighbor_nbr2_mean", lambda c: c.startswith("nbr2_mean_")),
    ("neighbor_contrast",  lambda c: c.startswith("contrast_")),
    ("neighbor_rank",      lambda c: c.startswith("rank_")),
    ("identity",        lambda c: c in {"hex_id", "lat", "lng", "area_km2", "parent_subzone", "parent_subzone_name", "parent_pa", "parent_region"}),
    ("buildings",       lambda c: c.startswith("bldg_") or c in {"avg_floors", "max_floors", "avg_height", "max_height", "hdb_blocks"}),
    ("v9_places_raw",   lambda c: c.startswith("place_") or c == "places_total"),
    ("transit",         lambda c: "mrt" in c or c.startswith("bus_") or c in {"bus_stops", "lrt_stations", "mrt_stations", "mrt_hex_rings", "dist_nearest_mrt_m", "transit_daily_taps", "mrt_daily_taps", "bus_daily_taps"}),
    ("roads_signals",   lambda c: c.startswith("road_cat_") or c.startswith("sig_") or c.startswith("ped_") or c.startswith("hex_") and c != "hex_id" or c == "bicycle_signal" or c == "ped_crossings_total"),
    ("amenities_v9",    lambda c: c in {"hawker_centres", "hotels", "tourist_attractions", "chas_clinics", "preschools_gov", "silver_zones", "school_zones", "supermarkets", "parks", "formal_schools"}),
    ("housing_price",   lambda c: c in {"hdb_median_psf", "hdb_median_price", "avg_gpr", "residential_weight"}),
    ("population",      lambda c: c in {"population", "elderly_pct", "elderly_count", "children_count", "walking_dependent_pct", "walking_dependent_count"}),
    ("personas",        lambda c: c.startswith("p_")),
    ("walkability",     lambda c: "walkability" in c or c == "amenity_types_nearby" or c.startswith("walk_") or c.startswith("dist_")),
    ("v9_rings",        lambda c: c.endswith("_ring1") or c.endswith("_ring2")),
    ("place_composition", lambda c: c.startswith("pc_")),
    ("micrograph",      lambda c: c.startswith("mg_")),
]


def assign_pillar(col: str) -> str:
    for label, rule in PILLAR_RULES:
        if rule(col):
            return label
    return "other"


def main() -> None:
    base = pd.read_parquet(BASE)
    rings = pd.read_parquet(RINGS)

    merged = base.merge(rings, on="hex_id", how="left")
    assert len(merged) == len(base), "row count changed during merge"
    print(f"Final hex_features_v1 shape: {merged.shape}")

    OUT_PARQUET.parent.mkdir(parents=True, exist_ok=True)
    merged.to_parquet(OUT_PARQUET, index=False)
    print(f"Wrote {OUT_PARQUET}")

    # Build catalog
    pillars: dict[str, list[str]] = {}
    for c in merged.columns:
        p = assign_pillar(c)
        pillars.setdefault(p, []).append(c)

    lines: list[str] = []
    lines.append("# Hex Features v1 — Catalog")
    lines.append("")
    lines.append(f"**Rows:** {len(merged):,} hexes (H3 res 9, Singapore, V9 universe)  ")
    lines.append(f"**Columns:** {merged.shape[1]} (raw, unnormalized)  ")
    lines.append(f"**File:** `{OUT_PARQUET.relative_to(ROOT)}`  ")
    lines.append("")
    lines.append("## Pillar summary")
    lines.append("")
    lines.append("| Pillar | # features | Source |")
    lines.append("|---|---|---|")
    pillar_sources = {
        "identity": "data/hex_v9/hex_features_v2.parquet",
        "buildings": "V9 (Overture + HDB fused)",
        "v9_places_raw": "V9 (13 pre-aggregated categories, legacy)",
        "transit": "V9 (LTA + OSM)",
        "roads_signals": "V9 (LTA traffic + OSM)",
        "amenities_v9": "V9 (data.gov.sg)",
        "housing_price": "V9 (HDB resale, URA GPR)",
        "population": "V9 (Census 2025)",
        "personas": "V9 (NVIDIA personas, 148K)",
        "walkability": "V9 (OSM-derived)",
        "v9_rings": "V9 (pre-computed ring aggregates)",
        "place_composition": "v2 places (174K) → per-hex counts, shares, HHI, entropy",
        "micrograph": "micrograph_output/ (v2, 66K generic + 2.9K cafe-specific)",
        "neighbor_nbr1_mean": "k=1 (6 neighbors) mean over influence basis",
        "neighbor_nbr1_max": "k=1 max",
        "neighbor_nbr2_mean": "k=2 (18 neighbors) mean",
        "neighbor_contrast": "self - nbr1_mean (positive = self exceeds neighbors)",
        "neighbor_rank": "percentile rank of self within self+k=1 ∈ [0,1]",
    }
    for p, cols in sorted(pillars.items(), key=lambda kv: -len(kv[1])):
        lines.append(f"| `{p}` | {len(cols)} | {pillar_sources.get(p, '—')} |")
    lines.append("")
    lines.append("## Provenance notes")
    lines.append("")
    lines.append("- **Gap scores dropped** (no leakage): `transit_gap_score`, `elderly_transit_stress`, `clinic_gap_score`, `school_gap_score`.")
    lines.append("- **Place composition** recomputed from the 174K v2 master file. 166,582 of 174,713 places landed in the V9 hex universe (95.3%); 8,131 outside (offshore islands, near-border).")
    lines.append("- **Micrograph** uses v2 locally (66K v1 places). 11 of 12 v2 jsonl files are duplicates of the same spatial context, so we treat them as one universal per-place signal. V3 (174K, per-category) is on the server and will upgrade these features when synced.")
    lines.append("- **Neighbor features** are built over a 28-feature influence basis (see `INFLUENCE_BASIS` in `scripts/representation_v1/build_hex_rings.py`). Neighbors outside the 5,897-hex universe are excluded (not imputed).")
    lines.append("- **No normalization** applied in this file. Sqrt normalization is a separate downstream step.")
    lines.append("")
    lines.append("## Columns by pillar")
    lines.append("")
    for p, cols in pillars.items():
        lines.append(f"### `{p}` ({len(cols)})")
        lines.append("")
        for c in cols:
            lines.append(f"- `{c}`")
        lines.append("")

    OUT_CATALOG.write_text("\n".join(lines))
    print(f"Wrote {OUT_CATALOG}")
    print()
    print("Pillar breakdown:")
    for p, cols in sorted(pillars.items(), key=lambda kv: -len(kv[1])):
        print(f"  {p:24s} {len(cols):4d}")


if __name__ == "__main__":
    main()
