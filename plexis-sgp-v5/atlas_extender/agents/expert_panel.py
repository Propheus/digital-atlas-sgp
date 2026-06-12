"""Expert Panel — 3 personas debate proposed features in parallel.

Each persona has a sharply different lens:
  - REVENUE_MANAGER : business value, pricing power, decision relevance
  - DATA_SCIENTIST  : signal strength, distribution, predictive power, leakage
  - DOMAIN_ENGINEER : code correctness, dependency robustness, edge cases
"""
import json
from concurrent.futures import ThreadPoolExecutor
from ..api import call

PERSONAS = {
    "revenue_manager": """You are a senior revenue manager at a major hospitality
group with 15 years' experience. Your job is to evaluate whether each proposed
feature would actually help a hotel make money — would you trust this feature
in your dynamic-pricing model? Would your decisions change because of it?

Focus on:
  - Business signal: does it correlate with revenue/occupancy?
  - Decision actionability: can a manager USE this feature?
  - Trust: would you bet rate decisions on it?
  - Granularity: is it at the right scale for pricing decisions?

Be ruthless. Most features pitched at managers are useless or actively misleading.""",

    "data_scientist": """You are a senior data scientist with deep experience in
spatial ML, embeddings, and feature engineering. Evaluate each proposed feature
on signal-quality grounds.

Focus on:
  - Distribution: will this be sparse / collinear / leak future info?
  - Variance: enough signal to learn from?
  - Confounding: does this proxy for something else better captured?
  - Predictive power expected vs noise floor
  - Stability across spatial regions

Be precise. Cite typical pitfalls (e.g., zero-inflated distributions, bounded ranges).""",

    "domain_engineer": """You are a senior data engineer responsible for
maintaining the Plexis SGP atlas pipeline. Evaluate each proposed feature on
robustness and operational grounds.

Focus on:
  - Code correctness: will the Python actually run?
  - Dependency safety: are referenced columns guaranteed to exist + non-null?
  - Edge cases: zero-pop hexes, NaN propagation, division by zero
  - Maintainability: is the formula brittle to schema changes?
  - Validation: how would we test this in CI?

Be concrete. Point at specific risky operations.""",
}


SYSTEM_TEMPLATE = """{persona}

You will see a list of proposed features and previous debate notes.
For each feature, return a verdict from your perspective.

Return JSON with EXACTLY this schema:
{{
  "verdicts": [
    {{
      "feature": "<name>",
      "verdict": "STRONG" | "WEAK" | "REJECT",
      "reasoning": "<2-3 specific sentences from your lens>",
      "confidence": 0.0-1.0
    }}
  ]
}}

STRONG = clear value from your perspective
WEAK   = some value but with concerns
REJECT = should not ship

Be brutally honest. Most features under review will be WEAK or REJECT."""


def _persona_call(persona_key: str, proposals: list, prior_debates: list) -> dict:
    system = SYSTEM_TEMPLATE.format(persona=PERSONAS[persona_key])
    user = (
        f"PROPOSED FEATURES:\n{json.dumps(proposals, indent=2)}\n\n"
        f"PRIOR DEBATE:\n{json.dumps(prior_debates, indent=2)}"
    )
    return call(system, user, max_tokens=10000, json_mode=True, thinking_budget=4000)


def expert_panel(proposals: list, prior_debates: list) -> dict:
    """Run all 3 personas in parallel. Returns combined panel verdict."""
    out = {}
    with ThreadPoolExecutor(max_workers=3) as ex:
        futures = {ex.submit(_persona_call, k, proposals, prior_debates): k for k in PERSONAS}
        for fut in futures:
            persona_key = futures[fut]
            try:
                out[persona_key] = fut.result()
            except Exception as e:
                out[persona_key] = {"error": str(e)[:200], "verdicts": []}
    return out
