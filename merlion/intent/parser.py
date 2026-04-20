"""
Intent parser — natural language → structured Intent object.

Two strategies, both pluggable:
  1. RULE_BASED: regex + keyword rules (no deps, deterministic, fast)
  2. LLM: call an LLM to extract intent + entities (better for ambiguous queries)

Intent schema:
  use_case:   str              canonical use-case name (e.g. "site_selection")
  entities:   dict[str, Any]   extracted slot values (anchor, brand, category, ...)
  confidence: float            0..1 how sure we are
  raw_query:  str              original input
  strategy:   str              "rule_based" | "llm" | "direct"

The parser.parse() returns a list of candidate Intents ranked by confidence.
"""
import re
from dataclasses import dataclass, field, asdict
from typing import Any, Callable, Optional


# ============================================================
# Intent dataclass
# ============================================================
@dataclass
class Intent:
    use_case: str
    entities: dict = field(default_factory=dict)
    confidence: float = 0.0
    raw_query: str = ""
    strategy: str = "rule_based"

    def to_dict(self) -> dict:
        return asdict(self)


# ============================================================
# Known use cases and their trigger patterns
# Each pattern: (regex, intent_name, required_entities, confidence_boost)
# ============================================================
USE_CASE_PATTERNS = [
    # --- site selection ---
    (r"\b(where\s+should|find\s+sites?|site\s+for|location\s+for|where\s+to\s+put|expand(?:ing)?)\b",
     "site_selection", ["anchor_or_brand"], 0.9),
    (r"\b(similar\s+to|like\s+the|lookalike|look-?alike)\b",
     "site_selection", ["anchor"], 0.7),

    # --- gap analysis ---
    (r"\b(gap|under.?served|under.?supplied|missing|deficit)\b",
     "gap_analysis", ["category"], 0.9),
    (r"\b(expected\s+vs\s+actual|what\s+should\s+exist|whitespace)\b",
     "gap_analysis", ["category"], 0.8),

    # --- archetype / clustering ---
    (r"\b(archetype|cluster(?:ing)?|segment(?:ation)?|group(?:ing)?\s+by\s+character)\b",
     "archetype_clustering", [], 0.9),
    (r"\b(what\s+kind\s+of\s+area|neighborhood\s+type|urban\s+type)\b",
     "archetype_clustering", [], 0.8),

    # --- comparable market / valuation ---
    (r"\b(comparable|comps?|valuation|appraise|comparison)\b",
     "comparable_market", ["target"], 0.9),
    (r"\b(hexes?\s+like|neighborhoods?\s+like|places\s+like)\b",
     "comparable_market", ["target"], 0.8),

    # --- brand whitespace ---
    (r"\b(whitespace|white\s+space|uncontested|no\s+competition)\b",
     "whitespace_analysis", ["brand"], 0.9),
    (r"\b(where\s+(?:is|are)\s+.*?\s+missing|absent)\b",
     "whitespace_analysis", ["brand"], 0.7),

    # --- predictions ---
    (r"\b(predict|expected\s+count|forecast|how\s+many)\b",
     "category_prediction", ["category"], 0.85),

    # --- feature-profile match ---
    (r"\b(hexes?\s+with|profile\s+like|combination\s+of|feature\s+query)\b",
     "feature_query", [], 0.75),

    # --- food / amenity desert ---
    (r"\b(food\s+desert|amenity\s+desert|transit\s+desert)\b",
     "amenity_desert", [], 0.95),

    # --- 15-min city ---
    (r"\b(15.?min(?:ute)?\s+city|walkability\s+score|walkable)\b",
     "fifteen_minute_city", [], 0.95),
]


# ============================================================
# Entity extraction patterns
# ============================================================
# Singapore planning areas / landmarks we recognize by name
SGP_LOCATIONS = {
    # Major landmarks
    "raffles place": ("DOWNTOWN CORE", (1.2841, 103.8515)),
    "marina bay": ("DOWNTOWN CORE", (1.2838, 103.8591)),
    "marina bay sands": ("DOWNTOWN CORE", (1.2838, 103.8591)),
    "orchard": ("ORCHARD", (1.3048, 103.8318)),
    "orchard road": ("ORCHARD", (1.3048, 103.8318)),
    "tiong bahru": ("BUKIT MERAH", (1.2852, 103.8306)),
    "changi": ("CHANGI", (1.3554, 103.9840)),
    "changi airport": ("CHANGI", (1.3554, 103.9840)),
    "sentosa": ("SOUTHERN ISLANDS", (1.2541, 103.8231)),
    "tampines": ("TAMPINES", (1.3549, 103.9442)),
    "jurong east": ("JURONG EAST", (1.3331, 103.7428)),
    "jurong west": ("JURONG WEST", (1.3404, 103.7090)),
    "tuas": ("TUAS", (1.3240, 103.6360)),
    "bedok": ("BEDOK", (1.3236, 103.9273)),
    "nus": ("QUEENSTOWN", (1.2966, 103.7764)),
    "kent ridge": ("QUEENSTOWN", (1.2966, 103.7764)),
    "woodlands": ("WOODLANDS", (1.4382, 103.7883)),
    "ang mo kio": ("ANG MO KIO", (1.3691, 103.8454)),
    "toa payoh": ("TOA PAYOH", (1.3343, 103.8563)),
    "hougang": ("HOUGANG", (1.3612, 103.8864)),
    "yishun": ("YISHUN", (1.4297, 103.8352)),
    "choa chu kang": ("CHOA CHU KANG", (1.3854, 103.7441)),
    "bukit batok": ("BUKIT BATOK", (1.3590, 103.7637)),
    "pasir ris": ("PASIR RIS", (1.3721, 103.9474)),
    "serangoon": ("SERANGOON", (1.3554, 103.8679)),
    "punggol": ("PUNGGOL", (1.3984, 103.9072)),
    "sengkang": ("SENGKANG", (1.3868, 103.8914)),
    "clementi": ("CLEMENTI", (1.3162, 103.7649)),
    "queenstown": ("QUEENSTOWN", (1.2942, 103.8058)),
    "geylang": ("GEYLANG", (1.3189, 103.8865)),
    "kallang": ("KALLANG", (1.3110, 103.8637)),
    "novena": ("NOVENA", (1.3203, 103.8435)),
    "bukit timah": ("BUKIT TIMAH", (1.3294, 103.8021)),
    "tanjong pagar": ("OUTRAM", (1.2758, 103.8461)),
    "chinatown": ("OUTRAM", (1.2842, 103.8439)),
    "bugis": ("DOWNTOWN CORE", (1.3006, 103.8555)),
    "little india": ("ROCHOR", (1.3067, 103.8498)),
    "katong": ("MARINE PARADE", (1.3055, 103.9023)),
}

# Category vocabulary (maps colloquial → canonical pc_cat_*)
# Keys include singular + plural forms so regex boundary matches both.
CATEGORIES = {
    "cafe": "cafe_coffee",
    "cafes": "cafe_coffee",
    "coffee shop": "cafe_coffee",
    "coffee shops": "cafe_coffee",
    "coffee": "cafe_coffee",
    "restaurant": "restaurant",
    "restaurants": "restaurant",
    "hawker": "hawker_street_food",
    "hawkers": "hawker_street_food",
    "hawker centre": "hawker_street_food",
    "hawker centres": "hawker_street_food",
    "hawker center": "hawker_street_food",
    "hawker centers": "hawker_street_food",
    "hawker stall": "hawker_street_food",
    "hawker stalls": "hawker_street_food",
    "fast food": "fast_food_qsr",
    "qsr": "fast_food_qsr",
    "bar": "bar_nightlife",
    "bars": "bar_nightlife",
    "nightlife": "bar_nightlife",
    "bakery": "bakery_pastry",
    "bakeries": "bakery_pastry",
    "convenience": "convenience_daily_needs",
    "convenience store": "convenience_daily_needs",
    "convenience stores": "convenience_daily_needs",
    "mart": "convenience_daily_needs",
    "marts": "convenience_daily_needs",
    "supermarket": "convenience_daily_needs",
    "supermarkets": "convenience_daily_needs",
    "school": "education",
    "schools": "education",
    "childcare": "education",
    "preschool": "education",
    "preschools": "education",
    "kindergarten": "education",
    "kindergartens": "education",
    "clinic": "health_medical",
    "clinics": "health_medical",
    "hospital": "health_medical",
    "hospitals": "health_medical",
    "gym": "fitness_recreation",
    "gyms": "fitness_recreation",
    "fitness": "fitness_recreation",
    "hotel": "hospitality",
    "hotels": "hospitality",
    "office": "office_workspace",
    "offices": "office_workspace",
    "shop": "shopping_retail",
    "shops": "shopping_retail",
    "retail": "shopping_retail",
    "mall": "shopping_retail",
    "malls": "shopping_retail",
    "beauty": "beauty_personal_care",
    "salon": "beauty_personal_care",
    "salons": "beauty_personal_care",
    "church": "religious",
    "churches": "religious",
    "temple": "religious",
    "temples": "religious",
    "mosque": "religious",
    "mosques": "religious",
    "religious": "religious",
    "culture": "culture_entertainment",
    "entertainment": "culture_entertainment",
    "museum": "culture_entertainment",
    "museums": "culture_entertainment",
}

# Known brands (extensible)
BRANDS = {
    "starbucks", "toast box", "ya kun", "killiney", "mcdonald's", "mcdonalds",
    "kfc", "burger king", "subway", "dominos", "pizza hut",
    "fairprice", "cold storage", "giant", "ntuc", "sheng siong",
    "7-eleven", "7 eleven", "cheers", "guardian", "watsons",
    "the coffee bean", "tim hortons", "bread talk", "paris baguette",
    "din tai fung", "crystal jade", "paradise",
}

HEX_ID_RE = re.compile(r"\b[0-9a-f]{15}\b")
LATLNG_RE = re.compile(r"\b(1\.\d{3,})\s*[,\s]\s*(103\.\d{3,})\b")


def extract_entities(query: str) -> dict:
    """Pull locations, categories, brands, hex IDs, lat/lng from a free-text query."""
    q = query.lower()
    entities = {}

    # Locations (prefer longer matches)
    matched_locs = []
    for name in sorted(SGP_LOCATIONS.keys(), key=len, reverse=True):
        if name in q:
            pa, (lat, lng) = SGP_LOCATIONS[name]
            matched_locs.append({"name": name, "pa": pa, "lat": lat, "lng": lng})
            q = q.replace(name, "")  # avoid double-matching
    if matched_locs:
        entities["locations"] = matched_locs

    # Categories
    matched_cats = []
    for k in sorted(CATEGORIES.keys(), key=len, reverse=True):
        if re.search(rf"\b{re.escape(k)}\b", q):
            matched_cats.append(CATEGORIES[k])
    if matched_cats:
        entities["categories"] = list(dict.fromkeys(matched_cats))  # dedupe preserving order

    # Brands
    matched_brands = []
    for b in sorted(BRANDS, key=len, reverse=True):
        if re.search(rf"\b{re.escape(b)}\b", query, re.IGNORECASE):
            matched_brands.append(b)
    if matched_brands:
        entities["brands"] = matched_brands

    # Hex IDs
    hex_ids = HEX_ID_RE.findall(query)
    if hex_ids:
        entities["hex_ids"] = hex_ids

    # Raw lat/lng pairs
    latlng = LATLNG_RE.findall(query)
    if latlng:
        entities["coords"] = [(float(la), float(ln)) for la, ln in latlng]

    # Integer k (top-k)
    m = re.search(r"\btop\s+(\d{1,3})\b|\b(\d{1,3})\s+(?:sites?|hexes?|candidates?|results?)\b", q)
    if m:
        k = int(m.group(1) or m.group(2))
        entities["k"] = max(1, min(k, 200))

    return entities


# ============================================================
# Parser
# ============================================================
class IntentParser:
    """
    Parse a free-text query into a ranked list of Intent candidates.

    Usage:
      parser = IntentParser()
      intents = parser.parse("find 20 sites similar to tanjong pagar for a cafe")
      top = intents[0]
      # top.use_case == "site_selection"
      # top.entities == {"locations": [...], "categories": ["cafe_coffee"], "k": 20}
    """

    def __init__(self, llm_backend: Optional[Callable[[str], dict]] = None):
        """
        llm_backend: optional callable(query) -> {"use_case": ..., "entities": {...}}
                     When set, falls back to LLM if rule-based confidence < 0.5.
                     Currently not wired; extension point.
        """
        self.llm_backend = llm_backend

    def parse(self, query: str, top_n: int = 3) -> list[Intent]:
        """Return ranked Intent candidates (highest confidence first)."""
        q = query.strip()
        if not q:
            return []

        entities = extract_entities(q)

        # Score each use case pattern
        candidates: list[Intent] = []
        ql = q.lower()
        for pattern, use_case, _required, boost in USE_CASE_PATTERNS:
            if re.search(pattern, ql, re.IGNORECASE):
                # Entity bonus: if we extracted relevant entities, bump confidence
                ent_bonus = 0.0
                if entities.get("brands"):        ent_bonus += 0.05
                if entities.get("locations"):     ent_bonus += 0.05
                if entities.get("categories"):    ent_bonus += 0.03
                if entities.get("hex_ids"):       ent_bonus += 0.05
                conf = min(1.0, boost + ent_bonus)
                candidates.append(Intent(
                    use_case=use_case,
                    entities=entities,
                    confidence=conf,
                    raw_query=query,
                    strategy="rule_based",
                ))

        # Dedupe: keep highest-confidence per use_case
        best_per_uc: dict[str, Intent] = {}
        for c in candidates:
            if c.use_case not in best_per_uc or c.confidence > best_per_uc[c.use_case].confidence:
                best_per_uc[c.use_case] = c

        ranked = sorted(best_per_uc.values(), key=lambda i: -i.confidence)[:top_n]

        # Fallback: if nothing matched confidently and entities suggest a topic, guess
        if (not ranked or ranked[0].confidence < 0.5):
            guess = self._fallback_guess(query, entities)
            if guess is not None:
                ranked = [guess] + ranked

        # Optional LLM backup (stub — wire up later)
        if self.llm_backend and (not ranked or ranked[0].confidence < 0.5):
            llm_result = self.llm_backend(query)
            if llm_result:
                ranked = [Intent(
                    use_case=llm_result.get("use_case", "unknown"),
                    entities={**entities, **llm_result.get("entities", {})},
                    confidence=0.6,
                    raw_query=query,
                    strategy="llm",
                )] + ranked

        return ranked

    def _fallback_guess(self, query: str, entities: dict) -> Optional[Intent]:
        """If no pattern matched but entities are present, make an educated guess."""
        if entities.get("brands"):
            return Intent(use_case="site_selection", entities=entities,
                          confidence=0.45, raw_query=query, strategy="rule_based_fallback")
        if entities.get("categories") and "gap" not in query.lower():
            return Intent(use_case="category_prediction", entities=entities,
                          confidence=0.4, raw_query=query, strategy="rule_based_fallback")
        if entities.get("locations"):
            return Intent(use_case="comparable_market", entities=entities,
                          confidence=0.4, raw_query=query, strategy="rule_based_fallback")
        return None
