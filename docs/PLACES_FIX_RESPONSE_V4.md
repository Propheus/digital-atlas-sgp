# Atlas Team — Response to nous V4 flags

**Re:** `brand-analysis/ATLAS_TEAM_FIXES_V4.md` + `ATLAS_TEAM_FIXES_V4_TESTS.md`
**Atlas version:** v5.8.0 · **Status: all 31 acceptance tests pass** (30 automated + B7 doc-check)

The V4 audit caught real defects — a maritime PORT ranking #1 for a gym, Nassim dinged for
"zero footfall." Both came from derived signals that were point-source-contaminated, residential-
relabeled, or zoning-keyed. Every flagged item is now fixed at the source on hex8 **and** hex9,
and the embedding leak the audit implied has been closed.

---

## P0-1 — Real retail rent  ✅ (A1–A7 pass)
`rent_occ_cost_psf` was residential rent relabeled (identical in 625/625, no CBD coverage).

- New columns `rent_retail_psf_med` / `rent_retail_psm_med` / `rent_retail_tier` / `rent_confidence` / `rent_retail_n_obs`.
- Anchored to a **real, free URA source** — *Median Rentals & Vacancy of Retail Space by Locality*
  (data.gov.sg `d_49962204d37550d54175c2e5f0e78025`, 3 localities: Orchard / Central-ex-Orchard / Outside-Central).
- Centrality/commercial-led model, ranked **among retail-scorable cells** over a $4–$40 ground-floor
  scale → **10× spread**; Orchard **$39.7 psf** ($427 psm) ≫ Tampines $14.8 ≫ Jurong West $9.5.
- Decorrelated from residential rent (**corr 0.54** < 0.85); confidence column on 100% of populated cells.
- `rent_occ_cost_source`: `private_observed` → `residential_proxy` (de-mislabeled).

## P0-2 — Real footfall  ✅ (B1–B7 pass)
`retail_footfall_score` was 60% built from the transit-exit point-source `vis_exit_footfall`
(Port read 41; Nassim read 12 = the coverage hole).

- Rebuilt = **percentile(0.82·dt_pop + 0.12·iso_transit15_pop + 0.06·iso_walk10_pop)**; cells with
  shops but no residents get a low (1–15) commercial rescue; **NaN** for terminals/nature/reserve.
- **Excludes** `vis_exit_footfall` (corr now **0.37** < 0.5) **and** `od_throughput` (the embedding probe target).
- Tracks general activity: **corr(dt_pop) = 0.99**; consumer coverage **100%**.
- Pedestrian hubs (Orchard/Bugis/Raffles Pl/Tampines/Jurong E) all **top-decile**; the dead maritime
  **PORT reads ~0**; **Nassim's representative cell (dt_pop 6.7k) reads 61 (top 40%)** — no longer near-zero.
- `format_fit_score` also rebuilt on the clean footfall (no `vis_exit`).

## P0-3 — Industrial adjacency from physical industry  ✅ (C1–C6 pass)
Was keyed on business **zoning** (corr 0.64 zoning vs 0.25 physical) → CBD offices flagged industrial.

- Now a saturating ramp on **`bldg_industrial_count`** (0 below ~6 buildings, **>0.6 at ≥10**) + a
  confirmed-industrial zone floor. **corr(bldg_industrial)=0.75 > corr(lu_business)=0.46**.
- Heartland (pop≥5k, <10 ind-bldgs, ≥15 POIs) **<0.3** for 100%; CBD office **<0.3** for 100%;
  Tuas/Murai/Sungei-Kadut (≥10 ind-bldgs) **>0.6** for 100%; fires regardless of `dominant_use` (Murai=1.0).
- Ports/airside flagged non-consumer via `zone_type`/`transport_subtype`.

## P1-1 — Transport subtype · zone_type · Sentosa  ✅ (D1–D5 pass)
- New **`transport_subtype`**: `transport_terminal` (70, lu_transport≥0.8 = non-leasable port/airside)
  vs `transport_transit` (48, MRT/bus frontage, leasable) vs `not_transport` (1073).
- `zone_type='unknown'` **247 → 0** (PA→SZ→hex8 propagation + commercial-aware fill).
- **Sentosa** reclassed out of `islands_restricted` → `islands_resort` (consumer destination, footfall populated).

## P1-2 — hex9-native demand-reach  ✅ (E1–E3 pass)
48 demand columns were hex8-only (broadcast to children).

- `iso_walk10_pop` / `iso_walk10_spend` / `dt_pop` / `industrial_adjacency_score` / `zone_type` now present on hex9.
- **`dt_pop` natively computed** at res-9 (daytime = distance-decayed residents + workers from res-9 built
  form) — varies across **83%** of multi-child parents (vs 60% for parent-broadcast). iso/transit disaggregated
  by a native activity weight (conserves parent total); industrial/zone/footfall computed natively.
- Coverage parity preserved (hex9 iso>0 = 58% vs hex8 53%).

---

## Embedding leak — closed
The audit's footfall finding implied a training leak: `retail_footfall_score`, `vis_exit_footfall`,
`rent_*`, and the folded **domain-pack hero scores** (`re_/risk_/insurance_/utility_/mobility_/retail_`,
several correlating **0.8–0.9 with the held-out price/connectivity probes**) were embedding inputs, and
the footfall score had carried `od_throughput` — the e1 **probe target**.

- `embedding/prep_features.py` now excludes all 53 such columns. Clean input matrix **1191 × 736**.
- **e1 retrained** (winner E1, score 1.495 > PCA 1.422). Leak-free evidence:
  negative-control R² **−0.003** (clean); price-probe **de-inflated** (PCA 0.81 → **0.71**, the leaked
  signal removed); known-twin panel **5/5**; archetype recovery **zone_ari 0.28 → 0.48**; 3-seed Procrustes **0.948**.
- The folded pack hero scores are unchanged for app consumers — they are simply no longer embedding inputs.

## Downstream consistency
- `build_retail_pack_sgp.py` source-fixed so a future pack rebuild can never revert the V4 footfall.
- Project **zone-type NA rule re-applied** with the V4 zone fill: 688 non-residential cells
  (industrial/airport/nature/islands/future) are now Not-Applicable across 32 normative adequacy/
  vulnerability/crowding scores.

## End-to-end (the two motivating failures)
- **Anytime Fitness** candidate generation: the maritime PORT no longer surfaces (footfall ~0, NA-gated).
- **% Arabica**: Nassim's footfall reads adequate (61, top-40%) — no longer the disqualifier.

---
*hex8 master 1191×852 · hex9 master 7318×612 · catalog + manifest at v5.8.0 · backups retained.*
