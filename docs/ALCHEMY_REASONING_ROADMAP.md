# Alchemy — roadmap to the best urban-reasoning model

**Thesis (validated by probe).** Vanilla Gemma-12B is a strong *general* reasoner — on plain reason-in-context
it ties or beats us. The durable moat is **reasoning over Singapore's proprietary urban metrics** (anchor
strength · demand support · provision gap · saturation · demand pull · synergy) that Gemma has no model for.
Given those metrics, Gemma *ignores them and describes the area*; Alchemy reasons over them. We make that
edge **reliable and verifiable** by leaning on the deterministic atlas — never by mass-producing confident
guesses.

The whole strategy rests on one line (see `ALCHEMY_METRIC_ONTOLOGY.md` §4):
> **Deterministic** facts (rank / compare / gap / pull) → verifiable → trainable + tool-able + GRPO-rewardable.
> **Judgment** verdicts (siting / what-if) → grounded in those facts but emitted as *caveated estimates*, never as fact.

---

## Status (done)
- ✅ **Metric ontology** — `ALCHEMY_METRIC_ONTOLOGY.md`. Families, scales, directionality (gap +1 = under-served,
  confirmed empirically), valid chains, the anchor-canary resolution (opportunity follows `gap_`, not anchor).
- ✅ **Richer context injection (live)** — `serve_plexis.py` now injects a compact "location-intelligence" line
  (top anchors, top gaps, saturation, pull/competitors/MRT-distance) + an interpretation key in the system
  prompt. Probe confirmed: Alchemy reasons over gaps; Gemma still ignores them.
- ✅ **Deterministic generator** — `generate_metric_reasoning.py` → 1,884 verifiable pairs (7 families) from the
  parquet; opportunity family caveated. Foundation for the v1 corpus.

## Phase 1 — scale the data (no GPU)
- Natural-language phrasing pass (flash) over the deterministic skeletons → 3 registers, like the main corpus.
- Extend families: PA + region scale; `pull_*` accessibility questions; `syn_*` synergy "why"; multi-metric
  synthesis ("under-served **and** accessible"); decomposition ("why is vibrancy high here?").
- Scale pairs/scopes with seen-sets for distinctness → target ~40–60K metric-reasoning pairs.
- QC with the same numeric-fidelity verifier; entity-holdout split.

## Phase 2 — the tool layer (the durable moat; biggest single lift)
Wire `atlas_tools` metric functions as **inference tools** the model calls:
`rank(metric, scope)`, `gap(area, category)`, `compare(a, b, metric)`, `pull(area)`, `anchor_top(area)`.
- Exact, fresh, **verifiable** answers; the model supplies the *which-tool + interpretation*, the atlas supplies
  the number. Gemma can't call a metric it doesn't know exists.
- Closes the closed-book gap (no need to memorise 214×50 metrics) and the "ours hallucinated a national
  average" failure — the tool returns the real benchmark or nothing.

## Phase 3 — SFT v1 (retrain, ~30 h GPU)
- Merge: metric-reasoning corpus + the 15K verified deep traces + **characterful answers** (fix the writing
  regression by default, not by prompt) + tool-call traces.
- Same QLoRA recipe; entity-holdout eval.

## Phase 4 — GRPO (verifiable RL; the reasoning unlock)
- Reward = the deterministic verifier (`atlas_tools.verify`) — a rare, free, *correct* reward signal.
- Targets the multi-step weak spots (the `filt_super` 0% class, multi-metric chains).
- Opportunity/what-if get a **partial** reward (direction correct + caveat present), never full credit for a
  magnitude — keeps the verifiability line intact.

## Phase 5 — eval & proof
- A held-out **metric-reasoning benchmark** (deterministic answers) scored by the verifier — report Alchemy vs
  raw Gemma vs Gemma+context. This is the number that proves "best urban reasoner": Gemma can't move on it.
- Keep the Compare panel as the live, public demonstration.

---

## Why this wins
- **Facts from the atlas, metric-semantics + chaining from the weights, exact lookups from the tools** — three
  layers Gemma has none of.
- Every claim is either a verifiable fact or an explicitly-caveated estimate → it is *trustworthy*, which is the
  property a grounded analyst model must have and a raw LLM can't guarantee.
- The deterministic atlas is the unfair advantage: it generates the data, verifies it, rewards the RL, and
  serves the tools — four roles, one source.

**Open decision (yours):** the anchor-canary directionality — opportunity currently follows `gap_` (find-the-gap).
If the business reading is "ride-the-cluster" (high anchor = proven demand = safe), the verifier and generator
flip. Confirm before Phase 1 scale-up.
