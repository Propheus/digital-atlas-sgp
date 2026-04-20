"""
Hex v10 — personas per hex (intentional NO-OP).

The NVIDIA persona features in data/personas/persona_features_by_subzone.parquet
are per-subzone-coded but contain only 48 unique signatures across 318 subzones —
i.e. they are actually broadcast at the PLANNING AREA level, not subzone, let
alone hex.

At hex level there is no honest way to give these features within-PA variance
without per-building demographic data we don't have. Dasymetric weighting by
residential floor area preserves the ratios as subzone/PA constants (numerator
and denominator scale identically), and building a "count" version just
recovers population scaled by a PA-level constant — which is redundant with the
population column already in hex v10.

Decision: do not emit any persona columns at hex level. Personas are a
planning-area-level attribute and will be included in the subzone (or PA)
representation later, where they still carry 48-signature signal.

If you want per-hex persona data in the future, the upstream fix is to
recompute personas from the source 148K NVIDIA persona records with a proper
spatial join to hex, not to subzone/PA.

This script writes a stub parquet (hex_id + one flag column) purely to keep the
pipeline manifest complete.
"""
from __future__ import annotations

from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
UNI = ROOT / "data" / "hex_v10" / "hex_universe.parquet"
OUT = ROOT / "data" / "hex_v10" / "hex_personas.parquet"


def main() -> None:
    uni = pd.read_parquet(UNI, columns=["hex_id", "parent_pa"])
    # Stub: one row per hex, no persona features emitted.
    # We do leave behind parent_pa for anyone who wants to join the PA-level
    # persona signature back in as an explicit reference feature.
    out = uni[["hex_id", "parent_pa"]].copy()
    out.to_parquet(OUT, index=False)
    print(f"Wrote stub (no persona features emitted) — {len(out):,} rows: {OUT}")
    print("See script docstring for why personas are dropped at hex level.")


if __name__ == "__main__":
    main()
