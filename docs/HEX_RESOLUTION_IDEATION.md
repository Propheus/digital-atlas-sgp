# Hex Resolution Ideation — Should We Move Beyond Subzones?

**Date:** 2026-04-05
**Context:** V8 adequacy app ready at 332 subzones. Exploring whether finer spatial units would improve urban planning analysis for SGP government demo.
**Status:** Ideation only — no code changes. Decision: **defer to V9 post-demo**.

---

## The core question

Is the 332-subzone unit the right resolution for the SGP adequacy app, or should we move to H3 hexagons (or similar) for finer-grained analysis?

## Why subzones are problematic

The 332 URA subzones are **politically meaningful but analytically flawed**:

1. **Wildly uneven sizes**: Selegie (0.05 km²) and Central Water Catchment (68.6 km²) are both "1 row" — a 1,300× difference in area
2. **Administrative, not organic**: URA drew them for planning purposes, not around activity clusters
3. **Boundary artifacts**: Paya Lebar MRT station sits at the intersection of 3 subzones, so its ridership gets split arbitrarily
4. **Aggregation smoothing**: Aljunied contains both 40-storey HDB blocks AND low-rise shophouses — averaging gives you "mixed" nonsense that's hard to interpret
5. **Edge effects**: A resident 20m inside Tampines East's boundary may actually shop, school, and commute from Tampines Central
6. **Population-activity mismatch**: Jurong Island = 1 subzone with 0 residents but 12,000 industrial buildings. Mixing this with residential zones pollutes every per-capita statistic
7. **Unequal demand granularity**: Tampines East (4.3 km², 126K people) is averaged just like Selegie (0.05 km², 0 people) — scale artifacts

## H3 resolution options for Singapore

Singapore's land area is 735 km². H3 is Uber's global hexagonal grid system.

| Resolution | Hex area | Hex edge | # hexes in SGP | Suitability |
|---|---|---|---|---|
| H3-7 | 5.16 km² | ~1.3 km | ~143 | Too coarse — worse than current subzones |
| **H3-8** | **0.74 km²** | **~530m** | **~1,000** | Matches MRT 500m walking catchment |
| **H3-9** | **0.105 km²** | **~175m** | **~7,000** | **Sweet spot** — matches HDB estate block cluster |
| H3-10 | 0.015 km² | ~65m | ~49,000 | Individual buildings — too sparse for most features |

**For SGP specifically, H3-9 is the sweet spot.** A 175m hex edge = ~350m diameter = the natural walking distance where "can I reach X" matters.

## What we'd gain at H3-9

### Resolution improvement
- 7,000 hexes vs 332 subzones = **21× finer granularity** with consistent cell size
- No more 1,300× size variance

### True walking catchments
- Every hex gets its own `dist_nearest_mrt`, `walkability_score`, `amenity_types_nearby`
- No more averaging a 500m hex with a 5km hex

### Hot-spot detection
- Instead of "Yishun East is underserved", you'd see the specific **3-4 hexes inside Yishun East** where the gap exists
- Most of Yishun East is fine — hexification surfaces the actual problem area

### Better government demo narrative
- Point at a map and say: *"this 200m × 200m area has 1,200 elderly residents and the nearest clinic is 800m away — that's 10 minutes walking for someone with a walker"*
- Concrete, actionable, 1 intervention away

### Dasymetric population
- Census gives us population per subzone
- At hex level, redistribute using building footprints + HDB blocks as weights
- Much more accurate than uniform-density assumption

### Data-nature alignment

| Data type | Source | Natural unit |
|---|---|---|
| Points (MRT, bus, places, buildings) | LTA, Overture, V2 | Hex is natural |
| Lines (roads, cycleways) | OSM | Map segment midpoints to hex |
| Polygons (census, zoning) | DOS, URA | Interpolate — introduces error but quantifiable |

## Feature-by-feature implications

| Feature group | Source | H3-9 behavior |
|---|---|---|
| **Population** | DOS subzone | Dasymetric split via buildings → accurate |
| **MRT ridership** | LTA station-level | Map directly — each hex has 0 or 1 station |
| **Bus ridership** | LTA stop-level | Direct — avg 1-3 stops per populated hex |
| **Buildings (377K)** | Overture + HDB + OSM | **Perfect** — every building already has lat/lon |
| **Places (174K)** | V2 jsonl | **Perfect** — point data |
| **Micrographs (800K)** | Per-place | **Already hex-ready** — computed per-place, trivially hex-aggregable |
| **Land use zoning** | URA polygons | Overlay — hex gets weighted mix |
| **Congestion (LTA)** | Road segments | Map midpoints, each hex gets real speed |
| **Walkability** | Derived | **Dramatically better** — actual walking distance per hex |
| **HDB resale prices** | Point-level | Perfect — map each transaction to its hex |
| **Personas (NVIDIA)** | Planning area aggregates | **Worse** — must distribute uniformly within PA |

**Verdict:** 90% of features become *more accurate* at H3-9. Only personas get worse because they're already aggregated at planning area level.

## Hybrid architecture (recommended if we go this route)

```
┌─────────────────┐         ┌─────────────────┐
│  332 Subzones   │◀────────│  7,000 H3-9 Hex │
│  (reporting)    │  parent │  (analytical)   │
└─────────────────┘         └─────────────────┘
       ▲                            ▲
       │                            │
   (what gov shows)         (what model learns)
```

### Design principles
- **Subzone table stays** — for government-facing reports, since gov thinks in subzones
- **Hex table is new** — for modeling, gap detection, validation
- Each hex has `parent_subzone_code` so you can roll up
- Each subzone has a list of hex IDs so you can drill down
- Features live at their natural resolution:
  - MRT/bus/places/buildings → computed at hex, summed to subzone
  - Census/zoning → computed at subzone, distributed to hex
- **The app shows both** — zoom out to subzone, zoom in to hex

## Alternatives we considered

1. **HDB blocks as the unit** (13,386 authoritative blocks)
   - Pros: Perfect for residential gap analysis, already have geometry
   - Cons: Doesn't work for commercial/industrial zones (Jurong Island, CBD)

2. **200m × 200m grid** (~18,000 cells)
   - Pros: UN-style, matches WorldPop resolution (which we have!), aligns to satellite imagery
   - Cons: Square cells less naturally suited to walking-distance modeling than hexagons

3. **Road segments** (550K OSM edges)
   - Pros: The true unit for street-level walkability
   - Cons: Overkill for most features, computationally heavy

4. **MRT station catchments** (231 circular 500m buffers)
   - Pros: Perfect for transit-specific analysis
   - Cons: Only works for one dimension, overlaps, leaves gaps

## Recommendation

**Not now — but yes, for V9 (post-demo).**

### For the current demo timeline
- The 332-subzone V8 is enough for the government demo
- Urban planners and officials think in subzones
- Adding a hex layer now would double the data engineering effort for marginal narrative gain
- **Keep it simple: ship V8, win the demo, then densify**

### For the production adequacy app (post-demo)
- Add **H3-9 hex layer** (~7,000 cells) as the underlying analytical unit
- Compute all point-based features directly at hex
- Dasymetrically distribute census/zoning polygons
- Keep subzone as the reporting rollup
- The app shows hex overlay when zoomed in, subzone boundaries when zoomed out

## Blockers to solve before hex-ification

1. **Dasymetric population interpolation** — need a defensible method:
   - Building footprints (have these via Overture + HDB)
   - HDB block capacity estimates
   - WorldPop 100m grid (have this on server) — cross-validation
2. **Persona redistribution** — NVIDIA data is only at planning area level; can't make it finer without new data. Would need to either accept the limitation or drop personas from hex-level features.
3. **Subzone → hex mapping table** — one-time computation, ~4 hours
4. **UI design for dual-resolution** — the explorer app needs to handle zoom-in/zoom-out gracefully
5. **Computational cost** — H3-9 = 7,000 hexes × 243 features = 1.7M cells, manageable but heavier than current 80K cells

## The killer insight

**Our micrographs are already hex-ready.**

We've computed 800K place-level anchor graphs in V3. Each place has lat/lon. If we switch to H3-9, every micrograph maps directly to a hex without any re-computation. That's ~90% of the analytical firepower already working at the right resolution, just currently being aggregated up to the wrong unit.

The transition cost is lower than it looks.

## What this unlocks for the 6 adequacy dimensions

| Dimension | Subzone limitation | Hex improvement |
|---|---|---|
| **Transit** | "Yishun East has 0 MRT stations" — but some residents are 200m from a station in the neighbouring subzone | "These 8 specific hexes in Yishun East have 0 MRT within 500m" — actionable |
| **Healthcare** | "Bedok North has 11 CHAS clinics per 10K elderly" — but they're clustered on one street | "These 4 hexes have 0 clinics within 10-min walk" — a specific gap |
| **Education** | "Sembawang East has 3,712 children, 0 formal schools" — but avg 800m to nearest school | Per-hex walking distance to nearest school — precise commute burden |
| **Elderly** | "Frankel has 345 elderly at risk" — aggregate tells you to intervene, not where | Per-hex elderly-friendly score — intervention at block level |
| **Daily living** | Subzone-level walkability averages out good and bad streets | True hex-level walkability — identifies streets to upgrade |
| **Safety & resilience** | "This subzone is 30% flood-prone" | "These 5 hexes flood during heavy rain; these 15 are safe" |

## Priority interventions at hex level (hypothetical)

If we had H3-9 hexes today, the top outputs for government would be:

1. **"Top 50 hexes with >500 elderly residents + no MRT within 500m"** → Silver Zone 3.0 candidates
2. **"Top 20 hexes with high ride-hail + no transit within 800m"** → future MRT station locations
3. **"Top 30 hexes with GPR >3 but built at <40%"** → redevelopment parcels
4. **"Top 40 hexes with >1000 residents + 0 clinics within 800m"** → MOH polyclinic priorities
5. **"Top 25 hexes with traffic jam >60% + school zone active"** → traffic-calming priorities

None of these are possible at subzone resolution — they require sub-subzone granularity.

## Decision log

- **Decision:** Defer hex-ification to V9 post-demo
- **Rationale:** Current subzone V8 is sufficient for demo narrative; government audience thinks in subzones; adding hex now doubles engineering effort for marginal demo gain; better to ship V8 and then densify based on demo feedback
- **Target for V9:** H3-9 (~7,000 hexes) as analytical unit, subzones remain reporting unit
- **Estimated effort:** 2-3 weeks (dasymetric interpolation + hex table build + UI dual-resolution)
- **Reviewer:** TBD (post-demo)

## Open questions for V9

1. Do we use H3-9 only, or a multi-scale approach (H3-8 for overview, H3-9 for detail)?
2. How do we handle the persona data limitation at hex level — drop, accept coarse, or acquire finer data?
3. Should we pre-compute all 243 features at hex level, or lazy-compute per query?
4. UI: single-layer toggle (subzone/hex switch) or continuous zoom-based rendering?
5. How do we validate hex-level predictions without ground truth at that resolution?
