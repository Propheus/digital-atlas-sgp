"""
Plexis SGP v4 — Stage 1a summary: what did we just enrich?
"""
import json
from pathlib import Path
from collections import Counter

import pandas as pd

ROOT = Path(__file__).parent
df = pd.read_parquet(ROOT / "places/sgp_places_geoattached.parquet")

print(f"=== Places enriched ===")
print(f"Total rows: {len(df):,}")
print(f"Has hex9: {df['hex9_id'].notna().sum():,}")
print(f"Has hex8: {df['hex8_id'].notna().sum():,}")
print(f"Has subzone: {df['parent_subzone_c'].notna().sum():,}")
print(f"Offshore marine (orphan subzone): {df['parent_subzone_c'].isna().sum():,}")
print(f"Inside HDB town: {df['hdb_town'].notna().sum():,}  ({100*df['hdb_town'].notna().mean():.1f}%)")

print(f"\n=== Distribution by Region ===")
for rg, c in df['parent_region'].value_counts().items():
    print(f"  {str(rg):20s}  {c:>7,}  ({100*c/len(df):.1f}%)")

print(f"\n=== Top 15 Planning Areas ===")
for pa, c in df['parent_pa'].value_counts().head(15).items():
    print(f"  {str(pa):22s}  {c:>7,}")

print(f"\n=== HDB town presence (places inside HDB town polygon) ===")
hdb_counts = df[df['hdb_town'].notna()]['hdb_town'].value_counts()
print(f"  {len(hdb_counts)} towns have places")
for town, c in hdb_counts.head(15).items():
    print(f"  {town:22s}  {c:>7,}")

print(f"\n=== Top 10 dense hex-9 cells ===")
hex9_counts = df.groupby('hex9_id').agg(n=('id', 'count'), pa=('parent_pa', 'first'), subzone=('parent_subzone_name', 'first')).sort_values('n', ascending=False).head(10)
for hid, row in hex9_counts.iterrows():
    print(f"  {hid}  {row['n']:>4}  {str(row['subzone']):25s}  ({row['pa']})")

print(f"\n=== Top 10 dense hex-8 cells ===")
hex8_counts = df.groupby('hex8_id').agg(n=('id', 'count'), pa=('parent_pa', 'first'), subzone=('parent_subzone_name', 'first')).sort_values('n', ascending=False).head(10)
for hid, row in hex8_counts.iterrows():
    print(f"  {hid}  {row['n']:>5}  {str(row['subzone']):25s}  ({row['pa']})")

print(f"\n=== Category mix (top 20) ===")
cat_counts = df['primary_category'].value_counts().head(20)
for cat, c in cat_counts.items():
    print(f"  {c:>7,}  {cat}")

# Save rollups
ROOT_OUT = ROOT / "places"
df.groupby('hex9_id').size().reset_index(name='n_places').to_parquet(ROOT_OUT / "hex9_place_counts.parquet", index=False)
df.groupby('hex8_id').size().reset_index(name='n_places').to_parquet(ROOT_OUT / "hex8_place_counts.parquet", index=False)
df.groupby('parent_subzone_c').size().reset_index(name='n_places').to_parquet(ROOT_OUT / "subzone_place_counts.parquet", index=False)
df.groupby('parent_pa').size().reset_index(name='n_places').to_parquet(ROOT_OUT / "pa_place_counts.parquet", index=False)
df.groupby('hdb_town').size().reset_index(name='n_places').to_parquet(ROOT_OUT / "hdb_town_place_counts.parquet", index=False)
print(f"\nRollups saved to {ROOT_OUT}/")
