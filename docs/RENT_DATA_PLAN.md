# Rent Data Plan — adding rental to the Digital Atlas (hex9 + hex8)

*Plexis SGP · 2026-06-21 · scope: a proper rental layer at **hex9 (7,318) and hex8
(1,191)**, extending the current hex8-only residential rent surface and closing the
HDB + commercial gaps.*

---

## 0. TL;DR
- We already ingest **URA private-residential rent** (`PMI_Resi_Rental_Median`, 917
  projects, quarterly $psf/mo) but build it **only at hex8** (`hex8_rent_surface.parquet`).
- **Plan:** (1) rebuild the residential surface at **hex9 first → roll up to hex8**;
  (2) add **HDB median rent by town × flat-type** (data.gov.sg, free) for the
  heartland; (3) ship a blended occupancy-cost signal; (4) keep **commercial rent**
  as a flagged Tier-2 gap (Realis/URA-SPACE only).
- Output: `hex9_rent_surface.parquet` + `hex8_rent_surface.parquet`, patched into
  both masters → **v5.7**. Pure derivation from the rental points; ~1 session.

---

## 1. Current state & the gap

| | Have | Where | Gap |
|---|---|---|---|
| **Private residential rent** | `rent_resi_psf_med`, `rent_resi_n_obs`, `rent_resolution` | hex8 only | not at hex9; uses project *medians* (could use contract-level) |
| **HDB rent** | — | — | **missing** — the heartland has no rent signal |
| **Commercial (office/retail) rent** | — | — | **URA Data Service has no commercial endpoint** (`PMI_Comm_*` = invalid); Realis/URA-SPACE only |
| **Industrial rent** | — | — | missing (JTC) |

Current build: `build_rent_surface.py` → median of project medians (last 4 quarters)
→ **IDW (k=5, p=2, ≤2.5 km)** onto hex8 activity centroids · `rent_resolution` =
`local` (≤800 m) / `idw` (≤2.5 km) / `none`. Source cached at
`data/external/ura_rental_median.json`.

---

## 2. Datasets to add (tiered)

### Tier 1 — free, do now
1. **URA Private Residential Rental** — `PMI_Resi_Rental_Median` (already fetched).
   *Upgrade:* also pull the **contract-level** list (per-lease `$psf`, `areaSqft`,
   `leaseDate`, `propertyType`) for finer spatial resolution than project medians.
   917 projects → thousands of contracts/quarter. SVY21 coords → WGS84.
2. **HDB Median Rent by Town & Flat Type** — data.gov.sg (HDB approved subletting),
   quarterly, by **town × flat-type** (1R…EXEC). Free API. Snap by HDB-town polygon
   → hex9/hex8. This is the only rent signal for ~80% of the population.

### Tier 2 — gap (partnership / scrape, flag honestly)
3. **URA Commercial Rental** — office & retail median rent / rental index, quarterly.
   Only via **Realis** (paid) or scraping the URA-SPACE quarterly tables. Until then,
   commercial occupancy-cost stays a residential-proxy (as the packs already note).
4. **Industrial Rental** — JTC J-Space / quarterly industrial rental index (by region).

---

## 3. Target schema (identical at hex9 + hex8)

```
hex9_id / hex8_id            key
rent_resi_psf_med            private-resi median $psf/mo (IDW-smoothed)
rent_resi_n_obs              # contributing projects/contracts
rent_resolution              local (<=800m) | idw (<=2.5km) | none
rent_hdb_med                 HDB median rent $/mo (town-level)           [NEW]
rent_hdb_4r_med              HDB 4-room median $/mo                      [NEW]
rent_hdb_resolution          town | none                                [NEW]
rent_occ_cost_idx            blended occupancy-cost index (resi+HDB, 0-100) [NEW]
roi_cap_per_rent_<cat>       Huff demand ÷ rent (existing, recomputed)
pw1/pw2/max1/max2_rent_*     ring poolings (existing pattern)
```

`rent_resolution` keeps the layer **honest** — a cell tells you whether its rent is
observed locally or interpolated, so downstream never treats an IDW guess as data.

---

## 4. Build approach — hex9 first, then roll up to hex8

1. **Points** — geocode URA rental (SVY21→WGS84) + HDB town centroids; cache to
   `data/external/`.
2. **hex9 aggregate (finest)** — for each of 7,318 hex9 cells, IDW the private-resi
   $psf onto the cell's activity centroid (k=5, p=2, ≤2.5 km); attach HDB town rent
   by the cell's parent HDB-town. Flag `rent_resolution`.
3. **hex8 roll-up** — aggregate the 7 child hex9 cells (activity-weighted mean) **or**
   re-IDW at hex8 centroids — pick whichever the validation gate prefers; they should
   agree within a few %.
4. **Blended occupancy-cost** — `rent_occ_cost_idx` = percentile-blend of resi $psf
   (private hexes) and HDB town rent (HDB hexes), so every populated cell has one
   comparable signal.
5. **Ring features** — `pw1/pw2/max1/max2_rent_resi_psf_med` (reuse `build_pop_weighted`).
6. **ROI** — recompute `roi_cap_per_rent_<cat>` = Huff demand ÷ rent at both scales.

Generalises `build_rent_surface.py` (which already does steps 1–2 + ROI at hex8) to
hex9, plus the HDB join — small, additive change.

---

## 5. Integration

- New: `hex/hex9_rent_surface.parquet` + refreshed `hex/hex8_rent_surface.parquet`.
- **Patch into both masters** (`hex9_all_features`, `hex8_all_features`) the same way
  the places fix patched `pc_cat_` — drop stale `rent_*`/`roi_*`, merge fresh.
- Refresh `feature_catalog` (+ HDB/occ-cost rows), `atlas_manifest`, `DATA_SOURCES`
  (add HDB rent + URA contracts rows), `PLACES`/data catalogs.
- Tag **CHECKPOINT_v5.7.0** ("rental layer: hex9+hex8, +HDB rent").

---

## 6. Validation gates & honest limits

**Gates (frozen before build):**
- range: private-resi $psf in ~$2.5–$9/mo; HDB 4R rent ~$2.3k–$4.0k/mo.
- coverage: every *populated* hex has `rent_resolution != none` (private *or* HDB).
- **known-answer:** highest resi rent = **Orchard / River Valley / CBD-fringe**;
  lowest = **Woodlands / Jurong West / Sembawang**; HDB rent tracks maturity.
- hex8 roll-up ≈ direct hex8 IDW within ~5%.
- dedup/no-leak: rent never enters the **e1/p1 embedding inputs** (it's a probe
  target / ECON-view output, not a representation input) — preserves the exam.

**Honest limits:**
- **Commercial & industrial rent remain gaps** (Realis/JTC) — retail/office
  occupancy-cost stays a residential proxy until a paid feed lands.
- Private-resi rent is **condo/landed only**; HDB rent is **town-level** (not
  per-block) — `rent_resolution` / `rent_hdb_resolution` make this explicit.
- URA medians lag ~1 quarter; refresh quarterly.

---

## 7. Effort
~1 session, CPU-only, no new paid data for Tier 1. Tier 2 (commercial) needs a
Realis subscription or a quarterly URA-SPACE scrape — separate decision.

*Build script: extend `build_rent_surface.py` → emit hex9 + hex8; add
`build_hdb_rent.py` (data.gov.sg). Then patch masters + bump v5.7.*
