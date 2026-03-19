# Digital Atlas SGP — Data Needs & Sources

## Objective
Mathematically represent Singapore's urban structure at subzone level (332 zones).
Each subzone gets a dense feature vector capturing: physical infrastructure, demographics,
economic activity, mobility, land use, and place composition.

---

## WHAT WE HAVE (Ready)

| Layer | Data | Records | Status |
|-------|------|---------|--------|
| Boundaries | Subzones (332), Planning Areas (55) | 387 | READY |
| Places | Curated places with categories, brands, ratings | 66,851 | READY |
| Census | Population by age/sex/ethnicity (subzone), HH income/size (planning area) | 7 files | READY |
| Housing | HDB buildings, property info, resale prices 2017+ | 253K records | READY |
| Transit | MRT/LRT stations, bus stops, rail lines, traffic signals | 52K features | READY |
| Land Use | Master plan zoning parcels with GPR | 113,212 | READY |
| Amenities | Hawkers, parks, schools, hotels, supermarkets | 44K features | READY |
| OSM | Full Singapore extract | 231 MB PBF | RAW - needs extraction |

---

## WHAT WE NEED — PHYSICAL INFRASTRUCTURE

### 1. Road Network (P0) — Extract from OSM PBF
**What:** Street segments with road type (highway, trunk, primary, secondary, residential, service),
lanes, speed limit, one-way, surface type, sidewalk presence
**Why:** Road density, walkability score, street connectivity per subzone. Critical for accessibility modeling.
**Source:** `data/osm/singapore-latest.osm.pbf` — extract with osmium/pyrosm
**Output:** `roads.geojson` with properties: road_type, lanes, maxspeed, oneway, surface, sidewalk

### 2. Building Footprints (P0) — Extract from OSM PBF
**What:** All building polygons with height, floors, building type (residential, commercial, industrial, retail)
**Why:** Built density, floor area ratio, building typology per subzone. Physical form of the city.
**Source:** `data/osm/singapore-latest.osm.pbf` — extract buildings layer
**Output:** `buildings.geojson` with properties: height, floors, building_type, area_sqm

### 3. Cycling Infrastructure (P2) — Extract from OSM PBF
**What:** Cycle paths, bicycle parking, bike-share stations
**Why:** Active mobility infrastructure quality per subzone
**Source:** OSM PBF
**Output:** `cycling.geojson`

---

## WHAT WE NEED — MOBILITY & DEMAND

### 4. MRT/Bus Passenger Volume (P1)
**What:** Monthly ridership per MRT station and bus stop
**Why:** Transit demand signal — which stations are heavily used. Proxy for foot traffic.
**Source:** LTA DataMall API (https://datamall.lta.gov.sg/content/datamall/en.html)
  - API: Transport Volume → Passenger Volume by Train Station / Bus Stop
  - Free registration required, API key issued
**Output:** `mrt_passenger_volume.csv`, `bus_passenger_volume.csv`

### 5. Taxi Availability / Ride-Hail Demand (P2)
**What:** Taxi availability by location, pickup/dropoff density
**Why:** Demand proxy for commercial areas
**Source:** LTA DataMall API → Taxi Availability endpoint (real-time, need to poll & aggregate)
**Output:** `taxi_demand_grid.csv`

---

## WHAT WE NEED — ECONOMIC SIGNALS

### 6. Private Property Prices (P1)
**What:** Condo/landed transaction prices, psf, by location
**Why:** Affluence signal beyond HDB. Purchasing power per subzone.
**Source:** URA REALIS (https://www.ura.gov.sg/reis/index)
  - Requires paid subscription OR
  - URA Property Market Statistics (free quarterly aggregates)
  - data.gov.sg: "Private Residential Property Transactions"
**Output:** `private_property_prices.csv`

### 7. Commercial Rental Rates (P2)
**What:** Office/retail/industrial rental rates per sqft by location
**Why:** Economic value of location. Rental = willingness to pay for proximity.
**Source:** URA Rental Statistics (https://www.ura.gov.sg/realEstateIIWeb/rental/search.action)
  - data.gov.sg: "Median Rentals of Office Space"
  - JTC for industrial: https://www.jtc.gov.sg/industrial-land-and-space/pages/statistics.aspx
**Output:** `commercial_rents.csv`

### 8. Business Registration Density (P2)
**What:** Number of registered businesses by SSIC code per postal code
**Why:** Ground truth for business density. Our places (67K) vs ACRA registered (300K+)
**Source:** ACRA BizFile (https://www.bizfile.gov.sg)
  - Bulk data not freely available
  - Alternative: Singstat Table Builder → Business Counts by Industry & Geography
**Output:** `business_density.csv`

---

## WHAT WE NEED — DEMOGRAPHIC ENRICHMENT

### 9. Gridded Population (P2)
**What:** Population density at 100m grid resolution
**Why:** Census is subzone-level (coarse). Gridded pop gives intra-subzone demand variation.
**Source:** WorldPop (https://www.worldpop.org/geodata/summary?id=49687)
  - File: `sgp_ppp_2020_1km_Aggregated_UNadj.tif` (free download)
  - Or: Facebook/Meta High Resolution Settlement Layer
**Output:** `population_grid.tif`

### 10. Household Expenditure Survey (P2)
**What:** Spending patterns by income group, region
**Why:** What do people spend on — food, transport, retail, healthcare
**Source:** Singstat (https://www.singstat.gov.sg/publications/reference/hes)
  - Published every 5 years, latest 2017/18
**Output:** `household_expenditure.csv`

### 11. Age-Specific Services Demand (P2)
**What:** Elderly ratio, young family ratio per subzone
**Why:** Drives demand for different place types (preschool vs aged care)
**Source:** Already have `pop_age_sex.csv` — just need to compute ratios
**Output:** Computed feature in subzone vector

---

## WHAT WE NEED — ENVIRONMENTAL & PHYSICAL

### 12. Elevation / Flood Risk (P3)
**What:** Digital Elevation Model, flood-prone areas
**Why:** Physical constraints, flood risk affects property value and place viability
**Source:** 
  - SRTM 30m DEM (free): https://earthexplorer.usgs.gov/
  - PUB flood maps: https://www.pub.gov.sg/drainage/floodmanagement
**Output:** `elevation.tif`, `flood_zones.geojson`

### 13. Nighttime Lights (P3)
**What:** Satellite-derived nighttime radiance
**Why:** Proxy for economic activity intensity, urbanization level
**Source:** VIIRS DNB (https://eogdata.mines.edu/products/vnl/)
  - Monthly composites, free
**Output:** `nightlights.tif`

### 14. Green Cover / NDVI (P3)
**What:** Vegetation index from satellite imagery
**Why:** Green space quality, urban heat, livability
**Source:** Sentinel-2 via Google Earth Engine or Copernicus
**Output:** `ndvi.tif`

---

## WHAT TO COMPUTE (from existing data)

| Feature | Input | Method |
|---------|-------|--------|
| **Competitor density** | Places | Count same place_type within 100/200/500m of each place |
| **Category composition vector** | Places + Subzones | % of each main_category per subzone (24-dim vector) |
| **Place type composition** | Places + Subzones | Count of each place_type per subzone (165-dim vector) |
| **Brand density** | Places | Branded vs independent ratio per subzone |
| **Transit accessibility** | Transit + Places | Walk-dist to nearest MRT, bus stops within 500m |
| **Land use mix** | Land Use + Subzones | Shannon entropy of land use types per subzone |
| **HDB price signal** | Housing | Median resale PSF per subzone, price trend |
| **Built density** | Buildings (from OSM) | Total built area / subzone area, avg height |
| **Road density** | Roads (from OSM) | Total road length / subzone area, intersection density |
| **Park accessibility** | Amenities + Places | Walk-dist to nearest park, green area ratio |
| **Co-location graph** | Places | Which place_types co-occur within same subzone (PMI matrix) |
| **Age-demand mismatch** | Census + Places | Elderly ratio vs aged care count, child ratio vs preschool count |

---

## DATA SOURCE REGISTRY

| Source | URL | Access | Data |
|--------|-----|--------|------|
| data.gov.sg | https://data.gov.sg | Free API | Many government datasets |
| LTA DataMall | https://datamall.lta.gov.sg | Free (API key) | Transport, traffic, parking |
| URA | https://www.ura.gov.sg | Free/Paid | Property, planning, rental |
| Singstat | https://www.singstat.gov.sg | Free | Census, economic, trade |
| OneMap | https://www.onemap.gov.sg/apidocs/ | Free API | Geocoding, planning info |
| OSM | https://download.geofabrik.de/asia/malaysia-singapore-brunei.html | Free | Roads, buildings, POIs |
| WorldPop | https://www.worldpop.org | Free | Gridded population |
| VIIRS | https://eogdata.mines.edu/products/vnl/ | Free | Nighttime lights |
| Sentinel-2 | https://scihub.copernicus.eu | Free | Satellite imagery (NDVI) |
| JTC | https://www.jtc.gov.sg | Free | Industrial space stats |

---

## PRIORITY ORDER

1. **P0 (Do Now):** Extract roads + buildings from OSM, compute subzone feature vectors
2. **P1 (This Week):** LTA passenger volume, URA property prices
3. **P2 (Next Week):** WorldPop gridded pop, commercial rents, business density
4. **P3 (Later):** Elevation, nightlights, NDVI, flood maps

---

*Last updated: 2026-03-19*
