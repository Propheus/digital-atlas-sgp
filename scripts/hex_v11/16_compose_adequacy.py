"""Compose the 5 adequacy dimensions into a single adequacy_default score.

adequacy_default = 0.40 × availability   (existing gap_core, simplified)
                 + 0.25 × frequency       (peak wait time)
                 + 0.20 × reach           (% destinations within 45 min)
                 + 0.10 × crowding        (peak load factor at nearest MRT)
                 + 0.05 × resilience      (distinct lines to CBD)

Where availability ≈ today's gap_core (distance / accessibility / connectivity /
last_mile composite), kept for continuity. The 5 new dimensions ADD service-
quality on top of mere presence.

Outputs (added to hex8_adequacy_features.parquet):
  reach_adequacy_gap         (0 = great reach, 1 = isolated)
  availability_adequacy_gap  (alias of existing gap_core)
  adequacy_core
  adequacy_default           (the new composite that's loud vs availability-only)
"""

import numpy as np
import pandas as pd
from pathlib import Path

HEX_PATH = Path('data/hex_v11/hex8_adequacy_features.parquet')

# Quality-only weights (renormalised — excludes availability).
# Used to compute quality_only, which is then floored at availability.
# Adequacy CANNOT be better than availability — quality only compounds the gap.
QUALITY_WEIGHTS = {
    'frequency':    0.42,   # = 0.25 / 0.60
    'reach':        0.33,   # = 0.20 / 0.60
    'crowding':     0.17,   # = 0.10 / 0.60
    'resilience':   0.08,   # = 0.05 / 0.60
}

def main():
    h = pd.read_parquet(HEX_PATH)
    print(f'Loaded {h.shape}')

    # Reach factor: 0 if pct_dest_within_45min ≥ 80%, ramping to 1 at 0%
    pct45 = h['pct_dest_within_45min'].fillna(0)
    h['reach_adequacy_gap'] = (1 - pct45 / 80.0).clip(0, 1)

    # === Availability v2 — PURE spatial proximity, no double-count with new
    # adequacy factors. The old gap_core mixed in f_low_frequency and
    # f_line_pressure which are already represented by `frequency` and
    # `crowding` below — counting them twice biased adequacy unfairly. ===
    def safe(col, default=0):
        return h[col].fillna(default) if col in h.columns else pd.Series(default, index=h.index)
    h['availability_adequacy_gap'] = (
        0.30 * safe('f_distance')        +  # raw distance
        0.25 * safe('f_accessibility')   +  # walkability
        0.25 * safe('f_last_mile')       +  # door-to-stop friction
        0.20 * safe('f_connectivity')       # mode count + lines + routes
    ).clip(0, 1)

    # Ensure the three new factors exist (they should from steps 13-15)
    for col in ['frequency_adequacy_gap','crowding_adequacy_gap','resilience_adequacy_gap']:
        if col not in h.columns:
            print(f'⚠ Missing {col} — filling with 0.5')
            h[col] = 0.5
        h[col] = h[col].fillna(0.5).clip(0, 1)

    # === Quality-only composite (NO availability weight) ===
    # Renormalised weights, captures service-quality dimensions only.
    h['quality_only_gap'] = (
        QUALITY_WEIGHTS['frequency']  * h['frequency_adequacy_gap'] +
        QUALITY_WEIGHTS['reach']      * h['reach_adequacy_gap'] +
        QUALITY_WEIGHTS['crowding']   * h['crowding_adequacy_gap'] +
        QUALITY_WEIGHTS['resilience'] * h['resilience_adequacy_gap']
    ).clip(0, 1)

    # === HARD FLOOR — adequacy ≥ availability ALWAYS ===
    # If you can't comfortably reach transit, great service quality doesn't
    # help — adequacy is capped at the availability gap.
    # If service quality is BAD, it compounds the gap → adequacy = quality_only.
    # Quality dimensions can ONLY make adequacy WORSE than availability, never better.
    h['adequacy_core'] = np.maximum(
        h['availability_adequacy_gap'],
        h['quality_only_gap']
    ).clip(0, 1)

    # Adequacy_default = adequacy_core blended with the same equity overlay
    # we use for gap_default, so the equity story stays coherent across both scores.
    # Note: the floor (adequacy ≥ availability) is already enforced in adequacy_core;
    # the equity overlay can only further increase the gap (worsen the score).
    eq_max = h.get('gap_equity_max', pd.Series(0, index=h.index)).fillna(0)
    h['adequacy_default'] = (h['adequacy_core'] * 0.7 + eq_max * 0.3).clip(0, 1)
    # Re-apply the availability floor AFTER equity blend so equity damping can't
    # push adequacy back below availability.
    h['adequacy_default'] = np.maximum(
        h['adequacy_default'],
        h['availability_adequacy_gap']
    ).clip(0, 1)

    h.to_parquet(HEX_PATH, index=False)
    print(f'Wrote {HEX_PATH}')

    active = h[h['cell_active_flag'] == 1]
    print('\n=== ADEQUACY COMPOSITE ===')
    for f in ['availability_adequacy_gap','frequency_adequacy_gap','reach_adequacy_gap',
              'crowding_adequacy_gap','resilience_adequacy_gap','adequacy_core','adequacy_default']:
        print(f'  {f:>28s}: mean={active[f].mean():.3f}  median={active[f].median():.3f}')

    # Compare vs gap_default
    print('\n=== ADEQUACY vs GAP DEFAULT ===')
    print(f'  gap_default      mean={active["gap_default"].mean():.3f}  median={active["gap_default"].median():.3f}')
    print(f'  adequacy_default mean={active["adequacy_default"].mean():.3f}  median={active["adequacy_default"].median():.3f}')
    print(f'  correlation: {active[["gap_default","adequacy_default"]].corr().iloc[0,1]:.3f}')

    # Worst-cell band shifts (compared via gap_default vs adequacy_default)
    def band(v):
        if v < 0.30: return 'excellent'
        if v < 0.50: return 'good'
        if v < 0.70: return 'moderate'
        if v < 0.85: return 'poor'
        return 'critical'
    active = active.copy()
    active['gap_band'] = active['gap_default'].apply(band)
    active['adeq_band'] = active['adequacy_default'].apply(band)
    print('\n=== BAND DISTRIBUTION ===')
    print(f'  gap_default bands:      {dict(active["gap_band"].value_counts())}')
    print(f'  adequacy_default bands: {dict(active["adeq_band"].value_counts())}')

if __name__ == '__main__':
    main()
