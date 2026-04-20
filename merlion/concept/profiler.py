"""
Concept Profiler — Layer 2.5.

Translates a brand name or concept description into a structured feature
profile that downstream use cases can query against.

The profile answers: "What kind of neighborhoods does THIS brand need?"
  - target demographics (age, income, household type)
  - price tier (value / mid / premium / luxury)
  - locality preferences (heartland / CBD / industrial / tourism)
  - feature signals (pop density, transit access, walkability, etc.)
  - primary + related categories (pc_cat_*)
  - competitor brands (for whitespace filtering)

Uses Claude Sonnet to expand brand knowledge into a Singapore-context profile.
Falls back to a small hard-coded dictionary for common brands when no LLM.
"""
import json
import os
from dataclasses import dataclass, field, asdict
from typing import Optional


# ============================================================
# Profile schema
# ============================================================
@dataclass
class ConceptProfile:
    name: str                               # e.g. "Alfamart"
    kind: str                               # e.g. "minimart chain"
    primary_category: str                   # e.g. "convenience_daily_needs"
    related_categories: list[str] = field(default_factory=list)
    price_tier: str = "mid"                 # value | mid | premium | luxury
    target_demographics: dict = field(default_factory=dict)
    locality_fit: list[str] = field(default_factory=list)        # archetype groups
    locality_avoid: list[str] = field(default_factory=list)
    competitor_brands: list[str] = field(default_factory=list)
    signals: dict = field(default_factory=dict)                  # feature → constraint
    reasoning: str = ""
    source: str = "llm"                     # "llm" | "hardcoded" | "default"

    def to_dict(self) -> dict:
        return asdict(self)


# ============================================================
# SGP archetype → planning-area groups
# Used both for profile locality_fit/avoid AND for locality filtering.
# ============================================================
PA_ARCHETYPES = {
    "cbd_core":         {"DOWNTOWN CORE", "MARINA SOUTH", "MARINA EAST", "ROCHOR",
                          "MUSEUM", "OUTRAM", "SINGAPORE RIVER"},
    "orchard_corridor": {"ORCHARD", "NEWTON", "NOVENA", "TANGLIN"},
    "heritage_cultural":{"BUKIT MERAH", "QUEENSTOWN", "SINGAPORE RIVER", "GEYLANG", "KALLANG"},
    "heartland_mature": {"TAMPINES", "BEDOK", "HOUGANG", "SERANGOON", "TOA PAYOH",
                          "ANG MO KIO", "BUKIT BATOK", "BUKIT PANJANG", "CLEMENTI",
                          "PASIR RIS"},
    "heartland_young":  {"PUNGGOL", "SENGKANG", "YISHUN", "CHOA CHU KANG", "SEMBAWANG"},
    "west_edge":        {"JURONG WEST", "JURONG EAST", "CLEMENTI", "BUKIT BATOK",
                          "CHOA CHU KANG"},
    "north_suburban":   {"WOODLANDS", "YISHUN", "SEMBAWANG", "MANDAI"},
    "industrial":       {"TUAS", "PIONEER", "JURONG ISLAND", "WESTERN ISLANDS",
                          "BOON LAY", "SUNGEI KADUT", "LIM CHU KANG"},
    "airport_aviation": {"CHANGI", "CHANGI BAY", "PAYA LEBAR"},
    "islands_resort":   {"SOUTHERN ISLANDS", "NORTH-EASTERN ISLANDS", "WESTERN ISLANDS"},
    "education":        {"QUEENSTOWN", "BUKIT TIMAH", "CLEMENTI"},
    "greenery":         {"CENTRAL WATER CATCHMENT", "WESTERN WATER CATCHMENT",
                          "NORTH-EASTERN ISLANDS", "SIMPANG"},
}

ARCHETYPES = list(PA_ARCHETYPES.keys())


def pa_to_archetypes(pa: str) -> set[str]:
    """Reverse lookup: which archetype groups does this PA belong to?"""
    out = set()
    for group, pas in PA_ARCHETYPES.items():
        if pa in pas:
            out.add(group)
    return out

# SGP canonical categories (match pc_cat_*)
CATEGORIES = [
    "cafe_coffee", "restaurant", "hawker_street_food", "fast_food_qsr",
    "bar_nightlife", "bakery_pastry", "convenience_daily_needs",
    "education", "health_medical", "fitness_recreation", "hospitality",
    "office_workspace", "shopping_retail", "beauty_personal_care",
    "religious", "culture_entertainment", "transport", "services",
    "automotive", "business", "residential", "civic_government",
    "general", "ngo",
]

# Raw features worth shortlisting in signals (sample; full set has 391)
KEY_SIGNAL_FEATURES = [
    "population_total", "working_age_count", "walking_dependent_count",
    "walkability_score", "walk_bus_m", "walk_mrt_score", "mrt_stations",
    "bus_interchange_count", "hdb_blocks", "bldg_private_residential",
    "lu_residential_pct", "lu_commercial_pct", "lu_business_pct",
    "pc_total", "pc_unique_place_types",
    "pc_tier_value", "pc_tier_mid", "pc_tier_premium", "pc_tier_luxury",
    "tourist_draw_est",
]


# ============================================================
# Hard-coded profiles for common brands (fast-path, no LLM)
# These are also used as few-shot examples for the LLM.
# ============================================================
HARDCODED_PROFILES: dict[str, ConceptProfile] = {
    "starbucks": ConceptProfile(
        name="Starbucks",
        kind="premium specialty coffee chain",
        primary_category="cafe_coffee",
        related_categories=["cafe_coffee", "shopping_retail", "office_workspace"],
        price_tier="premium",
        target_demographics={"age_range": "25-45 working professional",
                              "income_band": "mid_to_high"},
        locality_fit=["cbd_core", "orchard_corridor", "heartland_mature",
                       "heritage_cultural"],
        locality_avoid=["industrial", "islands_resort", "greenery"],
        competitor_brands=["toast box", "ya kun", "the coffee bean", "costa"],
        signals={
            "pc_tier_premium":   {"weight": 0.25, "direction": "high"},
            "pc_total":          {"weight": 0.15, "direction": "high"},
            "walkability_score": {"weight": 0.15, "direction": "high", "min": 50},
            "office_workspace":  {"weight": 0.15, "direction": "high"},
            "mrt_stations":      {"weight": 0.10, "direction": "high"},
            "tourist_draw_est":  {"weight": 0.10, "direction": "high"},
        },
        reasoning="Premium third-place chain; targets office workers + affluent shoppers. "
                   "Needs high foot traffic, MRT access, premium retail density.",
        source="hardcoded",
    ),
    "alfamart": ConceptProfile(
        name="Alfamart",
        kind="Indonesian value-tier minimart chain",
        primary_category="convenience_daily_needs",
        related_categories=["convenience_daily_needs", "services"],
        price_tier="value",
        target_demographics={"age_range": "broad family",
                              "income_band": "low_to_mid",
                              "household": "HDB residents"},
        locality_fit=["heartland_mature", "heartland_young",
                       "west_edge", "north_suburban"],
        locality_avoid=["cbd_core", "orchard_corridor", "islands_resort",
                         "industrial"],
        competitor_brands=["7-eleven", "cheers", "giant express", "fairprice"],
        signals={
            # NOTE feature scales: lu_*_pct is 0-1, walkability 0-98,
            # population 0-13k, hdb_blocks 0-109, pc_tier_* counts.
            "population_total":        {"weight": 0.30, "direction": "high", "min": 200},
            "hdb_blocks":              {"weight": 0.20, "direction": "high", "min": 1},
            "lu_residential_pct":      {"weight": 0.15, "direction": "high", "min": 0.15},
            "walkability_score":       {"weight": 0.15, "direction": "high", "min": 40},
            "mrt_stations":            {"weight": 0.10, "direction": "high"},
            "pc_tier_value":           {"weight": 0.05, "direction": "high"},
            "pc_tier_premium":         {"weight": 0.05, "direction": "low"},
        },
        reasoning="Value-tier minimart targeting HDB heartland dwellers. Needs high "
                   "residential density, transit-adjacent, price-sensitive areas. Avoid "
                   "CBD/premium zones where rent doesn't match price point.",
        source="hardcoded",
    ),
    "fairprice": ConceptProfile(
        name="FairPrice",
        kind="mass-market supermarket",
        primary_category="convenience_daily_needs",
        related_categories=["convenience_daily_needs", "shopping_retail"],
        price_tier="value",
        target_demographics={"age_range": "family-wide",
                              "income_band": "low_to_mid",
                              "household": "HDB residents"},
        locality_fit=["heartland_mature", "heartland_young", "west_edge",
                       "north_suburban"],
        locality_avoid=["cbd_core", "industrial", "islands_resort"],
        competitor_brands=["giant", "sheng siong", "cold storage"],
        signals={
            "population_total":   {"weight": 0.30, "direction": "high", "min": 500},
            "hdb_blocks":         {"weight": 0.25, "direction": "high", "min": 1},
            "lu_residential_pct": {"weight": 0.20, "direction": "high", "min": 0.15},
            "walkability_score":  {"weight": 0.15, "direction": "high", "min": 40},
            "mrt_stations":       {"weight": 0.10, "direction": "high"},
        },
        reasoning="Singapore's NTUC grocery chain. Anchors HDB heartland with daily needs. "
                   "Typically needs 800+ residents in the hex and good transit access.",
        source="hardcoded",
    ),
}


# ============================================================
# LLM profiler
# ============================================================
SYSTEM_PROMPT = """You are an expert in Singapore retail + urban planning.
Given a brand or concept name, produce a structured feature profile for site
selection in Singapore's hex-level urban data model.

Return STRICT JSON only — no prose, no code fences. Schema:

{
  "name": "<brand/concept>",
  "kind": "<short descriptor e.g. 'value-tier minimart chain'>",
  "primary_category": "<one of pc_cat_* canonical keys below>",
  "related_categories": ["<canonical>", ...],
  "price_tier": "<value|mid|premium|luxury>",
  "target_demographics": {
      "age_range": "<string>",
      "income_band": "<low|low_to_mid|mid|mid_to_high|high>",
      "household": "<HDB|condo|mixed|...>"
  },
  "locality_fit": ["<archetype group>", ...],
  "locality_avoid": ["<archetype group>", ...],
  "competitor_brands": ["<brand>", ...],
  "signals": {
      "<feature_name>": {"weight": <0..1>, "direction": "high|low", "min": <optional>},
      ...
  },
  "reasoning": "<1-2 sentences why>"
}

Canonical categories (pc_cat_* keys): cafe_coffee, restaurant, hawker_street_food,
fast_food_qsr, bar_nightlife, bakery_pastry, convenience_daily_needs, education,
health_medical, fitness_recreation, hospitality, office_workspace,
shopping_retail, beauty_personal_care, religious, culture_entertainment,
transport, services, automotive, business, residential, civic_government,
general, ngo.

Archetype groups: cbd_core, orchard_corridor, heritage_cultural,
heartland_mature, heartland_young, west_edge, north_suburban, industrial,
airport_aviation, islands_resort, education, greenery.

Signal features to choose from (with value ranges so you set correct 'min'):
  population_total       (0 - 13,000 residents per hex)
  working_age_count      (0 - 8,000)
  walking_dependent_count(0 - 4,000)
  walkability_score      (0 - 98, higher better)
  walk_bus_m             (0 - 1500 meters; LOWER is better)
  walk_mrt_score         (0 - 1, higher better)
  mrt_stations           (0 - 5 count)
  bus_interchange_count  (0 - 3)
  hdb_blocks             (0 - 109 count)
  bldg_private_residential (0 - 120 count)
  lu_residential_pct     (0 - 1 fraction, higher = more residential)
  lu_commercial_pct      (0 - 0.93 fraction)
  lu_business_pct        (0 - 1 fraction)
  pc_total               (0 - 800 total places)
  pc_unique_place_types  (0 - 24 categories represented)
  pc_tier_value          (0 - N places in value tier)
  pc_tier_mid            (0 - N)
  pc_tier_premium        (0 - N)
  pc_tier_luxury         (0 - N)
  tourist_draw_est       (0 - large, tourist attraction weight)

IMPORTANT about 'min' values: use the feature's actual scale above.
  - walkability_score min=40 is fine (scale 0-98)
  - lu_residential_pct min=0.2 (NOT 20 — scale is 0-1)
  - population_total min=500 (residents, scale up to 13k)

Rules:
- Weights must sum to roughly 1.0 across signals.
- Use 3-6 signals, not all features.
- locality_fit and locality_avoid are small lists (2-5 each).
- Be specific to Singapore context.

EXAMPLE for "Starbucks":
{
  "name": "Starbucks",
  "kind": "premium specialty coffee chain",
  "primary_category": "cafe_coffee",
  "related_categories": ["cafe_coffee", "shopping_retail"],
  "price_tier": "premium",
  "target_demographics": {"age_range": "25-45 working professional",
                           "income_band": "mid_to_high", "household": "mixed"},
  "locality_fit": ["cbd_core", "orchard_corridor", "heartland_mature"],
  "locality_avoid": ["industrial", "islands_resort", "greenery"],
  "competitor_brands": ["toast box", "ya kun", "the coffee bean"],
  "signals": {
    "pc_tier_premium":   {"weight": 0.3, "direction": "high"},
    "walkability_score": {"weight": 0.2, "direction": "high", "min": 50},
    "mrt_stations":      {"weight": 0.2, "direction": "high"},
    "pc_total":          {"weight": 0.15, "direction": "high"},
    "tourist_draw_est":  {"weight": 0.15, "direction": "high"}
  },
  "reasoning": "Premium third-place chain. Targets office workers + affluent shoppers; needs MRT + premium retail density."
}"""


class ConceptProfiler:
    def __init__(self, llm_backend=None):
        self.llm = llm_backend  # ClaudeIntentBackend or compatible

    def profile(self, name: str, hint: str = "") -> ConceptProfile:
        """Return a ConceptProfile for this brand/concept."""
        key = name.lower().strip()

        # Fast path: hard-coded dictionary
        if key in HARDCODED_PROFILES:
            return HARDCODED_PROFILES[key]

        # LLM path
        if self.llm is not None:
            prompt = f"Brand/concept name: {name}"
            if hint:
                prompt += f"\nAdditional context: {hint}"
            try:
                data = self._ask_llm(prompt)
                if data and data.get("name"):
                    return ConceptProfile(
                        name=data.get("name", name),
                        kind=data.get("kind", ""),
                        primary_category=data.get("primary_category", "general"),
                        related_categories=data.get("related_categories", []),
                        price_tier=data.get("price_tier", "mid"),
                        target_demographics=data.get("target_demographics", {}),
                        locality_fit=data.get("locality_fit", []),
                        locality_avoid=data.get("locality_avoid", []),
                        competitor_brands=data.get("competitor_brands", []),
                        signals=data.get("signals", {}),
                        reasoning=data.get("reasoning", ""),
                        source="llm",
                    )
            except Exception as e:
                print(f"[merlion] ConceptProfiler LLM error: {e}")

        # Default fallback
        return ConceptProfile(
            name=name,
            kind="unknown",
            primary_category="general",
            reasoning=f"No profile available for '{name}'; using defaults.",
            source="default",
        )

    def _ask_llm(self, user_prompt: str) -> dict:
        """Call the LLM backend with our profiler system prompt."""
        # Reuse the Anthropic client from llm_backend if wired
        import anthropic
        key = os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            return {}
        client = anthropic.Anthropic(api_key=key)
        response = client.messages.create(
            model=getattr(self.llm, "model", "claude-sonnet-4-6"),
            max_tokens=1500,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )
        text = response.content[0].text.strip()
        if text.startswith("```"):
            text = text.split("```", 2)[1]
            if text.startswith("json"):
                text = text[4:].strip()
            text = text.rstrip("`").strip()
        return json.loads(text)
