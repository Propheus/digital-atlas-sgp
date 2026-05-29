# LTA DataMall pull — 2026-05-29

Pulled via `scripts/hex_v11/17_pull_lta_datamall.py` and follow-up direct
downloads, using API key at `~/notes/lta-datamall-key.txt`. Total ~393 MB.

## Key discovery

The `GeospatialWholeIsland?ID=<LayerName>` API supports many more layer IDs
than the documented direct downloads. The mapping is:

- The static-data page (`datamall.lta.gov.sg/content/datamall/en/static-data.html`)
  shows ~35 geospatial dataset names. **The CDN URLs are 403-locked for
  scripted access**, but…
- All those same layers are reachable via the API endpoint
  `https://datamall2.mytransport.sg/ltaodataservice/GeospatialWholeIsland?ID=<LayerName>`
  which returns a presigned S3 link that downloads cleanly.

So `GeospatialWholeIsland` is the canonical scriptable interface to all the
LTA static datasets.

## ✅ Pulled — high-value walkability + transit data (in WGS84 geojson)

### Walking infrastructure (dimension 5 of adequacy — now measurable)
| Layer | Features | Length | Notes |
|---|---|---|---|
| **`coveredlinkway_mar2026.geojson`** | **7,012 segs** | — | **NEW** — sheltered walkway network. The "Walk2Ride" Singapore covered-linkway data. Tropical climate factor finally measurable. |
| **`footpath_mar2026.geojson`** | **110,951 segs** | **3,982 km** | **NEW** — full pedestrian network (every sidewalk). The base for true OSRM-style walking isochrones. |
| **`pedestrainoverheadbridge_underpass_mar2026.geojson`** | **770** | — | 674 POBs + 75 underpasses + 16 footbridges + 4 ped bridges + 1 eco bridge. TYP_CD_DES classifies each. |
| **`roadcrossing_mar2026.geojson`** | **9,695** | **138 km** | Polyline crossings — every zebra / signalised crossing. |
| `kerbline_mar2026.geojson` | 181,513 | 9,242 km | Kerb edges — for road-severance analysis (where can you NOT cross). |
| `railing_mar2026.geojson` | 41,084 | 1,384 km | Pedestrian railings (which side of road has barrier). |
| `streetpaint_mar2026.geojson` | 1,925 | — | Painted markings — some accessibility-relevant. |

### Crossings + signals
| Layer | Features | Notes |
|---|---|---|
| **`trafficlight_mar2026.geojson`** | **45,076 signals** | **NEW** — finally with types! Breakdown: 16,689 Ground Signal · 11,454 Pedestrian Signal · 5,433 Beacon · 4,550 Overhead Signal · 2,636 Green Filter Arrow · 2,043 RAG · **823 Pedestrian Signal with Countdown** · 724 Countdown Timer for Pedestrian · **255 Ground Signal with Green Man+** (elderly-friendly). |

### Cycling (dimension 2 — multi-modal isochrones)
| Layer | Features | Length | Notes |
|---|---|---|---|
| `cycling_path_mar2026.geojson` | **4,830 segs** | **332 km** | Official LTA cycling network (separate from NParks PCN 340 km). |

### Transit (refresh + new attributes)
| File | Records | Notes |
|---|---|---|
| `bus_stops.jsonl` | 5,202 stops | Refresh |
| `bus_services.jsonl` | 788 service-dirs | Peak/off-peak headways |
| `bus_routes.jsonl` | **26,754 records** | Canonical SG stop-to-service mapping (better than GTFS) |
| `train_station_exits_mar2026.geojson` | **595 exits** | Per-exit with `stn_name` + `exit_code` (Macpherson Exit A, B, C) |
| `taxistand_mar2026.geojson` | 371 stands | Fixed taxi stand locations + TYPE_CD_DE |

### Live + forecast (refreshes)
| File | Notes |
|---|---|
| `crowd_forecast/{LINE}.json` × 11 lines | 213 stations × 7d × 24h hourly forecast |
| `train_service_alerts.json` | 2 live messages (TEL + Sengkang LRT planned adjustments) |
| `pv_train_latest.zip` | April 2026 passenger volume (fresher than our Jan 2026 file) |

## ❌ Still missing (need non-LTA sources)

| Wanted | Where to get it | Effort |
|---|---|---|
| **Lift / escalator real-time status** | SMRT Trains API (separate auth) · OneMap accessibility theme · OSM wheelchair tags | Medium |
| **Bicycle racks / parking** | OneMap (LTA published a layer there?) | Low (1 OneMap theme call) |
| **Wheelchair-accessible bus services** | OneMap or manual lookup | Low |
| **Sidewalk width** | Not published by LTA. Could derive from Footpath line-buffer in OSM | Medium |
| **Gradient** | USGS SRTM 30m OR Singapore SLA LiDAR (1m, possibly via OneMap) | Low (SRTM) / Medium (SLA) |
| **Aerial sidewalk detection** | TomTom Orbis Maps · HERE Maps Pedestrian Network · Mapbox Terrain RGB · Microsoft Buildings | Commercial; only useful if SG-specific data above is insufficient |

## Source priority for SG-specific data

1. **LTA DataMall `GeospatialWholeIsland` API** ← what we just used. Covers everything LTA owns.
2. **OneMap.gov.sg `themes` API** ← 100+ thematic layers from many gov agencies. Best for accessibility/barrier-free.
3. **data.gov.sg API** ← lighter slice, mostly survey + statistics.
4. **OSM Singapore** ← good for `covered=yes`, `wheelchair=*` complementing official data.
5. **TomTom / HERE / Mapbox** ← would only marginally improve SG-specific coverage. For a Singapore-focused project, the LTA + OneMap stack is more authoritative.

## What this unlocks in adequacy v3

| Adequacy dimension | Currently | After this pull |
|---|---|---|
| **5. Walkability quality — shelter** | 0% measured (no data) | Compute `sheltered_walkway_length_m` per hex from CoveredLinkWay |
| **5. Walkability quality — severance** | Proxy via crossings count | Real severance via KerbLine + RoadCrossing + Railing |
| **5. Walkability quality — crossings** | Traffic signals count (no type) | Distinguish Ped Signal · Countdown · Green Man Plus · POB |
| **6. Inclusivity / barrier-free** | 0% measured | Partial (`Green Man +` count as elderly proxy) — full requires SMRT lift data |
| **2. Reachability — pedestrian** | Centroid haversine to nearest amenity | True walking isochrones via Footpath (3,982 km) |
| **2. Reachability — cycling** | Not measured | Cycling network + PCN combined |
| **4. Connectivity — exit choice** | Single station ID | Pick the closest *exit* (595) — last-mile improvement |
| **3. Frequency / crowding** | Static daily taps | Hourly 7-day crowd forecast per line |

## Source reference

- Static page: https://datamall.lta.gov.sg/content/datamall/en/static-data.html
- API base: https://datamall2.mytransport.sg/ltaodataservice/
- Auth: AccountKey header (key file `~/notes/lta-datamall-key.txt`)
- Pulled: 2026-05-29 (Mar 2026 vintage data)
