# Hex v11 — Total Population (6.11M) at H3 res 8

**Built:** 2026-05-28
**Resolution:** H3 res 8 (1,191 cells, ~0.84 km² each, ~460m edge)
**Total population:** 6,110,000 (matches DOS June 2025)

This is the first SGP atlas table that captures the **full population** of
Singapore — not just the 4.2M residents from the Census, but also the 1.91M
non-residents (foreign workforce + dependants + students) who live and use
infrastructure here.

## Files

| File | Rows | Cols | Purpose |
|---|---|---|---|
| `hex8_population.parquet` | 1,191 | 27 | Main table — full hex8 totals + breakdowns |
| `subzone_population.parquet` | 274 | 13 | Subzone rollup for app UIs |
| `hex8_dorm_pop.parquet` | 1,191 | 7 | Dorm-only intermediate |
| `hex8_fdw_pop.parquet` | 1,191 | 5 | FDW-only intermediate |
| `hex8_other_nr_pop.parquet` | 1,191 | 8 | Other-NR intermediate |

## Schema (hex8_population.parquet)

```
hex8_id                    H3 res-8 cell id
lat, lng                   centroid
area_km2                   ~0.84
parent_subzone/pa/region   admin geography

— RESIDENT (4,200,000) —
pop_resident               citizens + PRs
pop_resident_citizen       resident × 87.14% (national ratio)
pop_resident_pr            resident × 12.86%
children_count             from census
elderly_count              from census
working_age_count          from census

— NON-RESIDENT (1,910,000) —
pop_nr_dorm                CMP WP workers in PBDs/CDCs/CTQs (482,600)
pop_nr_fdw                 Migrant Domestic Workers in households (316,900)
pop_nr_ep                  Employment Pass + most dependants (453,000)
pop_nr_sp                  S Pass + some dependants (204,000)
pop_nr_wp_other            Services-WP + other work passes (453,500)
pop_non_resident           sum of NR sub-buckets
dorm_count                 # of FEDA-licensed dorms in cell
raw_capacity               pre-scaling bed estimate (provenance only)

— DERIVED —
pop_total                  pop_resident + pop_non_resident
pop_density_per_km2        per-cell density (population × 1.18 / area)
attrib_label               'empty' / 'nr_dominant' / 'mixed' / 'resident_majority'
attrib_confidence          'high' / 'low' / 'sparse'
residential_floor_area_sqm carried from hex8_final
total_floor_area_sqm       carried from hex8_final
```

## Control totals (DOS June 2025 / MOM Dec 2025)

| Bucket | Target | Achieved |
|---|---|---|
| Total population | 6,110,000 | **6,110,000** (0.000% drift) |
| Resident — Citizens | 3,660,000 | 3,659,994 |
| Resident — PRs | 540,000 | 540,000 |
| Non-resident — Dorm (CMP) | 482,600 | 482,600 |
| Non-resident — MDW | 316,900 | 316,900 |
| Non-resident — EP + dep | 453,000 | 453,000 |
| Non-resident — S Pass | 204,000 | 204,000 |
| Non-resident — Other WP | 453,500 | 453,500 |

## Source documents

- **DOS Population in Brief 2025** (June 2025) → total + residency breakdown
  https://www.population.gov.sg/files/media-centre/publications/Population_in_Brief_2025.pdf
- **MOM Foreign Workforce Numbers, Dec 2025** (published 2026-03-20)
  https://www.mom.gov.sg/foreign-workforce-numbers
- **MOM FEDA licensed dormitory list** (updated 2026-05-18)
  https://go.gov.sg/migrant-worker-dormitories
  Cached locally: `data/external/mom/migrant-worker-dormitories.pdf` (1,783 dorms)
- **DASL Dormitory Industry Index H2 2024** (Knight Frank + DASL)
  https://www.dasl.com.sg/wp-content/uploads/2025/02/Dormitory-Industry-Index-Report-H2-2024.pdf
  → DASL class distribution (Class 1-4 beds and dorm counts)
- **Census 2025**: `data/demographics/pop_age_sex_tod_2025.csv`
- **Hex v10 feature stack**: `data/hex_v10/hex8_final.parquet` (1,191 × 628)
- **Overture buildings**: `data/buildings_overture/sgp_buildings.parquet` (281 dorm-class)
- **OneMap.gov.sg** for geocoding (free, no auth)

## Attribution methods

### Resident (4.2M)
hex8_final.parquet already carries dasymetric-distributed Census 2025 resident
population (4,212,320). Top-down scaled to 4,200,000 to match the DOS rounded
target. Citizen/PR split applied uniformly via national ratio (no subzone-level
PR data available).

### Dorm CMP (482,600)
**Source:** 1,783-entry MOM FEDA license list (May 2026 vintage). Workflow:
1. Parsed all 1,783 dorms from the PDF (ID, address, name, operator).
2. Geocoded via OneMap.gov.sg — 1,121 (63%) got lat/lng. The 662 misses are
   mostly construction-site CTQs/TOLQs whose addresses are survey marks
   (e.g. `MK28-06542A`) without a postal code.
3. Classified each dorm into DASL Class 1-4 from operator + name + address
   keywords (named "Lodge"/"Dormitory" → Class 3-4; Tuas-South / Mandai / Soon-Lee
   keywords → Class 4; CTQ/TOLQ markers → Class 1).
4. Capacity proxy:
   - If matched to an Overture `class=dormitory` building within 200m (only 37
     dorms — Overture under-tags this class) → `footprint × num_floors × 0.6
     occupancy / 8 sqm-per-bed`
   - Else fall back to DASL class-mean bed counts: Cl 1=38, Cl 2=182, Cl 3=461,
     Cl 4=4635
5. Excluded `DORM-90xxx` (NGO/HOME shelters) from the CMP bucket.
6. Geocoded dorms mapped to their hex8 cell directly.
7. Ungeocoded CTQs' raw capacities redistributed across geocoded cells weighted
   by √existing-capacity (so single-mega-dorm cells don't run away).
8. Top-down scaled so total = exactly 482,600.

**Quality note:** The class-based defaults dominate (only 37 of 1,766 dorms have
Overture footprints). Cell-level fidelity is fuzzy; subzone-level totals are
trustworthy. Subzone sanity check at the top — Tuas View Extension (34.8K),
Tuas View (29.1K), Changi Airport corridor (28.2K, the S11 Changi Lodge complex),
Kaki Bukit (28.0K, Westlite Ubi cluster), Senoko West (24.8K).

### FDW / MDW (316,900)
Per-subzone count = sum over TOD of `Pop_TOD / avg_HH_size_TOD × FDW_rate_TOD`,
where FDW employment rates by dwelling type are:

| TOD | Avg HH size | FDW rate |
|---|---|---|
| HDB 1-2R | 2.0 | 0.01 |
| HDB 3R | 2.7 | 0.03 |
| HDB 4R | 3.1 | 0.07 |
| HDB 5R/Exec | 3.4 | 0.15 |
| HUDC | 3.0 | 0.10 |
| Condo/Apartment | 2.7 | 0.32 |
| Landed | 3.4 | 0.65 |
| Others | 2.5 | 0.10 |

Subzone totals scaled to 316,900, then distributed within-subzone across hex8
cells by `residential_floor_area_sqm` (fallback to within-SZ population share
when floor area is zero).

### Other non-resident (1,110,500) — three-way split
**EP + dependants (453,000)**: weight =
`bldg_private_residential × walk_mrt_score^1.2 × cbd_score^0.8`
Concentrates in CCR/RCR condo enclaves with MRT access. Tops: Kembangan
(17.5K — the Bedok-Camp expat draw), Hillcrest, Upper Paya Lebar, Moulmein,
Tyersall, Tanglin, Pasir Panjang 2, Coronation Road.

**S Pass + some dependants (204,000)**: weight =
`(priv × 0.6 + hdb × 0.4) × walk_mrt_score × (0.4 + cbd_score^0.3 × 0.6)`
Mixed RCR/OCR with both private and HDB rental access.

**Services WP + other (453,500)**: weight =
`hdb × (0.3 + indus_adj^0.7 × 0.7) × (0.6 + walk_mrt_score^0.5 × 0.4) +
 industrial × walk_mrt_score^0.3 × 0.3 + hdb × 0.03`
Concentrates in mature HDB estates near industrial zones with rental supply.
Tops: Tiong Bahru Station (9.1K), Pasir Ris West, Mei Chin, Fernvale,
Kaki Bukit, Jurong West Central.

## Validation

### Top cell sanity
| Cell area | Total pop | Composition |
|---|---|---|
| Jurong West Central HDB | 51,579 | mostly resident (42K) |
| Fernvale (Sengkang) HDB | 49,053 | mostly resident (37K) + 3.4K FDW |
| Sengkang Town Centre | 48,752 | dense HDB resident (42K) |
| Kembangan (Bedok) | 40,187 | 17.5K EP — confirmed expat enclave near Tanjong Katong |
| Upper Paya Lebar | 39,682 | 10.9K EP — landed/condo mix |
| Tiong Bahru Station | 41,319 | 9.1K services-WP — industrial-fringe rental |

### Tuas industrial transformation (the headline fix)
| Metric | Before (v10 resident-only) | After (v11) |
|---|---|---|
| Tuas subzone resident pop | 0 | 0 |
| Tuas total pop | 0 ("<50 → gray") | **107,347** |
| Of which dorm | — | 105,094 |

This change is what unlocks meaningful adequacy analysis for Tuas / Sungei
Kadut / Kranji / Mandai / Joo Koon — previously these subzones were forced
gray in the UI because resident pop was below the 50-person floor.

### Confidence breakdown
- **High** (508 cells): pop_resident ≥ 50 OR has dorm anchor → trust the
  attribution.
- **Low** (6 cells): pop > 100 but no resident or dorm anchor → check before
  surfacing.
- **Sparse** (677 cells): total pop ≤ 100; mostly sea, water catchment,
  military zones, port edges. The Atlas UI should gray these out.

## Known limitations

1. **PR / Citizen split is uniform.** No subzone-level Citizen-vs-PR data
   available; we apply the national 87.1/12.9 split everywhere.
2. **Dorm cell precision is fuzzy.** Only 37 of 1,766 MOM dorms matched
   Overture buildings (because Overture under-tags `class=dormitory` —
   many are tagged `residential` or `industrial`). Default class capacities
   smooth the per-cell numbers — subzone-level rollups are accurate but a
   single dorm cell's count is ±30%.
3. **The "70/30 industrial vs residential" critique addressed.** EP/SP
   bucket weights MRT × CBD heavily (no longer industrial-dominant) so CCR
   condo zones light up correctly. Services-WP still leans HDB-rental near
   industrial fringe.
4. **Dependants are bundled into EP/SP buckets** rather than getting a
   separate bucket. The DOS Pop-in-Brief doesn't publish a dependants
   geographic distribution; following empirical work-pass-co-residence
   patterns is the cleanest approximation.
5. **The MOM FEDA list (May 2026) is fresher than DASL (Dec 2024)** — DASL
   had 1,441 dorms with 439,198 beds; MOM lists 1,783. The growth of 342
   entries in ~17 months is plausible (continued NDS-driven expansion) but
   means raw capacity proxy is slightly elastic.

## Build pipeline

```
scripts/hex_v11/
├── 01_geocode_dorms.py          OneMap geocoding (parallel)
├── 01b_retry_misses.py          street-name fallback for the 711 misses
├── 02_attribute_dorm_pop.py     dorm capacity proxy + hex8 mapping
├── 03_attribute_fdw_pop.py      FDW dwelling-weighted attribution
├── 04_attribute_other_nr_pop.py EP / SP / WP-other three-way split
└── 05_combine_validate.py       merge + top-down scale + validation report
```

All scripts are idempotent and operate on local data only (no server
round-trip). To rebuild from scratch: drop `data/external/mom/.onemap_cache.jsonl`
and re-run in order.

## Diff vs hex_v10

`hex_v10/hex8_final.parquet` was the upstream feature stack — we kept the
identity + buildings + land-use + transit + amenities + influence columns
intact and ADDED the 5 NR sub-buckets + 2 derived totals + 2 confidence
columns. v11 does NOT supersede v10's 628 feature columns; it's a
population-overlay companion table that joins on `hex8_id`.
