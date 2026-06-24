import re, pathlib
p=pathlib.Path("/home/azureuser/da-sgp/v5/embedding/prep_features.py")
s=p.read_text()
old_exact='''EXCLUDE_EXACT = {"hex8_id", "lat", "lng", "n_children", "n_children_wk",
                 "n_children_tr", "hdb_resale_4r_median_psm", "od_throughput",
                 "adq_default"}'''
new_exact='''EXCLUDE_EXACT = {"hex8_id", "lat", "lng", "n_children", "n_children_wk",
                 "n_children_tr", "hdb_resale_4r_median_psm", "od_throughput",
                 "adq_default", "ca_footfall", "industrial_adjacency_score",
                 "format_fit_score", "vis_exit_footfall"}'''
old_pre='''EXCLUDE_PREFIX = ("cap_", "colo_fit_", "roi_", "parent_", "zone_type",
                  "archetype", "pop_callout", "adq_primary", "adq_worst_factor",
                  "mrt_reach_mode", "dominant_use", "pc_dominant",
                  "best_max", "rent_resolution", "vis_exit_station",
                  "pipe_mrt_name", "cap_best", "dt_class")'''
new_pre='''# nous V4 embedding-leak fix: derived footfall + rent are NOT inputs (they correlate with
# the held-out price/connectivity probes -> inflate recovery). Folded DOMAIN-PACK hero scores
# (re_/risk_/insurance_/utility_/mobility_/retail_) are downstream MODEL OUTPUTS -- same class
# as cap_/roi_/colo_fit_. Original urbanism indices (walkability_score, vibrancy_index, ...)
# are STRUCTURAL inputs and are kept.
EXCLUDE_PREFIX = ("cap_", "colo_fit_", "roi_", "parent_", "zone_type",
                  "archetype", "pop_callout", "adq_primary", "adq_worst_factor",
                  "mrt_reach_mode", "dominant_use", "pc_dominant",
                  "best_max", "rent_", "vis_exit_station",
                  "pipe_mrt_name", "cap_best", "dt_class",
                  "re_", "risk_", "insurance_", "utility_", "mobility_",
                  "retail_", "format_fit", "transport_subtype")'''
assert old_exact in s, "EXACT block not found"
assert old_pre in s, "PREFIX block not found"
s=s.replace(old_exact,new_exact).replace(old_pre,new_pre)
p.write_text(s)
print("patched prep_features.py OK")
# verify new input count
import pandas as pd, numpy as np, importlib.util
spec=importlib.util.spec_from_file_location("pf",p); 
