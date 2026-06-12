# Alchemy Metric Ontology — the urban-reasoning kernel

The knowledge Gemma does **not** have: what Singapore's proprietary urban metrics *mean*, their scale,
which direction is "good", and how to *chain* them into a conclusion. This document is the canonical
reference for (a) the context-injection key shown to the model, (b) the deterministic reasoning-data
generator, and (c) the verifier. Directionality calls here are **load-bearing** — they decide what the
verifier scores as correct.

> Division of labour: the **values** of these metrics are facts → they come from the atlas (RAG/tool).
> The **semantics + chaining rules** below are what we bake into the weights. A model that has internalised
> this kernel reasons like a location analyst; a model without it (vanilla Gemma) ignores the metrics.

---

## 1. Metric families

### A. Demand pull — `pull_*`  (0 → ~0.76, distance-decay attraction to major anchors)
How strongly an area is *pulled* toward a major regional anchor (closer/larger ⇒ higher).
| metric | meaning | high = | low = |
|---|---|---|---|
| `pull_cbd` | gravity toward the Central Business District | central / commute-in to CBD | peripheral |
| `pull_mall` | pull of major malls | near big retail | retail-isolated |
| `pull_hospital` | pull of major hospitals | good acute-care access | far from hospitals |
| `pull_mrt_interchange` | pull of MRT interchanges | highly rail-connected | rail-thin |
| `pull_school_premium` | pull of premium/branded schools | in a sought school belt | outside it |
| `pull_airport` | pull of Changi | east / airport-oriented | far |
| `pull_composite` | blended demand pull | a well-connected, "central-feeling" location | an edge/dormitory location |

### B. Anchor strength — `mg_<category>_anchor_strength`  (≈0 → 500+, **the demand-generation signal**)
How strongly a category **draws people / generates footfall** to the area (magnet places, review-weighted) —
**our demand generator.** 23 categories (shopping_retail, restaurant, cafe_coffee, fast_food, beauty_personal,
services, entertainment_culture, transportation, business_office, fitness_recreation, hotel_hospitality, hawker,
health_medical, supermarket, bakery, …). **High anchor = strong demand generation: proven pull, a good
catchment — a POSITIVE signal.** It is *not* a saturation warning (that's `sat_`/competition). For opportunity,
it is the footfall axis; pair it with `gap_C` (is the category under-provided?) and `sat_C`/competition.

### C. Demand support — `mg_<category>_support_400m`  (nearby supporting-amenity density within a 400 m walk)
The **demand-side ecosystem** around the category: how much supporting footfall/amenity exists within walking
distance. High = a live catchment; low = thin surroundings.

### D. Provision gap — `gap_<category>`  (−1 → +1, **the under/over-served verdict, pre-computed**)
The atlas's own normalised provision signal (9 categories: cafe_coffee, restaurant, hawker, fast_food,
supermarket, bakery, beauty_personal, fitness_recreation, health_medical).
**Empirically (corr ≈ −0.77 with per-capita provision):**
| value | meaning | implication |
|---|---|---|
| `gap_C → +1` | **under-served** for category C | unmet demand → opportunity signal |
| `gap_C ≈ 0` | balanced provision | adequately served |
| `gap_C → −1` | **over-served / saturated** | crowded, hard for a new entrant |

### E. Saturation — `sat_<category>_per_1k`  (provision per 1,000 residents, 0 → ~190)
Raw per-capita provision. High = lots of that category per resident (well/over-served); low = scarce.
Inverse-ish of opportunity. (Pairs with `gap_`: high `sat` ↔ low `gap`.)

### F. Synergy — `syn_*`  (multiplicative co-presence interactions)
Where two ingredients reinforce each other: `syn_pop_x_walk`, `syn_pop_x_transit`, `syn_office_x_transit`,
`syn_retail_x_anchors`, `syn_density_x_amenities`, `syn_far_x_transit`, `syn_residential_x_school`,
`syn_premium_school_x_4r`. High = the combination is strongly present (e.g. dense **and** walkable).

### G. Composite indices  (0 → 1)
| metric | high = |
|---|---|
| `vibrancy_index` | lively, lots happening |
| `commercial_intensity` | commercial/retail heavy |
| `density_pressure` | crowding pressure on infrastructure |
| `walkability_score` | pedestrian-friendly |
| `nl_commercial_indicator` | night-light commercial activity |

### H. Friction / context — `mg_avg_*`
`mg_avg_competitors_400m` (saturation of same-category competitors nearby — high = competitive),
`mg_avg_anchor_strength` (overall magnet pull of the area), `mg_avg_walk_dist_mrt_m` (metres to MRT — **lower
is better**).

---

## 2. Directionality — "which way is good" (the verifier's truth table)

| signal | "good / opportunity" direction | notes |
|---|---|---|
| `pull_*`, accessibility | higher | more connected |
| `mg_avg_walk_dist_mrt_m` | **lower** | closer to rail |
| `gap_C` | **higher = more under-served = bigger opportunity** for C | the atlas verdict |
| `sat_C_per_1k`, `mg_avg_competitors_400m` | **lower = less saturated** | for a new entrant |
| `anchor_strength` (demand generator) | **higher = more demand drawn = good catchment** | NOT saturation — that's `sat_`/competitors |
| `support_400m` | higher = stronger catchment | demand-side |

**Anchor = demand generator (RESOLVED).** High `anchor_strength` means the area *generates* demand for that
category — footfall, proven pull. It is a **POSITIVE** signal, not a saturation warning. Demand and provision
are **orthogonal axes**:
- **Demand axis** — `anchor_strength` (+ `support_400m`): how much footfall/demand the area pulls in.
- **Provision axis** — `gap_C` (unmet) ↔ `sat_C` / `mg_*_pressure_400m` / `competitors` (saturated).

→ **A strong site = high demand generation (anchors/footfall) × unmet category gap (`gap_C` high) × low
saturation (`sat_C`/competitors low).** You *ride the footfall into the under-served category.* Saturation lives
only in `sat_`/pressure/competitors — never in anchor.

---

## 3. Valid reasoning chains (what we teach)

Each chain is deterministic where it ends in a `gap_/sat_/pull_/rank` fact, and **estimate-with-caveat**
where it ends in a forward-looking verdict.

1. **What is this area a draw for?** → `argmax(anchor_strength)` → "regionally known for shopping & dining."
   *(deterministic)*
2. **Is area X under-served for category C?** → `gap_C`: +ve ⇒ yes, under-served; −ve ⇒ over-served.
   *(deterministic — atlas verdict)*
3. **Best category to open in X?** → the area's **demand generation** (anchors/`support_C`/footfall) makes a
   site viable; within that, pick the highest `gap_C` (most under-served) with tolerable `sat_C`/`competitors`.
   *Ride the footfall into the gap.* *(deterministic ranking; the final "open this" is a caveated recommendation.)*
4. **Where in region R is the biggest gap for C?** → `rank(gap_C, scope=R, desc)`. *(deterministic)*
5. **Is X saturated for C?** → high `sat_C_per_1k` + high `competitors` + low/negative `gap_C`. *(deterministic)*
6. **How accessible / central is X?** → `pull_composite`, `pull_mrt_interchange`, `mg_avg_walk_dist_mrt_m`.
   *(deterministic)*
7. **Why is X vibrant / commercial?** → decompose `vibrancy_index` / `commercial_intensity` by the
   anchors & synergies driving it. *(deterministic decomposition; the "why" framing is interpretive.)*
8. **What-if (add transit / amenity)?** → analog to a comparable better-served area; commit to a *direction*,
   label magnitude **"an estimate, not a forecast."** *(judgment — never emitted as fact, `mrt_gap_analog` mold.)*

---

## 4. Deterministic vs judgment (the verifiability line)

- **Deterministic (verifier scores correctness, GRPO-rewardable):** ranking/compare/argmax/aggregate over
  any column; under-served diagnosis via `gap_/sat_`; accessibility via `pull_`; "known-for" via `anchor`.
- **Judgment (show the chain + explicit caveat, never "verified fact"):** forward-looking siting
  recommendations, what-if magnitudes, "best place to live for me" — grounded in the deterministic signals
  above but ending in an estimate.

This line is the whole game: it lets us mass-generate **correct** reasoning, and keeps verdicts honest.

---

## 5. How the kernel is used
1. **Context injection** — a compact version of §1 (a one-line key per relevant metric + its value) is prepended
   so the model reasons over real numbers instead of ignoring them.
2. **Tool layer** — `atlas_tools` exposes `rank/compare/gap/pull` over these columns; the model calls them for
   exact, fresh answers (the durable moat — Gemma can't call a metric it doesn't know exists).
3. **Training data** — the deterministic chains in §3 become a verifiable reasoning-data family; verdicts use the
   caveated mold; GRPO uses the verifier as reward.
