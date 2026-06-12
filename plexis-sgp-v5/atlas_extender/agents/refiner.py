"""Refiner — Round 2 of the synthesizer. Defends or fixes each feature based on
debate, proposes replacements for irredeemable ones."""
import json
from ..api import call

SYSTEM = """You are the Synthesizer in Round 2. The Debater has critiqued your
Round 1 proposals. For each feature, you must:

  1. DEFEND with revised code, OR
  2. WITHDRAW and propose a replacement that addresses the critique

Be honest — if a critique is correct, accept it and revise. Don't be stubborn.

For each Round 1 proposal, return one entry:
  - action: "REVISE" (keep concept, fix code), "DEFEND" (keep as-is, justify),
            or "REPLACE" (drop and propose new feature)
  - revised_code: required if REVISE or REPLACE; single-line pandas/numpy expr
  - justification: why this addresses the debater's points
  - new_name (only if REPLACE): different name for the replacement feature
  - new_description / new_rationale (only if REPLACE)

Plus 3-5 entirely new features that the debate revealed are needed but missing.

Return JSON with EXACTLY this schema:
{
  "refined_proposals": [
    {
      "original_name": "<name from R1>",
      "action": "REVISE" | "DEFEND" | "REPLACE",
      "name": "<final name; same as original_name if REVISE/DEFEND>",
      "description": "<final description>",
      "scale": "...",
      "dtype": "...",
      "derivation_type": "derive" | "external" | "learned",
      "code": "<final code (for derive)>",
      "dependencies": ["..."],
      "rationale": "<why this matters AFTER the debate>",
      "addresses_critique": "<which debater point this responds to>"
    }
  ],
  "new_proposals": [
    {
      "name": "...",
      "description": "...",
      "scale": "...",
      "dtype": "...",
      "derivation_type": "derive" | "external" | "learned",
      "code": "...",
      "dependencies": ["..."],
      "rationale": "<gap the debate exposed that this fills>"
    }
  ]
}"""


def refine(proposals_r1: list, debates_r1: list, ucs: dict, sample_columns: list) -> dict:
    user = (
        f"USE CASE:\n{json.dumps(ucs, indent=2)}\n\n"
        f"ROUND 1 PROPOSALS:\n{json.dumps(proposals_r1, indent=2)}\n\n"
        f"ROUND 1 DEBATER CRITIQUES:\n{json.dumps(debates_r1, indent=2)}\n\n"
        f"SAMPLE OF AVAILABLE COLUMNS at target scale:\n{', '.join(sample_columns[:200])}"
    )
    return call(SYSTEM, user, max_tokens=16000, json_mode=True, thinking_budget=8000)
