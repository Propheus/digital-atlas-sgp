"""Step 8 — assemble REPORT.md from the computed outputs."""
import pandas as pd
from common import ART, OUT, PKG

idx = pd.read_csv(ART["index"])
gd = pd.read_csv(ART["geodetector"])
gi = pd.read_csv(OUT / "geodetector_interaction.csv")
full = pd.read_csv(OUT / "schools_index_drivers.csv")

top = idx.sort_values("friendliness", ascending=False).head(10)
bot = idx.sort_values("friendliness").head(10)
byzone = idx.groupby("zone")["friendliness"].mean().round(1).sort_values(ascending=False)
lvl = idx["level"].value_counts().reindex(["Low", "Medium", "High"])

def tbl(df, cols):
    return df[cols].to_markdown(index=False, floatfmt=".1f")

md = f"""# Active School Travel Space (ASTS) Friendliness — Singapore

Replication of *Land* 2024, 13(8), 1319 — "Evaluating the Quality of Children's
Active School Travel Spaces and the Mechanisms of School District Friendliness
Impact Based on Multi-Source Big Data" (Lanzhou, 151 primary schools).

**Singapore:** {len(idx)} MOE primary schools · catchment = 1 km network distance
(MOE home-school priority band) · entropy-weighted friendliness index ·
Geographic Detector for driving factors.

> **Scope note (Phase 1):** This measures network structure + objective environment
> proxies (space syntax, safety, greenery, footpath provision). The paper's
> street-view experiential dimension (green-view index, sky/enclosure, sidewalk
> ratio) is **not** yet included — that is Phase 2 (Google Street View / Mapillary
> + semantic segmentation).

## Friendliness levels
{lvl.to_frame('schools').to_markdown()}

## Top 10 friendliest school districts
{tbl(top, ['name','zone','friendliness'])}

## Bottom 10
{tbl(bot, ['name','zone','friendliness'])}

## Mean friendliness by region (core-periphery pattern)
{byzone.to_frame('mean_friendliness').to_markdown()}

## Geographic Detector — single-factor q
{gd.to_markdown(index=False, floatfmt='.4f')}

q ∈ [0,1]: share of friendliness variance explained by stratifying on each driver.

## Interaction detector
{gi.to_markdown(index=False, floatfmt='.4f')}

## Index components (entropy-weighted)
integration · choice (space syntax) · crossing_dens · signal_dens (safety) ·
green_pct · pcn_dens (greenery) · footpath_dens (provision). Weights printed by
`06_friendliness.py`.

## Files
- `output/friendliness_index.csv` / `.geojson` — per-school scores + level
- `output/schools_index_drivers.csv` — index + all drivers
- `output/geodetector.csv`, `geodetector_interaction.csv`
"""
(PKG / "REPORT.md").write_text(md)
print(f"wrote {PKG/'REPORT.md'}")
print(md)
