"""
Hex v10 — HDB resale prices per hex (intentional NO-OP for hex, see note).

The HDB resale table (data/property/hdb_resale_prices.csv, 227K transactions)
only has town + block + street_name. There is no lat/lng in the resale file,
and the authoritative HDB buildings geojson uses ST_COD (street code) rather
than street name, so without external geocoding (OneMap) we cannot reliably
assign a transaction to its building's hex.

A fuzzy (town, block) match collapses to PA-level data anyway because within
one town many blocks share block numbers across different streets — the
street_name disambiguation is exactly what we can't resolve.

Two honest options:
    (a) Broadcast subzone-level median HDB psf to every hex in the subzone.
    (b) Drop HDB price from hex level. Include it at subzone level where
        227K transactions give a clean per-subzone signal.

We take option (b). HDB price is a first-class feature for the subzone
representation (where we will use data/property/hdb_resale_prices.csv with
a town -> planning area mapping and still get real per-subzone variance).
At hex level, without geocoding, it would just be broadcast noise and re-
introduce the exact leakage we are trying to fix.

Upgrade path: when OneMap batch geocoding is available offline, rerun this
script to produce real per-hex medians. The script will then replace the
stub with the dasymetric-free, count-≥3 version.
"""
from __future__ import annotations

from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
UNI = ROOT / "data" / "hex_v10" / "hex_universe.parquet"
OUT = ROOT / "data" / "hex_v10" / "hex_hdb_prices.parquet"


def main() -> None:
    uni = pd.read_parquet(UNI, columns=["hex_id"])
    # Stub: emit hex_id only. No HDB price columns at hex level.
    uni.to_parquet(OUT, index=False)
    print(f"Wrote stub (no HDB price features emitted) — {len(uni):,} rows: {OUT}")
    print("See script docstring for why HDB prices are dropped at hex level.")


if __name__ == "__main__":
    main()
