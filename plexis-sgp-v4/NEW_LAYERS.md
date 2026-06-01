# hex8 new layers (2026-06-01)

Three standalone layers added to hex8 master only (hex9/subzone unchanged; +52 cols, 549->601).

## OD matrix (LTA DataMall, 2026-04) — 13 cols, prefix od_
Source: Passenger Volume by OD Bus Stops + Train Stations (weekday, monthly totals).
Bus stops via DataMall BusStops API; train codes via cheeaun/sgraildata sg-rail.geojson
(interchange codes joined by '-'). 100% of bus (88.3M) + train (63.4M) weekday trips mapped.
Full sparse hex8->hex8 matrix at data/lta_od/hex8_od_matrix.parquet (trips_wd/am/pm).
Per-hex8: od_out/in/net/self_trips, od_throughput, od_dest_entropy, od_self_containment,
od_am_pm_out_ratio, od_*_am/pm, od_n_dest_hex. 547 transit-served hexes.

## Commercial activity index — 6 cols, prefix ca_ + commercial_activity_index
Footfall-weighted economic activity, DISTINCT from supply-only commercial_intensity (corr 0.84).
Components (minmax, averaged): ca_nl (nl_2024), ca_spend (nl_commercial_indicator),
ca_taps (bus+train daily taps), ca_places (office+retail+f&b+services), ca_footfall (od_throughput).

## NVIDIA Nemotron personas — 33 cols, prefix nvp_
Source: nvidia/Nemotron-Personas-Singapore (148k synthetic personas, CC-BY-4.0). PA-resolution
ONLY (48 PAs) -> broadcast to hex8 by parent_pa. All 48 NVIDIA PAs matched atlas; 7 atlas PAs
(water catchment/marina/islands) have no personas (zero-filled). Distributions: age bands, sex,
marital, education, occupation (10), industry (10), nvp_affluence_idx, nvp_persona_n, nvp_low_n
(<30 personas: Tuas, Tengah, Boon Lay, etc.). Narrative text fields NOT spatialized.

Build scripts: build_od_hex8.py, build_commercial_activity_hex8.py, build_personas_hex8.py.
build_all_features.py patched to merge the 3 (od/ca/nvp). Rollback: v4_prelayers_backup.
