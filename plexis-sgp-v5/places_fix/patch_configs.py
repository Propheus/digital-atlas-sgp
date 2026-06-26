import pathlib
ROOT=pathlib.Path("/home/azureuser/da-sgp/v5")
def patch(fn, old, new, label):
    p=ROOT/fn; s=p.read_text()
    assert old in s, f"NOT FOUND in {fn}: {old[:40]}"
    assert new not in s or "pharmacy_beauty" not in old, None
    s=s.replace(old,new); p.write_text(s); print(f"patched {fn}: {label}")

# 1. category_map.py — taxonomy + Pharmacy route
patch("category_map.py",
  '    "residential",           "park_open",             "other_uncategorized",\n]',
  '    "residential",           "park_open",             "other_uncategorized",\n    "pharmacy_beauty",\n]',
  "TAXONOMY += pharmacy_beauty")
patch("category_map.py", '    "Pharmacy": "health_medical",', '    "Pharmacy": "pharmacy_beauty",  # nous-consolidated: retail H&B, footfall-driven', "Pharmacy->pharmacy_beauty")

# 2. build_place_composition.py CATS
patch("build_place_composition.py",
  '    "financial_services","automated_kiosk",\n]',
  '    "financial_services","automated_kiosk","pharmacy_beauty",\n]',
  "composition CATS += pharmacy_beauty")

# 3. build_huff_capture.py CATS + LAMBDA
patch("build_huff_capture.py",
  '        "shopping_retail", "education"]',
  '        "shopping_retail", "education", "pharmacy_beauty"]',
  "huff CATS += pharmacy_beauty")
patch("build_huff_capture.py",
  '    "health_medical": 700.0, "beauty_personal": 700.0,',
  '    "health_medical": 700.0, "beauty_personal": 700.0, "pharmacy_beauty": 700.0,',
  "huff LAMBDA += pharmacy_beauty (neighborhood retail)")

# 4. build_saturation_gap.py CATEGORIES
patch("build_saturation_gap.py",
  '    "supermarket","bakery","beauty_personal","fitness_recreation","health_medical",\n]',
  '    "supermarket","bakery","beauty_personal","fitness_recreation","health_medical",\n    "pharmacy_beauty",\n]',
  "saturation CATEGORIES += pharmacy_beauty")
print("ALL CONFIGS PATCHED")
