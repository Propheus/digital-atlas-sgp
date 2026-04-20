import { useState, useEffect, useRef, useMemo, useCallback } from 'react'
import mapboxgl from 'mapbox-gl'
import 'mapbox-gl/dist/mapbox-gl.css'
import './App.css'

mapboxgl.accessToken = 'MAPBOX_TOKEN_PLACEHOLDER'

// ═══════════════════════════════════════════════════════════
// METRICS — each metric has: label, key, formatter, color stops
// ═══════════════════════════════════════════════════════════
const METRICS = {
  walkability_score_v2: {
    label: '15-Min City Score',
    key: 'walkability_score_v2',
    desc: 'Access to 6 essentials (MRT, hawker, park, clinic, supermarket, bus) within walking distance',
    fmt: v => v != null ? Math.round(v) : '—',
    stops: [[0,'#1e0e0f'],[15,'#4a1e20'],[30,'#8b2c30'],[45,'#cc5f3f'],[60,'#e8a84a'],[80,'#a8e066'],[100,'#14b8a6']],
  },
  transit_gap_score: {
    label: 'Transit Gap',
    key: 'transit_gap_score',
    desc: 'Population × distance to MRT. High = underserved residential zones',
    fmt: v => v != null ? Math.round(v).toLocaleString() : '—',
    stops: [[0,'#0f1a1b'],[500,'#2a4248'],[2000,'#7a4e3a'],[5000,'#cc6b3a'],[12000,'#ef4444'],[20000,'#ff3333']],
  },
  population: {
    label: 'Population',
    key: 'population',
    desc: 'Dasymetrically distributed from census using building footprints',
    fmt: v => v != null ? Math.round(v).toLocaleString() : '—',
    stops: [[0,'#0a1a1c'],[500,'#133035'],[2000,'#1e5b5e'],[5000,'#20b2aa'],[10000,'#6de4d4'],[20000,'#c7fff6']],
  },
  dist_mrt_m: {
    label: 'Distance to MRT',
    key: 'dist_mrt_m',
    desc: 'Haversine distance to nearest MRT station (real meters)',
    fmt: v => v != null ? `${Math.round(v)}m` : '—',
    stops: [[0,'#14b8a6'],[300,'#7bd6c0'],[600,'#e8c760'],[1000,'#ef8e3e'],[2000,'#d94747'],[5000,'#4a1e20']],
  },
  elderly_transit_stress: {
    label: 'Elderly Transit Stress',
    key: 'elderly_transit_stress',
    desc: 'Elderly count × distance to MRT. High = mobility-challenged seniors far from rail',
    fmt: v => v != null ? Math.round(v).toLocaleString() : '—',
    stops: [[0,'#0a1a1c'],[10,'#1a2c35'],[100,'#4a4246'],[500,'#cc4444'],[1500,'#ff2222']],
  },
  bldg_count: {
    label: 'Building Density',
    key: 'bldg_count',
    desc: 'Number of buildings in this 0.12 km² hex',
    fmt: v => v != null ? Math.round(v).toLocaleString() : '—',
    stops: [[0,'#0a0f1a'],[20,'#1e3a3c'],[80,'#3e6e5a'],[200,'#20b2aa'],[400,'#7bd4c0'],[800,'#c7fff6']],
  },
  hex_jam_pct: {
    label: 'Traffic Jam %',
    key: 'hex_jam_pct',
    desc: 'Share of road segments jammed (<20 km/h) in this hex right now',
    fmt: v => v != null ? `${Math.round(v)}%` : '—',
    stops: [[0,'#0a1a1c'],[10,'#1a3a38'],[30,'#e8c760'],[50,'#ef8e3e'],[80,'#d94747'],[100,'#ff1a1a']],
  },
  p_affluence_idx: {
    label: 'Affluence Index',
    key: 'p_affluence_idx',
    desc: 'NVIDIA persona composite: university % × professional % × finance industry',
    fmt: v => v != null ? v.toFixed(3) : '—',
    stops: [[0,'#1e0e1a'],[0.1,'#3a1e3a'],[0.2,'#6a3e6a'],[0.3,'#a078b0'],[0.4,'#e0b8f0']],
  },
  max_floors: {
    label: 'Max Building Height',
    key: 'max_floors',
    desc: 'Tallest building in hex (floors). CBD peaks at 70, HDB 30+, landed 1-4',
    fmt: v => v != null ? `${Math.round(v)} fl` : '—',
    stops: [[0,'#0a0f1a'],[3,'#243a52'],[10,'#3e6e8c'],[25,'#60a5fa'],[40,'#a8c7fa'],[70,'#e0edff']],
  },
  avg_gpr: {
    label: 'Plot Ratio (GPR)',
    key: 'avg_gpr',
    desc: 'URA Master Plan Gross Plot Ratio — how much can be built',
    fmt: v => v != null ? v.toFixed(2) : '—',
    stops: [[0,'#0a1a1c'],[0.8,'#1e3a3c'],[1.8,'#3e6e5a'],[2.5,'#20b2aa'],[4,'#6de4d4'],[8,'#c7fff6']],
  },
}

const REGION_COLORS = {
  'CENTRAL REGION': '#20B2AA',
  'EAST REGION': '#60A5FA',
  'NORTH REGION': '#34D399',
  'NORTH-EAST REGION': '#F59E0B',
  'WEST REGION': '#EC4899',
}

// Feature groups for the detail panel
const DETAIL_GROUPS = [
  { title: 'Population', color: '#60A5FA', items: [
    ['population', 'Residents', v => v?.toLocaleString()],
    ['pop_ring1', 'Ring-1 Pop (7 hexes)', v => v?.toLocaleString()],
    ['pop_ring2', 'Ring-2 Pop (19 hexes)', v => v?.toLocaleString()],
    ['elderly_count', 'Elderly', v => v?.toLocaleString()],
    ['elderly_pct', 'Elderly %', v => v != null ? `${v.toFixed(1)}%` : null],
    ['children_count', 'Children', v => v?.toLocaleString()],
    ['walking_dependent_count', 'Walking-dependent', v => v?.toLocaleString()],
  ]},
  { title: 'Buildings', color: '#A78BFA', items: [
    ['bldg_count', 'Total buildings', v => v?.toLocaleString()],
    ['hdb_blocks', 'HDB blocks', v => v?.toLocaleString()],
    ['bldg_private_residential', 'Private residential', v => v?.toLocaleString()],
    ['bldg_commercial', 'Commercial', v => v?.toLocaleString()],
    ['bldg_industrial', 'Industrial', v => v?.toLocaleString()],
    ['bldg_institutional', 'Institutional', v => v?.toLocaleString()],
    ['avg_floors', 'Avg floors', v => v != null ? v.toFixed(1) : null],
    ['max_floors', 'Max floors', v => v ? `${Math.round(v)}` : null],
    ['max_height', 'Max height', v => v ? `${Math.round(v)} m` : null],
    ['avg_gpr', 'GPR allowance', v => v != null ? v.toFixed(2) : null],
  ]},
  { title: 'Transit', color: '#34D399', items: [
    ['mrt_stations', 'MRT stations', v => v],
    ['lrt_stations', 'LRT stations', v => v],
    ['bus_stops', 'Bus stops', v => v],
    ['dist_mrt_m', 'Nearest MRT', v => v ? `${Math.round(v)} m` : null],
    ['dist_bus_m', 'Nearest bus', v => v ? `${Math.round(v)} m` : null],
    ['mrt_daily_taps', 'MRT daily taps', v => v?.toLocaleString()],
    ['bus_daily_taps', 'Bus daily taps', v => v?.toLocaleString()],
    ['transit_daily_taps', 'Total transit taps', v => v?.toLocaleString()],
  ]},
  { title: 'Amenities & Access', color: '#F59E0B', items: [
    ['places_total', 'Total places', v => v?.toLocaleString()],
    ['hawker_centres', 'Hawker centres', v => v],
    ['dist_hawker_m', 'Nearest hawker', v => v ? `${Math.round(v)} m` : null],
    ['parks', 'Parks', v => v],
    ['dist_park_m', 'Nearest park', v => v ? `${Math.round(v)} m` : null],
    ['chas_clinics', 'CHAS clinics', v => v],
    ['dist_clinic_m', 'Nearest clinic', v => v ? `${Math.round(v)} m` : null],
    ['supermarkets', 'Supermarkets', v => v],
    ['dist_super_m', 'Nearest supermarket', v => v ? `${Math.round(v)} m` : null],
    ['formal_schools', 'Formal schools', v => v],
    ['preschools_gov', 'Govt preschools', v => v],
    ['hotels', 'Hotels', v => v],
    ['tourist_attractions', 'Attractions', v => v],
  ]},
  { title: 'Walkability', color: '#14B8A6', items: [
    ['walkability_score_v2', '15-Min City Score', v => `${Math.round(v)}/100`],
    ['amenity_types_nearby', 'Amenity types ≤350m', v => `${v}/6`],
  ]},
  { title: 'Traffic & Congestion', color: '#EF4444', items: [
    ['hex_avg_speed_kmh', 'Avg speed', v => v ? `${v.toFixed(1)} km/h` : null],
    ['hex_jam_pct', 'Jam %', v => v != null ? `${v.toFixed(1)}%` : null],
    ['hex_flow_pct', 'Free-flow %', v => v != null ? `${v.toFixed(1)}%` : null],
    ['hex_seg_count', 'Road segments sampled', v => v],
    ['road_cat_expressway', 'Expressway segments', v => v],
    ['road_cat_major_arterial', 'Major arterials', v => v],
  ]},
  { title: 'Signals', color: '#EC4899', items: [
    ['sig_ground', 'Ground signals', v => v],
    ['sig_overhead', 'Overhead signals', v => v],
    ['ped_standard', 'Standard ped crossings', v => v],
    ['ped_countdown', 'Countdown crossings', v => v],
    ['ped_elderly', 'Green Man+ (elderly)', v => v],
    ['bicycle_signal', 'Bicycle crossings', v => v],
  ]},
  { title: 'Housing Market', color: '#8B5CF6', items: [
    ['hdb_median_psf', 'HDB median $/psf', v => v ? `$${Math.round(v)}` : null],
    ['hdb_median_price', 'HDB median price', v => v ? `$${Math.round(v).toLocaleString()}` : null],
  ]},
  { title: 'NVIDIA Personas', color: '#76B900', items: [
    ['p_median_age', 'Median age', v => v != null ? v.toFixed(1) : null],
    ['p_pct_university', 'University %', v => v != null ? `${(v*100).toFixed(1)}%` : null],
    ['p_pct_professional', 'Professional %', v => v != null ? `${(v*100).toFixed(1)}%` : null],
    ['p_pct_finance', 'Finance industry %', v => v != null ? `${(v*100).toFixed(1)}%` : null],
    ['p_pct_tech', 'Tech industry %', v => v != null ? `${(v*100).toFixed(1)}%` : null],
    ['p_hobby_food', 'Food hobby %', v => v != null ? `${(v*100).toFixed(1)}%` : null],
    ['p_hobby_fitness', 'Fitness hobby %', v => v != null ? `${(v*100).toFixed(1)}%` : null],
    ['p_affluence_idx', 'Affluence index', v => v != null ? v.toFixed(3) : null],
    ['p_youth_idx', 'Youth index', v => v != null ? v.toFixed(3) : null],
    ['p_family_idx', 'Family index', v => v != null ? v.toFixed(3) : null],
  ]},
  { title: 'Adequacy Gaps', color: '#F97316', items: [
    ['transit_gap_score', 'Transit gap score', v => v?.toLocaleString()],
    ['elderly_transit_stress', 'Elderly transit stress', v => v?.toLocaleString()],
    ['clinic_gap_score', 'Clinic gap score', v => v?.toLocaleString()],
    ['school_gap_score', 'School gap score', v => v?.toLocaleString()],
  ]},
]

function getDNATags(p) {
  const tags = []
  if (p.dist_mrt_m <= 300) tags.push({ label: 'MRT Adjacent', color: '#14B8A6' })
  else if (p.dist_mrt_m > 1500 && p.population > 1000) tags.push({ label: 'Transit Desert', color: '#EF4444' })
  if (p.walkability_score_v2 >= 60) tags.push({ label: 'Walkable', color: '#10B981' })
  else if (p.walkability_score_v2 < 15 && p.population > 500) tags.push({ label: 'Car-Dependent', color: '#F97316' })
  if (p.hdb_blocks >= 5) tags.push({ label: 'HDB Estate', color: '#8B5CF6' })
  if (p.bldg_commercial >= 10) tags.push({ label: 'Commercial', color: '#6366F1' })
  if (p.bldg_industrial >= 20) tags.push({ label: 'Industrial', color: '#78716C' })
  if (p.max_floors >= 30) tags.push({ label: 'High-Rise', color: '#EC4899' })
  if (p.hex_jam_pct >= 50) tags.push({ label: 'Gridlock', color: '#DC2626' })
  if (p.hawker_centres >= 2) tags.push({ label: 'Hawker Hub', color: '#FBBF24' })
  if (p.hotels >= 3) tags.push({ label: 'Tourist Zone', color: '#A78BFA' })
  if (p.elderly_pct > 1 && p.population > 2000) tags.push({ label: 'Silver Cluster', color: '#9CA3AF' })
  if (p.p_affluence_idx >= 0.3) tags.push({ label: 'Affluent', color: '#C084FC' })
  if (p.places_total >= 200) tags.push({ label: 'Place Dense', color: '#F97316' })
  if (p.transit_gap_score >= 5000) tags.push({ label: 'Transit Gap', color: '#EF4444' })
  return tags.slice(0, 8)
}

// ═══════════════════════════════════════════════════════════
// EXPLAINABILITY — break down each metric into its components
// ═══════════════════════════════════════════════════════════
function explainWalkability(h) {
  // From computation: walk_mrt × 25 + walk_hawker × 20 + walk_park × 15 + walk_clinic × 15 + walk_super × 15 + walk_bus × 10
  const score = (d, max) => Math.max(0, 1 - (d || 9999) / max)
  const comps = [
    { name: 'MRT access', key: 'dist_mrt_m', max_m: 800, weight: 25, dist: h.dist_mrt_m, color: '#8B5CF6' },
    { name: 'Hawker food', key: 'dist_hawker_m', max_m: 600, weight: 20, dist: h.dist_hawker_m, color: '#F59E0B' },
    { name: 'Parks', key: 'dist_park_m', max_m: 600, weight: 15, dist: h.dist_park_m, color: '#22C55E' },
    { name: 'Clinics', key: 'dist_clinic_m', max_m: 600, weight: 15, dist: h.dist_clinic_m, color: '#EF4444' },
    { name: 'Supermarket', key: 'dist_super_m', max_m: 500, weight: 15, dist: h.dist_super_m, color: '#3B82F6' },
    { name: 'Bus stops', key: 'dist_bus_m', max_m: 300, weight: 10, dist: h.dist_bus_m, color: '#14B8A6' },
  ]
  comps.forEach(c => {
    c.normalised = score(c.dist, c.max_m)
    c.contribution = Math.round(c.normalised * c.weight * 10) / 10
  })
  const total = comps.reduce((s, c) => s + c.contribution, 0)
  return { comps, total: Math.round(total) }
}

function explainTransitGap(h) {
  const pop = h.population || 0
  const dist = h.dist_mrt_m || 0
  const over800 = dist > 800
  const score = over800 && pop > 500 ? pop * Math.min(dist / 1000, 3) : 0
  return {
    pop, dist,
    is_gap: over800 && pop > 500,
    score: Math.round(score),
    formula: 'population × min(dist_mrt_m / 1000, 3)',
    condition: `Applies when distance > 800m AND population > 500`,
    severity: score >= 10000 ? 'severe' : score >= 3000 ? 'high' : score >= 1000 ? 'moderate' : 'low',
  }
}

function explainElderlyStress(h) {
  const elderly = h.elderly_count || 0
  const dist = h.dist_mrt_m || 0
  const score = elderly > 0 ? Math.round(elderly * dist / 1000) : 0
  return {
    elderly, dist, score,
    formula: 'elderly_count × dist_mrt_m / 1000',
    severity: score >= 500 ? 'severe' : score >= 100 ? 'high' : score >= 20 ? 'moderate' : 'low',
    narrative: elderly === 0 ? 'No elderly residents.' :
      elderly < 10 ? `Only ${elderly} elderly residents — low absolute stress.` :
      dist < 400 ? `${elderly} elderly within 400m of MRT — well served.` :
      dist < 800 ? `${elderly} elderly at ${Math.round(dist)}m — moderate walking distance.` :
      `${elderly} elderly at ${Math.round(dist)}m — significant burden for mobility-challenged.`
  }
}

function generateNarrative(h) {
  const pop = h.population || 0
  const dist = h.dist_mrt_m || 0
  const walk = h.walkability_score_v2 || 0
  const bldg = h.bldg_count || 0
  const hdb = h.hdb_blocks || 0
  const commercial = h.bldg_commercial || 0
  const industrial = h.bldg_industrial || 0
  const floors = h.max_floors || 0
  const jam = h.hex_jam_pct || 0
  const hawkers = h.hawker_centres || 0
  const hotels = h.hotels || 0
  const places = h.places_total || 0

  const parts = []

  // Zone type
  if (pop === 0 && bldg > 0) {
    if (industrial > 10) parts.push(`This is an industrial zone with ${industrial} industrial buildings and no residents.`)
    else if (commercial > 5) parts.push(`This is a commercial zone with ${commercial} office/retail buildings and no residents.`)
    else parts.push(`This 0.12 km² hex has ${bldg} buildings but no residents — likely infrastructure or mixed-use.`)
  } else if (hdb >= 10) {
    parts.push(`HDB estate with ${hdb} public housing blocks housing ${pop.toLocaleString()} residents${floors >= 20 ? `, max ${Math.round(floors)} floors` : ''}.`)
  } else if (pop > 500) {
    parts.push(`Residential zone with ${pop.toLocaleString()} residents across ${bldg} buildings${hdb > 0 ? ` (${hdb} HDB blocks)` : ''}.`)
  } else if (pop > 0) {
    parts.push(`Sparsely populated — ${pop} residents in ${bldg} buildings.`)
  }

  // Transit story
  if (dist <= 300) parts.push(`Excellent transit access — an MRT station is only ${Math.round(dist)}m away.`)
  else if (dist <= 600) parts.push(`Good transit access — MRT at ${Math.round(dist)}m (~${Math.round(dist/80)} min walk).`)
  else if (dist <= 1000 && pop > 500) parts.push(`Moderate walk to MRT — ${Math.round(dist)}m (~${Math.round(dist/80)} min). Bus stops partially compensate.`)
  else if (dist > 1000 && pop > 1000) parts.push(`⚠ Transit-deficient — nearest MRT is ${Math.round(dist)}m away (~${Math.round(dist/80)} min walk). ${pop.toLocaleString()} residents rely on bus or car.`)

  // Walkability
  if (walk >= 60) parts.push(`Highly walkable: score ${Math.round(walk)}/100 with ${h.amenity_types_nearby || 0}/6 amenity types within 350m.`)
  else if (walk >= 30) parts.push(`Moderately walkable: score ${Math.round(walk)}/100.`)
  else if (pop > 500) parts.push(`Low walkability: score ${Math.round(walk)}/100 — most essentials require a longer walk or vehicle.`)

  // Commercial hooks
  if (hawkers >= 2) parts.push(`Strong food scene — ${hawkers} government hawker centres in this hex alone.`)
  if (hotels >= 3) parts.push(`Tourist corridor — ${hotels} hotels, likely high daytime visitor traffic.`)
  if (places >= 200) parts.push(`Commercially dense — ${places.toLocaleString()} businesses across all categories.`)

  // Congestion
  if (jam >= 50) parts.push(`⚠ Severe congestion — ${Math.round(jam)}% of road segments jammed in latest LTA snapshot.`)

  return parts.join(' ')
}

function DetailPanel({ hex, onClose }) {
  if (!hex) return null
  const [tab, setTab] = useState('overview')
  const [openGroups, setOpenGroups] = useState({ Population: true, Buildings: false, Transit: true, 'Amenities & Access': false, Walkability: true, 'Traffic & Congestion': false, Signals: false, 'Housing Market': false, 'NVIDIA Personas': false, 'Adequacy Gaps': true })
  const toggle = t => setOpenGroups(prev => ({ ...prev, [t]: !prev[t] }))
  const tags = getDNATags(hex)

  const gapColor = hex.transit_gap_score > 5000 ? '#EF4444' : hex.transit_gap_score > 1000 ? '#F59E0B' : '#6B7280'
  const walkColor = hex.walkability_score_v2 >= 60 ? '#10B981' : hex.walkability_score_v2 >= 30 ? '#F59E0B' : '#EF4444'

  const walkExplain = explainWalkability(hex)
  const transitExplain = explainTransitGap(hex)
  const elderlyExplain = explainElderlyStress(hex)
  const narrative = generateNarrative(hex)

  return (
    <div className="panel">
      <button className="panel-close" onClick={onClose}>&times;</button>
      <div className="ph">
        <div className="ph-code">HEX {hex.hex_id?.slice(-8)}</div>
        <h2 className="ph-name">{hex.parent_subzone_name || 'Unknown'}</h2>
        <div className="ph-meta">
          <span className="ph-pa">{hex.parent_pa}</span>
          <span className="ph-sep">·</span>
          <span className="ph-region">{hex.parent_region?.replace(' REGION', '')}</span>
          <span className="ph-sep">·</span>
          <span>{hex.area_km2?.toFixed(2) || 0.12} km²</span>
        </div>
        {tags.length > 0 && (
          <div className="dna-tags">
            {tags.map(t => (
              <span key={t.label} className="dna-tag" style={{ color: t.color, borderColor: `${t.color}66`, background: `${t.color}14` }}>{t.label}</span>
            ))}
          </div>
        )}
      </div>
      <div className="hero">
        <div className="hc">
          <div className="hv">{hex.population?.toLocaleString() || 0}</div>
          <div className="hl">Residents</div>
        </div>
        <div className="hc">
          <div className="hv" style={{ color: walkColor }}>{Math.round(hex.walkability_score_v2 || 0)}</div>
          <div className="hl">Walkability</div>
        </div>
        <div className="hc">
          <div className="hv">{hex.dist_mrt_m ? `${Math.round(hex.dist_mrt_m)}m` : '—'}</div>
          <div className="hl">To MRT</div>
        </div>
        <div className="hc">
          <div className="hv" style={{ color: gapColor }}>{hex.transit_gap_score ? Math.round(hex.transit_gap_score).toLocaleString() : '0'}</div>
          <div className="hl">Transit Gap</div>
        </div>
      </div>

      <div className="tabs">
        <button className={`tab ${tab === 'overview' ? 'active' : ''}`} onClick={() => setTab('overview')}>Overview</button>
        <button className={`tab ${tab === 'explain' ? 'active' : ''}`} onClick={() => setTab('explain')}>Explain</button>
      </div>

      {tab === 'explain' && (
        <div className="explain">
          {/* Narrative summary */}
          <div className="ex-section">
            <div className="ex-title">📖 What's going on here?</div>
            <div className="ex-narrative">{narrative || 'No significant signals to explain for this hex.'}</div>
          </div>

          {/* Walkability breakdown */}
          <div className="ex-section">
            <div className="ex-title">🚶 Walkability Score — {walkExplain.total}/100</div>
            <div className="ex-formula">Weighted sum of 6 amenity distances, each scored 0-1 by (1 − dist/max_walkable_m)</div>
            <div className="ex-bars">
              {walkExplain.comps.map(c => (
                <div key={c.name} className="ex-bar-row">
                  <span className="ex-bar-name" style={{ color: c.color }}>{c.name}</span>
                  <span className="ex-bar-val">{c.dist != null ? `${Math.round(c.dist)}m` : 'n/a'}</span>
                  <div className="ex-bar-track">
                    <div className="ex-bar-fill" style={{ width: `${(c.contribution / c.weight) * 100}%`, background: c.color }} />
                  </div>
                  <span className="ex-bar-contrib">{c.contribution}/{c.weight}</span>
                </div>
              ))}
            </div>
            <div className="ex-note">
              {walkExplain.total >= 60 ? '✓ Highly walkable — most essentials within 10-min walk.' :
               walkExplain.total >= 30 ? 'Moderate — some amenities need longer walks or bus.' :
               '⚠ Low walkability — residents likely need a vehicle for daily needs.'}
            </div>
          </div>

          {/* Transit gap breakdown */}
          <div className="ex-section">
            <div className="ex-title">🚇 Transit Gap — {transitExplain.score.toLocaleString()}</div>
            <div className="ex-formula">{transitExplain.formula}</div>
            <div className="ex-calc">
              <div className="ex-calc-row"><span>Population</span><b>{transitExplain.pop.toLocaleString()}</b></div>
              <div className="ex-calc-row"><span>Distance to MRT</span><b>{Math.round(transitExplain.dist)}m</b></div>
              <div className="ex-calc-row"><span>Walking time</span><b>~{Math.round(transitExplain.dist / 80)} min</b></div>
              <div className="ex-calc-row"><span>Gap threshold</span><b>&gt; 800m + &gt; 500 residents</b></div>
              <div className="ex-calc-row ex-calc-total">
                <span>Score</span>
                <b className={`sev-${transitExplain.severity}`}>
                  {transitExplain.is_gap ? `${transitExplain.score.toLocaleString()} (${transitExplain.severity})` : '0 (not a gap)'}
                </b>
              </div>
            </div>
            <div className="ex-note">
              {!transitExplain.is_gap ? '✓ No transit gap — either close enough to MRT, or too few residents to flag.' :
               transitExplain.severity === 'severe' ? '⚠ Severe gap — priority candidate for new MRT/LRT station.' :
               transitExplain.severity === 'high' ? '⚠ Significant gap — needs improved bus feeders or future rail.' :
               'Moderate gap — watch for increases as population grows.'}
            </div>
          </div>

          {/* Elderly transit stress */}
          <div className="ex-section">
            <div className="ex-title">👴 Elderly Transit Stress — {elderlyExplain.score.toLocaleString()}</div>
            <div className="ex-formula">{elderlyExplain.formula}</div>
            <div className="ex-calc">
              <div className="ex-calc-row"><span>Elderly residents (65+)</span><b>{elderlyExplain.elderly.toLocaleString()}</b></div>
              <div className="ex-calc-row"><span>Distance to MRT</span><b>{Math.round(elderlyExplain.dist)}m</b></div>
              <div className="ex-calc-row ex-calc-total">
                <span>Stress score</span>
                <b className={`sev-${elderlyExplain.severity}`}>{elderlyExplain.score.toLocaleString()} ({elderlyExplain.severity})</b>
              </div>
            </div>
            <div className="ex-note">{elderlyExplain.narrative}</div>
          </div>

          {/* Building context */}
          {hex.bldg_count > 0 && (
            <div className="ex-section">
              <div className="ex-title">🏢 Building Context</div>
              <div className="ex-calc">
                <div className="ex-calc-row"><span>Total buildings</span><b>{hex.bldg_count.toLocaleString()}</b></div>
                {hex.hdb_blocks > 0 && <div className="ex-calc-row"><span>HDB blocks</span><b>{hex.hdb_blocks} <span className="ex-pct">({Math.round(hex.hdb_blocks / hex.bldg_count * 100)}%)</span></b></div>}
                {hex.bldg_private_residential > 0 && <div className="ex-calc-row"><span>Private residential</span><b>{hex.bldg_private_residential}</b></div>}
                {hex.bldg_commercial > 0 && <div className="ex-calc-row"><span>Commercial</span><b>{hex.bldg_commercial}</b></div>}
                {hex.bldg_industrial > 0 && <div className="ex-calc-row"><span>Industrial</span><b>{hex.bldg_industrial}</b></div>}
                {hex.max_floors > 0 && <div className="ex-calc-row"><span>Tallest building</span><b>{Math.round(hex.max_floors)} floors{hex.max_height ? ` (${Math.round(hex.max_height)}m)` : ''}</b></div>}
                {hex.avg_floors > 0 && <div className="ex-calc-row"><span>Avg building height</span><b>{hex.avg_floors.toFixed(1)} floors</b></div>}
              </div>
              <div className="ex-note">
                {hex.hdb_blocks >= 10 ? `Heartland HDB estate — ${Math.round(hex.hdb_blocks / hex.bldg_count * 100)}% of buildings are public housing.` :
                 hex.bldg_commercial >= hex.bldg_count * 0.3 ? `Commercial-dominant — office/retail focused.` :
                 hex.bldg_industrial >= hex.bldg_count * 0.3 ? `Industrial zone — manufacturing/logistics.` :
                 `Mixed-use zone.`}
              </div>
            </div>
          )}

          {/* Adequacy summary badge */}
          <div className="ex-section ex-summary">
            <div className="ex-title">📊 Adequacy Summary</div>
            <div className="ex-scores">
              <div className={`ex-score ${hex.walkability_score_v2 >= 60 ? 'good' : hex.walkability_score_v2 >= 30 ? 'ok' : 'bad'}`}>
                <div className="ex-score-label">Walkability</div>
                <div className="ex-score-val">{Math.round(hex.walkability_score_v2 || 0)}</div>
              </div>
              <div className={`ex-score ${(hex.dist_mrt_m || 9999) <= 500 ? 'good' : (hex.dist_mrt_m || 9999) <= 1000 ? 'ok' : 'bad'}`}>
                <div className="ex-score-label">Transit</div>
                <div className="ex-score-val">{hex.dist_mrt_m ? `${Math.round(hex.dist_mrt_m)}m` : '—'}</div>
              </div>
              <div className={`ex-score ${(hex.transit_gap_score || 0) < 1000 ? 'good' : (hex.transit_gap_score || 0) < 5000 ? 'ok' : 'bad'}`}>
                <div className="ex-score-label">Gap</div>
                <div className="ex-score-val">{(hex.transit_gap_score || 0).toLocaleString()}</div>
              </div>
              <div className={`ex-score ${(hex.hex_jam_pct || 0) < 20 ? 'good' : (hex.hex_jam_pct || 0) < 50 ? 'ok' : 'bad'}`}>
                <div className="ex-score-label">Traffic</div>
                <div className="ex-score-val">{Math.round(hex.hex_jam_pct || 0)}%</div>
              </div>
            </div>
          </div>
        </div>
      )}

      {tab === 'overview' && (
      <div className="groups">
        {DETAIL_GROUPS.map(group => {
          const rows = group.items
            .map(([key, label, fmt]) => {
              const v = hex[key]
              if (v == null || v === 0) return null
              try {
                const val = fmt(v)
                if (val == null) return null
                return { key, label, val: String(val) }
              } catch { return null }
            })
            .filter(Boolean)
          if (rows.length === 0) return null
          const isOpen = openGroups[group.title]
          return (
            <div key={group.title} className="group">
              <button className="group-h" onClick={() => toggle(group.title)}>
                <span className="gdot" style={{ background: group.color }} />
                <span className="gname">{group.title}</span>
                <span className="gcount">{rows.length}</span>
                <span className={`chev ${isOpen ? 'open' : ''}`}>&#9656;</span>
              </button>
              {isOpen && (
                <div className="group-body">
                  {rows.map(r => (
                    <div key={r.key} className="row">
                      <span className="rl">{r.label}</span>
                      <span className="rv">{r.val}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )
        })}
      </div>
      )}
    </div>
  )
}

export default function App() {
  const mapContainer = useRef(null)
  const mapRef = useRef(null)
  const popupRef = useRef(null)
  const metricRef = useRef('transit_gap_score')
  const [geojson, setGeojson] = useState(null)
  const [metric, setMetric] = useState('transit_gap_score')
  const [selected, setSelected] = useState(null)
  const [mapReady, setMapReady] = useState(false)
  const [regionFilter, setRegionFilter] = useState(null)
  const [populatedOnly, setPopulatedOnly] = useState(true)
  const [stats, setStats] = useState(null)
  const [view, setView] = useState('map')

  useEffect(() => { metricRef.current = metric }, [metric])

  // Load GeoJSON
  useEffect(() => {
    console.log('Loading hex GeoJSON...')
    fetch(`${import.meta.env.BASE_URL}data/hex.geojson`)
      .then(r => r.json())
      .then(data => {
        console.log(`Loaded ${data.features.length} hexes`)
        setGeojson(data)
        const totalPop = data.features.reduce((s, f) => s + (f.properties.population || 0), 0)
        const totalBldg = data.features.reduce((s, f) => s + (f.properties.bldg_count || 0), 0)
        const totalHDB = data.features.reduce((s, f) => s + (f.properties.hdb_blocks || 0), 0)
        setStats({
          hexes: data.features.length,
          pop: Math.round(totalPop),
          bldgs: Math.round(totalBldg),
          hdb: Math.round(totalHDB),
        })
      })
      .catch(e => console.error('GeoJSON error:', e))
  }, [])

  const regions = useMemo(() => {
    if (!geojson) return []
    const s = new Set()
    geojson.features.forEach(f => { if (f.properties.parent_region) s.add(f.properties.parent_region) })
    return [...s].sort()
  }, [geojson])

  // Mapbox filter
  const filter = useMemo(() => {
    const conds = []
    if (populatedOnly) conds.push(['>', ['coalesce', ['get', 'population'], 0], 0])
    if (regionFilter) conds.push(['==', ['get', 'parent_region'], regionFilter])
    if (conds.length === 0) return null
    if (conds.length === 1) return conds[0]
    return ['all', ...conds]
  }, [populatedOnly, regionFilter])

  // Init map
  useEffect(() => {
    if (!mapContainer.current || mapRef.current) return
    const map = new mapboxgl.Map({
      container: mapContainer.current,
      style: 'mapbox://styles/mapbox/dark-v11',
      center: [103.8198, 1.3521],
      zoom: 11.2,
      attributionControl: false,
    })
    map.addControl(new mapboxgl.NavigationControl(), 'bottom-right')
    popupRef.current = new mapboxgl.Popup({ closeButton: false, closeOnClick: false, className: 'hex-popup', offset: 8 })
    map.on('load', () => {
      console.log('Map loaded')
      setMapReady(true)
    })
    mapRef.current = map
    return () => { map.remove(); mapRef.current = null }
  }, [])

  // Add source + layers
  useEffect(() => {
    const map = mapRef.current
    if (!mapReady || !geojson || !map || map.getSource('hex')) return
    map.addSource('hex', { type: 'geojson', data: geojson })
    const m = METRICS[metric]
    map.addLayer({
      id: 'hex-fill',
      type: 'fill',
      source: 'hex',
      paint: {
        'fill-color': ['interpolate', ['linear'], ['coalesce', ['to-number', ['get', m.key]], 0], ...m.stops.flat()],
        'fill-opacity': ['case', ['>', ['coalesce', ['get', 'population'], 0], 0], 0.82, 0.5],
      },
    })
    map.addLayer({
      id: 'hex-line',
      type: 'line',
      source: 'hex',
      paint: { 'line-color': 'rgba(32,178,170,0.35)', 'line-width': 0.4 },
    })
    map.addLayer({
      id: 'hex-hl',
      type: 'line',
      source: 'hex',
      paint: { 'line-color': '#fff', 'line-width': 2.5, 'line-opacity': 1 },
      filter: ['==', ['get', 'hex_id'], '__none__'],
    })

    map.on('mousemove', 'hex-fill', e => {
      map.getCanvas().style.cursor = 'pointer'
      const f = e.features?.[0]
      if (f && popupRef.current) {
        const p = f.properties
        const cm = METRICS[metricRef.current]
        const v = p[cm.key]
        const numV = typeof v === 'string' ? parseFloat(v) : v
        popupRef.current
          .setLngLat(e.lngLat)
          .setHTML(`<b>${p.parent_subzone_name || 'Unknown'}</b><br/>${cm.label}: <b style="color:#14b8a6">${cm.fmt(numV)}</b><br/><span style="color:#888">Pop: ${(p.population||0).toLocaleString()} · ${p.parent_pa}</span>`)
          .addTo(map)
      }
    })
    map.on('mouseleave', 'hex-fill', () => {
      map.getCanvas().style.cursor = ''
      popupRef.current?.remove()
    })
    map.on('click', 'hex-fill', e => {
      const f = e.features?.[0]
      if (f) {
        const p = { ...f.properties }
        // Parse string numbers
        for (const k in p) {
          if (typeof p[k] === 'string' && !isNaN(Number(p[k])) && p[k] !== '' && !['hex_id','parent_subzone','parent_subzone_name','parent_pa','parent_region'].includes(k)) {
            p[k] = Number(p[k])
          }
        }
        setSelected(p)
      }
    })
  }, [mapReady, geojson])

  // Update fill on metric change
  useEffect(() => {
    const map = mapRef.current
    if (!mapReady || !map?.getLayer('hex-fill')) return
    const m = METRICS[metric]
    map.setPaintProperty('hex-fill', 'fill-color', [
      'interpolate', ['linear'],
      ['coalesce', ['to-number', ['get', m.key]], 0],
      ...m.stops.flat(),
    ])
  }, [metric, mapReady])

  // Update filter
  useEffect(() => {
    const map = mapRef.current
    if (!mapReady || !map?.getLayer('hex-fill')) return
    if (filter) {
      map.setFilter('hex-fill', filter)
      map.setFilter('hex-line', filter)
    } else {
      map.setFilter('hex-fill', null)
      map.setFilter('hex-line', null)
    }
  }, [filter, mapReady])

  // Highlight selected
  useEffect(() => {
    const map = mapRef.current
    if (!mapReady || !map?.getLayer('hex-hl')) return
    if (selected) {
      map.setFilter('hex-hl', ['==', ['get', 'hex_id'], selected.hex_id])
    } else {
      map.setFilter('hex-hl', ['==', ['get', 'hex_id'], '__none__'])
    }
  }, [selected, mapReady])

  return (
    <div className="app">
      {/* View tabs - top center */}
      <div className="view-tabs">
        <button className={`vt ${view === 'map' ? 'active' : ''}`} onClick={() => setView('map')}>Map</button>
        <button className={`vt ${view === 'gap' ? 'active' : ''}`} onClick={() => setView('gap')}>Transit Gap</button>
        <button className={`vt ${view === 'experiment' ? 'active' : ''}`} onClick={() => setView('experiment')}>Gap vs Congestion</button>
      </div>

      {view !== 'map' && (
        <div className="report-view">
          <iframe src={`${import.meta.env.BASE_URL}${view === 'gap' ? 'transit_gap_report.html' : 'transit_congestion_experiment.html'}`} className="report-iframe" title="Report" />
        </div>
      )}

      <div className="sidebar" style={{ display: view === 'map' ? 'flex' : 'none' }}>
        <div className="sb-head">
          <div className="sb-logo">Propheus</div>
          <h1>Hex Adequacy</h1>
          <p className="sb-tag">5,897 hexes · 92 features · 175m resolution</p>
        </div>

        {stats && (
          <div className="stat-strip">
            <div className="stat">
              <div className="sv">{stats.hexes.toLocaleString()}</div>
              <div className="sl">Hexes</div>
            </div>
            <div className="stat">
              <div className="sv">{(stats.pop/1e6).toFixed(1)}M</div>
              <div className="sl">Residents</div>
            </div>
            <div className="stat">
              <div className="sv">{(stats.bldgs/1000).toFixed(0)}K</div>
              <div className="sl">Buildings</div>
            </div>
            <div className="stat">
              <div className="sv">{(stats.hdb/1000).toFixed(1)}K</div>
              <div className="sl">HDB blocks</div>
            </div>
          </div>
        )}

        <div className="section">
          <div className="section-label">Metric</div>
          <div className="metric-grid">
            {Object.entries(METRICS).map(([k, m]) => (
              <button
                key={k}
                className={`metric-btn ${metric === k ? 'active' : ''}`}
                onClick={() => setMetric(k)}
                title={m.desc}
              >
                {m.label}
              </button>
            ))}
          </div>
          <div className="metric-desc">{METRICS[metric].desc}</div>
        </div>

        <div className="section">
          <div className="section-label">Region</div>
          <div className="pill-row">
            <button className={`pill ${regionFilter === null ? 'active' : ''}`} onClick={() => setRegionFilter(null)}>All</button>
            {regions.map(r => (
              <button
                key={r}
                className={`pill ${regionFilter === r ? 'active' : ''}`}
                style={regionFilter === r ? { background: `${REGION_COLORS[r]}22`, color: REGION_COLORS[r], borderColor: REGION_COLORS[r] } : {}}
                onClick={() => setRegionFilter(regionFilter === r ? null : r)}
              >
                {r.replace(' REGION', '')}
              </button>
            ))}
          </div>
        </div>

        <div className="section">
          <label className="toggle">
            <input type="checkbox" checked={populatedOnly} onChange={e => setPopulatedOnly(e.target.checked)} />
            <span className="slider" />
            <span className="toggle-label">Populated hexes only</span>
          </label>
        </div>

        <div className="about">
          <div className="about-title">About</div>
          <div className="about-text">
            Every 350m × 350m hexagon in Singapore gets its own population, buildings, transit access, walkability score, and adequacy gaps.
            Click any hex to see all 92 features including NVIDIA persona demographics and LTA live traffic data.
          </div>
        </div>
      </div>

      <div className="map-area" style={{ display: view === 'map' ? 'block' : 'none' }}>
        <div ref={mapContainer} className="map" />
        <div className="legend">
          <div className="lg-title">{METRICS[metric].label}</div>
          <div className="lg-bar">
            {METRICS[metric].stops.map(([, c], i) => <div key={i} style={{ background: c, flex: 1 }} />)}
          </div>
          <div className="lg-labels">
            <span>{METRICS[metric].fmt(METRICS[metric].stops[0][0])}</span>
            <span>{METRICS[metric].fmt(METRICS[metric].stops[METRICS[metric].stops.length - 1][0])}</span>
          </div>
        </div>
        <DetailPanel hex={selected} onClose={() => setSelected(null)} />
      </div>
    </div>
  )
}
