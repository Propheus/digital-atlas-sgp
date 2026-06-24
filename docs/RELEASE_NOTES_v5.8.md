# Plexis SGP Atlas — v5.8.0 Release Notes

**Theme:** nous V4 site-selection fixes (hex8 + hex9) + embedding leak closure
**Date:** 2026-06-24 · **Supersedes:** v5.7.1

v5.8.0 closes the defects from the nous V4 site-selection audit (`ATLAS_TEAM_FIXES_V4.md`)
across the hex8 **and** hex9 masters, and retrains the e1 embedding leak-free. **All 31 acceptance
tests pass** (30 automated in `hex/v4_test_harness.py` + B7 catalog doc-check).

## Highlights
| Area | Before | After (v5.8.0) |
|---|---|---|
| Retail rent | residential rent relabeled, no CBD | real URA-anchored model, **10× spread**, Orchard $40 ≫ heartland |
| Footfall | 60% transit-exit point-source; Port=41, Nassim=12 | dt-mostly + percentile; hubs top-decile, **Port ~0, Nassim 61**, corr(dt_pop)=0.99 |
| Industrial adjacency | business-zoning keyed (CBD flagged) | **physical buildings** (corr 0.75 > 0.46) |
| Transport / zone | single 'transport' bucket; 247 unknown zones | `transport_subtype` (terminal/transit); **0 unknown**; Sentosa → resort |
| hex9 demand | broadcast from hex8 | **native dt_pop** (E2 83%) + disaggregated reach |
| Embedding e1 | rent/footfall/pack-scores were inputs | **leak-free**: 53 cols excluded, negctrl −0.003, zone_ari 0.28→0.48 |

## New / changed columns
- **Added (hex8 + inherited hex9):** `rent_retail_psf_med`, `rent_retail_psm_med`, `rent_retail_tier`,
  `rent_confidence`, `rent_retail_n_obs`, `transport_subtype`.
- **Repaired:** `retail_footfall_score` (decontaminated), `format_fit_score` (clean footfall),
  `industrial_adjacency_score` (physical), `zone_type`/`zone_type_broad` (filled + Sentosa),
  `rent_occ_cost_source` (de-mislabeled), hex9 `dt_pop` (native).
- **Re-NA'd by zone rule:** 32 normative `adq_*`/`vulnerability_*`/`access_vuln*`/`crowd_*` columns
  set Not-Applicable on 688 non-residential cells.

## Embedding
- `embedding/prep_features.py` excludes derived footfall + `rent_*` + domain-pack hero scores +
  `od_throughput`/`vis_exit_footfall`. Inputs **1191 × 736**.
- e1 retrained → shipped `hex/hex8_embedding_plexis_e1_256d.parquet` (winner E1, 256-d). 13-check exam:
  twins 5/5, probes recover honestly (hdb 0.80 / od 0.86 / adq 0.96), **negctrl −0.003**, procrustes 0.948.
- Note: the extreme-contrast geometry softened (the retail/industrial-specific pack scores that sharply
  separated Tuas-vs-Orchard were leaky and removed); local semantic structure (twins, coherence, zone_ari)
  is **better** than before.

## Files
- Builders: `places_fix/nous_v4_hex8.py`, `nous_v4_hex9.py`; `places_fix/refold_v4.py`.
- Tests: `hex/v4_test_harness.py` (31 checks) → `hex/v4_test_results.json`.
- Catalog: `build_catalog.py` (+9 V4 descriptions) → `catalog/*` at v5.8.0; `CHECKPOINT_v5.8.0.json`.
- Response: `docs/PLACES_FIX_RESPONSE_V4.md`.
- Backups: `backups/v4fix_*` (hex8), `backups/v4fix9_*` (hex9), `embedding/*.PRELEAK.json`.

## Integrity
- hex8 1191×852, hex9 7318×612 — no cells lost; 0 hex9 orphans.
- F3 regression: **0 collateral** non-null drops across 833 untouched columns (fix-targets + zone-NA cols excluded).
