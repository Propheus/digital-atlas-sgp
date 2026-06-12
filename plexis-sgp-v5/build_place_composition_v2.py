"""
Plexis SGP v4 — Stage 24: finer-grained place composition (V2 taxonomy).

The v1 place_composition uses 24 plexis_categories. This V2 expands to
48 sub-categories via a deterministic primary_category → pc2_cat map.

Per scale:
  pc2_total                      total places
  pc2_branded_count              count with brand_norm
  pc2_unbranded_count            count without brand_norm
  pc2_cat_<48_cats>_count        per-finer-cat count
  pc2_dominant_category          string

Outputs:
  hex/hex9_place_composition_v2.parquet
  hex/hex8_place_composition_v2.parquet
  hex/subzone_place_composition_v2.parquet
"""
import json, time
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).parent

# Map from raw primary_category → finer pc2_cat (48 buckets)
CAT_MAP = {
    # ----- FOOD & BEVERAGE (8) -----
    "Restaurant":            "food_restaurant",
    "Cafe":                  "food_cafe",
    "Coffee Shop":           "food_cafe",
    "Fast Food":             "food_fast_food",
    "Hawker Stall":          "food_hawker",
    "Hawker Centre":         "food_hawker",
    "Food Court":            "food_hawker",
    "Bakery":                "food_bakery",
    "Dessert":               "food_dessert",
    "Bubble Tea":            "food_dessert",
    "Juice Bar":             "food_dessert",
    "Specialty Food":        "food_dessert",
    "Bar/Pub":               "food_bar",
    "Caterer":               "food_caterer",

    # ----- RETAIL (8) -----
    "Apparel":               "retail_apparel",
    "Tailor":                "retail_apparel",
    "Electronics Store":     "retail_electronics",
    "Jewelry":               "retail_jewelry_cosmetics",
    "Cosmetics":             "retail_jewelry_cosmetics",
    "Beauty Retail":         "retail_jewelry_cosmetics",
    "Furniture Store":       "retail_furniture_home",
    "Hardware Store":        "retail_furniture_home",
    "Stationery":            "retail_furniture_home",
    "Bookstore":             "retail_furniture_home",
    "General Store":         "retail_general",
    "Discount Store":        "retail_general",
    "Specialty Retail":      "retail_general",
    "Pet Store":             "retail_general",
    "Toy Store":             "retail_general",
    "Sports Store":          "retail_general",
    "Gift Shop":             "retail_general",
    "Pawnshop":              "retail_general",
    "Department Store":      "retail_general",
    "Florist":               "retail_general",
    "Bicycle Shop":          "retail_general",
    "Music Studio":          "retail_general",
    "Supermarket":           "retail_supermarket",
    "Health Store":          "retail_supermarket",
    "Market":                "retail_supermarket",
    "Convenience Store":     "retail_convenience",
    "Self-Service Kiosk":    "retail_convenience",
    "Vending Machine":       "retail_convenience",
    "Kiosk":                 "retail_convenience",
    "Lottery Retailer":      "retail_convenience",
    "Telecom Shop":          "retail_convenience",
    "ATM":                   "retail_convenience",
    "Parcel Locker":         "retail_convenience",
    "Shopping Mall":         "retail_mall",

    # ----- SERVICES (10) -----
    "Beauty Salon":          "service_beauty",
    "Hair Salon":            "service_beauty",
    "Nail Salon":            "service_beauty",
    "Massage/Spa":           "service_beauty",
    "Aesthetic Clinic":      "service_beauty",
    "Gym":                   "service_fitness",
    "Sports Facility":       "service_fitness",
    "Laundry":               "service_cleaning_repair",
    "Cleaning Service":      "service_cleaning_repair",
    "Plumber":               "service_cleaning_repair",
    "Electrician":           "service_cleaning_repair",
    "Locksmith":             "service_cleaning_repair",
    "Law Firm":              "service_legal_finance",
    "Accounting Firm":       "service_legal_finance",
    "Financial Services":    "service_legal_finance",
    "Insurance":             "service_legal_finance",
    "Bank":                  "service_legal_finance",
    "Money Transfer":        "service_legal_finance",
    "Real Estate":           "service_real_estate",
    "Consultant":            "service_consulting",
    "Engineering":           "service_consulting",
    "Marketing Agency":      "service_consulting",
    "Media Company":         "service_consulting",
    "Print Shop":            "service_consulting",
    "Photography Studio":    "service_consulting",
    "Research":              "service_consulting",
    "Laboratory":            "service_consulting",
    "Event Management":      "service_consulting",
    "Travel Agency":         "service_consulting",
    "Tour Operator":         "service_consulting",
    "Employment Agency":     "service_consulting",
    "Software/IT":           "service_consulting",
    "Pet Services":          "service_pet",
    "Veterinarian":          "service_pet",
    "Car Workshop":          "service_automotive",
    "Car Parts":             "service_automotive",
    "Car Dealer":            "service_automotive",
    "Car Rental":            "service_automotive",
    "Car Sharing":           "service_automotive",
    "Petrol Station":        "service_automotive",
    "Logistics":             "service_logistics",
    "Wholesale":             "service_logistics",
    "Trading Company":       "service_logistics",
    "Industrial Supplier":   "service_logistics",
    "Manufacturer":          "service_logistics",
    "Parcel/Courier":        "service_logistics",
    "Service Provider":      "service_other",
    "Interior Design":       "service_other",
    "Landscape Design":      "service_other",
    "Coworking Space":       "service_other",
    "Telecom":               "service_other",
    "Security Services":     "service_other",
    "Construction":          "service_other",

    # ----- EDUCATION (5) -----
    "Preschool":             "edu_preschool",
    "School":                "edu_primary_secondary",
    "University":            "edu_tertiary",
    "Polytechnic":           "edu_tertiary",
    "Junior College":        "edu_tertiary",
    "Tuition Centre":        "edu_tuition",
    "Art Studio":            "edu_specialty",
    "Performing Arts":       "edu_specialty",

    # ----- HEALTHCARE (5) -----
    "Medical Clinic":        "health_clinic",
    "Specialist Clinic":     "health_specialist",
    "Dental Clinic":         "health_specialist",
    "Optical":               "health_specialist",
    "Physiotherapy":         "health_specialist",
    "Pharmacy":              "health_pharmacy",
    "TCM Pharmacy":          "health_pharmacy",
    "TCM Clinic":            "health_tcm",
    "Hospital":              "health_hospital",
    "Polyclinic":            "health_hospital",

    # ----- RESIDENTIAL (3) -----
    "HDB":                   "res_hdb",
    "Condominium":           "res_private",
    "Private Apartment":     "res_private",
    "Housing Estate":        "res_private",
    "Housing Development":   "res_private",
    "Aged Care":             "res_aged_care",

    # ----- TRANSPORTATION (5) -----
    "MRT/LRT Station":       "transport_mrt",
    "Train Station":         "transport_mrt",
    "Bus Stop":              "transport_bus",
    "Bus Station":           "transport_bus",
    "Bus Interchange":       "transport_bus",
    "Taxi Stand":            "transport_bus",
    "Airport":               "transport_air",
    "Airline":               "transport_air",
    "Parking Lot":           "transport_parking",
    "EV Charging":           "transport_ev",
    "Transportation":        "transport_bus",
    "Bridge":                "transport_other",

    # ----- CIVIC (4) -----
    "Government Office":     "civic_government",
    "Police Station":        "civic_government",
    "Fire Station":          "civic_government",
    "Post Office":           "civic_government",
    "Embassy":               "civic_government",
    "Community Club":        "civic_community",
    "Library":               "civic_community",
    "Public Bathroom":       "civic_community",
    "Cultural Centre":       "civic_community",
    "Place of Worship":      "civic_religious",
    "Buddhist Temple":       "civic_religious",
    "Hindu Temple":          "civic_religious",
    "Mosque":                "civic_religious",
    "Church":                "civic_religious",
    "Chinese Temple":        "civic_religious",
    "Cemetery":              "civic_religious",
    "Funeral Service":       "civic_religious",
    "Non-profit":            "civic_nonprofit",

    # ----- LEISURE & CULTURE (3) -----
    "Park":                  "leisure_park",
    "Playground":            "leisure_park",
    "Tourist Attraction":    "leisure_tourist",
    "Cinema":                "leisure_entertainment",
    "Event Venue":           "leisure_entertainment",
    "Art Gallery":           "leisure_entertainment",
    "Museum":                "leisure_entertainment",

    # ----- BUSINESS / OFFICE (1) -----
    "Corporate Office":      "biz_office",

    # ----- UNKNOWN -----
    "Other":                 "other",
    "Uncategorized":         "other",
}

ALL_PC2_CATS = sorted(set(CAT_MAP.values()) | {"unmapped"})


def map_to_pc2(raw):
    return CAT_MAP.get(raw, "unmapped")


def aggregate(places, key_col):
    g = places.groupby(key_col)
    base = g.agg(
        pc2_total=("id", "count"),
        pc2_branded_count=("brand_norm", lambda s: s.notna().sum()),
    ).reset_index()
    base["pc2_unbranded_count"] = base["pc2_total"] - base["pc2_branded_count"]

    # Per-cat counts via crosstab
    ct = pd.crosstab(places[key_col], places["pc2_category"]).reindex(columns=ALL_PC2_CATS, fill_value=0)
    ct.columns = [f"pc2_cat_{c}_count" for c in ALL_PC2_CATS]
    ct = ct.reset_index()

    out = base.merge(ct, on=key_col, how="left")

    # Dominant cat
    cat_cols = [c for c in out.columns if c.startswith("pc2_cat_")]
    arr = out[cat_cols].values.astype(int)
    dom_idx = arr.argmax(axis=1)
    cats_arr = np.array([c.replace("pc2_cat_", "").replace("_count", "") for c in cat_cols])
    dom = cats_arr[dom_idx]
    dom[arr.sum(axis=1) == 0] = "none"
    out["pc2_dominant_category"] = dom
    return out


def fill_zeros(df, all_cat_cols):
    fill_cols = ["pc2_total","pc2_branded_count","pc2_unbranded_count"] + all_cat_cols
    for c in fill_cols:
        if c in df.columns: df[c] = df[c].fillna(0).astype(int)
    if "pc2_dominant_category" in df.columns:
        df["pc2_dominant_category"] = df["pc2_dominant_category"].fillna("none")
    return df


def main():
    t0 = time.time()
    print("Loading places...")
    places = pd.read_parquet(ROOT / "places/sgp_places_final.parquet").reset_index(drop=True)
    n = len(places)
    print(f"  {n:,} places")

    # Map raw → pc2
    places["pc2_category"] = places["primary_category"].map(map_to_pc2).fillna("unmapped")
    cat_counts = places["pc2_category"].value_counts()
    print(f"\n=== PC2 cat distribution ({len(cat_counts)} cats) ===")
    print(cat_counts.head(15))
    print(f"  unmapped: {cat_counts.get('unmapped', 0)}")

    # Re-key via hex9 universe
    h9_uni = pd.read_parquet(ROOT / "hex/hex9_universe.parquet")
    places = places.drop(columns=["hex8_id"], errors="ignore").merge(
        h9_uni[["hex9_id","parent_hex8","parent_subzone"]].rename(
            columns={"parent_hex8":"hex8_id","parent_subzone":"subzone_c_v4"}),
        on="hex9_id", how="left"
    )
    cat_cols = [f"pc2_cat_{c}_count" for c in ALL_PC2_CATS]

    # === HEX-9 ===
    print("\n--- HEX-9 ---")
    h9 = aggregate(places, "hex9_id")
    h9 = h9_uni[["hex9_id"]].merge(h9, on="hex9_id", how="left")
    h9 = fill_zeros(h9, cat_cols)
    h9.to_parquet(ROOT / "hex/hex9_place_composition_v2.parquet", index=False)
    print(f"  hex9_place_composition_v2: {h9.shape}")

    # === HEX-8 ===
    print("\n--- HEX-8 ---")
    h8 = aggregate(places, "hex8_id")
    h8_uni = pd.read_parquet(ROOT / "hex/hex8_universe.parquet")
    h8 = h8_uni[["hex8_id"]].merge(h8, on="hex8_id", how="left")
    h8 = fill_zeros(h8, cat_cols)
    h8.to_parquet(ROOT / "hex/hex8_place_composition_v2.parquet", index=False)
    print(f"  hex8_place_composition_v2: {h8.shape}")

    # === SUBZONE ===
    print("\n--- SUBZONE ---")
    sz_places = places.dropna(subset=["subzone_c_v4"])
    sz = aggregate(sz_places, "subzone_c_v4").rename(columns={"subzone_c_v4": "subzone_c"})
    sz_lu = pd.read_parquet(ROOT / "hex/subzone_land_use.parquet")[["subzone_c"]].drop_duplicates()
    sz = sz_lu.merge(sz, on="subzone_c", how="left")
    sz = fill_zeros(sz, cat_cols)
    sz.to_parquet(ROOT / "hex/subzone_place_composition_v2.parquet", index=False)
    print(f"  subzone_place_composition_v2: {sz.shape}")

    summary = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "wall_clock_s": round(time.time() - t0, 2),
        "input_places": n,
        "pc2_categories": len(ALL_PC2_CATS),
        "pc2_distribution": cat_counts.to_dict(),
        "shapes": {"hex9": list(h9.shape), "hex8": list(h8.shape), "subzone": list(sz.shape)},
    }
    with open(ROOT / "hex/place_composition_v2_report.json", "w") as f:
        json.dump(summary, f, indent=2, default=int)
    print(f"\n  total cats: {len(ALL_PC2_CATS)}")


if __name__ == "__main__":
    main()
