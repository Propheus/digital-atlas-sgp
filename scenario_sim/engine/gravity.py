"""
Gravity — Huff / multinomial logit destination choice model.

For category c, probability that a resident in subzone j visits a facility in
subzone i:

    P(i | j, c) = S(i,c) * exp(-β_c * T_c[i,j])  /  Σ_k [ S(k,c) * exp(-β_c * T_c[k,j]) ]

Outputs computed for each category:
  - A(j, c)  : logsum accessibility in minutes-equivalent welfare units
               A(j,c) = (1/β_c) * log Σ_i S(i,c) * exp(-β_c * T_c[i,j])
  - L(i, c)  : facility load at subzone i (sum of visits attracted from all j)
  - F(i, j)  : the full flow matrix (optional, expensive — compute on demand)

The parameter budget (per category):
  - β                   : distance decay (1/min). Fit to match median catchment.
  - visit_rate_per_cap  : base monthly visits per person
  - persona weights     : multipliers per persona class (elderly / working / young)

Visit rates and persona weights are priors (from public-health and retail
literature), not fitted to data. β is calibrated once at init against a target
median trip distance.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Literal
import numpy as np

from .state import State, LARGE_MIN


Category = Literal["clinic", "grocery"]


@dataclass
class CategoryParams:
    name: Category
    supply_key: str                     # key into State.supply
    beta: float                         # distance decay 1/min
    visit_rate_base: float              # monthly visits per person (adults baseline)
    persona_weights: tuple[float, float, float]  # (elderly, working, young) multipliers
    target_median_catchment_km: float   # used during calibration

    # For T selection: composite by default. Can override per-category later.
    travel_matrix_key: str = "T_composite"


DEFAULT_PARAMS: dict[Category, CategoryParams] = {
    "clinic": CategoryParams(
        name="clinic",
        supply_key="chas_clinics",
        beta=0.12,                        # initial guess, will be calibrated
        visit_rate_base=0.45,             # ~5 visits/year base
        persona_weights=(2.5, 1.0, 1.3),  # elderly visit clinics much more; young somewhat more (kids)
        target_median_catchment_km=1.5,
    ),
    "grocery": CategoryParams(
        name="grocery",
        supply_key="fairprice",           # modelled category; background adds to "all supply" implicitly
        beta=0.06,
        visit_rate_base=4.0,
        persona_weights=(0.8, 1.0, 0.7),  # elderly shop less (smaller households); families more
        target_median_catchment_km=2.5,
    ),
}


@dataclass
class GravityResult:
    category: Category
    A: np.ndarray           # (n,) logsum accessibility
    L: np.ndarray           # (n,) facility load
    prob: np.ndarray        # (n, n) P(i|j) — rows are origins, cols are destinations
    #   prob[j, i] = probability that resident at j visits facility at i
    demand: np.ndarray      # (n,) per-resident demand rate applied (monthly)
    total_visits: float


class Gravity:
    def __init__(self, state: State, params: dict[Category, CategoryParams] | None = None):
        self.state = state
        self.params = params or {k: CategoryParams(**v.__dict__) for k, v in DEFAULT_PARAMS.items()}
        self._cache: dict[tuple[Category, int], GravityResult] = {}

    # ----- core compute -----

    def compute(self, category: Category, T_override: np.ndarray | None = None,
                supply_override: np.ndarray | None = None) -> GravityResult:
        """
        Compute the gravity allocation for `category`.

        T_override lets callers pass a mutated travel matrix (e.g. after a BRT scenario).
        supply_override lets callers pass a mutated supply vector (e.g. adding a new facility).
        """
        s = self.state
        p = self.params[category]
        T = T_override if T_override is not None else getattr(s, p.travel_matrix_key)
        S = supply_override if supply_override is not None else s.supply[p.supply_key]

        # Clamp T at LARGE_MIN so exp(-β * large) ≈ 0 without overflow
        T_clamped = np.minimum(T, LARGE_MIN).astype(np.float32)

        # Utility: U(i|j) = log(S_i) - β * T[j, i]
        # Avoid log(0) by adding a tiny epsilon to zero-supply facilities
        S_safe = S + 1e-9
        logS = np.log(S_safe)[None, :]                # (1, n)
        util = logS - p.beta * T_clamped              # (n, n), util[j, i]

        # Softmax stabilization: subtract row-max to avoid overflow
        util_max = util.max(axis=1, keepdims=True)
        exp_u = np.exp(util - util_max)
        denom = exp_u.sum(axis=1, keepdims=True)
        prob = exp_u / np.clip(denom, 1e-30, None)    # (n, n)

        # Demand per resident per month, persona-weighted
        demand_per_capita = (
            s.elderly_share * p.persona_weights[0]
            + s.working_share * p.persona_weights[1]
            + s.young_share * p.persona_weights[2]
        ) * p.visit_rate_base                          # (n,)

        # Exclude non-populated subzones from generating demand
        demand_per_capita = demand_per_capita * s.included.astype(np.float32)
        origin_demand = s.population.astype(np.float32) * demand_per_capita   # (n,)

        # Facility load: sum over origins of origin_demand × prob
        L = prob.T @ origin_demand                     # (n,)
        total_visits = float(origin_demand.sum())

        # Logsum accessibility: A(j) = (1/β) * [log(denom) + util_max_row]
        # = (1/β) * log Σ_i exp(util(i|j))
        A = (np.log(denom.squeeze(-1)) + util_max.squeeze(-1)) / p.beta  # (n,)

        return GravityResult(
            category=category,
            A=A.astype(np.float32),
            L=L.astype(np.float32),
            prob=prob.astype(np.float32),
            demand=demand_per_capita.astype(np.float32),
            total_visits=total_visits,
        )

    # ----- calibration -----

    def calibrate_beta(self, category: Category, grid: tuple[float, ...] | None = None) -> float:
        """
        Find the β that produces a median trip distance (weighted by flow)
        closest to the target catchment distance. Returns the best β and
        updates self.params[category].beta in place.
        """
        s = self.state
        p = self.params[category]
        grid = grid or tuple(np.logspace(np.log10(0.02), np.log10(0.5), 15))
        target_km = p.target_median_catchment_km

        # Euclidean distance matrix in km — used as the catchment distance metric.
        # We use lat/lon equirectangular projection for speed.
        lat0 = float(s.home_lat.mean())
        mx = np.cos(np.deg2rad(lat0)) * 111.320
        my = 111.320
        x = (s.home_lon * mx).astype(np.float32)
        y = (s.home_lat * my).astype(np.float32)
        dist_km = np.sqrt((x[:, None] - x[None, :]) ** 2 + (y[:, None] - y[None, :]) ** 2)

        best = None
        for beta in grid:
            p.beta = float(beta)
            res = self.compute(category)
            # flow: f[j, i] = origin_demand[j] * prob[j, i]
            origin_demand = (res.demand * s.population.astype(np.float32))
            flows = res.prob * origin_demand[:, None]            # (n, n)
            total_flow = flows.sum()
            if total_flow <= 0:
                continue
            weighted_dist = (flows * dist_km).sum() / total_flow
            # Median-equivalent: since the flow-weighted mean is simpler, use mean as proxy.
            err = abs(weighted_dist - target_km)
            if best is None or err < best[0]:
                best = (err, float(beta), float(weighted_dist))

        if best is None:
            raise RuntimeError(f"calibrate_beta({category}) produced no valid β")
        _, best_beta, best_dist = best
        p.beta = best_beta
        return best_beta

    def calibrate_all(self) -> dict[Category, float]:
        return {c: self.calibrate_beta(c) for c in self.params.keys()}

    # ----- convenience -----

    def adequacy_index(self, category: Category, result: GravityResult | None = None) -> np.ndarray:
        """
        Convert logsum accessibility A(j) into a 0-100 score, relative to the
        population-weighted distribution across included subzones.
        """
        s = self.state
        res = result or self.compute(category)
        A = res.A.copy()
        inc = s.included
        # Rank-scale to [0, 100] based on included subzones only
        if inc.sum() == 0:
            return np.zeros_like(A)
        vals = A[inc]
        ranks = np.argsort(np.argsort(vals))
        score = np.zeros_like(A)
        score[inc] = (ranks / max(len(ranks) - 1, 1)) * 100.0
        return score.astype(np.float32)


if __name__ == "__main__":
    from .state import load_state
    s = load_state()
    g = Gravity(s)
    print("Calibrating β...")
    betas = g.calibrate_all()
    print(f"calibrated: {betas}")
    for cat in ("clinic", "grocery"):
        r = g.compute(cat)
        print(f"\n{cat}: β={g.params[cat].beta:.4f}")
        print(f"  total visits/mo: {r.total_visits:,.0f}")
        print(f"  A percentile (included): p10={np.percentile(r.A[s.included],10):.1f} "
              f"p50={np.percentile(r.A[s.included],50):.1f} "
              f"p90={np.percentile(r.A[s.included],90):.1f}")
        adq = g.adequacy_index(cat, r)
        worst = np.argsort(adq[s.included])[:5]
        print(f"  5 worst adequacy (included):")
        inc_idx = np.where(s.included)[0]
        for k in worst:
            i = inc_idx[k]
            print(f"    {s.codes[i]} ({s.subzone_name[i]}, {s.planning_area[i]}): "
                  f"A={r.A[i]:.1f}  adq={adq[i]:.0f}  pop={s.population[i]}")
