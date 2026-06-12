"""
Validation gate — spot checks against known findings:

  1. Yunnan grocery desert (60K residents, 1.4 km to nearest FairPrice).
     Expected: Yunnan subzone appears in bottom quartile for grocery adequacy.

  2. Yishun East transit deficit.
     Expected: Yishun East subzone has below-median composite accessibility.

Run:  python -m engine._validate
"""
import numpy as np
from .state import load_state
from .gravity import Gravity


def find_by_name(s, keyword: str):
    keyword = keyword.upper()
    matches = []
    for i, name in enumerate(s.subzone_name):
        if keyword in str(name).upper():
            matches.append(i)
    return matches


def main():
    s = load_state()
    g = Gravity(s)
    g.calibrate_all()

    r_grocery = g.compute("grocery")
    r_clinic = g.compute("clinic")
    adq_grocery = g.adequacy_index("grocery", r_grocery)
    adq_clinic = g.adequacy_index("clinic", r_clinic)

    print(f"calibrated β: clinic={g.params['clinic'].beta:.3f}  grocery={g.params['grocery'].beta:.3f}")
    print(f"total pop (included): {s.population[s.included].sum():,}\n")

    # -------- 1. Yunnan grocery --------
    print("===== TEST 1: Yunnan grocery desert =====")
    yunnan_hits = find_by_name(s, "YUNNAN")
    for i in yunnan_hits:
        print(f"  {s.codes[i]:8}  {s.subzone_name[i]:25}  {s.planning_area[i]:20}  "
              f"pop={s.population[i]:6,}  "
              f"fairprice={int(s.supply['fairprice'][i]):2d}  "
              f"adq={adq_grocery[i]:5.1f}  "
              f"A={r_grocery.A[i]:.2f}")
    if yunnan_hits:
        best = max(yunnan_hits, key=lambda i: s.population[i])
        pct = adq_grocery[best]
        quartile = "bottom" if pct <= 25 else ("lower-mid" if pct <= 50 else "upper")
        print(f"  → Yunnan adequacy percentile: {pct:.0f}  ({quartile})")
        if pct <= 25:
            print(f"  ✓ GATE 1 PASSED")
        else:
            print(f"  ✗ GATE 1 FAILED (expected bottom 25%)")
    else:
        print("  ! Yunnan not found in subzone names")

    # -------- 2. Yishun East --------
    print("\n===== TEST 2: Yishun East transit deficit =====")
    yishun_hits = find_by_name(s, "YISHUN")
    # Also explicitly for "NEE SOON" and "SPRINGLEAF" which are in Yishun
    # Get the planning area subzones
    yishun_pa = [i for i in range(s.n) if str(s.planning_area[i]).upper() == "YISHUN"]
    print(f"  {len(yishun_pa)} subzones in YISHUN planning area:")
    T = s.T_composite.copy()
    T_finite = np.where(T < 990, T, np.nan)
    pop = s.population.astype(np.float32)
    # Composite accessibility via logsum-style metric: mean time to nearest 20 population centres
    # Simple proxy: mean time to all included subzones, pop-weighted
    included_mask = s.included.astype(np.float32)
    accessibility_min = (T * included_mask * pop[None, :]).sum(axis=1) / np.clip(
        (included_mask * pop[None, :]).sum(axis=1), 1, None
    )
    # Lower is better (shorter mean travel). Rank among included.
    inc_idx = np.where(s.included)[0]
    vals = accessibility_min[inc_idx]
    order = np.argsort(vals)  # best first
    rank = np.zeros(s.n, dtype=int)
    for r, ii in enumerate(order):
        rank[inc_idx[ii]] = r
    for i in sorted(yishun_pa, key=lambda k: -s.population[k])[:6]:
        pct = (rank[i] / max(len(inc_idx) - 1, 1)) * 100
        print(f"  {s.codes[i]:8}  {s.subzone_name[i]:22}  pop={s.population[i]:6,}  "
              f"mean-access-min={accessibility_min[i]:5.1f}  percentile={pct:5.1f} (0=best)")

    # Biggest Yishun subzone (by pop) should be in bottom half for transit-only composite
    biggest = max(yishun_pa, key=lambda k: s.population[k])
    pct = (rank[biggest] / max(len(inc_idx) - 1, 1)) * 100
    print(f"  Biggest Yishun subzone: {s.codes[biggest]} ({s.subzone_name[biggest]}) at percentile {pct:.0f}")

    # -------- 3. Basic sanity --------
    print("\n===== BASIC SANITY =====")
    inc = s.included
    print(f"included subzones: {inc.sum()}")
    print(f"adequacy_grocery   mean={adq_grocery[inc].mean():.1f}  std={adq_grocery[inc].std():.1f}")
    print(f"adequacy_clinic    mean={adq_clinic[inc].mean():.1f}  std={adq_clinic[inc].std():.1f}")
    print(f"A_grocery (A)  p10={np.percentile(r_grocery.A[inc],10):.2f}  "
          f"p50={np.percentile(r_grocery.A[inc],50):.2f}  "
          f"p90={np.percentile(r_grocery.A[inc],90):.2f}")
    print(f"A_clinic  (A)  p10={np.percentile(r_clinic.A[inc],10):.2f}  "
          f"p50={np.percentile(r_clinic.A[inc],50):.2f}  "
          f"p90={np.percentile(r_clinic.A[inc],90):.2f}")

    # Per-subzone total supply should roughly match known totals
    print(f"\nTotal CHAS across all subzones: {int(s.supply['chas_clinics'].sum())} (expected 1192)")
    print(f"Total FairPrice across all subzones: {int(s.supply['fairprice'].sum())} (expected 294)")


if __name__ == "__main__":
    main()
