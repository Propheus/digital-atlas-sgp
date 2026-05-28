# hex_v11 — Transport Adequacy Report

**Built:** 2026-05-28  ·  **Hex resolution:** H3 res 8 (1,191 cells)  ·  **Total pop:** 6,110,000

## Active vs gray-out
- Active cells (pop ≥ 50 OR commercial/dorm activity): **556** / 1191
- Gray-out (sparse): 635 cells

## Composite gap distribution (active cells only)

| Band | Cells | % | Population | % of pop |
|---|---:|---:|---:|---:|
| Excellent | 170 | 30.6% | 3,154,200 | 51.6% |
| Good | 224 | 40.3% | 2,580,586 | 42.2% |
| Moderate | 111 | 20.0% | 301,092 | 4.9% |
| Poor | 33 | 5.9% | 35,302 | 0.6% |
| Critical | 18 | 3.2% | 38,497 | 0.6% |

## Per-factor band distribution (active cells)

| Factor | Excellent | Good | Moderate | Poor | Critical | Median |
|---|---:|---:|---:|---:|---:|---:|
| f_accessibility | 3 | 274 | 144 | 88 | 47 | 0.501 |
| f_distance | 407 | 68 | 44 | 14 | 23 | 0.154 |
| f_last_mile | 61 | 155 | 168 | 95 | 77 | 0.592 |
| f_connectivity | 9 | 124 | 168 | 169 | 86 | 0.681 |
| f_line_pressure | 518 | 9 | 11 | 4 | 14 | 0.000 |
| f_low_frequency | 297 | 37 | 61 | 38 | 123 | 0.225 |
| f_children_gap | 469 | 26 | 52 | 7 | 2 | 0.000 |
| f_low_income_gap | 441 | 54 | 61 | 0 | 0 | 0.094 |
| f_dorm_gap | 496 | 24 | 19 | 5 | 12 | 0.000 |
| f_elderly_gap | 405 | 124 | 19 | 5 | 3 | 0.191 |
| f_fdw_gap | 538 | 11 | 6 | 1 | 0 | 0.047 |

## Top-10 primary_gap_reason among active cells

| Reason | Cells | Pop |
|---|---:|---:|
| few_modes | 249.0 | 3,465,261 |
| last_mile_friction | 134.0 | 1,174,261 |
| low_service_frequency | 72.0 | 268,782 |
| walk_unfriendly | 56.0 | 374,396 |
| overcrowded_lines | 31.0 | 757,648 |
| far_from_transit | 9.0 | 10,191 |
| elderly_isolation | 3.0 | 34,211 |
| dorm_worker_connectivity_gap | 1.0 | 21,369 |
| fdw_off_day_gap | 1.0 | 3,559 |

## Top-20 worst hex cells

| Subzone | Hex | Pop | gap_default | Worst factor | Reason |
|---|---|---:|---:|---|---|
| Lim Chu Kang | dfffff | 844 | 0.965 | f_accessibility | walk_unfriendly |
|  | bfffff | 206 | 0.965 | f_accessibility | walk_unfriendly |
| Changi Airport | 1fffff | 24,477 | 0.965 | f_accessibility | walk_unfriendly |
| Lim Chu Kang | 3fffff | 2,073 | 0.958 | f_distance | far_from_transit |
| Lim Chu Kang | 9fffff | 844 | 0.955 | f_distance | far_from_transit |
| Lim Chu Kang | 5fffff | 534 | 0.953 | f_last_mile | last_mile_friction |
|  | bfffff | 168 | 0.944 | f_distance | far_from_transit |
|  | 1fffff | 483 | 0.931 | f_distance | far_from_transit |
| Murai | 5fffff | 844 | 0.906 | f_connectivity | few_modes |
|  | 5fffff | 332 | 0.900 | f_distance | far_from_transit |
| Murai | 9fffff | 534 | 0.896 | f_connectivity | few_modes |
|  | dfffff | 503 | 0.892 | f_accessibility | walk_unfriendly |
| Wenya | 7fffff | 206 | 0.890 | f_connectivity | few_modes |
| Sentosa | 3fffff | 1,914 | 0.881 | f_distance | far_from_transit |
| Murai | dfffff | 1,846 | 0.877 | f_connectivity | few_modes |
| Lim Chu Kang | 1fffff | 534 | 0.876 | f_last_mile | last_mile_friction |
| Sentosa | 7fffff | 2,082 | 0.868 | f_distance | far_from_transit |
| Murai | 3fffff | 74 | 0.853 | f_accessibility | walk_unfriendly |
| Murai | 5fffff | 206 | 0.846 | f_last_mile | last_mile_friction |
| North-Eastern Islands | 3fffff | 15 | 0.845 | f_accessibility | walk_unfriendly |