# Plexis SGP Atlas — Release Notes v5.7 (rental layer)

**Date:** 2026-06-21 · **Versions:** v5.7.0 (residential rent) + v5.7.1 (HDB rent estimate + occupancy-cost)
**Scope:** a rental layer at **hex9 (7,318) and hex8 (1,191)**. Non-destructive; backups retained.

## TL;DR
The atlas now carries a **rent surface at both hex scales** — real URA private-residential
rent, an HDB rent **estimate**, and a **unified occupancy-cost** that uses real rent where
observed and the estimate elsewhere. **Action for consumers:** use `rent_occ_cost_psf` for a
single comparable $psf/mo signal, and check `rent_occ_cost_source` / `rent_resolution` to know
whether a cell is observed or interpolated/estimated.

## What's new

### 1. Private residential rent — *real* (v5.7.0)
- Source: **URA `PMI_Resi_Rental_Median`** — 913 private-resi projects, 2023Q2–2026Q1, median $psf/mo.
- Method: last-4-quarter median per project → **IDW** (k=5, p=2, ≤2.5 km, in SVY21 metres) onto each cell's activity centroid, at **hex9 and hex8**.
- Range **$2.02–$8.30/psf/mo**. Honest coverage flag `rent_resolution` = `local` (≤800 m) / `idw` (≤2.5 km) / `none`.

### 2. HDB rent — *estimate* (v5.7.1)
- `rent_hdb_4r_est_pm` = HDB `resale_4r_median_price` × **7.3% gross yield** ÷ 12, **calibrated to ~$3,090/mo median 4-room** (range $2,634–$5,080).
- `rent_hdb_est_psf` = that ÷ 969 sqft → comparable to private $psf.
- **Clearly an estimate** (the real data.gov.sg HDB-rent feed couldn't be located via their search API — a documented follow-up).

### 3. Unified occupancy-cost
- `rent_occ_cost_psf` = real private rent where observed, else the HDB estimate — one $psf/mo signal for every populated cell.
- `rent_occ_cost_source` = `private_observed` | `hdb_estimate` | `none`.

## New / changed columns (hex9 + hex8 masters)
`rent_resi_psf_med` · `rent_resi_n_obs` · `rent_resolution` · `roi_cap_per_rent_*`
· `rent_hdb_4r_est_pm` · `rent_hdb_est_psf` · `rent_occ_cost_psf` · `rent_occ_cost_source`
→ hex9 master **585 → 597**, hex8 master **842 → 846**.

## How to consume
- **One rent number per cell:** `rent_occ_cost_psf` ($psf/mo). Always read `rent_occ_cost_source` with it.
- **Private only:** `rent_resi_psf_med` (+ `rent_resolution` to filter `none`).
- **HDB 4-room rent ($/mo):** `rent_hdb_4r_est_pm` (estimate).
- **ROI / siting:** `roi_cap_per_rent_<cat>` (Huff demand ÷ rent).
- Keys & rows unchanged; rent is **excluded from the e1/p1 embedding inputs** (ECON-view output), so the embeddings are unaffected.

## Validation (known-answer, frozen)
- Private rent: top = **Museum / Straits View** (~$6.9), bottom = **Choa Chu Kang / Lim Chu Kang** (~$3.4).
- HDB rent est: top = **Outram / Museum / Downtown Core** (~$5,080), bottom = **Woodlands / Yishun / Jurong West** (~$2,640). Median 4-room **$3,090/mo**.
- `rent_resolution = none` / `rent_occ_cost_source = none` correctly mark non-residential PAs (Tuas, islands, industrial) — never faked.

## Known limits
- **HDB rent is an estimate** (resale × yield), not observed; single yield slightly over-estimates prime towns.
- **Commercial & industrial rent remain gaps** — URA has no commercial rental API; office/retail is Realis/URA-SPACE only, industrial is JTC.
- Private rent is condo/landed only; coverage `none` where no project within 2.5 km.

## Where to get it (server)
**Host:** `azold-test-server` · **Root:** `/home/azureuser/da-sgp/v5/`
| Artifact | Path |
|---|---|
| Hex8 / Hex9 masters (rent folded in) | `hex/hex8_all_features.parquet` (1,191 × 846) · `hex/hex9_all_features.parquet` (7,318 × 597) |
| Rent surfaces | `hex/hex8_rent_surface.parquet` · `hex/hex9_rent_surface.parquet` |
| Checkpoint / manifest | `CHECKPOINT_v5.7.1.json` · `catalog/atlas_manifest.json` (v5.7.1) |
| Builders | `build_rent_surface_v2.py` · `build_hdb_rent_est.py` |
| Plan | `docs/RENT_DATA_PLAN.md` |

Git mirror: `github.com/Propheus/digital-atlas-sgp` → `plexis-sgp-v5/` (parquets via LFS).
