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
OUTPUT_DIR = os.path.join(BASE_DIR, "micrograph_output")

# ── Spatial ──
EARTH_RADIUS_M = 6_371_000
M_PER_DEG_LAT = 111_320
SGP_CENTER_LAT = 1.3521
M_PER_DEG_LNG = M_PER_DEG_LAT * 0.9997  # cos(1.35°) ≈ 0.9997 (near equator!)

# ── Tier Definitions ──
# T1: Transit anchors (MRT stations, bus interchanges)
# T2: Competitors (same category)
# T3: Complementary (adjacent categories)
# T4: Demand magnets (offices, schools, malls, HDB blocks)

TIER_IMPORTANCE = {1: 3.0, 2: 2.5, 3: 2.0, 4: 1.5}

# Walk-time budgets (seconds) per density band per tier
# SGP is denser than NYC and walkable — shorter budgets
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
MIN_REVIEWS = 5  # SGP has fewer reviews than NYC
SIGMOID_STEEPNESS = 100  # seconds
SIGMOID_T_HALF_RATIO = 0.6

# ── Density Band Thresholds ──
# Based on weighted place density within 200m
DENSITY_THRESHOLDS = {
    "hyperdense": 400,
    "dense": 120,
    "moderate": 30,
    # sparse: < 30
}

# ── Anchor Detection Thresholds ──
MRT_MAJOR_RIDERSHIP = 30_000  # daily (interchange stations)
MRT_STANDARD_RIDERSHIP = 10_000
ANCHOR_SEARCH_RADIUS_M = 600  # SGP is compact

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

# ── Category → Tier Mapping (for CAFE pipeline) ──
CAFE_CATEGORY_TO_TIER = {
    # T2: Coffee competitors
    "Cafe": 2, "Coffee Shop": 2, "Coffee Roastery": 2, "Internet Cafe": 2,
    "Themed Cafe": 2, "Bubble Tea": 2,
    # T3: Complementary F&B
    "Bakery": 3, "Patisserie": 3, "Cake Shop": 3, "Donut Shop": 3,
    "Hawker Stall": 3, "Food Court": 3, "Hawker Centre": 3,
    "QSR": 3, "Fast Food": 3, "Dessert": 3, "Ice Cream": 3,
    "Restaurant": 3, "Noodle House": 3,
    # T4: Demand magnets
    "Office": 3, "Industrial": 4, "Gym": 4, "Fitness Centre": 4,
    "Shopping Mall": 4, "Hotel": 4, "Hospital": 4, "University": 4,
    "Preschool": 4, "Training Centre": 4, "Retail Store": 4,
    "Bookstore": 4, "Library": 4,
}

# ── Brand → Tier Overrides (SGP-specific) ──
CAFE_BRAND_TO_TIER = {
    # T2: Coffee chain competitors
    "Starbucks": 2, "The Coffee Bean & Tea Leaf": 2, "Luckin Coffee": 2,
    "Flash Coffee": 2, "Common Man Coffee Roasters": 2, "% Arabica": 2,
    "KOI Thé": 2, "LiHO": 2, "iTea": 2, "Each A Cup": 2, "Gong Cha": 2,
    "Chicha San Chen": 2, "R&B Tea": 2, "Tiger Sugar": 2, "PlayMade": 2,
    "Ya Kun Kaya Toast": 2, "Toast Box": 2, "Fun Toast": 2,
    "Tim Hortons": 2,
    # T3: F&B chains (complementary)
    "McDonald's": 3, "KFC": 3, "Subway": 3, "Pizza Hut": 3,
    "Burger King": 3, "Jollibee": 3, "MOS Burger": 3,
    "BreadTalk": 3, "Swee Heng": 3, "Four Leaves": 3, "Paris Baguette": 3,
    "Old Chang Kee": 3, "Mr Bean": 3, "Bengawan Solo": 3,
    "Din Tai Fung": 3, "Saizeriya": 3, "Swensen's": 3,
    # T4: Demand magnets (chain brands)
    "FairPrice": 4, "Sheng Siong": 4, "Cold Storage": 4, "Giant": 4,
    "Guardian": 4, "Watsons": 4, "Courts": 4, "IKEA": 4,
    "Anytime Fitness": 4, "The Gym Pod": 4,
    "UNIQLO": 4, "H&M": 4, "Daiso": 4, "Miniso": 4,
}

# ── Competition Sets ──
COMPETITION_SETS = [
    frozenset({"Cafe", "Coffee Shop", "Coffee Roastery", "Themed Cafe", "Internet Cafe"}),
    frozenset({"Bubble Tea", "Juice Bar", "Ice Cream", "Dessert"}),
    frozenset({"Bakery", "Patisserie", "Cake Shop", "Donut Shop"}),
    frozenset({"Restaurant", "Chinese Restaurant", "Japanese Restaurant",
               "Indian Restaurant", "Western Restaurant", "Thai Restaurant",
               "Korean Restaurant", "Vietnamese Restaurant", "Italian Restaurant",
               "Seafood Restaurant", "Malay Restaurant", "Halal Restaurant"}),
    frozenset({"QSR", "Fast Food"}),
    frozenset({"Hawker Stall", "Food Court", "Hawker Centre"}),
    frozenset({"Hair Salon", "Barber", "Beauty Salon"}),
    frozenset({"Gym", "Fitness Centre", "Yoga & Pilates", "Personal Training"}),
    frozenset({"GP Clinic", "Dental Clinic", "Optical", "Clinic"}),
    frozenset({"Convenience Store", "Grocery", "Supermarket"}),
]

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
