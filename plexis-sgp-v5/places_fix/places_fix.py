"""
Plexis SGP — places data correction (addresses the nous ATLAS_TEAM_FIXES P0/P1).
Non-destructive: adds columns + flags, never drops rows. Writes a cleaned parquet
and dumps before/after stats. Source fixes #1,#2,#3,#5,#6,#7,#10.

Stages:
  1  taxonomy re-map: +financial_services +automated_kiosk; route ATM/bank/vending
     out of convenience/business_office; derive is_storefront
  2  co-location: host_venue + operator from "@" names; brand = operator (not host)
  3  dedup: store-code aliases + near-duplicate grouping -> is_duplicate + canonical_id
  4  brand resolution: fill brand_norm for known chains; parent_brand for food courts
  5  reclassify other_uncategorized via name heuristics
  10 zero_reviews flag (first_seen unavailable)
"""
import json, re, time
from pathlib import Path
import numpy as np, pandas as pd

ROOT = Path("/home/azureuser/da-sgp/v5")
import sys; sys.path.insert(0, str(ROOT))
from classify_heuristics import classify_by_name
from brand_map import detect_brand_from_name, normalize_brand

t0 = time.time()
p = pd.read_parquet(ROOT / "places/sgp_places_final.parquet").copy()
N = len(p)
before_cat = p["plexis_category"].value_counts().to_dict()
before_brand = int(p["brand_norm"].notna().sum())
print(f"loaded {N:,} places", flush=True)

# ============ Stage 1 — taxonomy re-map + is_storefront ============
RECAT = {  # primary_category -> corrected plexis_category
    "ATM": "financial_services", "Bank": "financial_services",
    "Financial Services": "financial_services", "Insurance": "financial_services",
    "Money Transfer": "financial_services", "Pawnshop": "financial_services",
    "Vending Machine": "automated_kiosk", "Self-Service Kiosk": "automated_kiosk",
    "Parcel Locker": "automated_kiosk", "Lottery Retailer": "services",
}
NON_STOREFRONT = {  # unmanned machines + pure transit infra -> not a countable storefront
    "ATM", "Vending Machine", "Self-Service Kiosk", "Parcel Locker", "EV Charging",
    "Bus Stop", "Bus Station", "Bus Interchange", "MRT/LRT Station", "Train Station",
    "Taxi Stand", "Parking Lot", "Bridge", "Public Bathroom",
}
ATM_RX = re.compile(r"\batm\b|cash\s*(machine|deposit|recycler)", re.I)
VEND_RX = re.compile(r"vending|ijooz|\bmbox\b|smart\s*locker|parcel\s*locker|pop\s*station|popstation|pick\s*locker|self-?service\s*kiosk|\baxs\b|\bsam\b\s*kiosk", re.I)
FIN_RX = re.compile(r"\b(dbs|posb|ocbc|uob|maybank|hsbc|citibank|standard\s*chartered|hong\s*leong|cimb|rhb|bank\b|moneygram|western\s*union|remit|insurance|prudential|\baia\b|great\s*eastern)\b", re.I)
nm = p["name"].fillna("")

# 1a. reclassify other_uncategorized first (so RECAT/name overrides can still apply)
mask_ou = p["plexis_category"].fillna("other_uncategorized").isin(["other_uncategorized"]) | p["plexis_category"].isna()
reclassed = nm[mask_ou].apply(lambda s: classify_by_name(s))
p.loc[mask_ou, "plexis_category"] = reclassed.fillna("other_uncategorized").values
n_reclassed = int((reclassed.notna()).sum())

# 1b. primary_category re-routing (ATM/bank/vending/etc.)
for pc, newc in RECAT.items():
    p.loc[p["primary_category"] == pc, "plexis_category"] = newc

# 1c. name-based overrides for unmanned/financial (catches reclassified residue too)
p.loc[nm.str.contains(VEND_RX, na=False), "plexis_category"] = "automated_kiosk"
p.loc[nm.str.contains(ATM_RX, na=False), "plexis_category"] = "financial_services"

# 1d. is_storefront
p["is_storefront"] = (~p["primary_category"].isin(NON_STOREFRONT)
                      & ~p["plexis_category"].isin(["automated_kiosk"])
                      & ~nm.str.contains(VEND_RX, na=False)
                      & ~nm.str.contains(ATM_RX, na=False))
print(f"[1] taxonomy re-mapped · reclassified {n_reclassed:,} from other_uncategorized", flush=True)

# ============ Stage 2 — co-location host_venue + operator brand ============
has_at = nm.str.contains("@", na=False)
split = nm.where(has_at).str.split("@", n=1, expand=True)
p["operator_name"] = split[0].str.strip().fillna(p["name"])
p["host_venue"] = split[1].str.strip() if 1 in split.columns else ""
p["host_venue"] = p["host_venue"].fillna("")
# brand should follow the OPERATOR (pre-@), not the host
op_brand = p.loc[has_at, "operator_name"].apply(lambda s: (detect_brand_from_name(s) or (None,))[0])
p.loc[has_at, "brand_norm"] = op_brand.where(op_brand.notna(), p.loc[has_at, "brand_norm"])
n_host = int(has_at.sum())
print(f"[2] host_venue extracted for {n_host:,} co-located tenants", flush=True)

# ============ Stage 4 — brand resolution (fill empties from name) ============
need_brand = p["brand_norm"].isna()
filled = p.loc[need_brand, "operator_name"].apply(lambda s: (detect_brand_from_name(s) or (None,))[0])
p.loc[need_brand, "brand_norm"] = filled.values
COURTS = re.compile(r"\b(koufu|kopitiam|foodfare|food\s*junction|food\s*republic|kopi\b|food\s*court|cs\s*fresh)\b", re.I)
p["parent_brand"] = np.where(p["host_venue"].str.contains(COURTS, na=False),
                             p["host_venue"], "")
after_brand = int(p["brand_norm"].notna().sum())
print(f"[4] brand_norm {before_brand:,} -> {after_brand:,} ({100*after_brand/N:.0f}%)", flush=True)

# ============ Stage 3 — dedup (store-code aliases + near-duplicates) ============
CODE_RX = re.compile(r"\s+([A-Z]{2,5}\d{1,4}|\#?\d{2,4}[A-Z]?)$")      # "McDonald's CKN5"
PAREN_RX = re.compile(r"\s*\([^)]*\)\s*$")
def normname(s):
    s = (s or "").strip()
    s = PAREN_RX.sub("", s); s = CODE_RX.sub("", s)
    s = re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()
    return s
p["_nn"] = p["operator_name"].map(normname)
p["_key"] = (p["brand_norm"].fillna(p["_nn"]).astype(str) + "|"
             + p["latitude"].round(4).astype(str) + "|" + p["longitude"].round(4).astype(str))
p["reviews_count"] = pd.to_numeric(p["reviews_count"], errors="coerce").fillna(0)
p["is_duplicate"] = False
p["canonical_id"] = p["id"]
dup_groups = 0
for key, g in p.groupby("_key"):
    if len(g) < 2:
        continue
    canon = g["reviews_count"].idxmax()
    cid = p.at[canon, "id"]
    others = g.index.difference([canon])
    p.loc[others, "is_duplicate"] = True
    p.loc[g.index, "canonical_id"] = cid
    dup_groups += 1
n_dup = int(p["is_duplicate"].sum())
p["zero_reviews"] = p["reviews_count"] == 0
p["is_phantom_suspect"] = p["is_duplicate"] & p["zero_reviews"]
p = p.drop(columns=["_nn", "_key"])
print(f"[3] {n_dup:,} duplicates flagged across {dup_groups:,} groups · "
      f"{N-n_dup:,} canonical stores", flush=True)

# ============ write + stats ============
OUT = ROOT / "places/sgp_places_cleaned.parquet"
p.to_parquet(OUT, index=False)
after_cat = p["plexis_category"].value_counts().to_dict()

def conv_breakdown(df, label):
    c = df[df["plexis_category"] == "convenience"]
    return {"convenience_total": int(len(c)),
            "real_stores_7e_cheers": int(c["name"].str.contains(r"7-?eleven|cheers|buzz|valu\$|choices|star\s*mart|fairprice\s*xpress", case=False, na=False).sum())}

stats = {
    "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"), "n_places": N,
    "secs": round(time.time() - t0),
    "taxonomy": {"before_n_categories": len(before_cat), "after_n_categories": len(after_cat),
                 "added": ["financial_services", "automated_kiosk"]},
    "category_before": {k: int(v) for k, v in sorted(before_cat.items(), key=lambda x:-x[1])},
    "category_after": {k: int(v) for k, v in sorted(after_cat.items(), key=lambda x:-x[1])},
    "convenience_cleanup": {
        "before": int(before_cat.get("convenience", 0)),
        "after": int(after_cat.get("convenience", 0)),
        "real_store_share_after": conv_breakdown(p, "after")},
    "financial_services_created": int(after_cat.get("financial_services", 0)),
    "automated_kiosk_created": int(after_cat.get("automated_kiosk", 0)),
    "is_storefront": {"true": int(p["is_storefront"].sum()), "false": int((~p["is_storefront"]).sum())},
    "other_uncategorized": {"before": int(before_cat.get("other_uncategorized", 0)),
                            "after": int(after_cat.get("other_uncategorized", 0)),
                            "reclassified": n_reclassed},
    "host_venue_extracted": n_host,
    "brand_norm_coverage": {"before": before_brand, "after": after_brand,
                            "before_pct": round(100*before_brand/N, 1), "after_pct": round(100*after_brand/N, 1)},
    "duplicates": {"flagged": n_dup, "groups": dup_groups, "canonical_stores": N - n_dup},
    "zero_reviews": int(p["zero_reviews"].sum()),
    "new_columns": ["is_storefront", "host_venue", "operator_name", "parent_brand",
                    "is_duplicate", "canonical_id", "zero_reviews", "is_phantom_suspect"],
    "output": str(OUT),
}
json.dump(stats, open(ROOT / "places/places_fix_report.json", "w"), indent=1)

# ---- printed dump ----
print("\n================ PLACES FIX — STATS ================")
print(f"places: {N:,} · cleaned -> {OUT.name} · {stats['secs']}s")
print(f"\nCATEGORY  before -> after  (Δ)")
allcats = sorted(set(before_cat) | set(after_cat), key=lambda c: -after_cat.get(c, 0))
for c in allcats:
    b, a = before_cat.get(c, 0), after_cat.get(c, 0)
    mark = "  <- NEW" if c in ("financial_services", "automated_kiosk") else ""
    d = a - b
    print(f"  {c:24s} {b:>7,} -> {a:>7,}  ({d:+,}){mark}")
print(f"\nconvenience  {stats['convenience_cleanup']['before']:,} -> {stats['convenience_cleanup']['after']:,}  "
      f"(now ~{conv_breakdown(p,'after')['real_stores_7e_cheers']} real chain stores)")
print(f"financial_services created: {stats['financial_services_created']:,}  (ATM/bank/insurance/remittance unified)")
print(f"automated_kiosk created:    {stats['automated_kiosk_created']:,}  (vending/locker/AXS)")
print(f"is_storefront: TRUE {stats['is_storefront']['true']:,}  /  FALSE {stats['is_storefront']['false']:,}  (unmanned excluded from supply)")
print(f"other_uncategorized: {stats['other_uncategorized']['before']:,} -> {stats['other_uncategorized']['after']:,}  (reclassified {n_reclassed:,})")
print(f"host_venue extracted: {n_host:,} co-located tenants")
print(f"brand_norm coverage: {before_brand:,} ({stats['brand_norm_coverage']['before_pct']}%) -> {after_brand:,} ({stats['brand_norm_coverage']['after_pct']}%)")
print(f"duplicates flagged: {n_dup:,}  ->  {N-n_dup:,} canonical stores")
print(f"zero-review (low-signal): {stats['zero_reviews']:,}")
print(f"\nreport -> places/places_fix_report.json")
