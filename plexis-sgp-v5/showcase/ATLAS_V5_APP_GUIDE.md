<div class="cards">
<div class="card"><div class="cv">1,191</div><div class="cl">hex8 cells</div></div>
<div class="card"><div class="cv">840</div><div class="cl">cols / hex (801 + packs)</div></div>
<div class="card"><div class="cv">190,591</div><div class="cl">places</div></div>
<div class="card"><div class="cv">256-d</div><div class="cl">hex embed e1</div></div>
<div class="card"><div class="cv">64-d</div><div class="cl">place embed p1</div></div>
<div class="card"><div class="cv">5 · 39</div><div class="cl">domain packs</div></div>
</div>

# Digital Atlas Singapore V5 — App Builder's Guide

*Everything you need to build on Plexis SGP v5.4.0: where the data lives, how to
load it, the keys that join it, the two embeddings, the five domain packs, and
eight copy-paste recipes. Review-free, exam-gated.*

---

## 0. TL;DR — zero to a twin query in 10 lines

```python
import pandas as pd, numpy as np
V5 = "/home/azureuser/da-sgp/v5"      # azold (authoritative); or local "plexis-sgp-v5/"

e1 = pd.read_parquet(f"{V5}/hex/hex8_embedding_plexis_e1_256d.parquet").set_index("hex8_id")
E  = e1[[f"e{i}" for i in range(256)]].values
ids = e1.index.to_numpy()
En = E / (np.linalg.norm(E, axis=1, keepdims=True) + 1e-9)

def hex_twins(hid, k=8):                       # nearest neighbours in fingerprint space
    v = En[list(ids).index(hid)]
    cos = En @ v
    return ids[np.argsort(-cos)[1:k+1]].tolist()

# "find the 8 hexes that behave most like this one" — no labels, no reviews
print(hex_twins(ids[0]))
```

That's the whole idea: **distance in the embedding = functional similarity.**
Everything below is variations on this.

---

## 1. What you're building on

| Scale | Key column | Count | Master file |
|---|---|---|---|
| **hex8** (product scale, ~0.74 km²) | `hex8_id` (H3 res-8) | 1,191 | `hex/hex8_all_features.parquet` |
| hex9 (fine, ~0.10 km² — *not used in products*) | `hex9_id` | 7,318 | `hex/hex9_all_features.parquet` |
| **subzone** (URA MP2019) | `subzone_c` (e.g. `AMSZ01`) | 326 (270 populated) | `hex/subzone_all_features.parquet` |
| **place** (venue) | `id` (12-char) | 190,591 | `places/sgp_places_final.parquet` |

Admin hierarchy on every hex/place: `parent_subzone` → `parent_pa` (planning
area) → `parent_region` (5 regions). Non-residential land carries
`zone_type_broad` (residential / commercial / industrial / nature / airport /
islands / future) — **always filter these out before scoring "adequacy"**, or an
airport will look like a clinic desert.

> **Build at hex8.** It's the scale every embedding, pack and app uses. hex9
> exists but is intentionally not wired into any product.

---

## 2. Where everything lives — file inventory

All paths under `azold-test-server:/home/azureuser/da-sgp/v5/` (authoritative) =
local `plexis-sgp-v5/`. Parquets are LFS-tracked in
`github.com/Propheus/digital-atlas-sgp`.

| File | Rows × cols | Key | Size | What |
|---|---|---|---|---|
| `hex/hex8_all_features.parquet` | 1,191 × **840** | `hex8_id` | 2.7 MB | **the master** — 801 base features **+ 39 pack scores folded in (v5.5.0)** |
| `hex/hex8_embedding_plexis_e1_256d.parquet` | 1,191 × 257 | `hex8_id` | 1.7 MB | hex fingerprints `e0…e255` |
| `places/sgp_places_final.parquet` | 190,591 × 27 | `id` | 12 MB | every venue + admin + brand |
| `places/sgp_places_micrograph.parquet` | 190,591 × 20 | `id` | — | per-venue local context `pmg_*` |
| `places/place_embedding_plexis_p1_64d.parquet` | 190,591 × 65 | `id` | 72 MB | place fingerprints `d0…d63` |
| `hex/subzone_all_features.parquet` | 326 × **428** | `subzone_c` | — | subzone rollup + 39 pack scores folded in |
| `hex/hex8_retail_pack.parquet` | 1,191 × 12 | `hex8_id` | 28 KB | retail hero scores |
| `hex/hex8_realestate_pack.parquet` | 1,191 × 12 | `hex8_id` | — | real-estate hero scores |
| `hex/hex8_utilities_pack.parquet` | 1,191 × 13 | `hex8_id` | — | utilities hero scores |
| `hex/hex8_transport_pack.parquet` | 1,191 × 13 | `hex8_id` | — | transport hero scores |
| `hex/hex8_insurance_pack.parquet` | 1,191 × 14 | `hex8_id` | — | insurance/risk hero scores |
| `hex/hex8_mobility_pack.parquet` | 1,191 × 99 | `hex8_id` | — | travel-times `time_to_*_min` + access |
| `hex/hex8_context_pack.parquet` | 1,191 × 17 | `hex8_id` | — | polyclinic/wet-market/carpark/coworking/condo counts |
| `hex/subzone_{pack}_pack.parquet` ×5 | 270 × … | `subzone_c` | — | pop-weighted pack rollups |
| `catalog/feature_catalog.json` | 2,735 entries | — | — | **data dictionary** (desc, units, range) |
| `catalog/atlas_manifest.json` | — | — | — | scales, keys, shapes, version |
| `catalog/pack_{pack}_catalog.json` ×5 | — | — | — | pack columns + use-cases + honest limits |

---

## 3. Loading & joining — the one pattern you'll reuse

Everything joins on its key. Load the master, left-join whatever you need:

```python
hex8 = pd.read_parquet(f"{V5}/hex/hex8_all_features.parquet")   # 840 cols — INCLUDES all 39 pack scores
e1   = pd.read_parquet(f"{V5}/hex/hex8_embedding_plexis_e1_256d.parquet")
df   = hex8.merge(e1, on="hex8_id", how="left")                 # add e0..e255 (the only join you need)

# hex8["retail_whitespace_score"], hex8["re_feasibility_score"], hex8["insurance_risk_score"] … already here
# ⚠ don't re-merge the hex8_<pack>_pack files onto the master — you'd get _x/_y duplicate columns

places = pd.read_parquet(f"{V5}/places/sgp_places_final.parquet")
p1     = pd.read_parquet(f"{V5}/places/place_embedding_plexis_p1_64d.parquet")
pl = places.merge(p1, on="id", how="left")                      # venues + d0..d63
```

**As of v5.5.0 the 39 pack scores are folded into the master** (801 → 840) — read
them as ordinary columns, no join needed. The standalone pack parquets + subzone
rollups are retained (for the per-pack catalogs and the 270-subzone rollup), but
for hex8 you don't need them.

Map coordinates: hex8 has `lat`,`lng` (centroid); places have
`latitude`,`longitude`. For hex polygons use H3:
`h3.cell_to_boundary(hex8_id)`.

---

## 4. The 801 hex features — five views

Features group into five "views". You rarely touch all 801; these are the
columns you'll actually use. Full dictionary: `catalog/feature_catalog.json` (or
the **Hex Feature Catalog** report).

- **WHO** — `pop_resident`, `pop_total_all`, `pop_0_14 / pop_15_64 / pop_65plus`,
  `pop_hdb`, `pop_dorm`, `dt_pop` (daytime), `nvp_*` (persona age/occupation/
  industry mix).
- **WHERE** — `lu_*_pct` (22 URA land-use fractions), `bldg_*` (count, height,
  GFA, high-rise), `road_density…`, `road_intersection_density_per_km2`,
  `dist_*_m` (distances).
- **WHAT** — `pc_total` (place count), `pc_cat_<cat>` (24 category counts),
  `is_magnet` density, `hawker_centre_count`, amenity counts, `mg_*` micrograph
  context.
- **FLOW** — `mrt_station_count`, `dist_mrt_m`, `transit_score`,
  `iso_walk10_*` (10-min walk reach), `iso_transit15_*` (15-min transit reach),
  `od_*` (origin-destination throughput), `walkability_score`, `min15_score`.
- **ECON** — `nl_2024` (night-lights), `rent_resi_psf_med`, `hdb_resale_*`,
  `biz_*` (ACRA formation/churn), `cap_<cat>` (Huff demand), `gap_<cat>`
  (whitespace), composites (`livability`, `vibrancy`, `adq_*`).

### The category system

24 `plexis_category` values drive the place counts and demand columns:

```
business_office services other_uncategorized industrial_mfg residential
shopping_retail transportation education restaurant beauty_personal
health_medical cafe_coffee hawker convenience park_open fitness_recreation
supermarket bakery entertainment_culture government_public religious_worship
hotel_hospitality bar_nightlife fast_food
```

Three families are keyed by category suffix:
- **`pc_cat_<cat>`** — count of that category in the hex (all 24).
- **`cap_<cat>`** — Huff capturable demand, review-free, outlet-equivalents
  (13: cafe_coffee, restaurant, fast_food, hawker, supermarket, convenience,
  health_medical, education, beauty_personal, fitness_recreation, shopping_retail
  + `cap_total`, `cap_best_category`).
- **`gap_<cat>`** — demand-vs-supply whitespace (9: bakery, beauty_personal,
  cafe_coffee, fast_food, fitness_recreation, hawker, health_medical, restaurant,
  supermarket). **Caveat:** `gap_*` reads ~0.84 island-wide (low variance) — for
  real whitespace use `iso_walk10_unserved_pop_<cat>` **+** `cap_<cat>` as an
  *additive* blend, never a product.

---

## 5. The two embeddings — your similarity engine

| | e1 — hex | p1 — place |
|---|---|---|
| File | `hex/hex8_embedding_plexis_e1_256d.parquet` | `places/place_embedding_plexis_p1_64d.parquet` |
| Key · cols | `hex8_id` · `e0…e255` | `id` · `d0…d63` |
| Trained on | review-free hex features | category + micrograph + chain-sibling pairs |
| Use it for | region twins, vibe search, ML features | venue twins, competitor radar, brand DNA |

**Trust scores** (exams frozen *before* training):
- **e1** — twin hit-rate **1.0**, probes OD R²**0.90** / adequacy R²**0.93** /
  HDB-psm R²**0.81**, stability **0.987**, forbidden-rating probe **−0.014**.
- **p1** — chain retrieval **0.814**, category-kNN purity **0.997**, geo-leak ρ
  **0.077**, forbidden-rating R²**0.094**, stability **0.98** (9/9 pass).

**The contract:** ratings & reviews are *never* inputs and are provably
unrecoverable (the forbidden-probe ≈ 0). Build on the fingerprints freely — they
describe what a place **is**, not how popular it is.

**Don't expect:** the embedding to rank "good vs bad" venues, recover a brand
name, or distinguish two genuinely-identical minimarts. It encodes *kind* and
*context*, nothing it wasn't given.

Cosine is the only operation you need:

```python
def cosine_twins(emb_df, key, dims, the_id, k=8):
    M = emb_df.set_index(key)[dims]
    Z = M.values; Z = Z / (np.linalg.norm(Z, axis=1, keepdims=True) + 1e-9)
    v = Z[M.index.get_loc(the_id)]
    order = np.argsort(-(Z @ v))
    return M.index[order[1:k+1]].tolist()

hex_dims   = [f"e{i}" for i in range(256)]
place_dims = [f"d{i}" for i in range(64)]
cosine_twins(e1, "hex8_id", hex_dims, "8865a1...ffff")   # region analogs
cosine_twins(p1, "id",      place_dims, "5JKvDPFYGMnq")   # venue analogs
```

---

## 6. The five domain packs — the "one number a buyer pays for"

Each pack adds hero scores (0–100). **These 39 scores are now columns in the
master** (v5.5.0) — `df = pd.read_parquet(".../hex8_all_features.parquet")` already
has them; the standalone pack files + subzone rollups are kept for the catalogs.
22 shared primitives + 39 hero scores, **zero new data** — pure re-composition.
Full columns + honest limits in `catalog/pack_<pack>_catalog.json`.

| Pack | File | Hero score(s) | Also has |
|---|---|---|---|
| 🛍️ Retail | `hex8_retail_pack` | `retail_whitespace_score`, `format_fit_score` | competition_pressure · cannibalization · delivery · footfall · rent_demand_tier |
| 🏢 Real estate | `hex8_realestate_pack` | `re_feasibility_score`, `re_livability_score`, `re_momentum_score` | enbloc · collateral · yield_proxy · lease_decay_penalty |
| ⚡ Utilities | `hex8_utilities_pack` | `utility_load_score`, `utility_ev_gap_score` | load_growth · water · waste · diurnal_swing · equity · resilience |
| 🚇 Transport | `hex8_transport_pack` | `mobility_access_score`, `mobility_desert_priority` | crowding · tod · ridehail · firstlast_gap · parking_stress · modal_split |
| 🛡️ Insurance | `hex8_insurance_pack` | `insurance_risk_score` | fire · auto · health · bi_failure · collateral · nuisance · coastal_proxy · accumulation_band |

Plus two utility sidecars: **`hex8_mobility_pack`** (99 cols — `time_to_cbd_min`,
`time_to_orchard_min`, `time_to_changi_business_min`, `time_to_nus_min`… real
travel-times to 12 anchors) and **`hex8_context_pack`** (polyclinic / wet-market /
carpark / coworking / condo counts + distances).

```python
re = pd.read_parquet(f"{V5}/hex/hex8_realestate_pack.parquet")
top = re.nlargest(10, "re_feasibility_score")[["hex8_id","re_feasibility_score"]]
# known-answer: Tengah tops feasibility; Jurong West tops transit-desert & whitespace
```

---

## 7. Eight recipes

### R1 · Region twin / analog search
`cosine_twins(e1, "hex8_id", hex_dims, hid)` → "neighbourhoods that behave like
this one." Foundation of vibe search, comps, transfer.

### R2 · Place twins / competitor radar
`cosine_twins(p1, "id", place_dims, pid)` → a venue's true rivals are its nearest
fingerprints, **not** "all cafés." Join back to `places` for name/category.

### R3 · Brand expansion ghost-map (whitespace)
```python
pl = places.merge(p1, on="id")
dna = pl[pl.brand_norm == "ya kun"][place_dims].mean().values          # brand siting DNA
dna /= np.linalg.norm(dna) + 1e-9
hexrep = pl.groupby("hex8_id")[place_dims].mean()                       # hex's place-mix vector
H = hexrep.values; H = H / (np.linalg.norm(H,axis=1,keepdims=True)+1e-9)
fit = pd.Series(H @ dna, index=hexrep.index)                           # similarity to the DNA
has = pl[pl.brand_norm=="ya kun"].groupby("hex8_id").size()
ghost = fit.drop(has.index, errors="ignore").nlargest(15)             # looks-like-it, no outlet yet
```

### R4 · Site score for a category
```python
cat = "cafe_coffee"
s = hex8.set_index("hex8_id")
score = (s[f"cap_{cat}"].rank(pct=True)*0.5
       + s[f"iso_walk10_unserved_pop_{cat}"].rank(pct=True)*0.5)      # demand + winnable
score = score[s["zone_type_broad"]=="residential"]                    # skip industrial/airport
```
(Or just read `retail_whitespace_score` from the retail pack — same idea, validated.)

### R5 · Vibe search ("feels like here")
Take a hex's e1 twins (R1); paint them on a map. A search box over fingerprints.

### R6 · Opportunity / gap finder
A hex's twins define what it *should* have; the per-category shortfall vs its
twins' mean = a ranked "add what, where" map. Use `pc_cat_*` differences across
the twin set.

### R7 · Embeddings as ML features (bring your own target)
```python
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import cross_val_score
X = e1.set_index("hex8_id")[hex_dims]
y = hex8.set_index("hex8_id")["hdb_resale_psm_med"]                    # any target you have
m = X.join(y).dropna()
print(cross_val_score(GradientBoostingRegressor(), m[hex_dims], m.iloc[:,-1], cv=5, scoring="r2").mean())
# the probes already proved the geometry carries structure (OD 0.90, adequacy 0.93)
```

### R8 · One-number lookup (domain packs)
Join the pack, read the hero column, map it. `insurance_risk_score` for an
address, `mobility_desert_priority` for a transport brief, `re_feasibility_score`
for a GLS bid.

---

## 8. Mapping the output

```python
import h3
hex8["boundary"] = hex8["hex8_id"].map(lambda h: h3.cell_to_boundary(h))   # [(lat,lng),…]
# → GeoJSON polygons for Mapbox/Deck.gl; colour by any score column
# places: scatter on latitude/longitude, colour by plexis_category or a p1 cluster
```

The reference apps already do this — copy their patterns (Mapbox GL + Deck.gl +
a score→colour ramp). The atlas ships centroids; you build the polygons client- or
server-side from the H3 id.

---

## 9. Reference apps — study these, they're built on exactly this data

| App | URL | Shows you |
|---|---|---|
| 🌗 **SG Pulse** | `http://10.0.2.25:16095` | day-night population/demand engine over all 1,191 hexes |
| 🌌 **Places Constellation** | `http://10.0.2.25:16096` | the 190K-place p1 galaxy + twin retrieval (R2) |
| 📓 **Atlas Diary** | `http://10.0.2.25:16097` | ten embedding use-cases answered live on the map |
| 🎬 Contrastive animation | `:14043/contrastive_learning_animation.html` | how e1/p1 are trained (the *why* behind cosine) |
| 🎞️ Domain packs animation | `:14043/domain_packs_animation.html` | the 5 packs recolouring the map |

The **Starter Idea Board** (`:14043/STARTER_IDEA_BOARD.html`) lists 23 more app
concepts on this same data.

---

## 10. Keys & services

- **Mapbox** (basemap/GL) — token in project `CLAUDE.md`.
- **OpenRouter** (LLM layer — explanations, the reasoner) — key in
  `~/notes/openrouter-keys-batch1.txt` (Haiku 4.5 / Sonnet 4.6 / Grok).
- **data.gov.sg** + **OneMap** — for any live SG layer refresh (keys in `CLAUDE.md`).
- No paid feed is required to *use* the atlas — it's static parquet.

---

## 11. Honest limits (so you don't over-promise)

- **No commercial-rent or private-property prices** — retail rent uses a
  residential proxy; private-unit AVM is RE v2 (paywalled).
- **No time-of-day OD** — `od_*` is aggregate; daypart is Phase 3.
- **No crime feed** — that peril is *omitted, not proxied* in the insurance pack.
- **Climate** (flood/heat) is Phase 3; `lu_water_pct` is only a weak coastal proxy.
- Three pack scores are honest re-framings of an existing column (waste ∝ pop,
  bi_failure ≈ `biz_recent_dead_share`, mobility_access ≈ adequacy) — flagged in
  each pack catalog. The embeddings encode *kind*, not *quality*.

---

## 12. Cheat-sheet — the 25 columns you'll reach for first

`hex8_id` · `lat` · `lng` · `parent_subzone` · `parent_pa` · `parent_region` ·
`zone_type_broad` · `pop_resident` · `pop_total_all` · `dt_pop` · `pop_65plus` ·
`pc_total` · `pc_cat_<cat>` · `cap_<cat>` · `iso_walk10_unserved_pop_<cat>` ·
`transit_score` · `mrt_station_count` · `dist_mrt_m` · `nl_2024` ·
`hdb_resale_psm_med` · `min15_score` · `time_to_cbd_min` · `e0…e255` (hex
fingerprint) · pack hero scores · `id` + `d0…d63` (place fingerprint).

---

*Built on Atlas v5.4.0 · `github.com/Propheus/digital-atlas-sgp` · everything
review-free, exam-gated, and reproducible from `plexis-sgp-v5/`. Now go build.*
