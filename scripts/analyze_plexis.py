import pandas as pd, numpy as np, json
from collections import Counter, defaultdict

DATA = "/home/azureuser/digital-atlas-sgp/data"
trips = pd.read_parquet(f"{DATA}/plexis/plexis_triplets.parquet")
pl = pd.read_parquet(f"{DATA}/places_consolidated/sgp_places_featured.parquet")
N = len(trips)
heads = set(trips['head']); tails = set(trips['tail']); all_nodes = heads | tails

print(f"PLEXIS: {len(all_nodes):,} nodes, {N:,} edges, {trips.relation.nunique()} relations")

# Degree
out_deg = Counter(trips['head']); in_deg = Counter(trips['tail'])
total_deg = Counter()
for n in all_nodes: total_deg[n] = out_deg.get(n,0) + in_deg.get(n,0)
degs = list(total_deg.values())
print(f"\nDegree: mean={np.mean(degs):.1f}, median={np.median(degs):.0f}, max={max(degs)}")
print(f"Isolated (deg<=1): {sum(1 for d in degs if d==1):,}")
print(f"Hubs (deg>100): {sum(1 for d in degs if d>100):,}")

# Top 10
print(f"\nTop 10 connected:")
for node, deg in total_deg.most_common(10):
    match = pl[pl['place_id']==node]
    if len(match)>0:
        r=match.iloc[0]; name=f"{r['name'][:30]} ({r['main_category']})"
    elif node.startswith('CAT_'): name=node
    elif node.startswith('STN_'): name=node
    else: name=node[:25]
    print(f"  {deg:>6,}  {name}")

# Void deck
void = trips[trips['relation']=='VOID_DECK_OF']
vc = Counter()
for _,row in void.iterrows():
    m=pl[pl['place_id']==row['head']]
    if len(m)>0: vc[m.iloc[0]['main_category']]+=1
print(f"\nVoid deck places ({len(void):,}):")
for c,n in vc.most_common(8): print(f"  {c:30s} {n:>5}")

# Undersupplied
under = trips[trips['relation']=='UNDERSUPPLIED']
uc = Counter(row['tail'] for _,row in under.iterrows())
print(f"\nUndersupplied ({len(under):,} edges):")
for c,n in uc.most_common(): print(f"  {c:30s} {n:>5} hexes")

# OD flows
od = trips[trips['relation']=='OD_FLOW']
if len(od)>0 and 'daily_trips' in od.columns:
    print(f"\nTop OD flows ({len(od):,} total):")
    for _,row in od.nlargest(5,'daily_trips').iterrows():
        h = str(row['head']).replace('STN_','')
        t = str(row['tail']).replace('STN_','')
        print(f"  {h:30s} -> {t:30s} {row.get('daily_trips',0):>6,.0f}/day")

# Exit frontage
ef = trips[trips['relation']=='EXIT_FRONTAGE']
ef_cats = Counter()
for _,row in ef.iterrows():
    m=pl[pl['place_id']==row['head']]
    if len(m)>0: ef_cats[m.iloc[0]['main_category']]+=1
print(f"\nExit frontage ({len(ef):,} places within 50m of MRT):")
for c,n in ef_cats.most_common(5): print(f"  {c:30s} {n:>5}")

# Competition by category
compete = trips[trips['relation']=='COMPETES_WITH']
cat_comp = Counter()
for _,row in compete.head(100000).iterrows():
    m=pl[pl['place_id']==row['head']]
    if len(m)>0: cat_comp[m.iloc[0]['main_category']]+=1
print(f"\nCompetition edges by category (sample):")
for c,n in cat_comp.most_common(8): print(f"  {c:30s} {n:>8,}")

# Graph vs UUKG comparison
print(f"\n{'='*50}")
print(f"PLEXIS vs UUKG (NYC)")
print(f"{'='*50}")
print(f"  {'':20s} {'UUKG':>10s} {'Plexis':>10s}")
print(f"  {'Nodes':20s} {'236,287':>10s} {len(all_nodes):>10,}")
print(f"  {'Edges':20s} {'930,240':>10s} {N:>10,}")
print(f"  {'Relations':20s} {'13':>10s} {trips.relation.nunique():>10}")
print(f"  {'Commercial edges':20s} {'0':>10s} {len(compete)+len(trips[trips.relation=='SYNERGIZES_WITH'])+len(trips[trips.relation=='SUBSTITUTES_FOR']):>10,}")
print(f"  {'Node features':20s} {'None':>10s} {'114-628d':>10s}")
