# Hex v10 — Validation Report

**Built:** 2026-04-12
**Updated:** 2026-04-12 (post influence-feature rebuild)

## Final scorecard: 32 PASS / 1 soft-fail out of 33 checks

### CHECK 1 — Totals conservation (6/6 PASS)
- Places: 169,294 + 5,419 outside = **174,713 exact**
- Population: 4,212,320 / 4,212,800 (**-0.011%**, 5 micro-subzones)
- MRT stations: **231 exact**
- HDB blocks: **13,386 exact** (patched via authoritative geojson)
- Hawker centres: **129 exact**
- Hotels: **468 exact**

### CHECK 2 — Named landmarks (8/8 PASS)
- VivoCity: 197 shopping retail ✓
- Marina Bay Sands: 68 luxury tier ✓
- ION Orchard: 1,245 places ✓
- Raffles Place: 384 business ✓
- Changi Airport T1: 84 shopping ✓
- Universal Studios Sentosa: 21 culture/entertainment ✓
- NUS Kent Ridge: 11 education, lu_institutional=1.00 ✓
- Jurong Island: lu_business=1.00 ✓

### CHECK 3 — Value ranges (7/7 PASS)
- 42 percentage columns all in [0, 1]
- 8 count columns all ≥ 0
- elderly ≤ population: all 7,318
- children ≤ population: all 7,318
- Σ category counts == pc_total: all 7,318
- Σ land use shares ≈ 1.0: all 7,318
- entropy in [0, ln(24)]: all 7,318

### CHECK 4 — Cross-feature coherence (4/4 PASS)
- corr(population, residential_floor_area) = 0.952
- corr(hdb_blocks, population) = 0.880
- 95.0% of hexes with MRT daily taps have MRT station in-hex
- 90.7% of hexes with lu_residential > 0.5 have population > 0

### CHECK 5 — Broadcast scan (1/1 PASS)
- **0 unintentional broadcast columns** (down from 40 in v1)

### CHECK 6 — Influence feature quality (2/3 PASS, 1 soft-fail)
- Sentosa transit max: **tr_max_pc_total = 1,356** (reaches Raffles Place via MRT) ✓
- Spatial vs transit correlation: **r = 0.605** (complementary, not redundant) ✓
- Void hex spatial max: mean 56.1 vs threshold 50 — soft fail, explained by Singapore's small size (even void hexes are near mainland suburbs within k=5)

### CHECK 7 — Unsupervised K=8 cluster recovery (4/4 PASS)
- CBD cluster: avg luxury 6.1 ✓
- HDB heartland: avg hdb_blocks 13.4 ✓
- Void: 1,835 hexes with avg pc_total < 1 ✓
- Industrial: avg lu_business 0.6 ✓

### Influence feature improvement (validated)
- Old k-ring (150 features): kNN PA accuracy 0.252 (+2.0% vs baseline)
- **New influence (124 features): kNN PA accuracy 0.551 (+29.9% vs baseline, 119% relative improvement)**
- Evidence confirmed: +12.3% lift is beyond positional (lat/lng) signal — genuine contextual information
- Sentosa → MBS → Jurong East tourism cluster recovered across subzone boundaries
- Bedok HDB → Yishun/Tampines/Bukit Batok/Sengkang/Woodlands heartland cluster recovered

### kNN structural sanity (3/3 PASS)
- CBD core → all Downtown Core / Orchard / Singapore River / Museum / Outram
- Sentosa → other Sentosa + Marina Bay Sands (DTSZ12) + Jurong East
- Bedok HDB → HDB heartlands across 7 different planning areas
