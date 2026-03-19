# Digital Atlas Singapore

Mathematical representation of Singapore's urban structure at the subzone level (332 zones).

## Structure

```
data/
  boundaries/     Subzones (332) + Planning Areas (55) + SGP boundary
  demographics/   Population by age/sex/dwelling (2025 Singstat)
  property/       HDB resale (227K txns) + private transactions
  amenities/      SFA eating (34K), CHAS clinics (1.2K), preschools (2.3K)
  transit/        Bus stops (5.2K), MRT stations (231), exits (595)
  roads/          Road network (551K edges from OSM)
  buildings/      Building footprints (126K from OSM)
  land_use/       Master Plan zoning (113K parcels from URA)
  places/         66,851 curated places with categories, brands
  business/       ACRA registered entities (2M)
  features/       Computed subzone feature vectors (11 parquets)
  graphs/         Adjacency, co-location PMI, transit connectivity

model/
  features/       Final feature matrices (332x205, 66Kx13)
  results/        Gap analysis and model report

scripts/          Processing and training pipeline
docs/             Architecture, reports, ideation
```

## Key Numbers

- 66,851 places | 24 categories | 165 place types | 232 brands
- 332 subzones | 202 features per subzone
- Density model R² = 0.773
- 1.9 GB total data
