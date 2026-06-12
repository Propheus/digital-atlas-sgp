# Alchemy — the Urban Reasoning Model (master design)

Combining every data layer into one model that reasons about a place the way a senior urban analyst would —
**grounded, cross-layer, and verifiable.** This supersedes the single-layer view in `ALCHEMY_METRIC_ONTOLOGY.md`
(which it now extends to all layers).

The intelligence is **not** in any one layer — those are lookups. It is in **reasoning *across* layers**:
> *Young families [people] who commute far out [movement], under-served for childcare [demand–supply], in an
> area with rising night-lights and new resale activity [form/activity] → an emerging family node with a
> childcare + F&B opportunity.* No single layer says that; no general model can assemble it.

---

## 1. The six layers (396 features, grouped)

| # | Layer | What it answers | Key signals |
|---|---|---|---|
| **L1** | **People** | who lives here | `pop_*`, age splits (`0_14/15_64/65plus`), `pop_hdb_share`, `pop_dorm`, `nonres_share` |
| **L2** | **Affluence / housing** | how well-off, what housing | `hdb_resale_median_psm`, `_4r_median`, `avg_lease_remaining_yrs`, HDB vs private, `pull_school_premium` |
| **L3** | **Movement** | how people move | `mrt/bus_*`, `dist_mrt_m`, `max_transit_score`, `daily_bus_taps` (LTA DataMall), **OD matrix**, `wp_pop`, self-containment |
| **L4** | **Places** | what's here | 190k POIs, 55 categories (`pc_cat_*`), brands, magnets, ratings/reviews |
| **L5** | **Demand–Supply (emergent)** | what's missing / saturated / drawing | `*_anchor_strength`, `*_support_400m`, `*_pressure_400m`, `gap_*`, `sat_*_per_1k`, `pull_*`, `syn_*` |
| **L6** | **Form & Activity** | the built fabric & pulse | `lu_*` land-use mix, `lu_entropy`, buildings/footprint, `nl_commercial_indicator`, `commercial_intensity` |
| **★** | **Outcome indices** | the atlas's own verdicts | `livability_index`, `family_index`, `vibrancy_index`, `walkability_score`, `density_pressure` |

---

## 2. Cross-layer reasoning patterns (the moat)

Each pattern chains 2-4 layers. Where it ends in a **computed column** it is *verifiable*; where it ends in a
forward verdict it is a *caveated estimate*.

1. **Archetype / typology** — L1+L2+L4+L6 → "mature family heartland", "young-professional enclave",
   "industrial-adjacent dormitory", "emerging mixed-use node". *(verifiable if we fix a deterministic
   rule over the layers; else caveated.)*
2. **Demand–supply mismatch, demographically weighted** — L1 × L5 → "high elderly share **and** a health_medical
   gap ⇒ under-served for senior care." *(verifiable: gap_ + demographic fact.)*
3. **Accessibility × opportunity** — L3 × L5 → "well-connected (high pull, low MRT-dist) **but** under-served for
   X ⇒ prime site." *(verifiable signals; the "site" recommendation is caveated.)*
4. **Behavioural role** — L3 (OD self-containment, wp_pop) × L6 → "bedroom community vs employment hub vs
   balanced." *(verifiable from self-containment + jobs.)*
5. **Equity / vulnerability** — L2 (low resale, old lease) × L5 (gaps) × L3 (transit-poor) → "under-served
   vulnerable area." *(verifiable composite; flag, don't moralise.)*
6. **Emergence / change** — L6 (night-lights, new construction) × L2 (resale 12m) → "an area on the up."
   *(directional; caveated — limited time series.)*
7. **Index decomposition ("why")** — ★ × drivers → "livability is 0.7 here, driven by walkability + amenity
   support, held back by density pressure." *(verifiable: the index value is real; the decomposition is the chain.)*
8. **Index ranking ("best for")** — ★ argmax/rank → "most family-friendly subzone in the West = …"
   *(fully verifiable — `family_index` is pre-computed.)*

**Why outcome indices are the unlock:** `family_index`, `livability_index`, `vibrancy_index` are *already
computed cross-layer outcomes*. So "which area is best for families?" or "why is X livable?" have a **real gold
answer** — we train the model to reproduce the index AND narrate the drivers. That makes cross-layer *verdicts*
verifiable, which a heuristic-scored model can never be.

---

## 3. The verifiability line (unchanged, applied to all layers)
- **Deterministic** → any computed column: facts, ranks, gaps, pulls, **and the outcome indices**. `verify()`
  works; GRPO-rewardable.
- **Judgment** → forward recommendations, what-ifs, emergence magnitudes → grounded in the above, emitted as
  explicit estimates (the `mrt_gap_analog` mold).

---

## 4. Architecture — three layers of knowing

```
   user question
        │
        ▼
  ┌───────────────────────────────────────────────┐
  │ REASONING (in the weights)                     │  ← the fine-tune: which layers matter for this Q,
  │  layer semantics · cross-layer chains · the     │     how to chain them, the SG-calibrated reading,
  │  verifiability line · honest abstention · voice │     verdict-first, caveat discipline
  └───────────────────────────────────────────────┘
        │ calls                          ▲ injects
        ▼                                │
  ┌──────────────────┐        ┌──────────────────────┐
  │ TOOLS (atlas_tools)│      │ CONTEXT (RAG)          │
  │ rank/gap/pull/od/  │      │ compact cross-layer    │
  │ index — exact,fresh│      │ profile of the area    │
  └──────────────────┘        └──────────────────────┘
        └──────────── the deterministic atlas (396 cols + OD) ───────────┘
```
Facts & exact lookups from the atlas; the *cross-layer reasoning* from the weights. Gemma has none of the three
for this domain.

---

## 5. Build plan (extends the reasoning roadmap)
1. **Cross-layer context injection** — surface one compact signal per layer (people, affluence, movement,
   places, demand-supply, activity, + the outcome indices) so the live model reasons across all six. *(start now)*
2. **Cross-layer generator** — extend `generate_metric_reasoning.py` with the §2 patterns; every pattern ending
   in a computed column (esp. the outcome indices) is verifiable; typology/what-if caveated.
3. **Index-decomposition family** — train "what is `family_index` here and why" with the real value + driver
   chain → teaches genuine cross-layer synthesis with a checkable target.
4. **Tools per layer** + **SFT v1** + **GRPO** (verifier reward) + a **cross-layer held-out benchmark** — the
   number that proves it: Gemma can't reproduce `family_index` from the raw layers; Alchemy can, and explains it.

---

## 6. One-liner
A model that holds the *semantics and cross-layer chains* of Singapore's six urban data layers in its weights,
pulls every *fact* from a deterministic atlas, and reasons to verdicts that are each either a verifiable fact or
an honestly-caveated estimate — the urban analyst general models can't be.
