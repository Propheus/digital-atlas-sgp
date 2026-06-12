"""
Opportunity — marginal welfare gain ranking for where to build next.

For each candidate subzone i (and each category c), compute the change in total
population-weighted accessibility if we added one unit of supply at i:

    Opp(i, c) = Σ_j Pop(j) · [A'(j, c) − A(j, c)]

where A'(j, c) is the logsum accessibility after S(i, c) += 1.

Optional adjustments:
  - λ (cannibalisation weight): subtract λ × the load diverted from existing
    facilities. λ=0 is welfare-maximising (good for public policy). λ>0 is
    "protected expansion" (good for brand strategy).
  - feasibility mask: drop candidates in excluded subzones.

Also produces:
  - top_opportunities: top-K by Opp
  - redundancy: facilities in over-served subzones (candidates for consolidation)
  - three_takeaways: a narrative (top opp, top redundancy, biggest loser)
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Literal
import numpy as np

from .state import State
from .gravity import Gravity, GravityResult, Category


@dataclass
class OpportunityResult:
    category: Category
    opp_raw: np.ndarray              # (n,) raw ΔW in person-minutes
    opp_score: np.ndarray            # (n,) 0-100 normalised (among feasible)
    cannib: np.ndarray               # (n,) diverted load from existing facilities
    feasible: np.ndarray             # (n,) bool mask
    top_opportunities: list[dict]    # ranked list (each: {subzone_code, name, planning_area, opp, pop, ...})


@dataclass
class RedundancyResult:
    category: Category
    redundancy: np.ndarray           # (n,) fraction of load lost relative to baseline
    top_redundant: list[dict]


@dataclass
class Takeaways:
    top_opportunity: dict | None
    top_redundancy: dict | None
    biggest_loser: dict | None       # subzone whose accessibility dropped the most
    narrative: list[str]


class Opportunity:
    def __init__(self, state: State, gravity: Gravity):
        self.state = state
        self.gravity = gravity

    # ----- opportunity -----

    def rank(
        self,
        category: Category,
        T_override: np.ndarray | None = None,
        supply_override: np.ndarray | None = None,
        lam: float = 0.0,
        top_k: int = 10,
    ) -> OpportunityResult:
        s = self.state
        g = self.gravity
        # Baseline under the current (possibly scenario-mutated) state
        baseline = g.compute(category, T_override=T_override, supply_override=supply_override)

        T = T_override if T_override is not None else getattr(s, g.params[category].travel_matrix_key)
        S = supply_override.copy() if supply_override is not None else s.supply[g.params[category].supply_key].copy()

        # Pop-weighted baseline welfare (only included subzones generate demand)
        pop = s.population.astype(np.float32) * s.included.astype(np.float32)
        W_base = float((pop * baseline.A).sum())

        # Feasibility: only included subzones
        feasible = s.included.copy()
        # Additional filter: reject tiny population subzones even if "included"
        feasible = feasible & (s.population >= 1000)

        n = s.n
        opp_raw = np.zeros(n, dtype=np.float64)
        cannib = np.zeros(n, dtype=np.float64)

        # For each candidate, temporarily +1 and recompute
        for i in range(n):
            if not feasible[i]:
                continue
            S_new = S.copy()
            S_new[i] += 1
            res_new = g.compute(category, T_override=T, supply_override=S_new)
            W_new = float((pop * res_new.A).sum())
            opp_raw[i] = W_new - W_base

            # Cannibalisation: how much load was taken from non-i facilities
            diff = baseline.L - res_new.L                # positive = lost load
            # Sum only where i != idx and diff > 0
            diff[i] = 0
            cannib[i] = float(np.clip(diff, 0, None).sum())

        opp_adjusted = opp_raw - lam * cannib

        # 0-100 scaled opportunity score among feasible
        opp_score = np.zeros(n, dtype=np.float32)
        if feasible.any():
            vals = opp_adjusted[feasible]
            if vals.max() > vals.min():
                ranks = np.argsort(np.argsort(vals))
                opp_score[feasible] = (ranks / max(len(ranks) - 1, 1)) * 100
            else:
                opp_score[feasible] = 50.0

        # Build ranked list
        feas_idx = np.where(feasible)[0]
        sorted_feas = feas_idx[np.argsort(-opp_adjusted[feas_idx])]
        top_opps = []
        for k, i in enumerate(sorted_feas[:top_k]):
            top_opps.append({
                "rank": k + 1,
                "subzone_code": s.codes[i],
                "subzone_name": str(s.subzone_name[i]),
                "planning_area": str(s.planning_area[i]),
                "opportunity_raw": float(opp_raw[i]),
                "opportunity_adjusted": float(opp_adjusted[i]),
                "opportunity_score": float(opp_score[i]),
                "cannibalization": float(cannib[i]),
                "population": int(s.population[i]),
                "current_supply": int(S[i]),
            })

        return OpportunityResult(
            category=category,
            opp_raw=opp_raw.astype(np.float32),
            opp_score=opp_score,
            cannib=cannib.astype(np.float32),
            feasible=feasible,
            top_opportunities=top_opps,
        )

    # ----- redundancy -----

    def redundancy(
        self,
        category: Category,
        baseline_L: np.ndarray,
        scenario_L: np.ndarray,
        threshold: float = 0.30,
        top_k: int = 10,
    ) -> RedundancyResult:
        s = self.state
        key = self.gravity.params[category].supply_key
        S = s.supply[key]
        # Only existing facilities can become redundant
        has_facility = S > 0
        loss = np.where(has_facility, np.clip(baseline_L - scenario_L, 0, None) / np.clip(baseline_L, 1, None), 0)
        top = np.argsort(-loss)
        top_red = []
        for i in top[:top_k]:
            if not has_facility[i] or loss[i] < threshold:
                continue
            top_red.append({
                "subzone_code": s.codes[i],
                "subzone_name": str(s.subzone_name[i]),
                "planning_area": str(s.planning_area[i]),
                "facility_count": int(S[i]),
                "baseline_load": float(baseline_L[i]),
                "scenario_load": float(scenario_L[i]),
                "loss_frac": float(loss[i]),
            })
        return RedundancyResult(
            category=category,
            redundancy=loss.astype(np.float32),
            top_redundant=top_red,
        )

    # ----- takeaways -----

    def takeaways(
        self,
        category: Category,
        baseline_A: np.ndarray,
        scenario_A: np.ndarray,
        opp_result: OpportunityResult,
        redundancy_result: RedundancyResult,
    ) -> Takeaways:
        s = self.state
        pop = s.population.astype(np.float32) * s.included.astype(np.float32)
        delta = scenario_A - baseline_A
        weighted = delta * pop
        loser_idx = int(np.argmin(weighted))

        top_opp = opp_result.top_opportunities[0] if opp_result.top_opportunities else None
        top_red = redundancy_result.top_redundant[0] if redundancy_result.top_redundant else None
        biggest = {
            "subzone_code": s.codes[loser_idx],
            "subzone_name": str(s.subzone_name[loser_idx]),
            "planning_area": str(s.planning_area[loser_idx]),
            "delta_A": float(delta[loser_idx]),
            "population": int(s.population[loser_idx]),
        } if weighted[loser_idx] < 0 else None

        narrative: list[str] = []
        if top_opp:
            narrative.append(
                f"Top {category} opportunity: {top_opp['subzone_name']} ({top_opp['planning_area']}). "
                f"Score {top_opp['opportunity_score']:.0f}/100, population {top_opp['population']:,}."
            )
        if top_red:
            narrative.append(
                f"Most at-risk {category} facility: {top_red['subzone_name']} "
                f"({top_red['loss_frac']*100:.0f}% load loss)."
            )
        if biggest:
            narrative.append(
                f"Biggest loser: {biggest['subzone_name']} ({biggest['delta_A']:+.1f} min accessibility)."
            )
        if not narrative:
            narrative.append("No significant opportunities, redundancies, or losers under this scenario.")

        return Takeaways(
            top_opportunity=top_opp,
            top_redundancy=top_red,
            biggest_loser=biggest,
            narrative=narrative,
        )


if __name__ == "__main__":
    from .state import load_state
    s = load_state()
    g = Gravity(s)
    g.calibrate_all()
    o = Opportunity(s, g)

    for cat in ("clinic", "grocery"):
        print(f"\n===== {cat.upper()} =====")
        res = o.rank(cat, lam=0.0, top_k=5)
        for row in res.top_opportunities:
            print(f"  #{row['rank']}  {row['subzone_code']:8}  {row['subzone_name'][:25]:25}  "
                  f"{row['planning_area'][:14]:14}  score={row['opportunity_score']:5.1f}  "
                  f"pop={row['population']:6,}  cur={row['current_supply']}")
