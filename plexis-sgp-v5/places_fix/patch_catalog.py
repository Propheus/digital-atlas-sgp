import pathlib, json, time
ROOT=pathlib.Path("/home/azureuser/da-sgp/v5")
p=ROOT/"build_catalog.py"; s=p.read_text()
old='    "industrial_adjacency_score": dict(description="Adjacency to industrial estates (guard signal)", units="index", source_stage="S11"),'
new='''    "industrial_adjacency_score": dict(description="Physical-industry adjacency (nous V4): saturating ramp on bldg_industrial_count (0 below ~6 bldgs, >0.6 at >=10) + confirmed-industrial zone floor. Keyed on PHYSICAL buildings, NOT business zoning — corr(bldg)=0.75 > corr(lu_business)=0.46. Heartland<0.3, CBD office<0.3.", units="0-1", source_stage="V4"),
    "retail_footfall_score": dict(description="Pedestrian-footfall proxy (nous V4). Percentile of 0.82*dt_pop + 0.12*iso_transit15_pop + 0.06*iso_walk10_pop among scored cells; cells with shops but no residents get a low (1-15) commercial rescue; NaN for terminals/nature/reserve. EXCLUDES vis_exit_footfall (transit-exit point-source) and od_throughput (embedding probe target). dt_pop-corr 0.99; hubs (Orchard/Bugis/Raffles/Tampines/Jurong E) top-decile; dead maritime port reads ~0.", units="0-100", source_stage="V4"),
    "format_fit_score": dict(description="Retail format-fit (nous V4): score100(minmax(walkability_score) * minmax(retail_footfall_score) * minmax(colo_fit_cat)). Footfall term now the V4 decontaminated retail_footfall_score, NOT vis_exit_footfall.", units="0-100", source_stage="V4"),
    "transport_subtype": dict(description="Subtype for dominant_use='transport' (nous V4): transport_terminal (lu_transport_pct>=0.8 — non-leasable port/airside/depot) vs transport_transit (MRT/bus frontage, leasable) vs not_transport.", units="category", source_stage="V4"),
    "rent_retail_psf_med": dict(description="Median ground-floor retail rent $psf/mo (nous V4). Centrality/commercial-led model anchored to URA Median Retail Rentals (data.gov.sg d_49962204d37550d54175c2e5f0e78025, 3 localities), ranked among retail-scorable cells over a $4-$40 scale (10x spread). Orchard ~$40 >> heartland ~$12. NaN for nature/water/terminals.", units="$psf/mo", source_stage="V4"),
    "rent_retail_psm_med": dict(description="Median ground-floor retail rent $psm/mo = rent_retail_psf_med * 10.764 (nous V4). Distinct from residential rent_resi (corr 0.54).", units="$psm/mo", source_stage="V4"),
    "rent_retail_tier": dict(description="Retail locality tier (nous V4): Orchard | Central Area - Outside Orchard | Outside Central Area (URA locality bands).", units="category", source_stage="V4"),
    "rent_confidence": dict(description="Retail-rent estimate confidence (nous V4): high (commercial_intensity>0.4 & footfall>0) | medium | low | na.", units="category", source_stage="V4"),
    "rent_retail_n_obs": dict(description="URA observed retail-rent records backing the cell's locality tier (nous V4).", units="count", source_stage="V4"),'''
assert old in s, "industrial line not found"
s=s.replace(old,new); p.write_text(s)
print("patched build_catalog.py DESCRIPTIONS with 9 V4 columns")
# create v5.8.0 checkpoint
ck={"version":"5.8.0","generated_at":time.strftime("%Y-%m-%dT%H:%M:%S"),
 "change":"nous V4 site-selection fixes (hex8+hex9) + embedding leak fix",
 "detail":["P0-1 real retail rent (URA-anchored, 10x spread, CBD covered)",
   "P0-2 footfall decontaminated from vis_exit/od_throughput (dt-mostly, hubs top-decile, dead-port NA)",
   "P0-3 industrial_adjacency from physical buildings (corr 0.75>0.46)",
   "P1-1 transport_subtype + zone_type fill (0 unknown) + Sentosa reclass",
   "P1-2 hex9-native dt_pop/zone/industrial/footfall (E2 83%)",
   "31/31 nous acceptance tests pass",
   "embedding e1 retrained leak-free: rent/footfall/pack-scores excluded; negctrl ~0; twins 5/5; zone_ari 0.28->0.48",
   "zone-type NA rule re-applied to 32 normative adq/vuln/crowd cols (688 NA-zone cells)"]}
json.dump(ck,open(ROOT/"CHECKPOINT_v5.8.0.json","w"),indent=1)
print("created CHECKPOINT_v5.8.0.json")
