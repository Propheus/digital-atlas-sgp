"""
Representation v1 — hex micrograph aggregates.

Source note (IMPORTANT):
    Local micrograph_output/ has 12 .jsonl files but 11 are IDENTICAL copies of the
    same 66,851 v1 places with the same context_vector — only cafe_micrographs.jsonl
    is category-distinct (2,904 real cafes). The real per-category v3 pipeline covering
    all 174,713 places lives on the server at micrograph_output_v3/.

    For representation v1 we treat ONE of the duplicate files as the canonical
    "universal per-place spatial context" (one micrograph per v1 place) and also pull
    cafe-specific aggregates from cafe_micrographs.jsonl. When v3 is synced we extend
    the schema with mg_{cat}_* per-category aggregates.

Input:
    micrograph_output/bakery_pastry_micrographs.jsonl   (treated as universal, 66,851 places)
    micrograph_output/cafe_micrographs.jsonl            (2,904 actual cafes)
    data/hex_v9/hex_features_v2.parquet                 (5,897 hexes)

Output:
    model/representation_v1/hex_micrograph.parquet

Schema (one row per hex in the hex universe):
    hex_id

    # universal per-place spatial context (66K v1 places)
    mg_n                        int    number of places with a micrograph
    mg_mean_transit             float  mean T1 (transit anchor weight) of cv
    mg_mean_competitor          float  mean T2 (competitor)
    mg_mean_complementary       float  mean T3 (complementary)
    mg_mean_demand              float  mean T4 (demand magnet)
    mg_mean_anchor_count        float  mean anchor_count (micrograph richness)
    mg_mean_comp_pressure       float  mean competitive_pressure
    mg_mean_demand_diversity    float  mean demand_diversity
    mg_mean_walkability         float  mean walkability_index
    mg_pct_hyperdense           float  share of places in hyperdense band
    mg_pct_dense                float  share in dense band
    mg_pct_moderate             float  share in moderate band
    mg_pct_sparse               float  share in sparse band

    # cafe-specific (2,904 places)
    mg_cafe_n                   int    number of cafes with a micrograph
    mg_cafe_mean_transit        float
    mg_cafe_mean_competitor     float
    mg_cafe_mean_complementary  float
    mg_cafe_mean_demand         float
    mg_cafe_mean_anchor_count   float
    mg_cafe_mean_comp_pressure  float

Hexes without any micrograph place have zeros and mg_n=0. Downstream consumers
should gate on mg_n > 0 before using the mean features.
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Iterable

import h3
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
UNIVERSAL_MG = ROOT / "micrograph_output" / "bakery_pastry_micrographs.jsonl"  # duplicate — used as universal
CAFE_MG = ROOT / "micrograph_output" / "cafe_micrographs.jsonl"
HEX_PATH = ROOT / "data" / "hex_v9" / "hex_features_v2.parquet"
OUT_PATH = ROOT / "model" / "representation_v1" / "hex_micrograph.parquet"

DENSITY_BANDS = ["hyperdense", "dense", "moderate", "sparse"]


class HexAcc:
    """Online mean accumulator per hex for a fixed list of numeric fields plus band shares."""

    def __init__(self, numeric_fields: list[str]) -> None:
        self.fields = numeric_fields
        self.n: dict[str, int] = defaultdict(int)
        self.sums: dict[str, dict[str, float]] = defaultdict(lambda: {f: 0.0 for f in numeric_fields})
        self.bands: dict[str, dict[str, int]] = defaultdict(lambda: {b: 0 for b in DENSITY_BANDS})

    def add(self, hex_id: str, values: dict[str, float], band: str | None) -> None:
        self.n[hex_id] += 1
        s = self.sums[hex_id]
        for f in self.fields:
            v = values.get(f)
            if v is not None:
                s[f] += float(v)
        if band in self.bands[hex_id]:
            self.bands[hex_id][band] += 1

    def row(self, hex_id: str, prefix: str) -> dict[str, float]:
        n = self.n.get(hex_id, 0)
        row: dict[str, float] = {f"{prefix}n": n}
        if n > 0:
            s = self.sums[hex_id]
            for f in self.fields:
                row[f"{prefix}mean_{f}"] = s[f] / n
            b = self.bands[hex_id]
            for band in DENSITY_BANDS:
                row[f"{prefix}pct_{band}"] = b[band] / n
        else:
            for f in self.fields:
                row[f"{prefix}mean_{f}"] = 0.0
            for band in DENSITY_BANDS:
                row[f"{prefix}pct_{band}"] = 0.0
        return row


def iter_micrographs(path: Path) -> Iterable[tuple[str, dict, str | None]]:
    """Yield (hex_id, normalized_value_dict, density_band) for each record with lat/lng."""
    with path.open() as f:
        for ln in f:
            d = json.loads(ln)
            lat = d.get("latitude")
            lng = d.get("longitude")
            if lat is None or lng is None:
                continue
            hex_id = h3.latlng_to_cell(lat, lng, 9)
            cv = d.get("context_vector") or {}
            if isinstance(cv, str):  # some legacy rows stringify
                try:
                    cv = json.loads(cv.replace("'", '"'))
                except Exception:
                    cv = {}
            vals = {
                "transit": cv.get("transit", 0.0),
                "competitor": cv.get("competitor", 0.0),
                "complementary": cv.get("complementary", 0.0),
                "demand": cv.get("demand", 0.0),
                "anchor_count": d.get("anchor_count", 0.0),
                "comp_pressure": d.get("competitive_pressure", 0.0),
                "demand_diversity": d.get("demand_diversity", 0.0),
                "walkability": d.get("walkability_index", 0.0),
            }
            yield hex_id, vals, d.get("density_band")


UNIVERSAL_FIELDS = [
    "transit", "competitor", "complementary", "demand",
    "anchor_count", "comp_pressure", "demand_diversity", "walkability",
]
CAFE_FIELDS = [
    "transit", "competitor", "complementary", "demand",
    "anchor_count", "comp_pressure",
]


def main() -> None:
    print(f"Loading hex universe: {HEX_PATH}")
    hex_universe = pd.read_parquet(HEX_PATH, columns=["hex_id"])["hex_id"].tolist()
    hex_set = set(hex_universe)
    print(f"  {len(hex_universe)} hexes")

    universal = HexAcc(UNIVERSAL_FIELDS)
    print(f"Streaming universal micrographs: {UNIVERSAL_MG}")
    n_u = n_u_outside = 0
    for hex_id, vals, band in iter_micrographs(UNIVERSAL_MG):
        n_u += 1
        if hex_id not in hex_set:
            n_u_outside += 1
            continue
        universal.add(hex_id, vals, band)
    print(f"  universal: {n_u:,} records | outside hex universe: {n_u_outside:,}")

    cafe = HexAcc(CAFE_FIELDS)
    print(f"Streaming cafe micrographs: {CAFE_MG}")
    n_c = n_c_outside = 0
    for hex_id, vals, band in iter_micrographs(CAFE_MG):
        n_c += 1
        if hex_id not in hex_set:
            n_c_outside += 1
            continue
        cafe.add(hex_id, vals, band)
    print(f"  cafe: {n_c:,} records | outside hex universe: {n_c_outside:,}")

    # Build output frame
    rows = []
    for hex_id in hex_universe:
        row: dict = {"hex_id": hex_id}
        row.update(universal.row(hex_id, "mg_"))
        # Cafe: we only want n + means (no bands, per schema above)
        crow_full = cafe.row(hex_id, "mg_cafe_")
        for k, v in crow_full.items():
            # drop band shares from cafe output to keep schema tight
            if k.startswith("mg_cafe_pct_"):
                continue
            row[k] = v
        rows.append(row)

    out = pd.DataFrame(rows)
    print(f"Output shape: {out.shape}")
    print(f"Hexes with any universal micrograph: {(out['mg_n']>0).sum():,}")
    print(f"Hexes with any cafe micrograph: {(out['mg_cafe_n']>0).sum():,}")

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    out.to_parquet(OUT_PATH, index=False)
    print(f"Wrote {OUT_PATH}")

    # quick sanity
    print()
    print("Top 5 hexes by universal mg_n:")
    print(out.nlargest(5, "mg_n")[["hex_id", "mg_n", "mg_mean_transit", "mg_mean_competitor", "mg_mean_anchor_count"]])


if __name__ == "__main__":
    main()
