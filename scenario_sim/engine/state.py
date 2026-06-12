"""
State — the t=0 world snapshot loaded from cache/.

Loads all pre-computed parquets into numpy/pandas structures. Provides indices,
population vectors, the travel matrix, supply vectors, and persona-derived
demand modifiers for downstream engine use.

All arrays are indexed by `codes` order (sorted subzone_code). This is the
canonical index for the whole engine.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
import numpy as np
import pandas as pd

CACHE_DIR = Path(__file__).parent.parent / "cache"

# Sentinel used in T for "unreachable by this mode"
LARGE_MIN = 999.0


@dataclass
class State:
    # Indexing
    codes: list[str]                 # ordered subzone codes (length n)
    code_to_idx: dict[str, int]
    n: int                           # number of subzones

    # Tabular state
    state_df: pd.DataFrame           # subzone_state: name, population, shares, flags

    # Numeric vectors (length n), aligned to codes
    population: np.ndarray           # int
    elderly_share: np.ndarray
    working_share: np.ndarray
    young_share: np.ndarray
    included: np.ndarray             # bool, True for non-excluded subzones

    # Travel matrices (n × n)
    T_walk: np.ndarray
    T_drive: np.ndarray
    T_rail: np.ndarray
    T_bus: np.ndarray
    T_composite: np.ndarray          # min across all modes (baseline)

    # Supply vectors per category (name -> array length n, integer counts)
    supply: dict[str, np.ndarray]

    # For display/geometry — lat/lon of home points
    home_lat: np.ndarray
    home_lon: np.ndarray

    # Planning area / region for grouping
    planning_area: np.ndarray        # object (strings)
    region: np.ndarray
    subzone_name: np.ndarray

    def idx(self, code: str) -> int:
        return self.code_to_idx[code]

    def describe(self) -> str:
        lines = [
            f"State: n={self.n} subzones  (included: {int(self.included.sum())})",
            f"  total population: {int(self.population[self.included].sum()):,}",
            f"  supply: " + "  ".join(f"{k}={int(v.sum())}" for k, v in self.supply.items()),
            f"  T_composite median: {np.median(self.T_composite[self.T_composite<LARGE_MIN]):.1f} min",
        ]
        return "\n".join(lines)


def load_state(cache_dir: Optional[Path] = None) -> State:
    cache = Path(cache_dir) if cache_dir else CACHE_DIR

    state_df = pd.read_parquet(cache / "subzone_state.parquet")
    state_df = state_df.sort_values("subzone_code").reset_index(drop=True)
    codes = state_df["subzone_code"].tolist()
    code_to_idx = {c: i for i, c in enumerate(codes)}
    n = len(codes)

    # Travel matrix
    tm = np.load(cache / "travel_matrix.npz", allow_pickle=False)
    tm_codes = [c for c in tm["codes"]]
    # Verify order matches
    assert tm_codes == codes, "travel_matrix codes order differs from subzone_state order"
    T_walk = tm["T_walk"].astype(np.float32)
    T_drive = tm["T_drive"].astype(np.float32)
    T_rail = tm["T_rail"].astype(np.float32)
    T_bus = tm["T_bus"].astype(np.float32)
    T_composite = tm["T_composite"].astype(np.float32)

    # Facility supply
    fs = pd.read_parquet(cache / "facility_supply.parquet").set_index("subzone_code")
    fs = fs.reindex(codes).fillna(0)
    supply = {
        "chas_clinics": fs["chas_clinics"].to_numpy(dtype=np.float32),
        "fairprice": fs["fairprice"].to_numpy(dtype=np.float32),
        "grocery_background": fs["grocery_background"].to_numpy(dtype=np.float32),
        "total_grocery": fs["total_grocery"].to_numpy(dtype=np.float32),
    }

    # Centroids
    cent = pd.read_parquet(cache / "centroids.parquet").set_index("subzone_code").reindex(codes)

    return State(
        codes=codes,
        code_to_idx=code_to_idx,
        n=n,
        state_df=state_df,
        population=state_df["population"].to_numpy(dtype=np.int64),
        elderly_share=state_df["elderly_share"].to_numpy(dtype=np.float32),
        working_share=state_df["working_share"].to_numpy(dtype=np.float32),
        young_share=state_df["young_share"].to_numpy(dtype=np.float32),
        included=(~state_df["excluded"].to_numpy()),
        T_walk=T_walk,
        T_drive=T_drive,
        T_rail=T_rail,
        T_bus=T_bus,
        T_composite=T_composite,
        supply=supply,
        home_lat=cent["home_lat"].to_numpy(dtype=np.float64),
        home_lon=cent["home_lon"].to_numpy(dtype=np.float64),
        planning_area=state_df["planning_area"].to_numpy(),
        region=state_df["region"].to_numpy(),
        subzone_name=state_df["subzone_name"].to_numpy(),
    )


if __name__ == "__main__":
    s = load_state()
    print(s.describe())
    # Spot check a known subzone
    if "AMSZ01" in s.code_to_idx:
        i = s.idx("AMSZ01")
        print(f"\nAMSZ01 ({s.subzone_name[i]}):")
        print(f"  population: {s.population[i]}")
        print(f"  elderly_share: {s.elderly_share[i]:.3f}")
        print(f"  chas_clinics: {int(s.supply['chas_clinics'][i])}")
        print(f"  fairprice: {int(s.supply['fairprice'][i])}")
