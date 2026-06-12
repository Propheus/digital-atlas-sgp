"""
Scenarios — mutations to the baseline state.

Three primitive knobs:
  1. add_transit_link(corridor_codes, speed_kmh, stop_time_min)
       Corridor = ordered list of subzone codes. For every pair along the
       corridor, overwrites T_transit-equivalent (T_bus / T_rail) with the
       faster corridor time if shorter. Also bleeds the benefit to walking-
       distance neighbours of corridor subzones.

  2. add_facility(subzone_code, category, count=1)
       Adds supply in the named subzone.

  3. remove_facility(subzone_code, category, count=1)
       Removes supply, clipped at zero.

A Scenario is a list of these mutations. When applied, it produces a mutated
(T, supply) tuple the caller can feed to Gravity.compute().
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Literal
import numpy as np

from .state import State, LARGE_MIN


MutationType = Literal["transit_link", "add_facility", "remove_facility"]


@dataclass
class Mutation:
    kind: MutationType
    # transit_link
    corridor: list[str] = field(default_factory=list)
    corridor_speed_kmh: float = 35.0       # BRT typical — 35 km/h between stops, incl. light dwell
    corridor_stop_min: float = 1.0         # seconds? No — minutes per intermediate stop
    adjacency_bleed_m: float = 1000.0      # km walkshed for adjacent subzones
    # facility
    subzone_code: str | None = None
    category: str | None = None            # "clinic" or "grocery"
    count: int = 1


@dataclass
class ScenarioResult:
    T_composite: np.ndarray      # mutated travel matrix
    supply: dict[str, np.ndarray]  # mutated supply (full dict, copied)
    notes: list[str]


class Scenario:
    def __init__(self, state: State):
        self.state = state
        self.mutations: list[Mutation] = []

    def add_transit_link(self, corridor: list[str], speed_kmh: float = 35.0, stop_min: float = 1.0) -> "Scenario":
        self.mutations.append(Mutation(
            kind="transit_link",
            corridor=list(corridor),
            corridor_speed_kmh=speed_kmh,
            corridor_stop_min=stop_min,
        ))
        return self

    def add_facility(self, subzone_code: str, category: str, count: int = 1) -> "Scenario":
        self.mutations.append(Mutation(
            kind="add_facility",
            subzone_code=subzone_code,
            category=category,
            count=count,
        ))
        return self

    def remove_facility(self, subzone_code: str, category: str, count: int = 1) -> "Scenario":
        self.mutations.append(Mutation(
            kind="remove_facility",
            subzone_code=subzone_code,
            category=category,
            count=count,
        ))
        return self

    # ----- apply -----

    def apply(self) -> ScenarioResult:
        s = self.state
        T = s.T_composite.copy()
        supply = {k: v.copy() for k, v in s.supply.items()}
        notes: list[str] = []

        for m in self.mutations:
            if m.kind == "transit_link":
                if len(m.corridor) < 2:
                    notes.append(f"transit_link: corridor too short ({len(m.corridor)} sz)")
                    continue
                # Map to indices
                try:
                    corridor_idx = [s.idx(c) for c in m.corridor]
                except KeyError as e:
                    notes.append(f"transit_link: unknown subzone {e}")
                    continue

                # Euclidean distance along corridor segments (proxy for ride dist)
                lat0 = float(s.home_lat.mean())
                mx = np.cos(np.deg2rad(lat0)) * 111320.0
                my = 111320.0
                hx = (s.home_lon * mx).astype(np.float64)
                hy = (s.home_lat * my).astype(np.float64)

                # Corridor-to-corridor cumulative distance from consecutive pairs
                cum = np.zeros(len(corridor_idx))
                for k in range(1, len(corridor_idx)):
                    a, b = corridor_idx[k - 1], corridor_idx[k]
                    d_m = np.hypot(hx[a] - hx[b], hy[a] - hy[b])
                    cum[k] = cum[k - 1] + d_m

                speed_m_min = m.corridor_speed_kmh * 1000 / 60
                # Time between any two corridor subzones (including intermediate stops)
                for ki in range(len(corridor_idx)):
                    for kj in range(len(corridor_idx)):
                        if ki == kj:
                            continue
                        i = corridor_idx[ki]
                        j = corridor_idx[kj]
                        dist = abs(cum[kj] - cum[ki])
                        stops_between = abs(kj - ki) - 1
                        t_new = dist / speed_m_min + stops_between * m.corridor_stop_min
                        if t_new < T[i, j]:
                            T[i, j] = t_new

                # Adjacency bleed: for each non-corridor subzone close to a corridor subzone,
                # assume a short walk then use corridor time.
                walk_speed_m_min = 4.0 * 1000 / 60  # 4 km/h
                for kc, c_idx in enumerate(corridor_idx):
                    for i in range(s.n):
                        if i in corridor_idx:
                            continue
                        d_to_c = np.hypot(hx[i] - hx[c_idx], hy[i] - hy[c_idx])
                        if d_to_c > m.adjacency_bleed_m:
                            continue
                        walk_t = (d_to_c / walk_speed_m_min) * 1.8  # walk penalty
                        # For each OTHER corridor subzone j, update T[i, j] = walk + T[c, j]
                        for kj, j in enumerate(corridor_idx):
                            if j == c_idx:
                                continue
                            t_new = walk_t + T[c_idx, j]
                            if t_new < T[i, j]:
                                T[i, j] = t_new
                            # symmetric
                            if t_new < T[j, i]:
                                T[j, i] = t_new
                notes.append(
                    f"transit_link: {len(m.corridor)} subzones, "
                    f"{cum[-1]/1000:.1f} km corridor at {m.corridor_speed_kmh:.0f} km/h"
                )

            elif m.kind == "add_facility":
                key = _supply_key(m.category)
                if key not in supply:
                    notes.append(f"add_facility: unknown category {m.category}")
                    continue
                try:
                    i = s.idx(m.subzone_code)
                except KeyError:
                    notes.append(f"add_facility: unknown subzone {m.subzone_code}")
                    continue
                supply[key][i] += float(m.count)
                notes.append(f"add_facility: +{m.count} {m.category} at {m.subzone_code}")

            elif m.kind == "remove_facility":
                key = _supply_key(m.category)
                if key not in supply:
                    notes.append(f"remove_facility: unknown category {m.category}")
                    continue
                try:
                    i = s.idx(m.subzone_code)
                except KeyError:
                    notes.append(f"remove_facility: unknown subzone {m.subzone_code}")
                    continue
                supply[key][i] = max(0.0, supply[key][i] - float(m.count))
                notes.append(f"remove_facility: -{m.count} {m.category} at {m.subzone_code}")

        return ScenarioResult(T_composite=T, supply=supply, notes=notes)


def _supply_key(category: str | None) -> str:
    if category == "clinic":
        return "chas_clinics"
    if category == "grocery":
        return "fairprice"
    return category or ""


if __name__ == "__main__":
    from .state import load_state
    from .gravity import Gravity
    s = load_state()
    g = Gravity(s)
    g.calibrate_all()

    # Example: open BRT corridor through 3 subzones + add a clinic + a FairPrice
    scen = Scenario(s)
    # Pick three codes that exist
    codes_available = [c for c in s.codes if s.included[s.idx(c)]][:3]
    scen.add_transit_link(codes_available, speed_kmh=40)
    scen.add_facility(codes_available[0], "clinic", count=1)
    scen.add_facility(codes_available[0], "grocery", count=1)
    result = scen.apply()
    print("Scenario notes:")
    for n in result.notes:
        print(f"  - {n}")
    print(f"T diff from baseline: {(s.T_composite != result.T_composite).sum()} cells changed")
    r = g.compute("clinic", T_override=result.T_composite, supply_override=result.supply["chas_clinics"])
    print(f"post-scenario clinic total visits: {r.total_visits:,.0f}")
