"""
Plexis SGP v4 — Stage 1b.1 taxonomy + deterministic mapping.

24 Plexis categories mapped from 166 V1 primary_category values.
Returns None for 'Other' / 'Uncategorized' — those go to Stage 1b.2 (LLM).
"""
from __future__ import annotations
from typing import Optional

# 24-category Plexis taxonomy
TAXONOMY = [
    "cafe_coffee",           "restaurant",            "fast_food",
    "hawker",                "bakery",                "bar_nightlife",
    "convenience",           "supermarket",           "shopping_retail",
    "health_medical",        "beauty_personal",       "fitness_recreation",
    "education",             "services",              "business_office",
    "hotel_hospitality",     "entertainment_culture", "transportation",
    "government_public",     "religious_worship",     "industrial_mfg",
    "residential",           "park_open",             "other_uncategorized",
]

# V1 primary_category -> Plexis category
CATEGORY_MAP: dict[str, Optional[str]] = {
    # cafe & coffee
    "Cafe": "cafe_coffee",
    "Coffee Shop": "cafe_coffee",
    "Bubble Tea": "cafe_coffee",
    "Juice Bar": "cafe_coffee",
    "Dessert": "cafe_coffee",
    # restaurant
    "Restaurant": "restaurant",
    "Caterer": "restaurant",
    # fast food
    "Fast Food": "fast_food",
    # hawker
    "Hawker Stall": "hawker",
    "Hawker Centre": "hawker",
    "Food Court": "hawker",
    # bakery
    "Bakery": "bakery",
    # bar & nightlife
    "Bar/Pub": "bar_nightlife",
    # convenience
    "Convenience Store": "convenience",
    "General Store": "convenience",
    "Kiosk": "convenience",
    "Vending Machine": "convenience",
    "Self-Service Kiosk": "convenience",
    "Parcel Locker": "convenience",
    "ATM": "convenience",
    "Lottery Retailer": "convenience",
    # supermarket & grocery
    "Supermarket": "supermarket",
    "Market": "supermarket",
    "Specialty Food": "supermarket",
    "Health Store": "supermarket",
    # shopping & retail
    "Apparel": "shopping_retail",
    "Jewelry": "shopping_retail",
    "Electronics Store": "shopping_retail",
    "Furniture Store": "shopping_retail",
    "Hardware Store": "shopping_retail",
    "Pet Store": "shopping_retail",
    "Florist": "shopping_retail",
    "Gift Shop": "shopping_retail",
    "Toy Store": "shopping_retail",
    "Beauty Retail": "shopping_retail",
    "Cosmetics": "shopping_retail",
    "Department Store": "shopping_retail",
    "Bookstore": "shopping_retail",
    "Sports Store": "shopping_retail",
    "Stationery": "shopping_retail",
    "Discount Store": "shopping_retail",
    "Specialty Retail": "shopping_retail",
    "Bicycle Shop": "shopping_retail",
    "Car Parts": "shopping_retail",
    "Telecom Shop": "shopping_retail",
    "Optical": "shopping_retail",
    "Shopping Mall": "shopping_retail",
    "Pawnshop": "shopping_retail",
    "Photography Studio": "shopping_retail",
    # health & medical
    "Medical Clinic": "health_medical",
    "Specialist Clinic": "health_medical",
    "Hospital": "health_medical",
    "Dental Clinic": "health_medical",
    "TCM Clinic": "health_medical",
    "TCM Pharmacy": "health_medical",
    "Pharmacy": "health_medical",
    "Physiotherapy": "health_medical",
    "Polyclinic": "health_medical",
    "Aesthetic Clinic": "health_medical",
    "Aged Care": "health_medical",
    "Laboratory": "health_medical",
    "Veterinarian": "health_medical",
    # beauty & personal care
    "Beauty Salon": "beauty_personal",
    "Hair Salon": "beauty_personal",
    "Nail Salon": "beauty_personal",
    "Massage/Spa": "beauty_personal",
    "Tailor": "beauty_personal",
    # fitness & recreation
    "Gym": "fitness_recreation",
    "Sports Facility": "fitness_recreation",
    # education
    "Tuition Centre": "education",
    "Preschool": "education",
    "School": "education",
    "University": "education",
    "Polytechnic": "education",
    "Junior College": "education",
    "Music Studio": "education",
    "Art Studio": "education",
    # services
    "Service Provider": "services",
    "Consultant": "services",
    "Marketing Agency": "services",
    "Print Shop": "services",
    "Laundry": "services",
    "Event Management": "services",
    "Cleaning Service": "services",
    "Security Services": "services",
    "Law Firm": "services",
    "Accounting Firm": "services",
    "Employment Agency": "services",
    "Real Estate": "services",
    "Car Workshop": "services",
    "Plumber": "services",
    "Electrician": "services",
    "Locksmith": "services",
    "Pet Services": "services",
    "Landscape Design": "services",
    "Interior Design": "services",
    "Funeral Service": "services",
    "Car Rental": "services",
    "Car Sharing": "services",
    "Travel Agency": "services",
    "Tour Operator": "services",
    "Research": "services",
    "Money Transfer": "services",
    "Telecom": "services",
    "Parcel/Courier": "services",
    "Non-profit": "services",
    # business & office
    "Corporate Office": "business_office",
    "Coworking Space": "business_office",
    "Trading Company": "business_office",
    "Financial Services": "business_office",
    "Bank": "business_office",
    "Insurance": "business_office",
    "Media Company": "business_office",
    "Software/IT": "business_office",
    "Engineering": "business_office",
    "Industrial Supplier": "business_office",
    # hotel & hospitality
    "Hotel": "hotel_hospitality",
    # entertainment & culture
    "Tourist Attraction": "entertainment_culture",
    "Museum": "entertainment_culture",
    "Art Gallery": "entertainment_culture",
    "Cinema": "entertainment_culture",
    "Performing Arts": "entertainment_culture",
    "Cultural Centre": "entertainment_culture",
    "Event Venue": "entertainment_culture",
    # transportation
    "Bus Stop": "transportation",
    "Bus Station": "transportation",
    "Bus Interchange": "transportation",
    "MRT/LRT Station": "transportation",
    "Taxi Stand": "transportation",
    "Parking Lot": "transportation",
    "Petrol Station": "transportation",
    "EV Charging": "transportation",
    "Airport": "transportation",
    "Train Station": "transportation",
    "Airline": "transportation",
    "Transportation": "transportation",
    "Bridge": "transportation",
    "Public Bathroom": "transportation",
    # government & public
    "Government Office": "government_public",
    "Post Office": "government_public",
    "Fire Station": "government_public",
    "Police Station": "government_public",
    "Library": "government_public",
    "Embassy": "government_public",
    "Community Club": "government_public",
    # religious & worship
    "Church": "religious_worship",
    "Buddhist Temple": "religious_worship",
    "Chinese Temple": "religious_worship",
    "Hindu Temple": "religious_worship",
    "Mosque": "religious_worship",
    "Place of Worship": "religious_worship",
    "Cemetery": "religious_worship",
    # industrial & manufacturing
    "Manufacturer": "industrial_mfg",
    "Wholesale": "industrial_mfg",
    "Logistics": "industrial_mfg",
    "Construction": "industrial_mfg",
    "Car Dealer": "industrial_mfg",
    # residential
    "HDB": "residential",
    "Condominium": "residential",
    "Private Apartment": "residential",
    "Housing Estate": "residential",
    "Housing Development": "residential",
    # parks
    "Park": "park_open",
    "Playground": "park_open",
    # unresolved -> None (Stage 1b.2 LLM)
    "Other": None,
    "Uncategorized": None,
}


def classify(primary_category: Optional[str]) -> Optional[str]:
    if primary_category is None:
        return None
    return CATEGORY_MAP.get(primary_category, None)


def unmapped_report(df) -> dict:
    """Given a dataframe with primary_category, report unmapped values."""
    import pandas as pd  # noqa
    cats = df["primary_category"].fillna("<null>").value_counts()
    unmapped = {}
    for cat, c in cats.items():
        if cat in ("Other", "Uncategorized", "<null>"):
            continue
        if cat not in CATEGORY_MAP:
            unmapped[cat] = int(c)
    return unmapped


if __name__ == "__main__":
    import sys
    import pandas as pd
    df = pd.read_parquet(sys.argv[1]) if len(sys.argv) > 1 else pd.read_parquet(
        "/Users/sumanth/propheus-projs/da-sgp/digital-atlas-sgp/plexis-sgp-v4/places/sgp_places_geoattached.parquet")
    u = unmapped_report(df)
    print(f"Total categories in data: {df['primary_category'].nunique()}")
    print(f"Mapping size: {len(CATEGORY_MAP)}")
    print(f"Unmapped (excluding Other/Uncategorized): {len(u)}")
    for c, n in sorted(u.items(), key=lambda x: -x[1]):
        print(f"  {n:>7,}  {c}")
