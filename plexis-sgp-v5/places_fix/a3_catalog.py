import pathlib, json, time
ROOT=pathlib.Path("/home/azureuser/da-sgp/v5")
p=ROOT/"build_catalog.py"; s=p.read_text()
anchor='    "rent_retail_n_obs": dict(description="URA observed retail-rent records backing the cell\'s locality tier (nous V4).", units="count", source_stage="V4"),'
if "rent_retail_locality_obs_psf" not in s:
    add='''    "rent_retail_locality_obs_psf": dict(description="OBSERVED URA median retail rent for the cell's locality ($psf/mo, latest qtr) — the defensible ABSOLUTE anchor (Orchard $8.59 / Central-ex-Orchard $4.59 / Outside-Central $5.15). Use this for absolute figures; use rent_retail_psf_med for within-grid ranking. (nous V5/A3).", units="$psf/mo", source_stage="V5"),
    "rent_retail_locality_obs_psm": dict(description="OBSERVED URA median retail rent for the locality in $psm/mo = obs_psf * 10.764 (nous V5/A3).", units="$psm/mo", source_stage="V5"),
    "rent_retail_vacancy_pct": dict(description="OBSERVED URA retail vacancy rate for the cell's locality, latest quarter (Orchard 6.5 / Central-ex 8.2 / Outside-Central 6.4). Demand-side signal (nous V5/A3).", units="%", source_stage="V5"),'''
    s=s.replace(anchor, anchor+"\n"+add); p.write_text(s); print("patched build_catalog.py +3 A3 cols")
ck={"version":"5.8.1","generated_at":time.strftime("%Y-%m-%dT%H:%M:%S"),
 "change":"nous V5 optional asks: A2 catalog consistency confirmed, A3 observed URA rent anchors added",
 "detail":["A1 measured pedestrian footfall: DECLINED (no telco/GPS/SDK/counter data source) — modeled retail_footfall_score retained",
   "A2 store_perf_all catalog<->disk: already consistent in v5.8.0 (0/50 datasets missing; store_perf not listed)",
   "A3 added rent_retail_locality_obs_psf/psm + rent_retail_vacancy_pct (observed URA anchors); modeled rent_retail_psf_med kept for ranking (literal conservation rejected: inverts Orchard, breaks A6 spread)"]}
json.dump(ck,open(ROOT/"CHECKPOINT_v5.8.1.json","w"),indent=1); print("created CHECKPOINT_v5.8.1.json")
