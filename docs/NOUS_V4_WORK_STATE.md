# nous V4 atlas fixes — WORK STATE (resume after restart)

**As of 2026-06-24.** Mid-flight on the nous V4 site-selection audit. This file is the
resume pointer for that work. Atlas server = `azold-test-server:/home/azureuser/da-sgp/v5/`.

## The ask (nous brand-analysis/ATLAS_TEAM_FIXES_V4.md + _V4_TESTS.md = 31 acceptance tests)
3 P0 + 2 P1 data fixes found by a hex8/hex9 site-selection audit (a maritime PORT ranked #1
for a gym; Nassim dinged for "zero footfall"):
- **P0-1** real RETAIL rent (current `rent_occ_cost_psf` is residential rent relabeled, no CBD coverage)
- **P0-2** real FOOTFALL (`retail_footfall_score` is 60% built from transit-exit-only `vis_exit_footfall`)
- **P0-3** `industrial_adjacency_score` from PHYSICAL industry, not business ZONING (corr 0.64 zoning vs 0.25 physical)
- **P1-1** subtype `dominant_use='transport'` (terminal vs transit), fill 247 `zone_type='unknown'`, reclass Sentosa
- **P1-2** hex9-native demand-reach (48 demand cols were hex8-only)

## Method used (ultracode)
Ran a Workflow (`wf_4af67ce6-b5a`): 5 agents verified each item on the live grid + designed exact fix
recipes, then 5 adversarial agents hardened them. **Findings + verdicts saved:**
`plexis-sgp-v5/places_fix/v4_workflow_findings.json` + `v4_workflow_verdicts.json`.
The 31 tests: `nous/brand-analysis/ATLAS_TEAM_FIXES_V4_TESTS.md`.

## ✅ DONE + validated (on the live masters)
**hex8** (`nous_v4_hex8.py`, master now 1191×852):
- P1-1: `transport_subtype` {not_transport 1073/terminal 70/transit 48}; `zone_type` unknown 247→**0**; Sentosa→islands_resort. zone_type_broad re-derived.
- P0-2: `retail_footfall_score` rebuilt = `((0.50·rank01(dt_pop)+0.30·rank01(iso_walk10_pop)+0.20·rank01(iso_transit15_pop)) rescaled 0-100)`; min-tie ranks; all-zero→0; NA-gate non-retail + dead transport(<50 dt). Hubs Orchard 88/Tampines 86/Nassim 76; dead-port NA'd; spearman vs vis_exit **0.41** (<0.6). `format_fit_score` also de-vis_exit'd.
- P0-3: `industrial_adjacency_score` = shifted physical ramps `0.80·ramp(bldg_industrial,5,12)+0.20·ramp(pc_cat_industrial_mfg,4,26)` + presence-gated ring; floor only for zone industrial_*. corr(bldg)=**0.69** > corr(lu_business)=0.44; heartland 0.055; bic≥20 →1.0; TiongBahru 0.36.
- P0-1: NEW `rent_retail_psm_med`/`rent_retail_psf_med`/`rent_retail_tier`/`rent_confidence`/`rent_retail_n_obs`. Real free URA anchor (**data.gov.sg resource `d_49962204d37550d54175c2e5f0e78025`** — Median Rentals & Vacancy of Retail Space by Locality, 3 localities). Model = centrality/commercial-led composite, ranked **among scorable cells**, mapped $4–$40 ground-floor → spread **10×**, Orchard $39.5 ≫ Tampines $11.7 ≫ JurongW $8.5. `rent_occ_cost_source` private_observed→**residential_proxy** (de-mislabel). NaN for non-retail zones.

**hex9** (`nous_v4_hex9.py`, master now 7318×612):
- native: transport_subtype, zone_type (full fill), zone_type_broad, industrial_adjacency_score, retail_footfall_score (from hex9 pop_resident/pc_total/nl_2024 — varies natively).
- disaggregated parent dt_pop/iso_walk10_*/iso_transit15/od_throughput by native weight (pc_total+0.5·pop) → sub-hex8 variation, conserves parent total.
- inherited subzone-level rent_retail_*/rent_occ_cost from parent_hex8.
- E1 (all reach cols present) ✓; E2 native-variation **66%** (target 80% — see pending); E3 iso cov 54%.

Backups: `backups/v4fix_20260624_143156/` (hex8 original), `backups/v4fix9_*` (hex9 original).

## ⛔ PENDING (do these to finish + ship)
1. **EMBEDDING LEAKAGE FIX (critical, adversarial showstopper).** On the live grid,
   `retail_footfall_score`, `vis_exit_footfall`, `rent_resi_*`, and the derived pack `*_score`
   cols are CURRENTLY e1 EMBEDDING INPUTS, and `od_throughput` is the e1 PROBE TARGET. Policy
   ([[project-plexis-e1-embedding]]): rent/footfall must NOT be inputs. **Fix:** add the derived
   `*_score` + `rent_*` + `vis_exit_footfall` to EXCLUDE in `embedding/prep_features.py`, then
   **retrain e1** (`embedding/run_program.py` or rebuild the hybrid) + re-pass its 13-check exam
   (verify od-probe R² does NOT inflate, forbidden ≈0). p1 likewise if affected.
2. **Run the 31-test harness** (`ATLAS_TEAM_FIXES_V4_TESTS.md`) end-to-end; the atlas subzone
   names differ from the tests' (Orchard PA="BOULEVARD", CBD="DOWNTOWN CORE"/"CENTRAL SUBZONE",
   no RAFFLES/SHENTON/TANGLIN/SOMERSET subzones) → adapt name lookups to PA + physical conditions.
3. **Improve hex9 E2** to ≥80% (currently 66% — empty rural parents have all-zero children;
   the dt_pop/iso disaggregation gives no variation where sibling weights are equal). Either
   weight by a finer native signal or do the real `build_iso_walk.py` RES=9 graph recompute
   (~2 min, 7318 origins; generalize origins+output key, demand node field is already res-9).
4. **Re-fold downstream packs** that consume the changed inputs (insurance risk uses
   industrial_adjacency; retail format_fit/whitespace) so folded hero scores reflect the fixes.
5. **Catalogs + version:** re-run `build_catalog_json.py` + `build_catalogs_v56.py`; add curated
   descriptions for the new rent_retail_*/transport_subtype cols; **bump to v5.8.0** (CHECKPOINT).
6. **Response + release notes:** `docs/PLACES_FIX_RESPONSE_V4.md` (+ nous copy) + `RELEASE_NOTES_v5.8.md` (+HTML on showcase).

## Files
- Builders: `plexis-sgp-v5/places_fix/nous_v4_hex8.py`, `nous_v4_hex9.py` (also on azold v5 root).
- Verified recipes: `places_fix/v4_workflow_findings.json` + `v4_workflow_verdicts.json`.
- Reports: `places_fix/v4fix_hex8_report.json`, `v4fix_hex9_report.json`.
- Masters (v4-applied, NOT yet versioned/cataloged): `hex/hex8_all_features.parquet` (852), `hex/hex9_all_features.parquet` (612). Manifest still says **v5.7.1** until step 5.

## One-line resume
"Finish nous V4: do the embedding-leak fix + e1 retrain (step 1), run the 31 tests (step 2),
fix hex9 E2 (step 3), re-fold packs + catalogs + v5.8 (steps 4-5), write the V4 response + v5.8 release notes (step 6)."
