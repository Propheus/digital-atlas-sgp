"""Phase 2 — pop-weighted rollup of each pack's scores to subzone."""
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).parent
PACKS = ["retail", "realestate", "utilities", "transport", "insurance"]
ADMIN = {"hex8_id", "parent_subzone", "parent_pa", "parent_region", "zone_type_broad"}


def main():
    pop = pd.read_parquet(ROOT / "hex/hex8_all_features.parquet")[["hex8_id", "pop_resident"]]
    for pack in PACKS:
        p = pd.read_parquet(ROOT / f"hex/hex8_{pack}_pack.parquet")
        score_cols = [c for c in p.columns if c not in ADMIN]
        df = p.merge(pop, on="hex8_id", how="left")
        df["w"] = df["pop_resident"].clip(lower=1)
        g = df.groupby("parent_subzone")
        wsum = g["w"].sum()
        out = pd.DataFrame({"parent_subzone": wsum.index})
        for c in score_cols:
            num = (df[c] * df["w"]).groupby(df["parent_subzone"]).sum()
            out[c] = (num / wsum).round(1).values
        out.to_parquet(ROOT / f"hex/subzone_{pack}_pack.parquet", index=False)
        print(f"subzone_{pack}_pack: {out.shape}")


if __name__ == "__main__":
    main()
