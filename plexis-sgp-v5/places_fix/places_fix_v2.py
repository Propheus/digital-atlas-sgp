"""
Plexis SGP — places fixes V2 (nous ATLAS_TEAM_FIXES_V2). Operates on the current
cleaned canonical places. Non-destructive (backup taken). Writes sgp_places_v2.parquet.
  #1  robust dedup — store-code aliases + pin-duplicates within ~60m (spatial merge)
  #3  operator / parent_brand for food-court & coffeeshop stalls
  #2a deterministic big SG-chain dictionary -> brand_norm (LLM residue runs after)
"""
import re, time, json, shutil
from pathlib import Path
import numpy as np, pandas as pd

ROOT = Path("/home/azureuser/da-sgp/v5")
BK = ROOT / "backups" / f"places_v2_{time.strftime('%Y%m%d_%H%M%S')}"; BK.mkdir(parents=True, exist_ok=True)
shutil.copy2(ROOT/"places/sgp_places_final.parquet", BK/"sgp_places_final.parquet")
p = pd.read_parquet(ROOT/"places/sgp_places_final.parquet").reset_index(drop=True)
N = len(p)
p["reviews_count"] = pd.to_numeric(p["reviews_count"], errors="coerce").fillna(0)
before_brand = int(p["brand_norm"].notna().sum())
before_dup = int(p.get("is_duplicate", pd.Series(False, index=p.index)).sum())
t0 = time.time()

# ===== #3 operator / parent_brand (food courts & coffeeshops) =====
COURT = {
    "Koufu": r"\bkoufu\b", "Kopitiam": r"\bkopitiam\b", "NTUC Foodfare": r"\bfoodfare\b",
    "Food Republic": r"food\s*republic", "Food Junction": r"food\s*junction",
    "Food Court": r"\bfood\s*court\b", "Kopibrew": r"kopibrew", "Broadway": r"broadway\s*food",
    "S-11": r"\bs-?11\b", "Cantine": r"\bcantine\b", "Megabites": r"megabites",
    "Food Folks": r"food\s*folks", "Rasapura": r"rasapura", "Picnic": r"\bpicnic\b\s*food",
}
nm = p["name"].fillna(""); host = p.get("host_venue", pd.Series("", index=p.index)).fillna("")
p["operator"] = ""
for brand, rx in COURT.items():
    hit = nm.str.contains(rx, case=False, regex=True, na=False) | host.str.contains(rx, case=False, regex=True, na=False)
    p.loc[hit & (p["operator"] == ""), "operator"] = brand
n_operator = int((p["operator"] != "").sum())

# ===== #2a deterministic SG-chain dictionary =====
CHAINS = {
 # F&B chains
 "Ya Kun Kaya Toast":r"ya\s*kun","Toast Box":r"toast\s*box","Killiney Kopitiam":r"killiney",
 "Heavenly Wang":r"heavenly\s*wang|wang\s*cafe","Fun Toast":r"fun\s*toast","Each A Cup":r"each\s*a\s*cup",
 "Starbucks":r"starbucks","The Coffee Bean & Tea Leaf":r"coffee\s*bean","Costa Coffee":r"costa\s*coffee",
 "Tim Hortons":r"tim\s*hortons","%Arabica":r"%?\s*arabica","Luckin Coffee":r"luckin",
 "LiHO":r"\bli\s*-?\s*ho\b","Gong Cha":r"gong\s*cha","KOI Thé":r"\bkoi\b\s*th|koi\s*the","Playmade":r"playmade",
 "Tiger Sugar":r"tiger\s*sugar","HEYTEA":r"hey\s*tea|heytea","CHICHA San Chen":r"chicha","R&B Tea":r"r&b\s*tea",
 "Mr Bean":r"mr\.?\s*bean","Jollibean":r"jollibean","Each-a-Cup":r"each.a.cup",
 "McDonald's":r"mcdonald|\bmcd\b","KFC":r"\bkfc\b","Burger King":r"burger\s*king","Subway":r"\bsubway\b",
 "MOS Burger":r"mos\s*burger","Long John Silver's":r"long\s*john","Popeyes":r"popeyes?","Texas Chicken":r"texas\s*chicken",
 "A&W":r"\ba\s*&\s*w\b","Wendy's":r"wendy","Jollibee":r"jollibee","Shake Shack":r"shake\s*shack","Five Guys":r"five\s*guys",
 "Din Tai Fung":r"din\s*tai\s*fung","Crystal Jade":r"crystal\s*jade","Paradise":r"paradise\s*(group|dynasty|inn|teochew)",
 "Putien":r"putien","Imperial Treasure":r"imperial\s*treasure","Sushi Tei":r"sushi\s*tei","Genki Sushi":r"genki\s*sushi",
 "Sakae Sushi":r"sakae","Sushiro":r"sushiro","Ramen Keisuke":r"keisuke","Ichiban Boshi":r"ichiban\s*boshi",
 "Saizeriya":r"saizeriya","PastaMania":r"pastamania","Swensen's":r"swensen","Astons":r"\bastons?\b",
 "Collin's":r"collin'?s","Nando's":r"nando","Pizza Hut":r"pizza\s*hut","Domino's":r"domino","Pezzo":r"\bpezzo\b",
 "Old Chang Kee":r"old\s*chang\s*kee","Hai Di Lao":r"hai\s*di\s*lao","Tim Ho Wan":r"tim\s*ho\s*wan",
 "Beauty in the Pot":r"beauty\s*in\s*the\s*pot","Tonkotsu Kazan":r"kazan","4Fingers":r"4\s*fingers",
 # bakery
 "BreadTalk":r"bread\s*talk","Four Leaves":r"four\s*leaves","PrimaDeli":r"prima\s*deli","Bengawan Solo":r"bengawan",
 "Polar Puffs & Cakes":r"polar\s*(puff|cake)","Swee Heng":r"swee\s*heng","Paris Baguette":r"paris\s*baguette",
 "Tous Les Jours":r"tous\s*les\s*jours","Gontran Cherrier":r"gontran","Bread Garden":r"bread\s*garden",
 # supermarket / grocery / convenience
 "NTUC FairPrice":r"fair\s*price|ntuc","Cold Storage":r"cold\s*storage","Giant":r"\bgiant\b",
 "Sheng Siong":r"sheng\s*siong","Prime Supermarket":r"prime\s*super","Don Don Donki":r"don\s*don|donki",
 "U Stars":r"u\s*stars","Mustafa":r"mustafa","7-Eleven":r"7-?\s*eleven","Cheers":r"\bcheers\b(?!.*pub)",
 "Buzz":r"\bbuzz\b\s*(pod|conv)","iJOOZ":r"ijooz",
 # health / pharmacy / dental
 "Guardian":r"\bguardian\b","Watsons":r"watsons?","Unity":r"\bunity\b\s*pharm","Healthway":r"healthway",
 "Raffles Medical":r"raffles\s*medical","Parkway":r"parkway\s*(shenton|east|health)","Q & M Dental":r"q\s*&?\s*m\b",
 "NHG Polyclinic":r"\bnhg\b","Banyan Clinic":r"banyan","My Family Clinic":r"my\s*family\s*clinic",
 # retail
 "Uniqlo":r"uniqlo","Cotton On":r"cotton\s*on","H&M":r"\bh\s*&\s*m\b","ZARA":r"\bzara\b","MUJI":r"\bmuji\b",
 "Challenger":r"challenger","Courts":r"\bcourts\b","Harvey Norman":r"harvey\s*norman","Best Denki":r"best\s*denki",
 "Gain City":r"gain\s*city","Popular":r"\bpopular\b\s*book","Times Bookstore":r"times\s*(bookstore|book)",
 "Kinokuniya":r"kinokuniya","Daiso":r"\bdaiso\b","MINISO":r"\bminiso\b","IKEA":r"\bikea\b","Decathlon":r"decathlon",
 "Sephora":r"sephora","SaSa":r"\bsa\s*sa\b","Pet Lovers Centre":r"pet\s*lovers","Valu\$":r"valu\$|valu\s*dollar",
 "Sports Direct":r"sports\s*direct","World of Sports":r"world\s*of\s*sports","Royal Sporting House":r"royal\s*sporting",
 # fitness / beauty
 "Anytime Fitness":r"anytime\s*fitness","Fitness First":r"fitness\s*first","ActiveSG":r"activesg",
 "Gold's Gym":r"gold'?s\s*gym","True Fitness":r"true\s*fitness","Virgin Active":r"virgin\s*active","GymmBoxx":r"gymmboxx",
 "Jean Yip":r"jean\s*yip","Kimage":r"kimage","EC House":r"\bec\s*house\b",
 # banks / telco
 "DBS":r"\bdbs\b","POSB":r"\bposb\b","OCBC":r"\bocbc\b","UOB":r"\buob\b","Maybank":r"maybank","HSBC":r"\bhsbc\b",
 "Standard Chartered":r"standard\s*chartered","Citibank":r"citibank","CIMB":r"\bcimb\b","Singtel":r"singtel",
 "StarHub":r"starhub","M1":r"\bm1\b\s*(shop|store)",
 # education
 "MindChamps":r"mindchamps","Kumon":r"\bkumon\b","EtonHouse":r"eton\s*house","MapleBear":r"maple\s*bear",
 "The Learning Lab":r"learning\s*lab","Berries":r"\bberries\b","I Can Read":r"i\s*can\s*read","PCF Sparkletots":r"sparkletots",
}
CHAIN_RX = [(b, re.compile(rx, re.I)) for b, rx in CHAINS.items()]
def detect_chain(name):
    if not name: return None
    for b, rx in CHAIN_RX:
        if rx.search(name): return b
    return None

need = p["brand_norm"].isna()
det = p.loc[need, "name"].fillna("").map(detect_chain)
p.loc[need, "brand_norm"] = det.values
after_dict_brand = int(p["brand_norm"].notna().sum())
print(f"[#2a dict] brand_norm {before_brand:,} -> {after_dict_brand:,} (+{after_dict_brand-before_brand:,})", flush=True)

# ===== #1 robust dedup — store-code aliases + pin-duplicates within ~60m =====
CODE = re.compile(r"\s+([A-Z]{2,6}\d{1,4}|#\d{2,4}[a-z]?|\d{3,4}[a-z]?)$")
DROP = re.compile(r"\s*[-(]?\s*(car\s*park|carpark|drop[-\s]?off|pick[-\s]?up|pickup|entrance|exit|"
                  r"basement|level\s*\d|b\d|#\d+|kiosk|counter|atm|takeaway|take\s*away)\b.*$", re.I)
PAREN = re.compile(r"\s*\([^)]*\)\s*$")
def norm(s):
    s = (s or "")
    s = PAREN.sub("", s); s = DROP.sub("", s); s = CODE.sub("", s)
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()
p["_nn"] = p["operator"].where(p["operator"] != "", p["name"].fillna("")).map(norm)
p["_grp"] = p["brand_norm"].fillna("").where(p["brand_norm"].notna(), p["_nn"])
lat = p["latitude"].to_numpy(); lon = p["longitude"].to_numpy()
p["is_duplicate"] = False
p["canonical_id"] = p["id"].values
dgroups = 0
RAD_M = 60.0
for key, g in p.groupby("_grp"):
    if key == "" or len(g) < 2: continue
    idxs = g.sort_values("reviews_count", ascending=False).index.to_list()
    used = set()
    for i in idxs:
        if i in used: continue
        la, lo = lat[i], lon[i]
        # equirectangular metres
        for j in idxs:
            if j == i or j in used: continue
            dx = (lon[j]-lo)*111320*np.cos(np.radians(la)); dy = (lat[j]-la)*110540
            if dx*dx+dy*dy <= RAD_M*RAD_M:
                p.at[j, "is_duplicate"] = True; p.at[j, "canonical_id"] = p.at[i, "id"]; used.add(j)
        used.add(i)
        if len(used) > 1: dgroups += 1
n_dup = int(p["is_duplicate"].sum())
p = p.drop(columns=["_nn", "_grp"])
print(f"[#1 dedup] {before_dup:,} -> {n_dup:,} duplicates ({dgroups:,} merge-groups, ~{RAD_M:.0f}m)", flush=True)

p.to_parquet(ROOT/"places/sgp_places_v2.parquet", index=False)
json.dump({"n":N,"brand_before":before_brand,"brand_after_dict":after_dict_brand,
           "operator":n_operator,"dup_before":before_dup,"dup_after":n_dup,
           "backup":str(BK),"secs":round(time.time()-t0)},
          open(ROOT/"places/places_v2_report.json","w"), indent=1)
print(f"\n[V2 deterministic] {round(time.time()-t0)}s -> places/sgp_places_v2.parquet")
print(f"  operator/parent_brand: {n_operator:,}")
print(f"  brand_norm (dict): {before_brand:,} -> {after_dict_brand:,} ({100*after_dict_brand/N:.1f}%)")
print(f"  duplicates: {before_dup:,} -> {n_dup:,} -> {N-n_dup:,} canonical")
print(f"  still unbranded (for LLM): {N-after_dict_brand:,}")
