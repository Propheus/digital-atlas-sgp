# Methodology — Active School Travel Space (ASTS) Friendliness, Singapore

*Powered by Propheus Digital Atlas SGP v4.8*

A faithful replication of:

> **Lu, C., Yu, C., & Liu, X. (2024). "Evaluating the Quality of Children's Active
> School Travel Spaces and the Mechanisms of School District Friendliness Impact
> Based on Multi-Source Big Data."** *Land*, **13**(8), 1319.
> doi:10.3390/land13081319 — 151 public primary schools, central Lanzhou, China.

adapted to Singapore's **160 primary schools** and computed end-to-end on Propheus
infrastructure (azold-test-server, 16 cores).

The paper's chain is preserved exactly:

> schools → walking-route network → space syntax → school catchment →
> entropy-weighted friendliness index → Geographic Detector (drivers + interactions)

### Glossary (plain language, for planners)

| Term | In one line | In this study |
|---|---|---|
| **Schools** | The anchor points everything is measured around. | 160 MOE primary schools (of ~179). |
| **Walking network** | Every footpath/crossing stitched into a graph the computer walks along. | OSM, 170,121 nodes / 463,880 edges. |
| **Space syntax** | Maths of how *reachable* (Integration) and *through-routed* (Choice) streets are. | cityseer angular, 235,600-node dual graph, 800/1600 m. |
| **Catchment** | The real area reachable within 1 km *of walking* — the Active School Travel Space. | ~31 km of streets, ~0.9 km² per school. |
| **Entropy index** | Fusing six measures into one 0–100 score with data-derived (unbiased) weights. | greenery 0.26 · choice 0.19 · signals 0.19 · integration 0.16 · crossings 0.12 · footpaths 0.08. |
| **Geographic Detector** | A test of *what explains* the friendliness map (power statistic q ∈ [0,1]). | school centrality q=0.22 strongest; all pairs nonlinear-enhancing. |

---

## 1. Spatial unit & study design

- **Unit of analysis:** the primary-school catchment — the *Active School Travel
  Space* (ASTS), the walkable area a child traverses to reach school.
- **Catchment definition:** streets reachable within **1 km network distance**
  (Dijkstra on the pedestrian graph, weighted by edge length), **not** a Euclidean
  buffer. 1 km is the **MOE home-school registration priority band** (Phase 2A/2C),
  which makes the catchment policy-grounded rather than arbitrary. The catchment
  polygon is the reachable edges buffered 40 m (the street-frontage corridor).
- **Lanzhou used** the Amap pedestrian routing API; Amap is China-only, so for
  Singapore the network comes from OpenStreetMap (dense, well-maintained footways).

## 2. Data sources

| Layer | Source | Detail |
|---|---|---|
| Primary schools (points) | Digital Atlas v4 `places/sgp_places_final.parquet` | 160 after cleaning (name-match, false positives removed) |
| Walking network | OpenStreetMap (`network_type=walk`) | 170,121 nodes / 463,880 edges |
| Road crossings | OpenStreetMap `highway=crossing` | 40,551 (safety) |
| Traffic signals | OpenStreetMap `highway=traffic_signals` | 5,443 (safety) |
| Parks / green space | OpenStreetMap `leisure`/`landuse` green | 4,658 polygons (greenery) |
| Bus stops | OpenStreetMap `highway=bus_stop` | 5,938 (driver) |
| MRT stations | OpenStreetMap `railway=station` | 324 (driver) |
| Population density | Digital Atlas v4 `subzone_population.parquet` + subzone polygons | pop ÷ area |

All OSM layers were fetched **server-side** via Overpass; v4 layers are the
authoritative Digital Atlas data.

## 3. Space syntax (cityseer, angular)

Space syntax is computed with **cityseer** angular ("simplest-path") analysis on
the **dual graph** (segments → nodes; 235,600 dual nodes), the modern equivalent
of axial/segment analysis:

- **Integration** ← angular **harmonic closeness** — how easily a segment reaches
  all others (reachability / legibility).
- **Choice** ← angular **betweenness** — through-movement potential.

Both at **800 m and 1600 m** radii (bracketing the 1 km / 2 km MOE tiers).
Computed on the **full network**, distance-thresholded — so there are **no
subgraph clipping artifacts**; catchment values are the mean over the dual nodes
falling inside each catchment.

> Why a dual graph: angular centrality measures turn-cost between segments, which
> only exists on the dual representation — `cityseer.metrics.networks.node_centrality_simplest`
> requires it.

## 4. Friendliness index (entropy weight method)

Six indicators per catchment, all oriented "higher = friendlier":

| Indicator | Dimension | Definition |
|---|---|---|
| `integration` | Network | mean angular harmonic closeness @800 m |
| `choice` | Network | mean angular betweenness @800 m |
| `crossing_dens` | Safety | controlled crossings per km of route |
| `signal_dens` | Safety | traffic signals per km of route |
| `green_pct` | Greenery | park/green area ÷ catchment area |
| `footpath_dens` | Provision | walkable network length per km² |

**Entropy weighting** (objective; no subjective tuning), over *n* catchments:

```
min-max normalise:  rᵢⱼ = (xᵢⱼ − min xⱼ) / (max xⱼ − min xⱼ)
proportion:         pᵢⱼ = rᵢⱼ / Σᵢ rᵢⱼ
entropy:            eⱼ  = −(1/ln n) · Σᵢ pᵢⱼ ln pᵢⱼ
weight:             wⱼ  = (1 − eⱼ) / Σⱼ (1 − eⱼ)
friendliness:       Fᵢ  = Σⱼ wⱼ rᵢⱼ      (rescaled 0–100)
```

Catchments are then split into **Low / Medium / High** tertiles.

**Resulting weights:** greenery 0.260 · choice 0.192 · signals 0.187 ·
integration 0.163 · crossings 0.120 · footpath density 0.079.

## 5. Geographic Detector (mechanisms)

The "mechanism" analysis uses the **Geographic Detector** *q*-statistic
(Wang & Xu) — the share of friendliness variance explained by stratifying on a
driver:

```
q = 1 − ( Σₕ Nₕ σ²ₕ ) / ( N σ² ) ∈ [0,1]
```

where *h* indexes the driver's strata (**5 quantile classes**), `Nₕ`/`σ²ₕ` are
the size/variance within stratum *h*. The **interaction detector** overlays two
drivers' strata and classifies the joint *q* (nonlinear-enhance / bi-enhance /
weaken / independent).

**Drivers** (independent variables):

| Driver | Definition |
|---|---|
| Population density | area-weighted residential density over the catchment |
| Transport convenience | z(bus-stop density) + z(−MRT distance) |
| School-district size | catchment area (km²) |
| School centrality | angular closeness @1600 m at the school's nearest node |

### The central design rule — disjoint sets

> The **index indicators** (route environment) and the **Geographic Detector
> drivers** (population density, transport convenience, district size, school
> centrality) are kept **strictly disjoint**.

If a driver (e.g. transport convenience) were also inside the friendliness
composite, *q* would be circular and meaningless. Keeping them separate is what
makes "transport convenience drives friendliness" a real finding. Transit and
population variables therefore appear **only** as drivers, never in the index.

## 6. Pipeline (scripts, server)

Run on `azold-test-server:/home/azureuser/da-sgp/asts/`:

| Script | Output |
|---|---|
| `01_schools.py` | `primary_schools.geojson` |
| `02_osm_layers.py` | walk graph + crossings/signals/parks/bus/MRT (OSM) |
| `03_space_syntax.py` | `syntax_nodes.gpkg` (cityseer angular, dual graph) |
| `04_catchments.py` | `catchments.gpkg` (1 km network, 12-core parallel) |
| `05_index_components.py` | `index_components.csv` |
| `06_friendliness.py` | `friendliness_index.{csv,geojson}` |
| `07_geodetector.py` | `geodetector.csv`, `geodetector_interaction.csv` |
| `08_report.py` | `REPORT.md` |
| `build_report.py` (local) | `SGP_ASTS_REPORT.html` (Propheus-themed) |

## 7. What the scores mean — relevance in the Singapore context

The friendliness value is a **0–100 relative ranking** of how supportive a school's
1 km walking catchment is for a child on foot: **100 = the friendliest catchment in
Singapore, 0 = the least**. It is *comparative* across the 160 schools, not an
absolute standard, and it rates the **walking environment**, not proximity to
amenities.

**Why this is policy-relevant in Singapore specifically:**

- **MOE distance-based admission.** Primary-1 registration gives priority to
  children living **within 1 km** (and then 1–2 km) of a school. Unlike most cities,
  a large share of Singapore pupils therefore live in genuine walking range — so the
  *quality of that 1 km* is a live determinant of whether they actually walk or are
  driven. The catchment radius is chosen to match this policy band exactly.
- **Active travel & child independent mobility.** A friendly catchment (legible
  routes, controlled crossings, continuous shaded footpaths) is precisely the
  condition under which parents permit unaccompanied walking/cycling — supporting
  childhood physical activity and the national **"car-lite"** agenda.
- **Tropical climate.** Greenery is the heaviest-weighted indicator (0.26) because in
  Singapore's heat it functions as **shade and thermal relief**, not mere amenity —
  a decisive comfort factor for a 7-year-old's walk.
- **Road safety.** Crossing and signal density are the front line of child
  pedestrian safety; space-syntax legibility (few turns, high reachability) means
  routes a young child can navigate without getting lost or crossing uncontrolled.

**How to read a low score.** A `Low` catchment is **not a "bad school"** — it flags
where the *walking environment* most needs investment (greening, signalised
crossings, footpath continuity). The bottom-decile catchments are the natural
priority list for intervention.

**Why the pattern inverts 15-minute access.** Friendly catchments cluster in
**newer towns** (Jurong West, Punggol), built with wide green park-connector
footpaths and regular signalised crossings; the **dense central core** (Bukit
Timah, Newton) scores lower because fine-grained mature street networks have more
turns, less green corridor and busier roads — even though shops sit closer. The
index deliberately measures the **quality of the journey**, which is what drives the
walk decision, rather than the proximity of destinations.

## 8. Scope & limitations

- **Phase 1** measures network structure + objective environment proxies. The
  paper's **street-view experiential layer** (green-view index, sky/enclosure,
  sidewalk ratio from semantic segmentation of Google Street View / Mapillary) is
  **Phase 2** and requires a GPU (azold has none).
- **School list:** 160 matched & cleaned from the v4 places master vs MOE's 179
  (≈90%); a few were dropped as name-match false positives (school gates,
  student-care tenants). The canonical MOE list can be substituted for exact parity.
- **Greenery** uses OSM park polygons, not street-level NDVI; street-level
  greenness arrives with Phase 2.
- No ground-truth friendliness labels exist; results are sanity-checked against
  the Digital Atlas calibration anchors and the expected core–periphery pattern.
