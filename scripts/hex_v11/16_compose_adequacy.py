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

# === Per-profile factor weights ===
# Each profile re-weights both the availability composite AND the quality-only
# composite to reflect what that population actually cares about. Toggling
# Profile in the UI is no longer cosmetic — it genuinely re-scores the map.

# Availability composite weights (sum to 1, four factors).
# default — balanced across all 4 spatial-proximity factors.
# elderly — distance + accessibility dominate; connectivity to far places is
#           less important (rarely commute to CBD).
# family  — last-mile and walkability matter most (kids in tow).
# workers — connectivity + last-mile dominate (industrial commutes).
AVAIL_WEIGHTS = {
    'default': {'f_distance': 0.30, 'f_accessibility': 0.25, 'f_last_mile': 0.25, 'f_connectivity': 0.20},
    'elderly': {'f_distance': 0.40, 'f_accessibility': 0.35, 'f_last_mile': 0.20, 'f_connectivity': 0.05},
    'family':  {'f_distance': 0.25, 'f_accessibility': 0.35, 'f_last_mile': 0.30, 'f_connectivity': 0.10},
    'workers': {'f_distance': 0.20, 'f_accessibility': 0.15, 'f_last_mile': 0.30, 'f_connectivity': 0.35},
}

# Quality-only composite weights (sum to 1, four quality dimensions).
# default — balanced.
# elderly — frequency matters most (can't wait long); crowding matters; reach
#           to CBD doesn't (don't commute).
# family  — frequency + crowding (peak times); reach to school not measured here.
# workers — reach (commute) dominates; crowding for peak; frequency moderate.
QUALITY_WEIGHTS = {
    'default': {'frequency': 0.42, 'reach': 0.33, 'crowding': 0.17, 'resilience': 0.08},
    'elderly': {'frequency': 0.55, 'reach': 0.15, 'crowding': 0.25, 'resilience': 0.05},
    'family':  {'frequency': 0.40, 'reach': 0.20, 'crowding': 0.30, 'resilience': 0.10},
    'workers': {'frequency': 0.30, 'reach': 0.40, 'crowding': 0.20, 'resilience': 0.10},
}

# Vulnerability multiplier — universal (applies regardless of profile).
# When a cell has an UNUSUALLY high share of vulnerable residents AND
# notably poor access, adequacy gets pushed worse. Double threshold:
#  - vuln_share must exceed VULN_SHARE_BASELINE (typical SG residential is
#    ~22%; the penalty only fires for cells above this baseline)
#  - avail_gap must exceed VULN_GAP_THRESHOLD (cells with Excellent access
#    don't get penalised — vulnerable people there are fine)
# This keeps the average score stable while sharply penalising cells that
# combine high vulnerability with poor access.
VULN_SHARE_BASELINE = 0.20    # baseline residential SG cell — no penalty below this
VULN_GAP_THRESHOLD  = 0.20    # Excellent access — no penalty below this
VULN_AMPLIFIER      = 2.5     # penalty = max(0, vuln-base) × max(0, gap-thresh) × 2.5
VULN_SHARE_CAP      = 0.55    # hard ceiling on vulnerable_share
VULN_PENALTY_CAP    = 0.25    # max penalty per cell (prevents runaway in extremes)

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

    # === Universal vulnerability share (used by all profiles) ===
    # We have FOUR vulnerable groups: walking-dep (elderly + children),
    # low-income (HDB 1-3R), dorm workers, FDWs. But walking-dep and low-income
    # OVERLAP heavily — an elderly person in HDB 1-3R is in BOTH. So we take
    # the MAX of those two (conservative, no double-count) and add the
    # non-overlapping NR groups (dorm + FDW are separate populations).
    walking_dep   = h.get('walking_dependent_count', pd.Series(0, index=h.index)).fillna(0)
    low_income    = h.get('low_income_pop',          pd.Series(0, index=h.index)).fillna(0)
    pop_dorm      = h.get('pop_nr_dorm',             pd.Series(0, index=h.index)).fillna(0)
    pop_fdw       = h.get('pop_nr_fdw',              pd.Series(0, index=h.index)).fillna(0)
    pop_tot_safe  = h['pop_total'].clip(lower=1)

    walking_dep_share = walking_dep / pop_tot_safe
    low_income_share  = low_income  / pop_tot_safe
    # Resident vulnerability = max of age-based and income-based (no double-count)
    # + a 30% bump for the non-max one (some incremental overlap)
    resident_max = np.maximum(walking_dep_share, low_income_share)
    resident_min = np.minimum(walking_dep_share, low_income_share)
    resident_vuln = resident_max + 0.30 * resident_min
    # NR groups — separate populations
    nr_vuln = (pop_dorm + pop_fdw) / pop_tot_safe

    h['vulnerability_share'] = (resident_vuln + nr_vuln).clip(0, VULN_SHARE_CAP)

    eq_max = h.get('gap_equity_max', pd.Series(0, index=h.index)).fillna(0)

    # === Per-profile composite ===
    for profile in ('default', 'elderly', 'family', 'workers'):
        aw = AVAIL_WEIGHTS[profile]
        qw = QUALITY_WEIGHTS[profile]

        # Availability composite for this profile
        avail = (
            aw['f_distance']      * h['f_distance']      +
            aw['f_accessibility'] * h['f_accessibility'] +
            aw['f_last_mile']     * h['f_last_mile']     +
            aw['f_connectivity']  * h['f_connectivity']
        ).clip(0, 1)

        # Quality-only composite for this profile
        qual = (
            qw['frequency']  * h['frequency_adequacy_gap']  +
            qw['reach']      * h['reach_adequacy_gap']      +
            qw['crowding']   * h['crowding_adequacy_gap']   +
            qw['resilience'] * h['resilience_adequacy_gap']
        ).clip(0, 1)

        # Hard floor: adequacy_core = max(availability, quality_only)
        core = np.maximum(avail, qual).clip(0, 1)

        # Equity overlay (30%), re-apply availability floor
        blend = (core * 0.7 + eq_max * 0.3).clip(0, 1)
        blend = np.maximum(blend, avail).clip(0, 1)

        # Vulnerability multiplier — additive penalty kicks in only when
        # BOTH thresholds are exceeded (vuln > baseline AND access > threshold).
        # Capped at VULN_PENALTY_CAP to prevent runaway in extreme cells.
        excess_vuln   = (h['vulnerability_share'] - VULN_SHARE_BASELINE).clip(lower=0)
        access_excess = (avail - VULN_GAP_THRESHOLD).clip(lower=0)
        penalty = (excess_vuln * access_excess * VULN_AMPLIFIER).clip(0, VULN_PENALTY_CAP)

        adq = (blend + penalty).clip(0, 1)

        suffix = '' if profile == 'default' else f'_{profile}'
        h[f'availability_adequacy_gap{suffix}'] = avail
        h[f'quality_only_gap{suffix}']          = qual
        h[f'adequacy_core{suffix}']             = core
        h[f'vulnerability_penalty{suffix}']     = penalty
        h[f'adequacy_default{suffix}']          = adq

    # Aliases for back-compat with downstream consumers that don't know about profiles
    h['adequacy_default'] = h['adequacy_default']    # already set above (default profile)
    h['adequacy_core']    = h['adequacy_core']
    # availability_adequacy_gap / quality_only_gap also set above for default profile

    h.to_parquet(HEX_PATH, index=False)
    print(f'Wrote {HEX_PATH}')

    active = h[h['cell_active_flag'] == 1]
    print('\n=== PER-PROFILE ADEQUACY COMPOSITE ===')
    print(f'  vulnerability_share: mean={active["vulnerability_share"].mean():.3f}  median={active["vulnerability_share"].median():.3f}  max={active["vulnerability_share"].max():.3f}')
    print()
    for profile in ('default','elderly','family','workers'):
        sfx = '' if profile == 'default' else f'_{profile}'
        avail = active[f'availability_adequacy_gap{sfx}'].mean()
        adq = active[f'adequacy_default{sfx}'].mean()
        pen = active[f'vulnerability_penalty{sfx}'].mean()
        n_penalized = int((active[f'vulnerability_penalty{sfx}'] > 0.05).sum())
        print(f'  {profile:>10s} | avail mean={avail:.3f}  adeq mean={adq:.3f}  penalty mean={pen:.3f}  '
              f'(penalty >0.05 in {n_penalized} cells)')

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
