"""
LLM intent backend using Claude Sonnet via the Anthropic API.

Activated when rule-based parser's confidence < threshold, OR explicitly requested.
Returns {"use_case": str, "entities": dict, "confidence": float}.

The API key is read from env var ANTHROPIC_API_KEY (preferred) or passed to __init__.
Never commit keys. Use .env (gitignored) or shell export.
"""
import json
import os
from typing import Optional

try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False


# The canonical use cases the LLM is allowed to pick from
KNOWN_USE_CASES = [
    "site_selection",
    "gap_analysis",
    "archetype_clustering",
    "comparable_market",
    "whitespace_analysis",
    "category_prediction",
    "feature_query",
    "amenity_desert",
    "fifteen_minute_city",
    "unknown",
]

SYSTEM_PROMPT = """You are an intent router for a Singapore urban-intelligence
API. Classify the query into ONE use case and extract entities.
Return STRICT JSON only — no prose, no code fences.

USE CASES (pick exactly one):
  site_selection        — find NEW locations to open a brand/concept ("open", "expand", "put", "new stores", "where to open")
  gap_analysis          — category is systemically under-supplied across an area ("gaps", "underserved", "deficit", "missing X")
  archetype_clustering  — group neighborhoods into urban archetypes ("cluster", "segment", "classify into types")
  comparable_market     — comparable neighborhoods for property VALUATION/appraisal ("comps", "valuation", "appraise")
  whitespace_analysis   — a SPECIFIC named brand is absent where it could fit ("Brand X missing")
  category_prediction   — expected COUNT / density of a category ("predict", "how many", "forecast")
  feature_query         — retrieve hexes matching a MULTI-FEATURE profile ("high X and low Y", "combination of")
  amenity_desert        — populations cut off from basic amenities (food/transit/healthcare deserts)
  fifteen_minute_city   — walkability / 15-min city scoring
  unknown               — none of the above fits

TWO SURGICAL DISAMBIGUATION RULES:

1. A specific NAMED BRAND (Starbucks, FairPrice, KFC, McDonald's, 7-Eleven, etc.)
   combined with "missing", "absent", "no competitors", "where one would fit",
   or "virgin territory" is ALWAYS whitespace_analysis — even if "expand",
   "gap", or "feature" also appear.

2. "like <place>" + valuation/property/comps/appraisal context → comparable_market.
   "like <place>" + opening/expanding a brand → site_selection.

ENTITY FIELDS (use SINGULAR names):
  brand        (str)        specific brand name
  category     (str)        amenity category (cafe, hawker, clinic, ...)
  location     (str)        SGP planning area or landmark
  target_hex   (str)        H3 hex id
  coords       (list)       [lat, lng]
  k            (int)        number of results (e.g. "top 20")
  anchor_hexes (list[str])  explicit anchor hexes
  profile      (dict)       feature profile for feature_query

Output EXACTLY this JSON:
{
  "use_case": "<name>",
  "entities": { ... },
  "confidence": <0..1>,
  "reasoning": "<one short sentence>"
}"""


class ClaudeIntentBackend:
    """
    LLM-powered intent extractor using Claude Sonnet.

    Usage:
      backend = ClaudeIntentBackend()   # reads ANTHROPIC_API_KEY from env
      result = backend.classify("where should I open a Starbucks near Tanjong Pagar?")
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-sonnet-4-6",
        max_tokens: int = 400,
    ):
        if not HAS_ANTHROPIC:
            raise RuntimeError(
                "Python package 'anthropic' not installed. "
                "Install with: pip install anthropic"
            )
        key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY not found. Set env var or pass api_key=..."
            )
        self.client = anthropic.Anthropic(api_key=key)
        self.model = model
        self.max_tokens = max_tokens

    def classify(self, query: str) -> dict:
        """Return structured intent dict, or {} on failure."""
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": query}],
            )
            text = response.content[0].text.strip()
            # Strip code fences if present
            if text.startswith("```"):
                text = text.split("```", 2)[1]
                if text.startswith("json"):
                    text = text[4:].strip()
                text = text.rstrip("`").strip()
            data = json.loads(text)
            # Sanity check: use_case must be known
            if data.get("use_case") not in KNOWN_USE_CASES:
                data["use_case"] = "unknown"
            return data
        except json.JSONDecodeError:
            return {"use_case": "unknown", "entities": {}, "confidence": 0.0,
                    "reasoning": "LLM response was not valid JSON"}
        except Exception as e:
            return {"use_case": "unknown", "entities": {}, "confidence": 0.0,
                    "reasoning": f"API error: {type(e).__name__}: {e}"}

    def __call__(self, query: str) -> dict:
        """Allow passing as a callable to IntentParser(llm_backend=...)."""
        return self.classify(query)
