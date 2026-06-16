"""
Fold the 5 domain packs' 39 hero scores into the canonical masters (in place).
  hex8_all_features.parquet     801 -> 840
  subzone_all_features.parquet  389 -> 428  (parity; pack rollups, NaN for non-populated)
Backs up originals, appends curated rows to feature_catalog.parquet, validates.
Run build_catalog_json.py afterwards to regenerate the JSON catalogs + manifest.
"""
import pandas as pd, time, shutil
from pathlib import Path

V5 = Path("/home/azureuser/da-sgp/v5")
BK = V5 / "backups" / f"prefold_{time.strftime('%Y%m%d_%H%M%S')}"
BK.mkdir(parents=True, exist_ok=True)

# fixed pack order -> hero score columns (39 total)
PACKS = ["retail", "realestate", "utilities", "transport", "insurance"]
ADMIN = {"hex8_id", "subzone_c", "parent_subzone", "parent_subzone_name",
         "parent_pa", "parent_region", "zone_type_broad", "n_hex", "pop_resident"}

DESC = {
 # retail
 "retail_whitespace_score":"Retail white-space — unmet, winnable demand for a new store (0–100)",
 "retail_competition_pressure":"Competition pressure from existing same-format retail (0–100)",
 "format_fit_score":"Best-fit store format (kiosk→flagship) suitability (0–100)",
 "retail_cannibalization_score":"Self-cannibalisation risk vs own-brand nearby outlets (0–100)",
 "retail_delivery_score":"Dark-store / delivery viability (0–100)",
 "retail_footfall_score":"Footfall / visit potential (0–100)",
 "rent_demand_tier":"Demand-vs-rent tier (residential-rent proxy)",
 # real estate
 "re_feasibility_score":"Development feasibility — FAR headroom × buildability (0–100)",
 "re_livability_score":"Neighbourhood livability / quality (0–100)",
 "re_momentum_score":"Momentum / gentrification signal (0–100)",
 "re_enbloc_score":"En-bloc redevelopment upside (0–100)",
 "re_collateral_score":"Mortgage collateral tier (0–100)",
 "re_yield_proxy":"Rental-yield proxy (0–100)",
 "re_lease_decay_penalty":"HDB lease-decay penalty (0–100)",
 # utilities
 "utility_load_score":"Relative electricity load (0–100)",
 "utility_load_growth_score":"Projected load growth (0–100)",
 "utility_water_score":"Water-demand estimate (0–100)",
 "utility_waste_score":"Waste-generation estimate (0–100; ∝ population)",
 "utility_ev_gap_score":"EV-charger provision gap (0–100)",
 "utility_diurnal_swing":"Day/night load swing (0–100)",
 "utility_equity_score":"Infrastructure-equity priority (0–100)",
 "utility_resilience_score":"Critical-customer resilience need (0–100)",
 # transport
 "mobility_access_score":"Transit / multimodal access (0–100; ≈ adequacy)",
 "mobility_desert_priority":"Transit-desert intervention priority (0–100)",
 "mobility_crowding_score":"Network crowding stress (0–100)",
 "mobility_tod_score":"Transit-oriented-development opportunity (0–100)",
 "mobility_ridehail_score":"Ride-hail demand hotspot (0–100)",
 "mobility_firstlast_gap_score":"First / last-mile gap (0–100)",
 "mobility_parking_stress":"Parking stress (0–100)",
 "modal_split_proxy":"Public-transport modal-split proxy (0–100)",
 # insurance
 "risk_fire_score":"Property / fire peril (0–100)",
 "risk_auto_score":"Motor / auto exposure (0–100)",
 "risk_health_score":"Life / health exposure (0–100)",
 "risk_bi_failure_score":"Business-interruption risk (≈ biz_recent_dead_share)",
 "risk_collateral_score":"Collateral-value risk tier (0–100)",
 "risk_nuisance_score":"Nuisance / liability peril (0–100)",
 "risk_coastal_proxy":"Coastal / flood proxy (weak; 0–100)",
 "insurance_risk_score":"Blended underwriting risk score (0–100)",
 "insurance_accumulation_band":"Accumulation / concentration band",
}
PACK_OF = {}  # column -> pack (for derivation note)

def pack_score_cols(df, pack):
    cols = [c for c in df.columns if c not in ADMIN]
    for c in cols: PACK_OF[c] = pack
    return cols

def fold(master_path, key, pack_file_fmt):
    m = pd.read_parquet(master_path)
    n0 = m.shape[1]
    added = []
    for pk in PACKS:
        pf = pd.read_parquet(V5 / pack_file_fmt.format(pk=pk))
        sc = [c for c in pack_score_cols(pf, pk) if c in DESC]
        sub = pf[[key] + sc].drop_duplicates(subset=[key])
        m = m.merge(sub, on=key, how="left")
        added += sc
    assert m[key].is_unique, "key dup after merge"
    assert len(added) == 39, f"expected 39, got {len(added)}"
    assert m.shape[1] == n0 + 39, f"width {m.shape[1]} != {n0}+39"
    return m, added

def catalog_rows(df, added, dataset, scale):
    rows = []
    for c in added:
        s = df[c]
        num = pd.api.types.is_numeric_dtype(s) and not pd.api.types.is_bool_dtype(s)
        rows.append({
            "dataset": dataset, "scale": scale, "column": c, "dtype": str(s.dtype),
            "null_pct": round(float(s.isna().mean()*100), 2),
            "desc_source": "pack", "description": DESC[c],
            "units": "score 0–100" if c not in ("rent_demand_tier","insurance_accumulation_band") else "tier/band",
            "source_stage": "pack", "derivation": f"domain pack: {PACK_OF[c]}",
            "n_unique": float(s.nunique()),
            "sample": str(s.dropna().iloc[0]) if s.notna().any() else "",
            "min": float(s.min()) if num else "", "max": float(s.max()) if num else "",
            "mean": round(float(s.mean()),4) if num else "",
            "median": round(float(s.median()),4) if num else "",
        })
    return pd.DataFrame(rows)

# ---- HEX8 ----
shutil.copy2(V5/"hex/hex8_all_features.parquet", BK/"hex8_all_features.parquet")
h, addedH = fold(V5/"hex/hex8_all_features.parquet", "hex8_id", "hex/hex8_{pk}_pack.parquet")
h.to_parquet(V5/"hex/hex8_all_features.parquet", index=False)
print(f"hex8: -> {h.shape}  (added {len(addedH)})")

# ---- SUBZONE (parity) ----
shutil.copy2(V5/"hex/subzone_all_features.parquet", BK/"subzone_all_features.parquet")
sz = pd.read_parquet(V5/"hex/subzone_all_features.parquet"); n0=sz.shape[1]
for pk in PACKS:
    pf = pd.read_parquet(V5/f"hex/subzone_{pk}_pack.parquet")
    sc = [c for c in pf.columns if c in DESC]
    sz = sz.merge(pf[["subzone_c"]+sc].drop_duplicates("subzone_c"), on="subzone_c", how="left")
sz.to_parquet(V5/"hex/subzone_all_features.parquet", index=False)
print(f"subzone: {n0} -> {sz.shape[1]}")

# ---- feature_catalog.parquet append ----
shutil.copy2(V5/"catalog/feature_catalog.parquet", BK/"feature_catalog.parquet")
fc = pd.read_parquet(V5/"catalog/feature_catalog.parquet")
newH = catalog_rows(h, addedH, "hex/hex8_all_features.parquet", "hex8")
newS = catalog_rows(sz, [c for c in addedH if c in sz.columns], "hex/subzone_all_features.parquet", "subzone")
fc2 = pd.concat([fc, newH, newS], ignore_index=True)
fc2.to_parquet(V5/"catalog/feature_catalog.parquet", index=False)
print(f"feature_catalog: {len(fc)} -> {len(fc2)} rows (+{len(newH)} hex8, +{len(newS)} subzone)")

# ---- validation (known-answer) ----
top_re = h.nlargest(3,"re_feasibility_score")["parent_subzone_name"].tolist()
top_desert = h.nlargest(3,"mobility_desert_priority")["parent_subzone_name"].tolist()
print("KNOWN-ANSWER  re_feasibility top3:", top_re)
print("KNOWN-ANSWER  transit-desert top3:", top_desert)
print("BI vs biz corr:", round(h["risk_bi_failure_score"].corr(h.get("biz_recent_dead_share", h["risk_bi_failure_score"])),3))
print(f"BACKUP at {BK}")
print("DONE — now run: python3 build_catalog_json.py")
