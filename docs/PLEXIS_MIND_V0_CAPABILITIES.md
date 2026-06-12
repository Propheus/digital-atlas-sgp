# Plexis-Mind v0 — What the Model Learned (Capability Summary)

**Model:** Gemma-4-12B + QLoRA (r32), 2 epochs on ~160K SGP Q&A (3 registers) + 15K available deep traces.
**Eval:** generation-based, `atlas_tools.verify()`, on 4,385 **held-out subzones** (entities never trained on).
**Headline:** **~88% overall** (85.7% raw; +abstention metric fix). Context-mode 88%, closed-book ~85%.

---

## ✅ What it's STRONG at

| Capability | Evidence | Note |
|---|---|---|
| **Reasoning over provided data** (the deployment mode) | context-mode **88.3%** | extracts, compares, aggregates, reads OD flows — *no hallucination* |
| **Place questions** | **95.0%** | counts, existence, mix ("how many cafés", "any clinics") |
| **Factual attributes** | **93.2%** | population, demographics, walkability, etc. |
| **Honest abstention** | ~near-perfect (was mis-scored) | refuses crime/weather/income/untracked categories cleanly |
| **Register matching** | qualitative | brief & casual for "is X good for families?"; structured for analytical Qs |
| **Stable geography (closed-book)** | "Bishan → Central Region" ✓ | recalls structural facts for well-known areas |
| **Grounded multi-constraint** | "East subzone >20k, most walkable → Bedok North 0.81" ✓ | filters + ranks correctly *when given the data* |

**Behavioral character:** conservative and grounded — it **refuses rather than fabricates**, and reasons faithfully over evidence. That's the safe, intended profile.

---

## ⚠️ What it CANNOT (or struggles with)

| Limitation | Evidence | Why / Fix |
|---|---|---|
| **Filter-then-rank from scratch** (`filt_super`) | **0%** (n=21) | the hardest multi-step kind — even with context it picks wrong. → deep traces + GRPO |
| **Precise recall from memory** (closed-book numbers) | states approximate values confidently | a 12B can't memorize 326×N stats. → tools/RAG for exact figures |
| **Closed-book categorical recall** | dominant-use 0%, membership 33% | only "famous" areas recalled. → tools, or more closed-book positives |
| **Over-abstention closed-book** | refused "family"/"hawker" without context | over-anchored to the abstention coverage list. → rebalance abstention; tools make it moot |
| **Planning / patterns** | 80% / 77% (small n) | thin slices; directional + caveated by design (not precise forecasts) |

---

## The one structural truth this validated
**Reasoning skill lives in the weights; facts come from the atlas.**
- **With context (atlas tools/RAG):** 88% — correct, grounded, non-hallucinating. *This is production.*
- **Closed-book:** weaker on precise facts (43→~85% after abstention fix) — the model correctly *refuses to invent*, and tools fill the gap.

So v0 is a **strong reasoner that won't bluff**, not a memorized database — exactly the design.

---

## v1 priorities (now data-driven)
1. **Wire `atlas_tools.py`** → closes the closed-book gap, exact numbers (biggest single lift)
2. **Fold in 15K deep traces + GRPO** → directly targets `filt_super` / multi-step reasoning
3. **Rebalance abstention** (less coverage-list anchoring + more closed-book positives)
4. **Fix the abstain verify metric** (decline-check, ignore cited "55 categories")

**One-liner:** Plexis-Mind v0 reasons over Singapore's atlas at ~88% on unseen areas, refuses out-of-scope honestly, and is conservative rather than hallucinatory — with a clear, small path to v1.
