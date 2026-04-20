# Universal Representation of Urban Regions
*Unifying Places and Region Metrics — Singapore H3 Hex Experiment*

**Date:** 2026-04-12 | **Resolution:** H3-9 (~175m edge) | **City:** Singapore

---

## Abstract

We construct a **305-dimensional** per-hex representation of Singapore across **7,318** H3 resolution-9 hexagons, unifying 174,713 places, 4,212,800 residents, 113K zoning parcels, 377K buildings, and 231 MRT stations. A spatial+transit influence graph improves nearest-neighbor accuracy by **127%** over self-features alone. Unsupervised k-means recovers Singapore's known urban archetypes and correctly identifies structural twins across planning area boundaries (Sentosa ↔ Marina Bay Sands).

| Hexes | Features | Places | Population | kNN Accuracy | Influence Lift |
|---|---|---|---|---|---|
| 7,318 | 305 | 174,713 | 4,212,800 | 55.1% | +34.5% |

---

## 1. Data Inventory

| Metric | Value |
|---|---|
| Total Hexes | 7,318 |
| Active Hexes | 3,934 |
| Void Hexes | 3,384 |
| Subzones Covered | 326 |
| Planning Areas | 55 |
| Total Columns Raw | 318 |
| Total Columns Normalized | 307 |
| Non Constant Features | 305 |
| Self Features | 184 |
| Influence Features | 121 |
| Places In Hexes | 169,294 |
| Places Outside | 5,419 |
| Total Population | 4,212,320 |
| Census Population | 4,212,800 |

## 2. Influence Feature Ablation

### 2.1 Aggregation Method Comparison (k=5 ring)

| Method | Accuracy | Lift |
|---|---|---|
| Self + lat/lng (baseline) | 0.242 | +0.000 |
| + Uniform k=5 mean | 0.323 | +0.080 |
| + Pop-weighted k=5 | 0.311 | +0.069 |
| + Place-weighted k=5 | 0.334 | +0.091 |
| + Gravity-weighted k=5 | 0.314 | +0.072 |
| + Max-influence k=5 | 0.374 | +0.132 |
| + Spatial (max + place-w) | 0.438 | +0.196 |
| + Transit only | 0.444 | +0.202 |
| **+ Spatial + Transit (FINAL)** | 0.587 | +0.345 |

### 2.2 Ring Radius Sweep

| k | Neighbors | Radius | Max-Influence | Place-Weighted | Combined |
|---|---|---|---|---|---|
| 1 | 6 | 175m | 0.283 | 0.286 | **0.312** |
| 2 | 18 | 350m | 0.323 | 0.313 | **0.366** |
| 3 | 36 | 525m | 0.347 | 0.323 | **0.401** |
| 5 | 90 | 875m | 0.374 | 0.334 | **0.438** |
| 8 | 216 | 1400m | 0.388 | 0.337 | **0.448** |

### 2.3 Position Disentanglement

> **Influence lift beyond position: +34.5%** — confirmed genuine contextual signal

## 3. Validation

- Totals conservation: places **174,713 exact**, pop 99.99%, MRT 231, HDB 13,386
- Value ranges: all 42 pct cols in [0,1], all counts >= 0, all constraints hold
- Broadcast columns: **0** (down from 40)
- corr(pop, RFA) = 0.952, corr(hdb, pop) = 0.88
- corr(spatial_max, transit_max) = 0.605 (complementary)

## 4. Unsupervised Cluster Recovery (k=8)

| Archetype | Hexes | Avg Places | Avg Pop | Avg HDB | Avg Luxury | Top PAs |
|---|---|---|---|---|---|---|
| **void / water / nature** | 1,835 | 1 | 1 | 0.0 | 0.0 | NORTH-EASTERN ISLANDS(502), WESTERN WATER CATCHMENT(320), WESTERN ISLANDS(212) |
| **mixed / transitional** | 1,585 | 3 | 13 | 0.0 | 0.0 | CENTRAL WATER CATCHMENT(160), CHANGI(151), SUNGEI KADUT(105) |
| **medium-density residential** | 1,072 | 26 | 821 | 2.0 | 0.1 | BEDOK(108), BUKIT TIMAH(76), TAMPINES(72) |
| **industrial belt** | 1,005 | 3 | 0 | 0.0 | 0.0 | TUAS(424), WESTERN ISLANDS(248), WESTERN WATER CATCHMENT(181) |
| **dense HDB heartland** | 752 | 64 | 3,821 | 13.4 | 0.1 | TAMPINES(56), BEDOK(54), WOODLANDS(51) |
| **low-density / landed** | 529 | 25 | 470 | 1.0 | 0.6 | BUKIT MERAH(108), TANGLIN(62), NOVENA(52) |
| **void / water / nature** | 341 | 0 | 0 | 0.0 | 0.0 | NORTH-EASTERN ISLANDS(160), WESTERN ISLANDS(99), TUAS(79) |
| **CBD / premium commercial** | 199 | 361 | 950 | 3.0 | 6.1 | GEYLANG(31), DOWNTOWN CORE(24), ROCHOR(15) |

## 5. Place Composition

### 5.1 Most Specialized Hexes

| Subzone | PA | Places | Entropy | Dominant | Share |
|---|---|---|---|---|---|
| WCSZ01 | WESTERN WATER CATCHMENT | 28 | 0.41 | **services** | 89% |
| SKSZ01 | SUNGEI KADUT | 214 | 0.76 | **automotive** | 84% |
| JWSZ05 | JURONG WEST | 23 | 0.92 | **business** | 74% |
| QTSZ15 | QUEENSTOWN | 50 | 0.95 | **shopping_retail** | 74% |
| TNSZ01 | TANGLIN | 180 | 1.03 | **health_medical** | 80% |
| QTSZ10 | QUEENSTOWN | 20 | 1.08 | **education** | 70% |
| QTSZ11 | QUEENSTOWN | 58 | 1.10 | **education** | 74% |
| PGSZ01 | PUNGGOL | 21 | 1.11 | **restaurant** | 71% |
| BSSZ01 | BISHAN | 261 | 1.13 | **automotive** | 70% |
| BDSZ01 | BEDOK | 152 | 1.21 | **automotive** | 68% |

### 5.2 Price Tier Profiles

| Archetype | Luxury | Premium | Mid | Value | Budget |
|---|---|---|---|---|---|
| **CBD** | 4.0% | 18.9% | 62.4% | 13.7% | 1.0% |
| **Heartland** | 0.1% | 6.0% | 56.9% | 33.7% | 3.2% |
| **Industrial** | 0.2% | 2.0% | 69.3% | 26.0% | 2.5% |

## 6. Micrograph Context Vectors

| Archetype | Hexes | T1 Transit | T2 Competitor | T3 Complementary | T4 Demand |
|---|---|---|---|---|---|
| **Near Mrt** | 183 | 0.380 | 0.355 | 0.100 | 0.164 |
| **Dense Commercial** | 390 | 0.106 | 0.527 | 0.144 | 0.212 |
| **Suburban Residential** | 431 | 0.065 | 0.564 | 0.120 | 0.240 |

## 7. Nearest-Neighbor Structural Sanity

### CBD_DTSZ05 (DTSZ05, DOWNTOWN CORE)

| # | Subzone | PA | Places | Pop |
|---|---|---|---|---|
| 1 | DTSZ09 | DOWNTOWN CORE | 1068 | 1,030 |
| 2 | OTSZ04 | OUTRAM | 762 | 0 |
| 3 | ORSZ02 | ORCHARD | 1245 | 165 |
| 4 | ORSZ03 | ORCHARD | 1110 | 58 |
| 5 | MUSZ01 | MUSEUM | 714 | 610 |
| 6 | DTSZ01 | DOWNTOWN CORE | 848 | 1,310 |
| 7 | DTSZ02 | DOWNTOWN CORE | 1154 | 0 |
| 8 | OTSZ04 | OUTRAM | 829 | 1,200 |
| 9 | DTSZ08 | DOWNTOWN CORE | 1140 | 560 |
| 10 | SRSZ03 | SINGAPORE RIVER | 876 | 99 |

### Sentosa_SISZ01 (SISZ01, SOUTHERN ISLANDS)

| # | Subzone | PA | Places | Pop |
|---|---|---|---|---|
| 1 | SISZ01 | SOUTHERN ISLANDS | 69 | 0 |
| 2 | SISZ01 | SOUTHERN ISLANDS | 36 | 0 |
| 3 | SISZ01 | SOUTHERN ISLANDS | 68 | 0 |
| 4 | DTSZ12 | DOWNTOWN CORE | 146 | 0 |
| 5 | DTSZ12 | DOWNTOWN CORE | 279 | 0 |
| 6 | SISZ01 | SOUTHERN ISLANDS | 12 | 0 |
| 7 | DTSZ11 | DOWNTOWN CORE | 20 | 0 |
| 8 | DTSZ12 | DOWNTOWN CORE | 129 | 0 |
| 9 | SISZ01 | SOUTHERN ISLANDS | 6 | 0 |
| 10 | JESZ05 | JURONG EAST | 19 | 0 |

### Bedok_HDB (BDSZ01, BEDOK)

| # | Subzone | PA | Places | Pop |
|---|---|---|---|---|
| 1 | BDSZ01 | BEDOK | 35 | 4,280 |
| 2 | WDSZ03 | WOODLANDS | 39 | 6,248 |
| 3 | BMSZ04 | BUKIT MERAH | 57 | 4,020 |
| 4 | BDSZ01 | BEDOK | 89 | 2,643 |
| 5 | HGSZ08 | HOUGANG | 59 | 3,049 |
| 6 | SESZ06 | SENGKANG | 49 | 7,318 |
| 7 | QTSZ02 | QUEENSTOWN | 63 | 6,649 |
| 8 | SESZ06 | SENGKANG | 42 | 7,666 |
| 9 | SESZ06 | SENGKANG | 61 | 7,217 |
| 10 | BKSZ07 | BUKIT BATOK | 45 | 4,773 |
