"""
Plexis SGP v4 — Stage 3b (DORM-AWARE replacement).

Recalibrates population to official SingStat June-2024 figures and places the
migrant-worker dormitory population at real dorm locations instead of smearing
it across business land-use.

Targets (SingStat, June 2024):
  resident     = 4,179,800
  non-resident = 1,857,100
  total        = 6,036,900

Dorm subset (DASL "Worker Dormitories in Singapore", H2 2024):
  439,198 licensed Class-4 dorm beds across 1,441 dorms (~full occupancy 2024).
  We carve this OUT OF the non-resident total (work-permit holders ARE
  non-residents — never additive) and allocate it equally across the geocoded
  dorm POINTS, so hexes with more dorms get more workers. The non-dorm
  non-resident remainder (FDWs, other WP/EP/S-pass, dependents, students) keeps
  the existing land-use-weighted distribution.

Operates on the CURRENT hex9_population.parquet (already post-3b: has
pop_resident + pop_nonresident), so it is idempotent w.r.t. the deployed atlas
and needs no pre-3b pop_total.

Output: hex/hex9_population.parquet  (adds pop_dorm; rewrites pop_* + shares)
"""
import json, time
from pathlib import Path
import numpy as np
import pandas as pd
import h3

ROOT = Path(__file__).parent

RESIDENT_TARGET = 4_179_800
NONRES_TARGET   = 1_857_100
DORM_POP        = 439_198          # DASL H2 2024 licensed beds (~full occupancy)

DORM_JSONL = ROOT / "data/external/mom/migrant-worker-dormitories.geocoded.jsonl"
POP_PQ     = ROOT / "hex/hex9_population.parquet"
REPORT     = ROOT / "hex/non_resident_dorm_report.json"

RES_SUBCOLS = ["pop_resident", "pop_hdb", "pop_non_hdb",
               "pop_0_14", "pop_15_64", "pop_65plus"]


def load_dorm_hex9(universe):
    """Return Series hex9_id -> dorm point count, for dorms inside the universe."""
    recs = []
    with open(DORM_JSONL) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            lat, lng = d.get("lat"), d.get("lng")
            if lat is None or lng is None:
                continue
            recs.append(h3.latlng_to_cell(float(lat), float(lng), 9))
    s = pd.Series(recs, name="hex9_id")
    total = len(s)
    in_uni = s[s.isin(universe)]
    counts = in_uni.value_counts()
    return counts, total, len(in_uni)


def main():
    t0 = time.time()
    pop = pd.read_parquet(POP_PQ)
    universe = set(pop["hex9_id"])
    res_before = pop["pop_resident"].sum()
    nonres_before = pop["pop_nonresident"].sum()
    print(f"Loaded {len(pop):,} hex9 | resident={res_before:,.0f} nonres={nonres_before:,.0f}")

    # 1) Resident -> official total (uniform rescale; keeps shares & all normalized
    #    resident-derived features invariant).
    rfac = RESIDENT_TARGET / res_before
    for c in RES_SUBCOLS:
        if c in pop.columns:
            pop[c] = pop[c] * rfac
    print(f"Resident rescale factor = {rfac:.6f} -> {pop['pop_resident'].sum():,.0f}")

    # 2) Dorm population placed at real dorm hexes (equal split across points).
    dorm_counts, n_total, n_in_uni = load_dorm_hex9(universe)
    per_dorm = DORM_POP / n_in_uni
    pop["pop_dorm"] = pop["hex9_id"].map(dorm_counts).fillna(0) * per_dorm
    print(f"Dorms: {n_total} geocoded, {n_in_uni} in-universe across "
          f"{dorm_counts.size} hexes | per-dorm={per_dorm:,.0f} | "
          f"pop_dorm sum={pop['pop_dorm'].sum():,.0f}")

    # 3) Non-dorm non-resident remainder keeps the existing land-use weighting.
    remainder = NONRES_TARGET - DORM_POP
    w = pop["pop_nonresident"].clip(lower=0)
    wsum = w.sum()
    pop["pop_nonresident"] = pop["pop_dorm"] + remainder * (w / wsum)
    print(f"Non-resident: dorm {DORM_POP:,} + remainder {remainder:,.0f} "
          f"-> {pop['pop_nonresident'].sum():,.0f}")

    # 4) Totals + shares
    pop["pop_total_all"] = pop["pop_resident"] + pop["pop_nonresident"]
    pop["nonres_share"] = np.where(pop["pop_total_all"] > 0,
                                   pop["pop_nonresident"] / pop["pop_total_all"], 0.0)
    if "pop_hdb_share" in pop.columns:
        pop["pop_hdb_share"] = np.where(pop["pop_resident"] > 0,
                                        pop["pop_hdb"] / pop["pop_resident"], 0.0)

    pop.to_parquet(POP_PQ, index=False)

    report = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "method": "official_2024_recal + dorm_point_allocation",
        "resident_total": float(pop["pop_resident"].sum()),
        "nonresident_total": float(pop["pop_nonresident"].sum()),
        "dorm_total": float(pop["pop_dorm"].sum()),
        "grand_total": float(pop["pop_total_all"].sum()),
        "dorms_geocoded": int(n_total),
        "dorms_in_universe": int(n_in_uni),
        "dorm_hexes": int(dorm_counts.size),
        "resident_rescale_factor": round(rfac, 6),
        "wall_clock_s": round(time.time() - t0, 2),
    }
    json.dump(report, open(REPORT, "w"), indent=2)
    print("\n" + json.dumps(report, indent=2))
    print(f"\nTop dorm hexes by pop_dorm:")
    top = pop.nlargest(8, "pop_dorm")[["hex9_id", "pop_dorm", "pop_nonresident", "pop_resident"]]
    print(top.to_string(index=False))


if __name__ == "__main__":
    main()
