"""
Digital Atlas SGP — Micrograph Config
Singapore-specific thresholds, tiers, and category mappings.
"""
import os

# ── Paths ──
BASE_DIR = "/home/azureuser/digital-atlas-sgp"
DATA_DIR = os.path.join(BASE_DIR, "data")
PLACES_FILE = os.path.join(DATA_DIR, "places", "sgp_places.jsonl")
MRT_FILE = os.path.join(DATA_DIR, "transit_updated", "train_stations_mar2026.geojson")
BUS_FILE = os.path.join(DATA_DIR, "transit_updated", "bus_stops_mar2026.geojson")
SUBZONE_FILE = os.path.join(DATA_DIR, "boundaries", "subzones.geojson")
HAWKER_FILE = os.path.join(DATA_DIR, "amenities_updated", "hawker_centres.geojson")
SCHOOLS_FILE = os.path.join(DATA_DIR, "amenities_updated", "schools_directory.csv")
OUTPUT_DIR = os.path.join(BASE_DIR, "micrograph_output")

# ── Spatial ──
EARTH_RADIUS_M = 6_371_000
M_PER_DEG_LAT = 111_320
SGP_CENTER_LAT = 1.3521
M_PER_DEG_LNG = M_PER_DEG_LAT * 0.9997  # cos(1.35°) ≈ 0.9997 (near equator!)

# ── Tier Definitions ──
# T1: Transit anchors (MRT stations, bus interchanges)
# T2: Competitors (same competition set as target)
# T3: Complementary (adjacent categories that share foot traffic)
# T4: Demand magnets (offices, schools, malls, HDB, residential)

TIER_IMPORTANCE = {1: 3.0, 2: 2.5, 3: 2.0, 4: 1.5}

# Walk-time budgets (seconds) per density band per tier
TIER_BUDGETS = {
    "hyperdense": {1: 420, 2: 210, 3: 210, 4: 270},
    "dense":      {1: 480, 2: 270, 3: 270, 4: 360},
    "moderate":   {1: 600, 2: 360, 3: 360, 4: 480},
    "sparse":     {1: 720, 2: 480, 3: 480, 4: 600},
}

TIER_QUOTAS = {
    1: {"min": 0, "max": 3},
    2: {"min": 0, "max": 8},
    3: {"min": 0, "max": 8},
    4: {"min": 0, "max": 6},
}

TOTAL_MAX_ANCHORS = 25
MIN_REVIEWS = 5
SIGMOID_STEEPNESS = 100  # seconds
SIGMOID_T_HALF_RATIO = 0.6

# ── Density Band Thresholds ──
DENSITY_THRESHOLDS = {
    "hyperdense": 400,
    "dense": 120,
    "moderate": 30,
}

# ── Anchor Detection Thresholds ──
MRT_MAJOR_RIDERSHIP = 30_000
MRT_STANDARD_RIDERSHIP = 10_000
ANCHOR_SEARCH_RADIUS_M = 600

# ── Anchor Types & Radii ──
ANCHOR_SCALE = {
    "mrt_major":        {"radius_m": 400, "directional": True},
    "mrt_standard":     {"radius_m": 300, "directional": True},
    "mrt_minor":        {"radius_m": 250, "directional": True},
    "bus_interchange":  {"radius_m": 200, "directional": True},
    "hawker_centre":    {"radius_m": 300, "directional": False},
    "shopping_mall":    {"radius_m": 400, "directional": False},
    "supermarket":      {"radius_m": 250, "directional": False},
    "hospital":         {"radius_m": 400, "directional": False},
    "university":       {"radius_m": 400, "directional": False},
    "school":           {"radius_m": 300, "directional": False},
    "hdb_cluster":      {"radius_m": 200, "directional": False},
    "office_cluster":   {"radius_m": 300, "directional": False},
}

# ── Anchor Flow Estimates (daily foot traffic) ──
ANCHOR_FLOW_TIERS = {
    "mrt_major": 50_000,
    "mrt_standard": 20_000,
    "mrt_minor": 8_000,
    "bus_interchange": 15_000,
    "hawker_centre": 5_000,
    "shopping_mall": 20_000,
    "supermarket": 3_000,
    "hospital": 8_000,
    "university": 10_000,
    "school": 2_000,
    "hdb_cluster": 5_000,
    "office_cluster": 8_000,
}

# ── Per-Category Target Place Types ──
# These define which places each category pipeline processes
CATEGORY_TARGETS = {
    "cafe": {"Cafe", "Coffee Shop", "Coffee Roastery", "Themed Cafe", "Internet Cafe"},
    "restaurant": {
        "Restaurant", "Chinese Restaurant", "Japanese Restaurant", "Indian Restaurant",
        "Western Restaurant", "Thai Restaurant", "Korean Restaurant", "Seafood Restaurant",
        "Italian Restaurant", "French Restaurant", "Vietnamese Restaurant",
        "Malay Restaurant", "Halal Restaurant", "Vegetarian Restaurant",
        "Peranakan Restaurant", "Mexican Restaurant", "Indonesian Restaurant",
        "Fine Dining", "Buffet", "Noodle House", "Noodle Restaurant",
        "Takeout", "Catering", "Soup Restaurant", "Dim Sum Restaurant", "Seafood",
    },
    "hawker": {
        "Hawker Stall", "Food Court", "Hawker Centre", "Kopitiam",
        "Noodle Shop", "Street Food", "Hawker",
    },
    "fast_food_qsr": {
        "QSR", "Fast Food Restaurant", "Bubble Tea", "Dessert",
        "Ice Cream", "Juice Bar", "Snack Shop",
    },
    "bakery_pastry": {"Bakery", "Patisserie", "Cake Shop", "Donut Shop"},
    "bar_nightlife": {
        "Bar", "Pub", "Nightclub", "Lounge", "Cocktail Bar",
        "Wine Bar", "Brewery", "Karaoke",
    },
    "beauty_personal_care": {
        "Hair Salon", "Beauty Salon", "Barber", "Spa & Massage", "Spa",
        "Nail Salon", "Facial & Skincare", "Aesthetic Clinic",
        "Brows & Lashes", "TCM & Wellness", "Cosmetics",
    },
    "health_medical": {
        "GP Clinic", "Dental Clinic", "Clinic", "Hospital", "Optical",
        "Specialist Clinic", "Physiotherapy", "Medical", "Vet Clinic",
    },
    "fitness_recreation": {
        "Gym", "Fitness Centre", "Fitness", "Swimming Pool",
        "Martial Arts", "Boxing Gym", "Dance Studio", "Pilates Studio",
        "Sports Centre", "Sports Center", "Sports Club", "Sports Facility",
        "Badminton Court", "Tennis Court", "Tennis Club",
        "Basketball Court", "Football Field",
    },
    "education": {
        "Preschool", "Primary School", "Secondary School", "International School",
        "University", "Tuition Centre", "Training Centre", "Music School",
        "Learning Center", "Arts Academy", "School", "Education",
    },
    "shopping_retail": {
        "Retail Store", "Fashion Store", "Electronics Store", "Shopping Mall",
        "Bookstore", "Hardware Store", "Furniture Store", "Jewellery & Watch",
        "Market", "Gift Shop", "Florist", "Pet Shop", "Pet Store",
        "Shoe Store", "Sports Store", "Clothing Store", "Electronics",
        "Stationery", "Toy Store", "Bridal Shop", "Showroom",
    },
    "convenience_daily_needs": {
        "Convenience Store", "Grocery", "Supermarket", "Pharmacy",
        "Laundry", "ATM", "Bank", "Post Office", "Money Changer",
        "Discount Store", "Singapore Pools Outlet",
    },
}

# ── Competition Sets ──
# Place types that compete directly with each other.
# Used to dynamically assign T2 (competitor) for ANY category pipeline.
COMPETITION_SETS = [
    frozenset({"Cafe", "Coffee Shop", "Coffee Roastery", "Themed Cafe", "Internet Cafe"}),
    frozenset({"Bubble Tea", "Juice Bar", "Ice Cream", "Dessert", "Snack Shop"}),
    frozenset({"Bakery", "Patisserie", "Cake Shop", "Donut Shop"}),
    frozenset({
        "Restaurant", "Chinese Restaurant", "Japanese Restaurant",
        "Indian Restaurant", "Western Restaurant", "Thai Restaurant",
        "Korean Restaurant", "Vietnamese Restaurant", "Italian Restaurant",
        "Seafood Restaurant", "Malay Restaurant", "Halal Restaurant",
        "Vegetarian Restaurant", "Peranakan Restaurant", "Mexican Restaurant",
        "Indonesian Restaurant", "Fine Dining", "Buffet", "Noodle House",
        "Noodle Restaurant", "Takeout", "Catering", "Soup Restaurant",
        "Dim Sum Restaurant", "Seafood", "French Restaurant",
    }),
    frozenset({"QSR", "Fast Food Restaurant"}),
    frozenset({"Hawker Stall", "Food Court", "Hawker Centre", "Kopitiam", "Noodle Shop", "Street Food", "Hawker"}),
    frozenset({"Hair Salon", "Barber", "Beauty Salon"}),
    frozenset({"Spa & Massage", "Spa", "Facial & Skincare", "Aesthetic Clinic", "TCM & Wellness"}),
    frozenset({"Nail Salon", "Brows & Lashes"}),
    frozenset({"Gym", "Fitness Centre", "Fitness", "Boxing Gym", "Pilates Studio", "Martial Arts"}),
    frozenset({"GP Clinic", "Dental Clinic", "Optical", "Clinic", "Specialist Clinic"}),
    frozenset({"Convenience Store", "Grocery", "Supermarket"}),
    frozenset({"Bar", "Pub", "Cocktail Bar", "Wine Bar", "Brewery"}),
    frozenset({"Nightclub", "Lounge", "Karaoke"}),
]

# ── Per-Category Complementary Types ──
# T3: Types that share foot traffic with the target category but aren't direct competitors.
# Built dynamically in build_tier_mapping() — these are the explicit overrides.
FNB_TYPES = {
    "Cafe", "Coffee Shop", "Coffee Roastery", "Themed Cafe",
    "Bakery", "Patisserie", "Cake Shop", "Donut Shop",
    "Restaurant", "Chinese Restaurant", "Japanese Restaurant", "Indian Restaurant",
    "Western Restaurant", "Thai Restaurant", "Korean Restaurant", "Seafood Restaurant",
    "Italian Restaurant", "French Restaurant", "Vietnamese Restaurant",
    "Malay Restaurant", "Halal Restaurant", "Vegetarian Restaurant",
    "Peranakan Restaurant", "Mexican Restaurant", "Indonesian Restaurant",
    "Fine Dining", "Buffet", "Noodle House", "Noodle Restaurant", "Soup Restaurant",
    "Dim Sum Restaurant", "Seafood", "Takeout", "Catering",
    "Hawker Stall", "Food Court", "Hawker Centre", "Kopitiam", "Noodle Shop",
    "Street Food", "Hawker",
    "QSR", "Fast Food Restaurant", "Bubble Tea", "Dessert", "Ice Cream",
    "Juice Bar", "Snack Shop",
    "Bar", "Pub", "Cocktail Bar", "Wine Bar", "Brewery",
    "Nightclub", "Lounge", "Karaoke",
}

# Per-category complementary overrides (types that are T3 even though not F&B)
CATEGORY_COMPLEMENTARY = {
    "cafe":        {"Bookstore", "Library", "Workspace"},
    "restaurant":  {"Bar", "Pub", "Cocktail Bar", "Wine Bar"},
    "bar_nightlife": {"Restaurant", "Chinese Restaurant", "Japanese Restaurant", "Korean Restaurant"},
    "fitness_recreation": {"Juice Bar", "Cafe", "Spa & Massage", "Pharmacy"},
    "health_medical": {"Pharmacy", "Physiotherapy"},
    "beauty_personal_care": {"Nail Salon", "Brows & Lashes", "Cosmetics"},
    "education":   {"Bookstore", "Stationery", "Cafe"},
    "shopping_retail": {"Cafe", "Restaurant", "Food Court"},
    "convenience_daily_needs": {"Pharmacy"},
}

# ── Extra Competitors (T2) per Category ──
# Types that compete with a category but aren't in the same COMPETITION_SET.
# These prevent unwanted bridging across competition sets.
EXTRA_COMPETITORS = {
    "cafe": {"Bubble Tea"},  # bubble tea competes for drink customers
    "hawker": {"Dim Sum Restaurant"},  # dim sum is hawker-adjacent
}

# ── Demand Magnet Types ──
# T4: Places that generate foot traffic (not F&B competitors or complementary)
DEMAND_MAGNET_TYPES = {
    # Offices & workplaces
    "Office", "Office Building", "Workspace", "Office & Workspace",
    "Industrial", "Tech Company", "Company", "Business",
    # Education
    "Preschool", "Primary School", "Secondary School", "International School",
    "University", "School", "Tuition Centre", "Training Centre", "Education",
    # Retail & commercial
    "Shopping Mall", "Retail Store", "Fashion Store", "Electronics Store",
    "Market", "Supermarket", "Convenience Store",
    # Hospitality
    "Hotel", "Hostel", "Budget Hotel", "Guesthouse",
    # Health
    "Hospital", "GP Clinic", "Dental Clinic", "Clinic",
    # Residential
    "HDB", "Condo", "Apartment", "Residential", "Landed Property",
    # Recreation
    "Gym", "Fitness Centre", "Swimming Pool", "Playground",
    "Park", "Park & Green Space",
    # Transport
    "Transport Hub", "Bus Stop",
    # Civic
    "Community Centre", "Library", "Government Office",
    # Culture
    "Museum", "Cultural Venue", "Heritage Site", "Attraction",
}

# ── Brand → Tier Overrides (SGP-specific) ──
# These override the dynamic tier for specific brands.
# Key = brand name, Value = dict of {category: tier}
# If no category key, applies to all pipelines.
BRAND_OVERRIDES = {
    # Coffee chains → T2 for cafe, T3 for others
    "Starbucks": {"cafe": 2, "_default": 3},
    "The Coffee Bean & Tea Leaf": {"cafe": 2, "_default": 3},
    "Luckin Coffee": {"cafe": 2, "_default": 3},
    "Flash Coffee": {"cafe": 2, "_default": 3},
    "Common Man Coffee Roasters": {"cafe": 2, "_default": 3},
    "% Arabica": {"cafe": 2, "_default": 3},
    "Ya Kun Kaya Toast": {"cafe": 2, "hawker": 2, "_default": 3},
    "Toast Box": {"cafe": 2, "hawker": 2, "_default": 3},
    "Fun Toast": {"cafe": 2, "hawker": 2, "_default": 3},
    "Tim Hortons": {"cafe": 2, "_default": 3},
    # Bubble tea chains → T2 for fast_food_qsr, T3 for cafe, T4 for rest
    "KOI Thé": {"fast_food_qsr": 2, "cafe": 2, "_default": 3},
    "LiHO": {"fast_food_qsr": 2, "cafe": 2, "_default": 3},
    "iTea": {"fast_food_qsr": 2, "cafe": 2, "_default": 3},
    "Each A Cup": {"fast_food_qsr": 2, "cafe": 2, "_default": 3},
    "Gong Cha": {"fast_food_qsr": 2, "cafe": 2, "_default": 3},
    "Chicha San Chen": {"fast_food_qsr": 2, "cafe": 2, "_default": 3},
    "R&B Tea": {"fast_food_qsr": 2, "cafe": 2, "_default": 3},
    "Tiger Sugar": {"fast_food_qsr": 2, "cafe": 2, "_default": 3},
    "PlayMade": {"fast_food_qsr": 2, "cafe": 2, "_default": 3},
    # QSR chains → T2 for fast_food_qsr, T3 for restaurant/hawker
    "McDonald's": {"fast_food_qsr": 2, "restaurant": 3, "hawker": 3, "_default": 3},
    "KFC": {"fast_food_qsr": 2, "restaurant": 3, "_default": 3},
    "Subway": {"fast_food_qsr": 2, "restaurant": 3, "_default": 3},
    "Pizza Hut": {"fast_food_qsr": 2, "restaurant": 3, "_default": 3},
    "Burger King": {"fast_food_qsr": 2, "restaurant": 3, "_default": 3},
    "Jollibee": {"fast_food_qsr": 2, "restaurant": 3, "_default": 3},
    "MOS Burger": {"fast_food_qsr": 2, "restaurant": 3, "_default": 3},
    # Bakery chains → T2 for bakery_pastry, T3 for cafe
    "BreadTalk": {"bakery_pastry": 2, "cafe": 3, "_default": 3},
    "Swee Heng": {"bakery_pastry": 2, "cafe": 3, "_default": 3},
    "Four Leaves": {"bakery_pastry": 2, "cafe": 3, "_default": 3},
    "Paris Baguette": {"bakery_pastry": 2, "cafe": 3, "_default": 3},
    "Old Chang Kee": {"bakery_pastry": 2, "fast_food_qsr": 3, "_default": 3},
    "Mr Bean": {"fast_food_qsr": 2, "_default": 3},
    "Bengawan Solo": {"bakery_pastry": 2, "_default": 3},
    # Restaurant chains
    "Din Tai Fung": {"restaurant": 2, "_default": 3},
    "Saizeriya": {"restaurant": 2, "_default": 3},
    "Swensen's": {"restaurant": 2, "_default": 3},
    # Supermarket/grocery chains → T4 demand magnets
    "FairPrice": {"convenience_daily_needs": 2, "_default": 4},
    "Sheng Siong": {"convenience_daily_needs": 2, "_default": 4},
    "Cold Storage": {"convenience_daily_needs": 2, "_default": 4},
    "Giant": {"convenience_daily_needs": 2, "_default": 4},
    "Guardian": {"convenience_daily_needs": 2, "health_medical": 3, "_default": 4},
    "Watsons": {"convenience_daily_needs": 2, "health_medical": 3, "_default": 4},
    # Retail chains → T4 demand magnets
    "Courts": {"shopping_retail": 2, "_default": 4},
    "IKEA": {"shopping_retail": 2, "_default": 4},
    "UNIQLO": {"shopping_retail": 2, "_default": 4},
    "H&M": {"shopping_retail": 2, "_default": 4},
    "Daiso": {"shopping_retail": 2, "_default": 4},
    "Miniso": {"shopping_retail": 2, "_default": 4},
    # Fitness chains → T4 demand magnets (T2 for fitness)
    "Anytime Fitness": {"fitness_recreation": 2, "_default": 4},
    "The Gym Pod": {"fitness_recreation": 2, "_default": 4},
}

# ── Negative Pairs ──
NEGATIVE_PAIRS = {
    ("Cafe", "Nightclub"): 0.3,
    ("Preschool", "Bar"): 0.8,
    ("Preschool", "Nightclub"): 0.8,
    ("GP Clinic", "Bar"): 0.4,
}

# ── Known Complementary ──
KNOWN_COMPLEMENTARY = {
    frozenset({"Cafe", "Bookstore"}): 0.7,
    frozenset({"Cafe", "Bakery"}): 0.7,
    frozenset({"Restaurant", "Bar"}): 0.6,
    frozenset({"Gym", "Juice Bar"}): 0.7,
    frozenset({"Gym", "Cafe"}): 0.5,
    frozenset({"Shopping Mall", "Cafe"}): 0.6,
    frozenset({"Office", "Cafe"}): 0.8,
    frozenset({"Hospital", "Pharmacy"}): 0.8,
    frozenset({"Preschool", "Cafe"}): 0.5,
    frozenset({"MRT / LRT Station", "Convenience Store"}): 0.7,
}

# ── Edge Weights ──
EDGE_WEIGHT_MIN = 0.05
CCM_THRESHOLD = 1.0
MAX_SEARCH_RADIUS_M = 600

# ── T2 Selection Strategy per Density Band ──
T2_SELECTION = {
    "hyperdense": "magnitude",
    "dense": "magnitude",
    "moderate": "walktime",
    "sparse": "walktime",
}

# ── OSM Network ──
OSM_WALK_SPEED_MS = 1.34  # 4.8 km/h
SNAP_K_CANDIDATES = 15
SNAP_MIN_REACHABLE = 100
SNAP_MAX_DISTANCE_M = 200

# ── Bus Interchange Names (subset of bus stops that are interchanges) ──
BUS_INTERCHANGE_KEYWORDS = {
    "INT", "INTERCHANGE", "TER", "TERMINAL",
}


# ============================================================
# DYNAMIC TIER MAPPING
# ============================================================
def build_tier_mapping(target_category):
    """
    Build a place_type → tier mapping for a given category pipeline.

    Logic:
    1. Find which COMPETITION_SETs overlap with the target's place types → T2
    2. Other F&B / related types → T3
    3. Demand magnets → T4
    """
    target_types = CATEGORY_TARGETS.get(target_category, set())

    # Find all competitor types: any COMPETITION_SET that overlaps with target types
    competitor_types = set()
    for cs in COMPETITION_SETS:
        if cs & target_types:
            competitor_types |= cs

    # Add the target types themselves as competitors
    competitor_types |= target_types

    # Add per-category extra competitors (avoids competition set bridging)
    competitor_types |= EXTRA_COMPETITORS.get(target_category, set())

    # Get category-specific complementary overrides
    extra_complementary = CATEGORY_COMPLEMENTARY.get(target_category, set())

    mapping = {}

    # T2: Competitors
    for pt in competitor_types:
        mapping[pt] = 2

    # T3: Complementary — other F&B types + category-specific extras
    is_fnb_category = target_category in FNB_CATEGORIES
    if is_fnb_category:
        # Other F&B types that aren't competitors → T3
        for pt in FNB_TYPES:
            if pt not in mapping:
                mapping[pt] = 3
        # Extra complementary
        for pt in extra_complementary:
            if pt not in mapping:
                mapping[pt] = 3
    else:
        # Non-F&B category: complementary overrides only
        for pt in extra_complementary:
            if pt not in mapping:
                mapping[pt] = 3

    # T4: Demand magnets (anything that generates foot traffic)
    for pt in DEMAND_MAGNET_TYPES:
        if pt not in mapping:
            mapping[pt] = 4

    return mapping


FNB_CATEGORIES = {
    "cafe", "restaurant", "hawker", "fast_food_qsr", "bakery_pastry", "bar_nightlife",
}

def get_brand_tier(brand, target_category):
    """Get tier override for a brand in a specific category pipeline.

    For non-F&B categories, _default=3 (complementary) is upgraded to 4 (demand magnet)
    since F&B chains generate foot traffic for non-F&B businesses, not complementary synergy.
    """
    if brand not in BRAND_OVERRIDES:
        return None
    overrides = BRAND_OVERRIDES[brand]
    if target_category in overrides:
        return overrides[target_category]
    default_tier = overrides.get("_default")
    # For non-F&B categories, F&B brands are foot traffic generators (T4), not complementary (T3)
    if default_tier == 3 and target_category not in FNB_CATEGORIES:
        return 4
    return default_tier
