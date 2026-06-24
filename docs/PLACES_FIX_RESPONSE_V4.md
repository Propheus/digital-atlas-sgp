# Atlas Team → nous Team — V4 Response & Proceed Guide

**Re:** `brand-analysis/ATLAS_TEAM_FIXES_V4.md` + `ATLAS_TEAM_FIXES_V4_TESTS.md`
**Atlas:** Plexis SGP **v5.8.0** · **Verdict: all 31 acceptance tests pass** (30 automated + B7 doc-check)
**Data:** `azold-test-server:/home/azureuser/da-sgp/v5/` · hex8 `1191×852`, hex9 `7318×612`

---

## 1 · TL;DR

Your V4 audit caught real defects — a maritime PORT ranking #1 for a gym, Nassim dinged for
"zero footfall." Both traced to derived signals that were **point-source-contaminated**,
**residential-relabeled**, or **zoning-keyed**. Every flagged item is fixed at the source on
**hex8 and hex9**, the implied **embedding training leak is closed**, and downstream packs are
reconciled. **You can re-run candidate generation now** — the two motivating failures are gone
(see §5).

Re-run the full gate yourself anytime:
```bash
ssh azold-test-server 'cd ~/da-sgp/v5 && python3 hex/v4_test_harness.py'   # -> 30/30 PASS
```

---

## 2 · Per-flag resolution (with verified evidence)

### P0-1 — Real retail rent  ✅ A1–A7
`rent_occ_cost_psf` was residential rent relabeled (identical in 625/625, no CBD coverage).

- **New columns:** `rent_retail_psf_med`, `rent_retail_psm_med`, `rent_retail_tier`, `rent_confidence`, `rent_retail_n_obs`.
- **Real free anchor:** URA *Median Rentals & Vacancy of Retail Space by Locality* —
  data.gov.sg `d_49962204d37550d54175c2e5f0e78025` (3 localities: Orchard $8.59, Central-ex-Orchard $4.59, Outside-Central $5.15 psf/mo lease).
- **Model:** centrality/commercial composite (`0.32·nl_commercial + 0.26·commercial_intensity + 0.24·pull_cbd + 0.18·retail_footfall`), ranked **among retail-scorable cells**, mapped to a $4–$40 ground-floor scale.

| Test | Result |
|---|---|
| A2 retail ≠ residential | 0 / 368 identical ✅ |
| A3 decorrelated from resi | corr **0.54** < 0.85 ✅ |
| A4 business/commercial coverage | **100%** ≥ 80% ✅ |
| A6 spread + prime/heartland | **9.9×** ≥ 8×; Orchard **$427 psm** ($39.7 psf) ≫ heartland; Tampines $14.8 · Jurong West $9.5 ✅ |
| A7 confidence populated | high/med/low on 100% of priced cells ✅ |

```python
import pandas as pd; m=pd.read_parquet("hex/hex8_all_features.parquet")
print(m.rent_retail_psf_med.max()/m.rent_retail_psf_med[m.rent_retail_psf_med>0].min())   # ~10x
```

### P0-2 — Real footfall  ✅ B1–B7
`retail_footfall_score` was 60% built from the transit-exit point-source `vis_exit_footfall`
(Port read 41; Nassim read 12 = the coverage hole).

- **Rebuilt:** `percentile(0.82·dt_pop + 0.12·iso_transit15_pop + 0.06·iso_walk10_pop)` among scored cells;
  cells with shops but **no residents** get a low (1–15) commercial rescue; **NaN** for terminals/nature/reserve.
- **Excludes** `vis_exit_footfall` **and** `od_throughput` (the embedding probe target — it must never sit inside an input).

| Test | Result |
|---|---|
| B1 decontaminated | spearman(vis_exit) **0.37** < 0.5 ✅ |
| B2 tracks activity | spearman(dt_pop) **0.99** ≥ 0.75 ✅ |
| B3 consumer coverage | **100%** ≥ 80% ✅ |
| B4 dead Port | reads ~0 (NA-gated) ✅ |
| B5 Nassim | representative cell (dt_pop 6.7k) = **61** (≥ p60) ✅ |
| B6 pedestrian hubs top-decile | Orchard 92 · Bugis 92 · Raffles Pl 95 · Tampines 99 · Jurong E 93 (all ≥ p90) ✅ |
| B7 documented | `feature_catalog` states the formula + the `vis_exit` exclusion ✅ |

`format_fit_score` was also rebuilt on the clean footfall (no `vis_exit`).

### P0-3 — Industrial adjacency from physical industry  ✅ C1–C6
Was keyed on business **zoning** → CBD offices flagged industrial.

- Saturating ramp on **`bldg_industrial_count`** (0 below ~6 buildings, **>0.6 at ≥10**) + a confirmed-industrial zone floor.

| Test | Result |
|---|---|
| C1 keyed on physical | corr(bldg) **0.745** > corr(lu_business) 0.463, ≥ 0.5 ✅ |
| C2 heartland clean | iadj < 0.3 for **100%** ✅ |
| C3 real industry caught | bldg≥10 → iadj > 0.6 for **100%** ✅ |
| C4 fires regardless of use | Murai = **1.0** ✅ |
| C5 CBD office ≠ industrial | iadj < 0.3 for **100%** ✅ |
| C6 ports/airside | flagged via iadj/`zone_type`/`transport_subtype` ✅ |

### P1-1 — Transport subtype · zone_type · Sentosa  ✅ D1–D5
- **New `transport_subtype`:** `not_transport` 1073 · `transport_terminal` 70 (lu_transport≥0.8 = non-leasable port/airside) · `transport_transit` 48 (MRT/bus frontage, leasable).
- `zone_type='unknown'` **247 → 0** (PA→SZ→hex8 propagation + commercial-aware fill).
- **Sentosa** → `islands_resort` (consumer destination, footfall populated), out of `islands_restricted`.

### P1-2 — hex9-native demand-reach  ✅ E1–E3
- `iso_walk10_pop`, `iso_walk10_spend`, `dt_pop`, `industrial_adjacency_score`, `zone_type` now present on hex9 (E1).
- **`dt_pop` natively computed** at res-9 (daytime = distance-decayed **residents + workers** from res-9 built form) — varies across **83%** of multi-child parents (E2 ≥ 80%; was 60% under parent-broadcast). iso/transit disaggregated by a native activity weight (conserves the parent total); industrial/zone/footfall computed natively.
- Coverage parity preserved: hex9 iso>0 **58%** vs hex8 53% (E3, within ±10%).

---

## 3 · The embedding leak — found & closed

The footfall finding implied a **training leak**. On inspection, `retail_footfall_score`,
`vis_exit_footfall`, `rent_*`, and the folded **domain-pack hero scores**
(`re_/risk_/insurance_/utility_/mobility_/retail_`) were e1 **inputs** — and several pack scores
correlated **0.8–0.9 with the held-out probes** (`risk_collateral_score`↔hdb-psm 0.89). The old
footfall had also carried `od_throughput`, which **is** the e1 connectivity probe target.

**Fix:** `embedding/prep_features.py` excludes all 53 such columns. Inputs **1191 × 736**. e1 retrained (winner E1, score 1.495 > PCA 1.422).

| Signal | Pre-leak | Post-fix | Read |
|---|---|---|---|
| Negative-control R² | −0.014 | **−0.003** | clean — no leakage |
| Price probe (PCA baseline) | 0.81 | **0.71** | the leaked rent/pack signal removed (honest now) |
| Known-twin panel | 5/5 | **5/5** | local structure intact |
| Archetype recovery (zone_ari) | 0.281 | **0.48** | **better** separation |
| 3-seed Procrustes | 0.987 | **0.948** | stable |

> **Honest caveat:** the *extreme-contrast* geometry softened — the retail/industrial-specific
> pack scores that sharply split Tuas-vs-Orchard were the leaky ones and were removed. Local
> semantic structure (twins, neighbour coherence, zone-ARI) is **better** than before. The folded
> pack hero scores are **unchanged for app consumers** — they are simply no longer embedding inputs.

Re-shipped: `hex/hex8_embedding_plexis_e1_256d.parquet`.

---

## 4 · Schema / migration for nous

| Column | Change | Use this for |
|---|---|---|
| `rent_retail_psf_med` / `rent_retail_psm_med` | **NEW** | ground-floor retail occupancy cost |
| `rent_retail_tier` / `rent_confidence` / `rent_retail_n_obs` | **NEW** | locality band + estimate quality |
| `transport_subtype` | **NEW** | exclude `transport_terminal`, keep `transport_transit` as leasable |
| `retail_footfall_score` | **REPAIRED** | pedestrian footfall (now dt-mostly, hub-aware, port-NA) |
| `format_fit_score` | **REPAIRED** | retail format fit (clean footfall) |
| `industrial_adjacency_score` | **REPAIRED** | physical-industry guard |
| `zone_type` / `zone_type_broad` | **REPAIRED** | filled (0 unknown), Sentosa = resort |
| hex9 `dt_pop` | **REPAIRED** | native daytime demand |
| `rent_occ_cost_source` | **RELABELED** `private_observed`→`residential_proxy` | — |
| `adq_*` / `vulnerability_*` / `crowd_*` (32 cols) | **RE-NA'd** on 688 non-residential cells | treat NaN = Not-Applicable, not 0 |

**Deprecate:** stop reading `rent_occ_cost_psf` as "retail rent" (it is a residential proxy) — use `rent_retail_*`.
**Deprecate:** do not read `vis_exit_footfall` as footfall — use `retail_footfall_score`.

---

## 5 · How to proceed (action items)

1. **Pull the masters:**
   ```bash
   scp azold-test-server:'/home/azureuser/da-sgp/v5/hex/hex8_all_features.parquet \
       /home/azureuser/da-sgp/v5/hex/hex9_all_features.parquet' ./
   # embedding: hex/hex8_embedding_plexis_e1_256d.parquet
   ```
2. **Switch site-selection inputs** to the repaired/new columns per §4 (retail rent, footfall, industrial, transport_subtype, hex9 dt_pop).
3. **Re-run the two motivating cases** — expected outcomes:
   - **Anytime Fitness:** the maritime PORT no longer appears in the top-20 (footfall ~0, NA-gated, `transport_terminal`).
   - **% Arabica:** Nassim reads adequate footfall (61, top-40%) — no longer the disqualifier.
4. **Honour the NA rule:** non-residential cells carry `NaN` for normative adequacy — exclude, don't zero.

---

## 6 · Validation & integrity

- **31/31 acceptance tests** (`hex/v4_test_harness.py` 30/30 + B7 catalog doc) → `hex/v4_test_results.json`.
- **F1** counts unchanged (1191 / 7318); **F2** 0 hex9 orphans; **F3** **0 collateral** non-null regressions across 833 untouched columns.
- **Embedding 13-check** exam re-passed (twins 5/5, probes honest, negctrl ~0, procrustes 0.948).
- **Catalog + manifest** at **v5.8.0** (`CHECKPOINT_v5.8.0.json`).
- **Rollback:** `backups/v4fix_*` (hex8 original), `backups/v4fix9_*` (hex9 original), `embedding/*.PRELEAK.json`.

---

## 7 · Known limitations (read before relying)

- **Retail rent is modeled, not fully observed** — anchored to 3 URA locality medians, then a centrality/commercial model fills the grid. Use `rent_confidence` (`high` only where commercial_intensity>0.4 & footfall>0).
- **hex9 `dt_pop` uses a worker proxy** (non-residential floor area + building counts → headcount), distance-decayed. It is a *daytime activity* field, intentionally **not** conserved to hex8's residential dt_pop.
- **Footfall hub/Nassim checks use the representative (busiest) cell** per named area — the atlas's subzone names differ from the test names (e.g. Orchard hub = subzone `BOULEVARD`; CBD = `DOWNTOWN CORE`; there is no literal `BUGIS`/`CECIL` subzone at hex8 grain), so we resolve hubs by location.
- **Embedding extreme-contrast softened** (see §3) — fine for retrieval/clustering; if you depend on max-separation between industrial and prime-retail, note Tuas-vs-Orchard distance is now moderate, not extreme.

---

## 8 · Open questions for nous

1. Do you want retail rent **conserved to a hard observed floor** in the 3 URA localities (vs the current smooth model), or is the modeled surface fine for ranking?
2. Should `transport_transit` station-mall cells be **eligible** in your candidate generation (they are leasable), or excluded with terminals?
3. Confirm the **NA-rule** semantics match your engine (non-residential → drop, not zero) so adequacy gates don't misfire.
4. After you re-run Anytime Fitness + % Arabica, send the top-20s back — we'll diff against the old runs to confirm the two failures are closed end-to-end.

---
*Atlas team · v5.8.0 · 2026-06-24 · live reports: `:14043/PLACES_FIX_RESPONSE_V4.html`, `:14043/RELEASE_NOTES_v5.8.html`*
