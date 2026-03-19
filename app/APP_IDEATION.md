# Digital Atlas SGP — App Build Plan

## What We're Building
A map-based exploration app for Singapore that progressively reveals urban structure
through layered storytelling — same look/feel/animation as the NYC Digital Atlas v2,
adapted for Singapore's unique urban fabric.

## NYC App Anatomy (what we're replicating)

### Core UX Pattern
1. **Progressive Layer Build** — Layers appear one at a time with animations
2. **Choropleth Map** — Subzones colored by active metric
3. **Left Panel** — Layer list with progress indicators
4. **Right Panel** — Selected subzone detail with metrics
5. **Bottom Strip** — Key metrics for active layer
6. **Place Scatter** — Individual places as dots on map
7. **Micrograph Detail** — Click a place → see star-graph with anchors
8. **Search/Filter** — By name, brand, category

### Tech Stack (identical)
- React 18 + TypeScript
- Mapbox GL JS (choropleth + point layers)
- Deck.gl (ScatterplotLayer, PathLayer for micrograph edges)
- Framer Motion (all animations)
- Zustand (state management)
- Tailwind CSS (styling)
- Vite (build)
- d3-scale + d3-scale-chromatic (color scales)

### Key Animations
- Layer list: staggered fade-in with slide
- Build progress bar: animated width
- Metric numbers: AnimatedNumber component (counts up)
- Panel transitions: slide in/out with opacity
- Place selection: scale pulse
- Detail panel: slide from right

---

## SGP Adaptation — 10 Layers

### Act I: The People (3 layers)

**Layer 1: "Who Lives Here"** 🏘️
- Color: `#6366f1` (indigo)
- Choropleth: population density
- Metrics: Population, Density/km², Elderly %, Dependency Ratio
- Insights: Most populated subzone, youngest area, oldest area
- SGP-specific: 4.17M residents across 332 subzones

**Layer 2: "How They Live"** 🏠
- Color: `#22c55e` (green)
- Choropleth: HDB resale PSF (affluence proxy)
- Metrics: Median HDB PSF, HDB 1-2rm %, Condo %, Landed %
- Insights: Most expensive subzone, most HDB-dense, most private
- SGP-specific: HDB dwelling type = income stratification signal

**Layer 3: "What's Planned"** 📐
- Color: `#f59e0b` (amber)
- Choropleth: land use entropy (zoning diversity)
- Metrics: Residential %, Commercial %, Industrial %, Mixed Use %, GPR
- Insights: Most mixed-use, most industrial, highest GPR
- SGP-specific: URA Master Plan IS the skeleton of SGP

### Act II: The Infrastructure (3 layers)

**Layer 4: "How They Move"** 🚇
- Color: `#3b82f6` (blue)
- Choropleth: transit accessibility (MRT distance)
- Metrics: Dist to MRT, MRT within 1km, Bus stops, Bus density
- Overlay: MRT stations as markers, bus stops as tiny dots
- SGP-specific: MRT network is the spine, everything walkable

**Layer 5: "What's Built"** 🏗️
- Color: `#06b6d4` (cyan)
- Choropleth: road density
- Metrics: Road density, Total road km, Building count
- Insights: Densest road network, most footways
- SGP-specific: No car-centric view — walk + transit only

**Layer 6: "What's Nearby"** 📍
- Color: `#8b5cf6` (purple)
- Choropleth: amenity accessibility score
- Metrics: Dist to park, Dist to hawker, Dist to school, Dist to supermarket
- SGP-specific: Hawker centre distance is a basic amenity in SGP

### Act III: The Places (2 layers)

**Layer 7: "What's There"** 🏪
- Color: `#ec4899` (pink)
- Choropleth: place density per km²
- Scatter: All 66,851 places colored by main_category
- Metrics: Total places, Place density, Category entropy, Avg rating
- Search + filter by category
- SGP-specific: 24 categories, hawker stalls as distinct type

**Layer 8: "Who Runs It"** 🏷️
- Color: `#14b8a6` (teal)
- Choropleth: brand density (chain vs independent ratio)
- Scatter: Branded places highlighted
- Metrics: Branded %, Unique brands, Top brand, Avg rating
- Filter by brand
- SGP-specific: 232 brands mapped (7-Eleven 174, Starbucks 50, etc.)

### Act IV: The Insight (2 layers)

**Layer 9: "What's Expected"** 🎯
- Color: `#10b981` (emerald)
- Choropleth: density gap (predicted - actual)
- Metrics: Predicted total, Actual total, Gap %, Model R²
- SGP-specific: Density model R²=0.773

**Layer 10: "The Micrograph"** 🔬
- Color: `#0ea5e9` (sky)
- Place-level view: click any place → see star-graph
- Context vector bars (transit, competitor, complementary, demand)
- Anchor list with walk times
- 12 category micrographs available
- SGP-specific: Walkable distances, hawker centres as T1 anchors

---

## Data Files Needed (already composed)

```
public/data/
  subzones_geo.geojson       372 KB   Choropleth boundaries
  subzone_profiles.json      617 KB   332 profiles with all metrics
  places_slim.json           7.4 MB   66,851 places as tuples
  summary_stats.json         2.3 KB   Global stats
  category_stats.json        12 KB    Per-category breakdowns
  brands.json                38 KB    232 brand registry
  mrt_stations.geojson       70 KB    231 MRT markers
  bus_stops.geojson           939 KB   5,177 bus stop markers
  hawker_centres.geojson     118 KB   129 hawker markers
  colocation.json            8.7 KB   Co-location PMI data

  cafe_slim.json             409 KB   3,368 cafe micrograph summaries
  hawker_slim.json           400 KB   3,157 hawker summaries
  restaurant_slim.json       688 KB   5,656 restaurant summaries
  ... (9 more category slims)

  cafe_details/              Per-subzone detail JSON files
  hawker_details/            Per-subzone detail JSON files
  restaurant_details/        Per-subzone detail JSON files
  ... (9 more detail directories)
```

Total frontend data: ~15 MB (excluding detail files loaded on demand)

---

## Component Architecture

```
App.tsx
├── MapGL (react-map-gl)
│   ├── Source "subzones" → Layer "subzone-fill" (choropleth)
│   ├── Source "subzones" → Layer "subzone-line" (borders)
│   ├── DeckGLOverlay
│   │   ├── ScatterplotLayer (places)
│   │   └── PathLayer (micrograph anchor edges)
│   └── MRT/Bus/Hawker marker layers
├── LayerListPanel (left sidebar)
│   ├── BuildProgress animation
│   └── LayerButton × 10
├── LayerDetailPanel (right sidebar)
│   ├── SubzoneMetrics
│   ├── PlaceList
│   └── CategoryBreakdown
├── BottomMetricsStrip
│   └── AnimatedNumber × 4-5
├── PlaceDetailCard (micrograph view)
│   ├── ContextVectorBars
│   ├── AnchorList
│   └── DensityBandBadge
├── SearchBar
│   └── PlaceSearch + CategoryFilter + BrandFilter
└── AnimatePresence wrappers
```

---

## Styling Guide

### Colors (same dark theme as NYC)
- Background: `#0a0f1a`
- Card: `#111827`
- Border: `#1e2a3a`
- Text: `#e5e7eb`
- Muted: `#9ca3af`
- Accent: `#14b8a6` (teal — Singapore green)

### Choropleth Palette
Teal gradient (Singapore's garden city identity):
```
["#e6f4f3", "#c0e4e1", "#94d1cc", "#68beb7", "#44aaa3",
 "#2d9690", "#20827d", "#166e6a", "#0d5a57", "#064644"]
```

### Map
- Center: `[103.8198, 1.3521]` (Singapore center)
- Zoom: 11.5 (shows full island)
- Style: `mapbox://styles/mapbox/dark-v11`

---

## Build Phases

### Phase 1: Skeleton (2 hours)
- Vite + React + TS + Tailwind setup
- MapGL with subzone choropleth
- Basic state management (zustand)
- Layer list panel (static)

### Phase 2: Progressive Build (3 hours)
- Build sequence animation (layers appear one by one)
- Choropleth switching per active layer
- Bottom metrics strip with AnimatedNumber
- Layer detail panel with subzone click

### Phase 3: Places Layer (2 hours)
- ScatterplotLayer for 66K places
- Color by category
- Search + filter
- Place click → detail panel

### Phase 4: Micrograph (3 hours)
- Cafe micrograph integration
- Star-graph visualization (PathLayer from place to anchors)
- Context vector bars
- Anchor list with walk times
- Detail files loaded on subzone click

### Phase 5: Polish (2 hours)
- All 10 layers with correct metrics
- Category/brand switching in micrograph
- Responsive layout
- Loading states
- Deploy to server

---

## Key Differences from NYC

| Aspect | NYC | SGP |
|--------|-----|-----|
| Region unit | Census tract (2,327) | Subzone (332) |
| Map center | -73.95, 40.73, zoom 10.5 | 103.82, 1.35, zoom 11.5 |
| Income signal | Census median income | HDB resale PSF |
| Transit | Subway ridership | MRT distance (no ridership data) |
| Crime layer | Yes | No — replace with Land Use |
| Demand model | Gravity model | Density model gap |
| Place categories | 253K generic | 66K with 24 SGP categories |
| Micrograph categories | Cafe, QSR | 12 categories |
| Unique layers | Crime, Commute | Zoning, Hawker, HDB estates |
| Walk routing | OSM Dijkstra | Distance-based (no OSM routing yet) |
