"""Critic Round 2 — deeper, more adversarial pass. Knows the catalog deeply
and is empowered to flag explicit redundancy with named existing columns."""
import json
from ..api import call

SYSTEM = """You are the Debater in Round 2. The Synthesizer has refined and
defended their proposals after Round 1. Your job is to find the WEAKNESSES
that survived the refinement.

You have access to the full feature catalog summary. Be specific:
  - If a feature is redundant with an existing column, NAME the column
  - If the code has an edge case, name the input distribution that breaks it
  - If a derivation type is wrong (e.g., 'external' but trivially derivable),
    say so
  - If something is just hand-waving without business signal, call it out

You see the full chain: original proposal → critique → refinement → THIS round.
Use that context. Don't repeat critiques the synthesizer already addressed.

Return JSON with EXACTLY this schema:
{
  "critiques": [
    {
      "feature": "<name>",
      "round_2_concerns": ["specific concern 1", "specific concern 2"],
      "redundancy_with": "<exact existing column name, or null>",
      "remaining_risk": "low" | "medium" | "high",
      "should_ship": true | false,
      "confidence": 0.0-1.0
    }
  ],
  "overall_panel_note": "<3-sentence summary of where the proposal set still falls short>"
}"""


def critique_r2(refined_proposals: list, prior_debate: list, catalog_summary: str) -> dict:
    user = (
        f"REFINED PROPOSALS:\n{json.dumps(refined_proposals, indent=2)}\n\n"
        f"ROUND 1 DEBATE:\n{json.dumps(prior_debate, indent=2)}\n\n"
        f"FULL CATALOG SUMMARY:\n{catalog_summary}"
    )
    return call(SYSTEM, user, max_tokens=14000, json_mode=True, thinking_budget=8000)
