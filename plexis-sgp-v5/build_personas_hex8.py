"""
Plexis SGP v4 — NVIDIA Nemotron-Personas-Singapore -> hex8 (PA broadcast).

Source: nvidia/Nemotron-Personas-Singapore (148k synthetic personas, CC-BY-4.0).
Spatial granularity is PLANNING AREA only (48 PAs) — there is no finer geography
in the dataset, so PA-level demographic distributions are broadcast to every
hex8 via parent_pa. Narrative text fields (professional_persona, etc.) cannot be
spatialized and are intentionally dropped; only structured distributions land.

Output: hex/hex8_personas_nv.parquet  (nvp_* cols) -> merged into master.
LOW-n PAs flagged (nvp_low_n) since a few PAs have <30 personas.
"""
import json, time
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).parent
NVP = ROOT / "data/nvidia_personas"
LOW_N = 30

OCC = {  # occupation -> grouped key
    "Professional": "professional", "Senior Official or Manager": "manager",
    "Associate Professional or Technician": "assoc_prof",
    "Service or Sales Worker": "service_sales", "Clerical Worker": "clerical",
    "Production Craftsman or Related Worker": "manual",
    "Plant or Machine Operator or Assembler": "manual",
    "Cleaner, Labourer or Related Worker": "manual",
    "Agricultural or Fishery Worker": "manual",
    "Retired": "retired", "Student": "student", "Unemployed": "unemployed",
    "Homemaker": "homemaker", "National Service": "ns",
}
IND = {
    "Financial & Insurance Services": "finance",
    "Information & Communications": "infocomm",
    "Manufacturing": "manufacturing",
    "Wholesale & Retail Trade": "retail",
    "Health & Social Services": "health",
    "Construction": "construction",
    "Professional Services": "prof_services",
    "Public Administration & Education Services": "public_edu",
    "Accommodation & Food Services": "food_accom",
    "Transportation & Storage": "transport",
}


def pa_profile(g):
    n = len(g)
    age = g["age"]
    edu = g["education_level"]
    occ = g["occupation"].map(OCC).fillna("other")
    ind = g["industry"].map(IND).fillna("other")
    d = {
        "nvp_persona_n": n,
        "nvp_median_age": float(age.median()),
        "nvp_pct_age_18_34": float((age < 35).mean()),
        "nvp_pct_age_35_54": float(((age >= 35) & (age < 55)).mean()),
        "nvp_pct_age_55plus": float((age >= 55).mean()),
        "nvp_pct_female": float((g["sex"] == "Female").mean()),
        "nvp_pct_married": float((g["marital_status"] == "Married").mean()),
        "nvp_pct_single": float((g["marital_status"] == "Single").mean()),
        "nvp_pct_univ": float((edu == "University").mean()),
        "nvp_pct_poly": float((edu == "Polytechnic").mean()),
        "nvp_pct_secondary_below": float(edu.isin(
            ["Secondary", "Lower Secondary", "Primary", "No Qualification"]).mean()),
    }
    for k in ["professional", "manager", "assoc_prof", "service_sales", "clerical",
              "manual", "retired", "student", "unemployed", "homemaker"]:
        d[f"nvp_occ_{k}"] = float((occ == k).mean())
    for k in ["finance", "infocomm", "manufacturing", "retail", "health",
              "construction", "prof_services", "public_edu", "food_accom", "transport"]:
        d[f"nvp_ind_{k}"] = float((ind == k).mean())
    # simple composite affluence proxy (univ + prof/manager + finance/infocomm)
    d["nvp_affluence_idx"] = float(np.mean([d["nvp_pct_univ"],
        d["nvp_occ_professional"] + d["nvp_occ_manager"],
        d["nvp_ind_finance"] + d["nvp_ind_infocomm"]]))
    return pd.Series(d)


def main():
    t0 = time.time()
    cols = ["sex", "age", "marital_status", "education_level", "occupation",
            "industry", "planning_area"]
    df = pd.concat([pd.read_parquet(f, columns=cols)
                    for f in sorted(NVP.glob("train-*.parquet"))], ignore_index=True)
    prof = df.groupby("planning_area").apply(pa_profile).reset_index()
    prof["pa_key"] = prof["planning_area"].str.upper().str.strip()
    prof["nvp_low_n"] = (prof["nvp_persona_n"] < LOW_N).astype(int)

    # --- join verification both directions ---
    h8 = pd.read_parquet(ROOT / "hex/hex8_all_features.parquet")[["hex8_id", "parent_pa"]]
    atlas_pa = set(h8["parent_pa"].dropna().unique())
    nv_pa = set(prof["pa_key"])
    nv_only = sorted(nv_pa - atlas_pa)
    atlas_only = sorted(atlas_pa - nv_pa)

    feat_cols = [c for c in prof.columns if c.startswith("nvp_")]
    merged = h8.merge(prof[["pa_key"] + feat_cols], left_on="parent_pa",
                      right_on="pa_key", how="left").drop(columns=["pa_key", "parent_pa"])
    cov = float(merged["nvp_persona_n"].notna().mean())
    out = merged.copy()
    for c in feat_cols:
        out[c] = out[c].round(5)
    out.to_parquet(ROOT / "hex/hex8_personas_nv.parquet", index=False)

    rep = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "source": "nvidia/Nemotron-Personas-Singapore",
        "personas": int(len(df)), "planning_areas": int(prof.shape[0]),
        "nvidia_PA_not_in_atlas": nv_only,
        "atlas_PA_not_in_nvidia": atlas_only,
        "hex8_coverage_pct": round(100 * cov, 2),
        "low_n_PAs": prof.loc[prof["nvp_low_n"] == 1, "pa_key"].tolist(),
        "n_feature_cols": len(feat_cols),
        "wall_clock_s": round(time.time() - t0, 2),
    }
    json.dump(rep, open(ROOT / "hex/personas_nv_report.json", "w"), indent=2)
    print(json.dumps(rep, indent=2))


if __name__ == "__main__":
    main()
