"""
Plexis SGP v4 — Stage 1c brand taxonomy + name-pattern detection.

Canonical brand table + regex patterns to fill brand from name when the
scrape's `brand` field is empty.
"""
from __future__ import annotations
import re
from typing import Optional

# Brand normalization map: variant -> canonical form
BRAND_ALIASES = {
    "bread talk": "BreadTalk", "breadtalk": "BreadTalk",
    "seven eleven": "7-Eleven", "7 eleven": "7-Eleven", "7eleven": "7-Eleven",
    "mcd": "McDonald's", "mcdonalds": "McDonald's", "mcdonald": "McDonald's",
    "li-ho": "LiHO", "liho": "LiHO", "li ho": "LiHO",
    "old chang kee": "Old Chang Kee",
    "kopitiam": "Kopitiam",
    "fair price": "NTUC FairPrice", "fairprice": "NTUC FairPrice",
    "ntuc fairprice": "NTUC FairPrice",
    "cold storage": "Cold Storage",
    "sheng siong": "Sheng Siong",
    "don don donki": "Don Don Donki", "donki": "Don Don Donki",
    "popeyes": "Popeyes",
}

# Name patterns for chain detection (regex applied to name after lowercase)
BRAND_PATTERNS: list[tuple[str, re.Pattern, str]] = [
    ("Kopitiam", re.compile(r"\bkopitiam\b", re.I), "hawker"),
    ("Koufu", re.compile(r"\bkoufu\b", re.I), "hawker"),
    ("Foodfare", re.compile(r"\bfoodfare\b", re.I), "hawker"),
    ("NTUC FairPrice", re.compile(r"fair\s*price|ntuc\s*fairprice", re.I), "supermarket"),
    ("Cold Storage", re.compile(r"cold\s+storage", re.I), "supermarket"),
    ("Giant", re.compile(r"\bgiant\b.{0,20}(super|hyp|express)", re.I), "supermarket"),
    ("Sheng Siong", re.compile(r"sheng\s*siong", re.I), "supermarket"),
    ("Prime Supermarket", re.compile(r"prime\s+supermarket", re.I), "supermarket"),
    ("Jason's", re.compile(r"\bjason'?s\b.{0,10}(deli|market)", re.I), "supermarket"),
    ("Don Don Donki", re.compile(r"don\s*don\s*donki|\bdonki\b", re.I), "supermarket"),
    ("7-Eleven", re.compile(r"7-?\s*eleven", re.I), "convenience"),
    ("Cheers", re.compile(r"\bcheers\b(?!.*pub)", re.I), "convenience"),
    ("iJooz", re.compile(r"\bijooz\b", re.I), "convenience"),
    ("Starbucks", re.compile(r"starbucks", re.I), "cafe_coffee"),
    ("Ya Kun Kaya Toast", re.compile(r"ya\s*kun", re.I), "cafe_coffee"),
    ("Toast Box", re.compile(r"toast\s*box", re.I), "cafe_coffee"),
    ("Killiney Kopitiam", re.compile(r"killiney", re.I), "cafe_coffee"),
    ("Wang Cafe", re.compile(r"wang\s+cafe", re.I), "cafe_coffee"),
    ("LiHO", re.compile(r"\bli\s*-?\s*ho\b", re.I), "cafe_coffee"),
    ("Mr Bean", re.compile(r"mr\.?\s*bean", re.I), "cafe_coffee"),
    ("Gong Cha", re.compile(r"gong\s*cha", re.I), "cafe_coffee"),
    ("Koi Thé", re.compile(r"\bkoi\b\s*(th[ée])?", re.I), "cafe_coffee"),
    ("The Coffee Bean", re.compile(r"coffee\s+bean", re.I), "cafe_coffee"),
    ("McDonald's", re.compile(r"mcdonald'?s?|\bmcd\b", re.I), "fast_food"),
    ("KFC", re.compile(r"\bkfc\b", re.I), "fast_food"),
    ("Burger King", re.compile(r"burger\s*king", re.I), "fast_food"),
    ("Subway", re.compile(r"\bsubway\b", re.I), "fast_food"),
    ("Pizza Hut", re.compile(r"pizza\s*hut", re.I), "fast_food"),
    ("Domino's", re.compile(r"domino'?s", re.I), "fast_food"),
    ("Popeyes", re.compile(r"popeyes?", re.I), "fast_food"),
    ("Texas Chicken", re.compile(r"texas\s*chicken", re.I), "fast_food"),
    ("Long John Silver's", re.compile(r"long\s*john\s*silver", re.I), "fast_food"),
    ("Mos Burger", re.compile(r"mos\s*burger", re.I), "fast_food"),
    ("Crystal Jade", re.compile(r"crystal\s*jade", re.I), "restaurant"),
    ("Din Tai Fung", re.compile(r"din\s*tai\s*fung", re.I), "restaurant"),
    ("Swensen's", re.compile(r"swensen'?s", re.I), "restaurant"),
    ("Hai Di Lao", re.compile(r"hai\s*di\s*lao", re.I), "restaurant"),
    ("Tim Ho Wan", re.compile(r"tim\s*ho\s*wan", re.I), "restaurant"),
    ("Pastamania", re.compile(r"pastamania", re.I), "restaurant"),
    ("Old Chang Kee", re.compile(r"old\s*chang\s*kee", re.I), "bakery"),
    ("BreadTalk", re.compile(r"breadtalk|bread\s+talk", re.I), "bakery"),
    ("Paris Baguette", re.compile(r"paris\s*baguette", re.I), "bakery"),
    ("Four Leaves", re.compile(r"four\s*leaves", re.I), "bakery"),
    ("Polar Puffs & Cakes", re.compile(r"polar\s*(puff|cake)", re.I), "bakery"),
    ("Bengawan Solo", re.compile(r"bengawan\s*solo", re.I), "bakery"),
    ("Pezzo", re.compile(r"\bpezzo\b", re.I), "bakery"),
    ("Watson's", re.compile(r"watsons?(?:\s*personal)?", re.I), "health_medical"),
    ("Guardian", re.compile(r"guardian\s*(health|pharmac|personal)", re.I), "health_medical"),
    ("Unity", re.compile(r"\bunity\b\s*pharmac", re.I), "health_medical"),
    ("Anytime Fitness", re.compile(r"anytime\s*fitness", re.I), "fitness_recreation"),
    ("ActiveSG", re.compile(r"activesg", re.I), "fitness_recreation"),
    ("True Fitness", re.compile(r"true\s*fitness", re.I), "fitness_recreation"),
    ("Yoga Movement", re.compile(r"yoga\s*movement", re.I), "fitness_recreation"),
    ("Pure Yoga", re.compile(r"pure\s*yoga", re.I), "fitness_recreation"),
    ("DBS", re.compile(r"\bdbs\b", re.I), "business_office"),
    ("POSB", re.compile(r"\bposb\b", re.I), "business_office"),
    ("UOB", re.compile(r"\buob\b", re.I), "business_office"),
    ("OCBC", re.compile(r"\bocbc\b", re.I), "business_office"),
    ("Maybank", re.compile(r"maybank", re.I), "business_office"),
    ("HSBC", re.compile(r"\bhsbc\b", re.I), "business_office"),
    ("Standard Chartered", re.compile(r"standard\s*chartered", re.I), "business_office"),
    ("Citibank", re.compile(r"citibank", re.I), "business_office"),
    ("NTUC Income", re.compile(r"ntuc\s*income", re.I), "business_office"),
    ("Prudential", re.compile(r"prudential", re.I), "business_office"),
    ("Great Eastern", re.compile(r"great\s*eastern", re.I), "business_office"),
    ("AXS", re.compile(r"\baxs\b", re.I), "convenience"),
    ("SingPost", re.compile(r"singpost|sam\s+kiosk", re.I), "government_public"),
    ("Singapore Pools", re.compile(r"singapore\s+pools", re.I), "services"),
    ("Shell", re.compile(r"\bshell\b\s*(petrol|station|recharge|service)", re.I), "transportation"),
    ("Esso", re.compile(r"\besso\b", re.I), "transportation"),
    ("Caltex", re.compile(r"\bcaltex\b", re.I), "transportation"),
    ("SPC", re.compile(r"\bspc\b\s*(petrol|station|pte)", re.I), "transportation"),
    ("BlueSG", re.compile(r"\bbluesg\b", re.I), "transportation"),
    ("SP Mobility", re.compile(r"sp\s*mobility|sp\s*charging", re.I), "transportation"),
    ("Charge+", re.compile(r"\bcharge\+|charge\s*plus", re.I), "transportation"),
    ("Shell Recharge", re.compile(r"shell\s*recharge", re.I), "transportation"),
    ("TotalEnergies Charging", re.compile(r"total\s*energies\s*charging|totalenergies", re.I), "transportation"),
    ("PCF Sparkletots", re.compile(r"pcf\s*sparkletots|sparkletots", re.I), "education"),
    ("My First Skool", re.compile(r"my\s*first\s*skool", re.I), "education"),
    ("Star Tots", re.compile(r"star\s*tots", re.I), "education"),
    ("The Little Gym", re.compile(r"little\s*gym", re.I), "fitness_recreation"),
]


def normalize_brand(b: Optional[str]) -> Optional[str]:
    if not b:
        return None
    b_clean = str(b).strip()
    if not b_clean:
        return None
    return BRAND_ALIASES.get(b_clean.lower(), b_clean)


def detect_brand_from_name(name: Optional[str]) -> Optional[tuple[str, str]]:
    """Return (brand, expected_plexis_category) if name matches a pattern; else None."""
    if not name:
        return None
    for brand, rx, cat in BRAND_PATTERNS:
        if rx.search(name):
            return (brand, cat)
    return None
