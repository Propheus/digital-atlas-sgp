# Plexis-Mind — SGP Spatial-Reasoning LLM · Q&A Training-Set Strategy

**Plexis-Mind** is the reasoning layer on top of the **Plexis** atlas: a fine-tuned LLM that
*reasons spatially about Singapore*, grounded in the Plexis v4.9.0 atlas
(`azold-test-server:/home/azureuser/da-sgp/v4/`). The atlas is the data; Plexis-Mind is the mind.

**Status:** planning only. No pairs generated yet. This doc is the build spec.

**Question categories (from the brief):** Factual · Places · Reasoning · Patterns · Planning.

---

## 0. Decision #0 — what is the model *for*? (resolve before generating)

"Spatial reasoning for SGP" forks into two incompatible training targets. This choice
changes every per-category spec, so it is decision zero.

| Target | Means | Good for | Danger |
|---|---|---|---|
| **A. Reason-in-context** *(recommended primary)* | Relevant atlas rows are in the prompt (or RAG-injected) at inference. Model learns to **compose, compare, rank, infer**. | Robust to atlas updates; teaches transferable reasoning; numbers never go stale. | Needs a retrieval layer at inference. |
| **B. Parametric recall** | No data at inference; facts baked into weights. | Stable *structural* geography only ("Tampines is East Region, adjacent to Pasir Ris"). | For the 1,007 numeric features + 190K place stats this **bakes in numbers that go stale at v5.0 and actively teaches confident hallucination.** |

**Recommendation:** **A as the spine** (~80% of pairs carry their evidence in-context),
plus a **small B slice limited to stable geography** — the containment hierarchy,
region/PA membership, adjacency, named landmarks. **Explicitly out of scope:** memorizing
190K place stats or volatile numeric features into weights.

> Everything below assumes A-primary. If we instead want a pure closed-book oracle, the
> per-category volumes and the in-context evidence blocks change — flag now, not at QC.

---

## 1. Pipeline architecture (6 stages, dependency-ordered)

```
(0) objective lock ─► (1) fact + relation substrate ─► (2) deterministic answer engine
       ─► (3) per-category generation ─► (4) QC / verify ─► (5) eval design ─► (6) format + train
```

Quality is won at **(1)** and **(2)**; detail-effort is spent at **(3)**. The cardinal rule:

> **Python computes every ground-truth answer from the parquet. The LLM only *phrases*
> Q and A — it never invents the number.** A model that generates both question and answer
> "based on" the data will seed plausible-but-wrong numbers into training, which is worse
> than no data at all.

---

## 2. Stage 1 — Fact + relation substrate

The catalog gives per-cell *attributes*. Real spatial reasoning needs *relations*, which
must be **derived before generation**. Two artifacts:

### 2a. Atomic fact store (`facts.parquet`)
Driven by `catalog/feature_catalog.parquet` (1,007 features, each with
`description / units / derivation / min·max·mean·median / n_unique`). One row per
(entity, feature, value) with provenance `(dataset, scale, column, key)`.
- Entities: 7,318 hex9 · 1,191 hex8 · 326 subzones · 55 planning areas · 5 regions · 190,591 places.
- Human labels already present: `parent_subzone_name`, `parent_pa`, `parent_region`,
  place `name` + `brand` + `category` — so questions read "Tampines", not "TMSZ01".

### 2b. Derived relation tables (the actual "spatial" substrate)
| Relation | How | Enables |
|---|---|---|
| **Adjacency** | H3 `grid_disk(k=1,2)` on hex8/hex9 | "neighbouring hexes", "ring around X" |
| **Distance + bearing** | centroid haversine + compass bearing (EPSG:3414 for metres) | "north of", "2 km from CBD", "between X and Y" |
| **Containment hierarchy** | place → hex9 → hex8 → subzone → PA → region (keys already in masters) | roll-up / drill-down multi-hop |
| **Rank + percentile** | per-metric sort within scale & within parent | "3rd-densest subzone", "top-decile night-light growth" |
| **Co-location** | place categories sharing a hex (from place_composition) | "what's typically near a hawker centre" |

Without 2b, "reasoning" questions silently collapse into single-cell lookups.

---

## 3. Stage 2 — Deterministic answer engine

A library of **answer functions** (`answers/*.py`), one per question *template*, each:
`f(entity_or_pair, atlas) -> {value, evidence_rows, derivation_text}`.

- The number/boolean/ranking is computed in Python from the parquet.
- `evidence_rows` = the exact cells used → become the in-context block (target A) **and** the
  QC recompute key.
- `derivation_text` = a short factual chain → seeds the reasoning trace.
- LLM step is constrained: "Phrase this Q and this A using only these evidence rows."

Every emitted pair carries provenance so Stage 4 can recompute and reject mismatches.

---

## 4. Stage 3 — Per-category generation specs

Volumes are first-pass targets (tunable). Each category mixes templated breadth with
LLM-paraphrased surface diversity, and every pair ships a reasoning trace + evidence.

### 4.1 Factual — "about subzones & nuances"  (~target 8–10k)
- **Source:** subzone / PA / region masters (pop, land-use shares, `dominant_use`, GPR, region).
- **Templates:** attribute lookup ("What is the dominant land use in Bishan?"),
  membership ("Which region is Jurong West in?"), superlatives ("Which subzone has the
  highest 65+ share?"), existence ("Is there an MRT station in Lim Chu Kang?").
- **Nuance layer:** `lu_entropy` (mixed-use), `nonres_share`, `pop_dorm`, `avg_gpr` —
  the non-obvious facts that distinguish a real model from a gazetteer.
- **Parametric-safe subset** (target B): region/PA membership, adjacency, dominant_use.

### 4.2 Places — density, existence, counts, mix  (~target 10–12k)
- **Source:** `place_composition` (24 cat) + `place_composition_v2` (55 cat:
  `pc2_cat_food_hawker_count`, `pc2_cat_health_clinic_count`, …), `brand_rollup`,
  `*_place_counts`, `pc_diversity`.
- **Templates:** count ("How many cafés in Tiong Bahru?"), density ("places per km² in
  Orchard"), existence ("Any hospitals in Punggol?"), **mix/diversity** ("What's the
  retail-to-F&B ratio in Bugis?", "most common place category in Yishun"),
  brand presence ("Is there a FairPrice in Sengkang?").
- **Grounding caveat:** counts are POI-snapshot → frame as "in the atlas" and keep in
  target A, not baked into weights.

### 4.3 Reasoning — multi-hop & comparative  (~target 12–15k, the core)
- **Source:** relation tables (2b) + composites + `saturation_gap` + `demand_pull`.
- **Templates:**
  - *Comparison*: "Which is denser, Toa Payoh or Ang Mo Kio, and by how much?"
  - *Multi-hop containment*: "How many MRT stations are in the planning area that
    contains subzone X?"
  - *Ranking/percentile*: "Where does Clementi rank on walkability among West-region subzones?"
  - *Why-grounded*: "Why might Tampines have a high vibrancy index?" → answer chains
    real correlated features (transit + place diversity + population), **not** speculation.
  - *Gap*: "Which subzone is most under-served for clinics relative to population?"
    (`saturation_gap`).
- Each answer = an explicit reasoning trace over named evidence rows.

### 4.4 Patterns — bus-stop, population, mobility  (~target 8–10k)
- **Source:** `transit_clean` (bus_stop_count, mrt/lrt), `gtfs_windows`
  (am/midday/pm/night headways), `lta_pv` / `od_features` (taps, `od_throughput`,
  `od_self_containment`, `od_am_pm_out_ratio`, `breathing_idx`), population age structure
  (`pop_0_14/15_64/65plus`, `pop_dorm`, `nonres_share`), `nl_change_pct`, `spatial_rings`.
- **Templates:** distributional ("How does bus-stop density vary between core and
  periphery?"), temporal ("Which areas empty out at night — high AM-out OD ratio?"),
  demographic gradient ("Where is the population oldest?"), growth ("Which corridors show
  the biggest night-light growth 2022→2024?"), commuter ("Which subzones are
  self-contained vs dormitory-commuter?").
- This is where the *spatial-statistics* flavour lives — answers describe gradients and
  distributions, computed via the rank/ring tables.

### 4.5 Planning — counterfactual "what-if"  (~target 5–7k, highest-care)
**There is no ground truth for "open a new MRT line" in a static atlas.** The plan must
*say so* in the training target. Three tiers, in priority:

1. **Historical analogs (real ground truth):** where before/after exists — VIIRS night-light
   2022→2024 (`nl_2024` vs prior, `nl_change_pct`), recently-opened stations/lines if we can
   date them. "After X opened, night-light/activity changed by Y." These teach *real* causal
   deltas.
2. **Gravity / OD projection (labelled model output):** use `demand_pull` (distance-decay to
   CBD/MRT/mall) + `hex8_od_matrix` to compute a *projected* accessibility/footfall delta for
   a hypothetical station — **explicitly labelled "model estimate under assumptions A,B,C"**,
   never stated as fact.
3. **Assumption→inference chains (teach the chain, not the digit):** target text of the form
   *"Under assumption X, accessibility for hexes within 800 m rises, so expect ↑ footfall and
   ↑ demand_pull because Z."* The training signal is the **reasoning structure**, not a
   fabricated number.

> Cardinal rule for this category: **train the chain, not the digit.** A planning pair whose
> target asserts a precise invented number teaches the model to fabricate planning numbers.

---

## 5. Stage 4 — QC / verification

- **Recompute-and-reject:** re-run the answer function from provenance; drop any pair whose
  stored answer ≠ recomputed answer.
- **Numeric sanity:** value within `[min,max]` from feature_catalog; units consistent.
- **Template-diversity guard:** cap pairs per template; paraphrase-cluster to avoid 5
  templates generating everything (surface-form overfit).
- **Dedup:** semantic dedup on (entity, metric, intent).
- **Adversarial pass:** a critic LLM tries to answer from evidence alone and flags
  unanswerable / leading / ambiguous pairs.
- **Planning-specific:** assert every tier-2/3 answer contains an explicit assumption clause
  and no unhedged invented number.

---

## 6. Stage 5 — Eval design

- **Entity holdout, not random split:** hold out *whole* subzones / a whole region from
  training so test measures generalization, not memorization. (Random pair splits leak the
  same entity into train+test.)
- **Hand-curated gold set** (~150–300 pairs, ~30–60 per category) written by us — catches
  systematic template bias that auto-eval cannot.
- **Per-category metrics:** exact-match for factual/counts; tolerance-band for numeric;
  rank-correct for comparative; rubric-graded reasoning trace for reasoning/planning.
- **Hallucination probe:** out-of-atlas questions ("population of subzone that doesn't
  exist") — model should abstain, not invent.

---

## 7. Stage 6 — Format, volume, base model

- **Format:** chat/instruction with an explicit reasoning trace. For target A, an
  evidence/context block precedes the question; for target B (geography), closed-book.
  Each record: `{system, context?, question, reasoning, answer, provenance}`.
- **Total first cut:** ~45–55k pairs across the five categories (table above), then scale
  the categories that eval shows weakest.
- **Base model:** small-to-mid instruct model (e.g. an 8B-class) for a first LoRA pass;
  decide after a 2–3k pilot batch + eval, not upfront.
- **Pilot gate:** generate ~2k pairs (all categories), run full QC + a tiny train, inspect
  eval before committing to full volume.

---

## 8. Build order / milestones

1. **M0 — objective lock** (Decision #0 above): A-primary + small geography B. *(needs sign-off)*
2. **M1 — substrate:** build `facts.parquet` + relation tables (adjacency, distance/bearing,
   hierarchy, rank/percentile). *Foundational; everything depends on it.*
3. **M2 — answer engine:** answer functions per template + provenance.
4. **M3 — pilot batch:** ~2k pairs all categories → full QC → inspect.
5. **M4 — eval harness:** entity holdout + hand gold set.
6. **M5 — full generation** to volume, category-by-category.
7. **M6 — train + eval loop**, scale weak categories.

---

## Reasoning families (built — `llm-qa/reasoning/generate_reasoning.py`)

"Make Plexis-Mind intelligent, not just factual." Four families, deterministic answers +
explicit multi-step reasoning traces:

| Family | What it teaches | Example |
|---|---|---|
| **topn** | concentration via **normalized** measures (share / density / per-capita) | "5 subzones with highest 65+ *share*" → Loyang West, Pearl's Hill, Telok Blangah (NOT the biggest towns) |
| **compare** | which higher, by how much, ratio; any named pair | "Tampines East vs Toa Payoh on elder share" |
| **odflow** | origin→destination flows, self-containment, net importer/exporter | "Where do commuters from Chinatown go?" → City Hall, Central, Tampines East |
| **rank** | position + percentile within scope | "Where does Bishan rank on walkability?" |

### Data-honesty rules (LEARNED — must encode in every answer)
1. **Concentration ⇒ normalize.** Raw count of elders = biggest towns (Tampines East); the
   real answer is *share*. Apply a ≥2,000-resident denominator floor for share/per-capita.
2. **No income field exists.** "Where do high-income live" = **affluence proxy**
   (education + occupation + housing). Personas are **PA-resolution**, so affluence questions
   live at PA scale, and **`nvp_low_n` areas are excluded** (else noise like new-town Tengah tops it).
3. **OD = weekday *monthly* totals (LTA Apr-2026), all-commuter aggregate.** Phrase as monthly,
   never single-day; it is **not dorm-tagged** — "where dorm workers go" is approximated by
   flows *from dorm-heavy origins*, stated as such.
4. **No weekend / Sunday data.** OD + taps are weekday; GTFS windows are am/midday/pm/night of a
   weekday. Sunday questions are a **data gap** (would need an LTA weekend-OD pull) — do not generate.

## Appendix — primary data hooks per category

| Category | Atlas files / fields |
|---|---|
| Factual | `subzone_all_features`, `parent_pa/region/subzone_name`, land-use `lu_*`, `dominant_use`, `avg_gpr`, `lu_entropy` |
| Places | `*_place_composition`, `*_place_composition_v2` (55 `pc2_cat_*`), `brand_rollup`, `*_place_counts`, `pc_diversity` |
| Reasoning | relation tables + `composites` (vibrancy/livability), `saturation_gap`, `demand_pull` |
| Patterns | `transit_clean`, `gtfs_windows`, `lta_pv`, `od_features` (`od_*`, `breathing_idx`), `population` age cols, `satellite` `nl_change_pct`, `spatial_rings` |
| Planning | `demand_pull`, `hex8_od_matrix`, `satellite` 2022→2024, transit accessibility |
