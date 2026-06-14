"""Phase 2 — QA gates for the domain packs (the atlas validation discipline)."""
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).parent
PACKS = ["retail", "realestate", "utilities", "transport", "insurance"]
ADMIN = {"hex8_id", "parent_subzone", "parent_pa", "parent_region", "zone_type_broad"}


def main():
    m = pd.read_parquet(ROOT / "hex/hex8_all_features.parquet")
    fails = []

    def gate(ok, msg):
        print(("  ✅ " if ok else "  ❌ ") + msg)
        if not ok:
            fails.append(msg)

    for pack in PACKS:
        print(f"\n[{pack}]")
        p = pd.read_parquet(ROOT / f"hex/hex8_{pack}_pack.parquet")
        scores = [c for c in p.columns if c.endswith(("_score", "_tier", "_band", "_proxy", "_priority", "_stress"))]
        gate(len(p) == 1191, f"row count 1191 (got {len(p)})")
        for c in scores:
            v = p[c]
            gate(v.nunique() > 1, f"{c} not constant")
            gate(v.dropna().between(-200, 100000).all(), f"{c} in sane range")
        # subzone rollup exists + sane count (atlas has 270 populated subzones)
        sz = pd.read_parquet(ROOT / f"hex/subzone_{pack}_pack.parquet")
        gate(260 <= len(sz) <= 280, f"subzone rollup {len(sz)} in [260,280]")

    # known-answer correlations (the meaningful checks)
    print("\n[known-answer]")
    r = pd.read_parquet(ROOT / "hex/hex8_retail_pack.parquet").merge(
        m[["hex8_id", "iso_walk10_unserved_pop_cafe_coffee", "cap_cafe_coffee"]], on="hex8_id")
    rho_u = r["retail_whitespace_score"].corr(r["iso_walk10_unserved_pop_cafe_coffee"])
    rho_c = r["retail_whitespace_score"].corr(r["cap_cafe_coffee"])
    gate(rho_u > 0.3 and rho_c > 0.3,
         f"retail whitespace tracks BOTH unserved (ρ={rho_u:.2f}) & winnable (ρ={rho_c:.2f})")

    i = pd.read_parquet(ROOT / "hex/hex8_insurance_pack.parquet").merge(
        m[["hex8_id", "biz_recent_dead_share"]], on="hex8_id")
    rho = i["risk_bi_failure_score"].corr(i["biz_recent_dead_share"])
    gate(rho > 0.5, f"insurance BI ~ biz_recent_dead_share (ρ={rho:.2f} > 0.5)")

    # dedup vs master (no hero score is just a renamed master col)
    print("\n[dedup]")
    for pack in PACKS:
        p = pd.read_parquet(ROOT / f"hex/hex8_{pack}_pack.parquet").merge(m, on="hex8_id")
        scores = [c for c in p.columns if c.endswith("_score") and c not in m.columns]
        num = p.select_dtypes("number")
        for c in scores:
            corr = num.corrwith(p[c]).drop(c, errors="ignore").abs()
            top = corr[corr > 0.98].index.tolist()
            if top:
                print(f"  ⚠ {pack}.{c} ~ {top[:2]} (|r|>0.98)")

    print(f"\n{'ALL GATES PASS ✅' if not fails else f'{len(fails)} GATE(S) FAILED ❌'}")
    return fails


if __name__ == "__main__":
    main()
