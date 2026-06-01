# Population recalibration + dorm placement (2026-06-01)

Calibrated to official SingStat June-2024 figures and placed migrant-worker
dormitory population at real dorm locations.

- resident     = 4,179,800   (uniform rescale ×0.992167 from prior 4,212,800)
- non-resident = 1,857,100
- total        = 6,036,900
- pop_dorm     = 439,198  (DASL H2-2024 licensed beds; NEW column; SUBSET of
                 non-resident, allocated equally across 1,121 geocoded dorm
                 points / 399 hex9 cells. 663 of 1,784 MOM dorms lacked
                 geocodes and were dropped; total preserved across the rest.)

Changed columns (verified faithful via reproduce-gate; all else byte-identical):
  base pop (9) + pop_dorm + ring1/2_pop_resident/nonresident +
  density_pressure + syn_density_x_amenities + pw1/2 & max1/2_density_pressure.
Layer parquets synced; build_all_features reproduces master (max|Δ|=2e-16).

Scripts: build_non_residents_dorm.py, recon_master.py, sync_layers.py.
Rollback: /home/azureuser/da-sgp/v4_predorm_backup.
