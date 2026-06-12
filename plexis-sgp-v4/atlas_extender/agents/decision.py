"""Decision agent — final KEEP / REVISE / REJECT call per feature."""
import json
from ..api import call

SYSTEM = """You are the chief architect deciding which proposed features to
add to the Plexis SGP atlas. You see both the synthesizer's proposals and the
debater's critiques. Make a final per-feature decision.

Decision rules:
  KEEP    — clear value, low redundancy with existing, low implementation risk
  REVISE  — good idea but the code or definition needs adjustment. Provide
            revised_code (a fixed Python expression) that addresses the
            debater's specific concerns. The revision must remain a single-
            line pandas/numpy expression assigning to df['<name>'].
  REJECT  — redundant with existing, weak signal, or high risk

Be selective. It's better to ship 3 strong features than 8 mediocre ones.

Return JSON with EXACTLY this schema:
{
  "decisions": [
    {
      "feature": "<name>",
      "decision": "KEEP" | "REVISE" | "REJECT",
      "justification": "<one sentence>",
      "priority": <int, 1=highest>,
      "revised_code": "<only if REVISE; else null>"
    }
  ]
}"""


def decide(proposals: list, debates: list) -> dict:
    user = (
        f"PROPOSALS:\n{json.dumps(proposals, indent=2)}\n\n"
        f"DEBATER CRITIQUES:\n{json.dumps(debates, indent=2)}"
    )
    return call(SYSTEM, user, max_tokens=4096, json_mode=True)
