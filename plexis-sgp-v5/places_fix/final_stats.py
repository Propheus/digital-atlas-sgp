"""Final combined before/after stats: original places vs fully-cleaned places."""
import json
from pathlib import Path
import pandas as pd
ROOT = Path("/home/azureuser/da-sgp/v5")
b = pd.read_parquet(ROOT / "places/sgp_places_final.parquet")
a = pd.read_parquet(ROOT / "places/sgp_places_cleaned.parquet")
N = len(b)
bc = b["plexis_category"].value_counts().to_dict()
ac = a["plexis_category"].value_counts().to_dict()

print("="*60)
print(f"PLACES CORRECTION — FINAL STATS   ({N:,} places)")
print("="*60)
print(f"\nCATEGORY                  before  ->   after     (Δ)")
for c in sorted(set(bc)|set(ac), key=lambda c:-ac.get(c,0)):
    bb, aa = bc.get(c,0), ac.get(c,0)
    tag = "  <-NEW" if c in ("financial_services","automated_kiosk") else ""
    print(f"  {c:24s} {bb:>7,} -> {aa:>7,}  ({aa-bb:+,}){tag}")
print(f"\nKEY FIXES")
print(f"  convenience polluted -> clean : {bc.get('convenience',0):,} -> {ac.get('convenience',0):,}")
print(f"  financial_services (new)      : {ac.get('financial_services',0):,}  (ATM+bank+insurance+remittance)")
print(f"  automated_kiosk (new)         : {ac.get('automated_kiosk',0):,}  (vending+locker+AXS)")
print(f"  other_uncategorized           : {bc.get('other_uncategorized',0):,} -> {ac.get('other_uncategorized',0):,}  "
      f"({ac.get('other_uncategorized',0)-bc.get('other_uncategorized',0):+,})")
print(f"  is_storefront TRUE / FALSE    : {int(a['is_storefront'].sum()):,} / {int((~a['is_storefront']).sum()):,}")
print(f"  host_venue (co-located)       : {int((a['host_venue'].fillna('')!='').sum()):,}")
print(f"  duplicates flagged            : {int(a['is_duplicate'].sum()):,}  -> {N-int(a['is_duplicate'].sum()):,} canonical")
print(f"  new columns                   : is_storefront, host_venue, operator_name, parent_brand,")
print(f"                                  is_duplicate, canonical_id, zero_reviews, is_phantom_suspect")
print(f"\noutput: places/sgp_places_cleaned.parquet  ({a.shape[1]} cols)")
json.dump({"n": N, "category_before": {k:int(v) for k,v in bc.items()},
           "category_after": {k:int(v) for k,v in ac.items()},
           "n_categories": {"before": len(bc), "after": len(ac)}},
          open(ROOT/"places/places_correction_final.json","w"), indent=1)
