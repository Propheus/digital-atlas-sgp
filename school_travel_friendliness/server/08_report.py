"""Step 8 — assemble REPORT.md from computed outputs (server)."""
import pandas as pd
from common import ART, OUT, PKG

idx = pd.read_csv(ART["index"])
gd = pd.read_csv(ART["geodetector"])
gi = pd.read_csv(OUT / "geodetector_interaction.csv")

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
Geographic Detector for driving factors. Computed on azold-test-server using the
v4 atlas (schools, population, boundaries) + OSM layers (walk network, crossings,
signals, parks, bus, MRT).

> **Phase 1 scope:** network structure + objective environment proxies. The paper's
> street-view experiential dimension (green-view index, sky/enclosure, sidewalk
> ratio) is Phase 2 (GSV/Mapillary + semantic segmentation).

## Friendliness levels
{lvl.to_frame('schools').to_markdown()}

## Top 10 friendliest
{tbl(top, ['name','zone','friendliness'])}

## Bottom 10
{tbl(bot, ['name','zone','friendliness'])}

## Mean friendliness by region (core-periphery)
{byzone.to_frame('mean_friendliness').to_markdown()}

## Geographic Detector — single-factor q
{gd.to_markdown(index=False, floatfmt='.4f')}

## Interaction detector
{gi.to_markdown(index=False, floatfmt='.4f')}

## Files
- `output/friendliness_index.csv` / `.geojson`
- `output/schools_index_drivers.csv`
- `output/geodetector.csv`, `geodetector_interaction.csv`
"""
(PKG / "REPORT.md").write_text(md)
print(f"wrote {PKG/'REPORT.md'}")
print(md)
