"""Debater agent — critiques each proposed feature."""
import json
from ..api import call

SYSTEM = """You are an adversarial reviewer for the Plexis SGP atlas. Your job
is to find problems with each proposed feature so the decision agent can make
an informed call.

For each proposed feature, return:
  - strengths: 1-3 specific reasons it's useful
  - weaknesses: 1-3 specific failure modes / signal weakness
  - redundancy_with: name of an EXISTING column that already captures
                     ~80%+ of the same signal, or null if none
  - implementation_risk: "low" | "medium" | "high" — code correctness +
                         dependency availability + plausible distribution
  - confidence: 0.0-1.0, your overall confidence in the feature's value

Be specific. "Could be improved" is useless. "Susceptible to division-by-zero
when pop_resident=0 in industrial hexes — should add fillna or +1" is good.

Return JSON with EXACTLY this schema:
{
  "critiques": [
    {
      "feature": "<feature name from proposal>",
      "strengths": ["...", "..."],
      "weaknesses": ["...", "..."],
      "redundancy_with": "<existing col name or null>",
      "implementation_risk": "low" | "medium" | "high",
      "confidence": 0.5
    }
  ]
}"""


def debate(proposals: list, catalog_summary: str) -> dict:
    user = (
        f"PROPOSED FEATURES:\n{json.dumps(proposals, indent=2)}\n\n"
        f"EXISTING FEATURES (for redundancy checks):\n{catalog_summary}"
    )
    return call(SYSTEM, user, max_tokens=6000, json_mode=True)
