# Atlas external feature pack for nous — 2026-06-11

Built by the Digital Atlas pipeline (plexis v5; script `plexis-sgp-v4/build_nous_features.py`). Shapes per FEATURES_TO_BUILD.md; H3 wiring stays on the nous side.

| File | Shape | Maps to 🔨 | Source | Sanity |
|---|---|---|---|---|
| `shophouse_conserved_buildings.parquet` | points | `shophouse_density` | URA MP19 SDCP Conserved Building layer (data.gov.sg) | PASS: 7,235 conserved bldgs; top hexes: CHINATOWN, LITTLE INDIA, LAVENDER, CRAWFORD (5/6 h |
| `hex8_shophouse_density.parquet` | hex8-keyed | `shophouse_density` | derived: conserved bldg count + cluster flag (≥20) | PASS: 7,235 conserved bldgs; top hexes: CHINATOWN, LITTLE INDIA, LAVENDER, CRAWFORD (5/6 h |
| `carparks.parquet` | points+capacity | `carpark_accessibility` | HDB Carpark Information + live availability total_lots (C) | PASS: 2,266 HDB carparks, capacity joined for 88%, 696,086 car lots total |
| `polyclinics.csv` | points | `polyclinic_distance` | OSM (name match), deduped | PASS: 27 polyclinics; known-name hits 5/5 |
| `female_pop_share.csv` | subzone table | `female_pop_share` | SingStat 2025 pop by SZ × age × sex (local atlas copy) | PASS: 332 subzones, national female share 0.514 |
| `wet_markets.csv` | points+flag | `wet_market_adjacency` | NEA hawker-centres layer, 'market' name flag | PASS: 129 centres, 63 flagged markets; landmarks 4/4 |
| `petrol_stations.csv` | points | `petrol_station_coverage` | OSM amenity=fuel | PASS: 201 stations, 188 major-brand named |
| `coworking_spaces.csv` | points | `coworking_density` | Atlas places (190K) brand/name match | PASS: 171 venues matched, 40% in CBD-core subzones |
| `condo_projects.parquet` | points+weight | `condo_density` | URA PMI_Resi_Transaction (strata only); units_sold = transaction volume, NOT stock | PASS: 2,384 strata projects (txn-derived; units_sold = txn volume weight, NOT total units) |
| `hdb_completion_by_town.csv` | town table | `new_estate_growth` | HDB completion status by town/estate (under-construction units) | PASS: 1640 rows to FY2024; 91,941 units under construction |

## Not deliverable (so you don't wait for it)
- **`rental_affordability` (shop rent)** — URA exposes NO commercial rental via API/data.gov.sg (probed 2026-06-10; Realis-only). The live hex8 view already carries `rent_resi_psf_med` + `rent_resolution` (913-project URA resi medians, IDW) — the best available rent *gradient*; treat as proxy with the same null-trap rule as HDB psm.
- **BTO project-level locations** — no longer openly published (HDB geojson on data.gov.sg is 2018-stale). Town-level under-construction units above + the live `pipe_dev_capacity_res` / `pipe_new_mrt_within_800m` hex8 columns are the workable combination.

## Sanity log

- [PASS] **shophouse** — 7,235 conserved bldgs; top hexes: CHINATOWN, LITTLE INDIA, LAVENDER, CRAWFORD (5/6 heritage)
- [PASS] **carparks** — 2,266 HDB carparks, capacity joined for 88%, 696,086 car lots total
- [PASS] **polyclinics** — 27 polyclinics; known-name hits 5/5
- [PASS] **female_pop_share** — 332 subzones, national female share 0.514
- [PASS] **wet_markets** — 129 centres, 63 flagged markets; landmarks 4/4
- [PASS] **petrol** — 201 stations, 188 major-brand named
- [PASS] **coworking** — 171 venues matched, 40% in CBD-core subzones
- [PASS] **condo_projects** — 2,384 strata projects (txn-derived; units_sold = txn volume weight, NOT total units), CCR share 29%
- [PASS] **hdb_completion_by_town** — 1640 rows to FY2024; 91,941 units under construction