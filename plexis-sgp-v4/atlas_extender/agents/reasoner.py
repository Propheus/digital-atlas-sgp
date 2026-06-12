"""Reasoner agent — natural language use case → structured Use Case Spec (UCS)."""
import json
from ..api import call

SYSTEM = """You are a senior urban-analytics data scientist analyzing a request.
Convert the user's natural-language request into a structured Use Case Spec (UCS)
for the Plexis SGP digital atlas.

The atlas has features at four spatial scales:
  - hex9: H3 res-9 hexagons (~174m edge, ~0.105 km²), 7,318 cells
  - hex8: H3 res-8 hexagons (~461m edge), 1,191 cells
  - subzone: URA Master Plan polygons, 326 subzones
  - place: 190,591 individual POIs

Decompose the use case into:
  - target_variable: what we want to predict / score / rank
  - decision_type: 'ranking' | 'prediction' | 'classification' | 'gap_analysis' | 'similarity'
  - scale: which spatial scale fits best
  - key_concepts: 3-7 short concept phrases that span what's needed
  - constraints: optional list of business / regulatory limits
  - evaluation_metric: how would success be measured
  - decision_horizon_months: temporal horizon (0 if instantaneous)
  - stakeholder: who consumes the output

Return JSON with EXACTLY this schema:
{
  "use_case": "<one-sentence summary>",
  "target_variable": "<what we want to predict / score>",
  "decision_type": "<one of: ranking, prediction, classification, gap_analysis, similarity>",
  "scale": "<one of: hex9, hex8, subzone, place>",
  "key_concepts": ["concept1", "concept2", "concept3"],
  "constraints": ["constraint1"],
  "evaluation_metric": "<how to measure success>",
  "decision_horizon_months": 0,
  "stakeholder": "<who uses this>"
}"""


def reason(use_case_text: str) -> dict:
    return call(SYSTEM, use_case_text, max_tokens=2048, json_mode=True)
