import React, { useEffect, useRef, useState, useMemo } from 'react'
import mapboxgl from 'mapbox-gl'

mapboxgl.accessToken = import.meta.env.VITE_MAPBOX_TOKEN || ''

const SEQ = ['#0b3b3a', '#0f766e', '#14b8a6', '#fcd34d', '#f97316', '#ef4444']
const NODATA = '#16213a'
const TABS = ['Pulse', 'Stories', 'Places', 'Ask', 'Sites', 'Twins', 'Future', 'Evidence']
const BAND = { good: '🟢', fair: '🟡', poor: '🔴', na: '⚪' }
const PCOLOR = { food: '#f97316', cafe: '#fcd34d', retail: '#38bdf8', night: '#c084fc',
  health: '#34d399', services: '#94a3b8', edu: '#fb7185', hotel: '#fbbf24',
  office: '#818cf8', other: '#64748b' }
const PLABEL = { food: 'Food', cafe: 'Cafes', retail: 'Retail', night: 'Nightlife',
  health: 'Health & fitness', services: 'Services', edu: 'Education',
  hotel: 'Hotels', office: 'Offices', other: 'Other' }

// every panel declares which Digital Atlas feature powers it (dim footer line)
const SRC = {
  pop_resident: 'pop_resident — SingStat 2025 dasymetric population, HDB-unit weighted',
  dt_pop: 'dt_pop — daytime population from LTA origin-destination flows (layer S3)',
  nl_2024: 'nl_2024 — VIIRS night-light radiance 2024 (evening commercial activity)',
  cap_supermarket: 'cap_supermarket — Huff capture model over 190,591 places (layer S1)',
  cap_cafe_coffee: 'cap_cafe_coffee — Huff capture model over 190,591 places (layer S1)',
  iso_walk10_unserved_pop_supermarket: 'iso_walk10_unserved_pop_supermarket — 800 m network-walk catchments (layer S2a)',
  labor_pool_45m: 'labor_pool_45m — 45-min GTFS transit reach (layer S5)',
  pipe_mrt_dist_m: 'pipe_mrt_dist_m — Master Plan 2019 future rail vs existing stations (layer S9)',
  labor_jobs_balance_45m: 'labor_jobs_balance_45m — jobs reachable ÷ workers reachable in 45-min transit (layer S5)',
  biz_recent_dead_share: 'biz_recent_dead_share — closure share of 2018+ registrations, 2.07M ACRA records (layer S4)',
}
const Src = ({ k, text }) => (
  <div className="src">ATLAS · {text || SRC[k] || k}</div>
)

// metric -> [lo, hi, log?] color domains (p2~p98, precomputed feel; log for heavy tails)
const DOMAINS = {
  pop_resident: [0, 26000, false],
  dt_pop: [0, 30000, false],
  cap_supermarket: [0, 2.6, false],
  cap_cafe_coffee: [0, 4.5, false],
  iso_walk10_unserved_pop_supermarket: [0, 2400, false],
  labor_pool_45m: [0, 1900000, false],
  labor_jobs_balance_45m: [0.05, 60, true],     // log: ratio jobs/workers reachable
  biz_recent_dead_share: [0, 0.6, false],
  pipe_mrt_dist_m: [400, 12000, true],
  pipe_dev_capacity_res: [0, 0.8, false],
}

// human-readable legend metadata per metric (title, end labels, note)
const fmtN = (v) => v >= 1e6 ? (v / 1e6).toFixed(1) + 'M' : v >= 1000 ? Math.round(v / 1000) + 'k' : String(Math.round(v))
const LEGENDS = {
  pop_resident: { title: 'People at home (night)', lo: '0', hi: '26k+', unit: 'residents per hex' },
  dt_pop: { title: 'People present by day', lo: '0', hi: '30k+', unit: 'daytime headcount per hex' },
  cap_supermarket: { title: 'Supermarket opportunity', lo: 'none', hi: '2.6+', unit: 'outlets a NEW store could sustain' },
  cap_cafe_coffee: { title: 'Cafe opportunity', lo: 'none', hi: '4.5+', unit: 'outlets a NEW cafe could sustain' },
  iso_walk10_unserved_pop_supermarket: { title: 'Unserved grocery demand', lo: '0', hi: '2.4k+', unit: 'people in reach with no supermarket near home' },
  labor_pool_45m: { title: 'Reachable workforce', lo: '0', hi: '1.9M', unit: 'workers within 45-min transit' },
  labor_jobs_balance_45m: { title: 'Jobs per reachable worker', lo: '<0.1', hi: '60+', unit: 'log scale — bright = jobs outrun workers' },
  biz_recent_dead_share: { title: 'Recent business closures', lo: '0%', hi: '60%+', unit: 'share of 2018+ registrations now closed' },
  pipe_mrt_dist_m: { title: 'Distance to FUTURE rail', lo: 'at a new station', hi: '12 km away', unit: 'brighter = closer to the coming JRL' },
}

// Twins tab: plain-language phrasing for each shared/different trait.
// hi/lo = how to say "both are unusually high/low on this" to a non-expert.
const TWIN_LBL = {
  pop_resident: { t: 'residents at night', hi: 'both densely lived-in', lo: 'both lightly lived-in', f: fmtN },
  dt_pop: { t: 'people present by day', hi: 'both fill up by day', lo: 'both quiet by day', f: fmtN },
  cap_total: { t: 'open commercial opportunity', hi: 'both have demand to spare', lo: 'both already fully served', f: v => v.toFixed(1) + ' outlets' },
  iso_walk10_pop: { t: 'people within a 10-min walk', hi: 'both walk-dense', lo: 'both walk-sparse', f: fmtN },
  iso_transit15_pop: { t: 'reach by 15-min transit', hi: 'both superbly connected', lo: 'both transit-isolated', f: fmtN },
  rent_resi_psf_med: { t: 'nearby rents', hi: 'both expensive postcodes', lo: 'both affordable postcodes', f: v => 'S$' + v.toFixed(2) + ' psf' },
  biz_live_robust: { t: 'street businesses', hi: 'both business-dense streets', lo: 'both business-thin', f: fmtN },
  biz_recent_dead_share: { t: 'recent business closures', hi: 'both high-churn for business', lo: 'both gentle on new business', f: v => Math.round(v * 100) + '%' },
  vis_exit_footfall: { t: 'MRT exit taps per day', hi: 'both heavy MRT footfall', lo: 'both little MRT footfall', f: fmtN },
  od_throughput: { t: 'transit trips touching it', hi: 'both major transit nodes', lo: 'both off the transit grid', f: fmtN },
  labor_pool_45m: { t: 'workforce within 45 min', hi: 'both can staff anything', lo: 'both hard to staff', f: fmtN },
  labor_jobs_balance_45m: { t: 'jobs per reachable worker', hi: 'both job-rich for their reach', lo: 'both bedroom communities', f: v => v.toFixed(1) + '×' },
  min15_score: { t: '15-minute-city score', hi: 'both complete neighbourhoods', lo: 'both amenity-poor', f: v => Math.round(v) + '/100' },
  time_to_cbd_min: { t: 'time to the CBD', hi: 'both far from the centre', lo: 'both close to the centre', f: v => Math.round(v) + ' min' },
  nl_2024: { t: 'night-time glow', hi: 'both bright after dark', lo: 'both dark after dark', f: v => v.toFixed(1) },
  pipe_mrt_dist_m: { t: 'distance to future rail', hi: 'both missed by coming rail', lo: 'both near coming rail', f: v => (v / 1000).toFixed(1) + ' km' },
  pipe_dev_capacity_res: { t: 'room left to build', hi: 'both have growth headroom', lo: 'both built out', f: v => v.toFixed(2) },
  pc_total: { t: 'places of every kind', hi: 'both packed with places', lo: 'both place-sparse', f: fmtN },
  pc_cat_restaurant: { t: 'restaurants', hi: 'both eating streets', lo: 'both thin on food', f: fmtN },
  pc_cat_shopping_retail: { t: 'retail shops', hi: 'both retail-heavy', lo: 'both light on retail', f: fmtN },
  pop_hdb_share: { t: 'share living in HDB', hi: 'both HDB heartland', lo: 'both private-housing turf', f: v => Math.round(v * 100) + '%' },
  lu_residential_pct: { t: 'land given to housing', hi: 'both housing-dominated land', lo: 'both little housing land', f: v => Math.round(v * 100) + '%' },
  lu_business_pct: { t: 'land zoned office/industry', hi: 'both working districts', lo: 'both not office country', f: v => Math.round(v * 100) + '%' },
  lu_entropy: { t: 'mix of land uses', hi: 'both genuinely mixed-use', lo: 'both single-use fabric', f: v => v.toFixed(2) },
  est_built_far: { t: 'built intensity (floor-area ratio)', hi: 'both built dense and tall', lo: 'both low-rise fabric', f: v => v.toFixed(1) },
  n_highrise_bldgs: { t: 'high-rise buildings', hi: 'both high-rise skylines', lo: 'both low-rise', f: fmtN },
}
const twinVal = (k, v) => (v == null ? '—' : TWIN_LBL[k].f(v))

function colorExpr(metric, reverse = false) {
  const [lo, hi, log] = DOMAINS[metric] || [0, 1, false]
  const pal = reverse ? [...SEQ].reverse() : SEQ
  const v = log ? ['ln', ['+', 1, ['to-number', ['get', metric], 0]]] : ['to-number', ['get', metric], 0]
  const L = log ? Math.log(1 + lo) : lo, H = log ? Math.log(1 + hi) : hi
  const stops = pal.flatMap((c, i) => [L + (i / (pal.length - 1)) * (H - L), c])
  return ['case', ['==', ['get', metric], null], NODATA, ['interpolate', ['linear'], v, ...stops]]
}

// ---- the 24-hour breathing cycle -------------------------------------
// Three activity fields, each normalised to ~[0,1], blended by time-of-day:
//   sleep   = residents at home          (pop_resident)
//   work    = daytime working population (dt_pop)
//   evening = commercial activity glow   (nl_2024 night lights)
function dayWeights(h) {
  const ramp = (x, a, b) => Math.max(0, Math.min(1, (x - a) / (b - a)))
  const work = ramp(h, 6.5, 9.5) * (1 - ramp(h, 16.5, 19.5))   // rush in, wind down
  const evening = ramp(h, 17, 19.5) * (1 - ramp(h, 22.5, 25))  // buzz, then fade
  const siesta = h >= 12 && h < 14 ? 0.15 : 0                  // noon lull dims work
  const sleep = Math.max(0, 1 - work - evening)
  return { sleep, work: Math.max(0, work - siesta), evening }
}
function cycleExpr(h) {
  const { sleep, work, evening } = dayWeights(h)
  const norm = (field, div) => ['/', ['ln', ['+', 1, ['to-number', ['get', field], 0]]], div]
  const mix = ['+',
    ['*', sleep, norm('pop_resident', 10.2)],
    ['*', work, norm('dt_pop', 10.5)],
    ['*', evening, norm('nl_2024', 4.0)]]
  const stops = SEQ.flatMap((c, i) => [0.04 + (i / (SEQ.length - 1)) * 0.92, c])
  return ['interpolate', ['linear'], mix, ...stops]
}
// Keyframe slideshow: jump straight to pivotal points of the day. The map
// colours CROSSFADE between states (paint transition); headline + clock snap.
const MOMENTS = [
  { h: 4.5, clock: '04:30', secs: 3.5, label: 'THE CITY SLEEPS', cls: 'night',
    sub: '6.04 million at home — the heartlands glow, the CBD is dark',
    tiles: [
      { name: 'RAFFLES PLACE', big: '600', sub: 'asleep — the towers stand empty' },
      { name: 'SENGKANG', big: '28,200', sub: 'everyone home in the heartlands' },
      { name: 'THE ISLAND', big: '6.04M', sub: 'at rest' },
    ] },
  { h: 9.0, clock: '09:00', secs: 3.5, label: 'MORNING RUSH', cls: '',
    sub: 'the great inversion: new towns drain, the centre inflates',
    tiles: [
      { name: 'RAFFLES PLACE', big: '88,000', sub: 'filled 19× in two hours' },
      { name: 'SENGKANG', big: '−12,800', sub: 'commuting out right now' },
      { name: 'TRANSIT', big: '6.9M', sub: 'journeys a day carry the swap' },
    ] },
  { h: 12.5, clock: '12:30', secs: 3.5, label: 'PEAK WORK', cls: '',
    sub: 'the daytime city at full strength',
    tiles: [
      { name: 'THE CBD', big: '88,000', sub: 'at desks in one subzone — on 600 beds' },
      { name: 'LUNCH CROWDS', big: '63', sub: 'wet-market & hawker hubs hit their peak' },
      { name: 'TWO CITIES', big: 'day ≠ night', sub: 'same map, different Singapore' },
    ] },
  { h: 19.5, clock: '19:30', secs: 3.5, label: 'EVENING BUZZ', cls: 'evening',
    sub: 'offices empty out — the commercial city lights up instead',
    tiles: [
      { name: 'ORCHARD', big: 'aglow', sub: 'the retail corridor at full radiance' },
      { name: 'TOWN HUBS', big: 'Tampines · Yishun · JE', sub: 'dinner crowds at the interchanges' },
      { name: 'FROM SPACE', big: 'VIIRS', sub: 'this glow is real satellite night-light data' },
    ] },
  { h: 23.5, clock: '23:30', secs: 3.5, label: 'WINDING DOWN', cls: 'night',
    sub: 'the glow heads home — and the day begins again',
    tiles: [
      { name: 'HEARTLANDS', big: 'glowing', sub: 'everyone is home again' },
      { name: 'THE CBD', big: 'dark', sub: '600 remain among the towers' },
      { name: 'TOMORROW', big: '04:30', sub: 'the cycle restarts' },
    ] },
]

export default function App() {
  const mapRef = useRef(null)
  const mapDiv = useRef(null)
  const pulseT = useRef(0)
  const pulseOn = useRef(true)
  const [entered, setEntered] = useState(false)
  const [tab, setTab] = useState('Pulse')
  const [data, setData] = useState({})
  const [scene, setScene] = useState(0)
  const [storyIdx, setStoryIdx] = useState(0)
  const [askSel, setAskSel] = useState(null)
  const [typed, setTyped] = useState('')
  const [site, setSite] = useState(null)
  const [clock, setClock] = useState('04:30')
  const [place, setPlace] = useState(null)
  const [pcat, setPcat] = useState(null)        // places category filter
  const placesLoaded = useRef(false)
  const tabRef = useRef('Pulse')
  const marksRef = useRef([])
  const dataRef = useRef({})
  const [twinSel, setTwinSel] = useState(null)   // selected hex on Twins tab
  const [twinOpen, setTwinOpen] = useState(null) // which twin box is expanded
  const [legend, setLegend] = useState({ kind: 'pulse' })  // what the colours mean RIGHT NOW

  // Twins tab: highlight a hex + its 5 functional twins, with connecting lines
  const hexCentroid = (f) => {
    const ring = f.geometry.coordinates[0]
    const n = ring.length - 1
    return [ring.slice(0, n).reduce((s, c) => s + c[0], 0) / n,
            ring.slice(0, n).reduce((s, c) => s + c[1], 0) / n]
  }
  const clearTwinViz = () => {
    const map = mapRef.current
    map?.getSource('twin-hl')?.setData({ type: 'FeatureCollection', features: [] })
    map?.getSource('twin-lines')?.setData({ type: 'FeatureCollection', features: [] })
  }
  const drawTwins = (hexId) => {
    const { hexes, twins } = dataRef.current
    const map = mapRef.current
    if (!hexes || !twins || !map) return
    const self = hexes.features.find(f => f.properties.id === hexId)
    const tws = (twins[hexId] || [])
      .map(t => hexes.features.find(f => f.properties.id === t.id)).filter(Boolean)
    if (!self) return
    setTwinSel({ id: hexId, name: self.properties.parent_subzone_name,
                 twins: twins[hexId] || [] })
    setTwinOpen(null)
    map.getSource('hl').setData({ type: 'FeatureCollection', features: [self] })
    map.getSource('twin-hl').setData({ type: 'FeatureCollection', features: tws })
    const c0 = hexCentroid(self)
    const meta = Object.fromEntries((twins[hexId] || []).map(t => [t.id, t]))
    map.getSource('twin-lines').setData({ type: 'FeatureCollection',
      features: tws.map(f => ({ type: 'Feature',
        properties: { s: meta[f.properties.id]?.s ?? 0.7 },
        geometry: { type: 'LineString', coordinates: [c0, hexCentroid(f)] } })) })
    map.flyTo({ center: c0, zoom: 10.6, duration: 1500 })
  }

  // story map markings: pulsing ring + label callout at named places
  const clearMarks = () => { marksRef.current.forEach(m => m.remove()); marksRef.current = [] }
  const setMarks = (list = []) => {
    clearMarks()
    const map = mapRef.current
    if (!map) return
    list.forEach((mk, i) => {
      const el = document.createElement('div')
      el.className = 'mark'
      el.style.animationDelay = `${i * 0.25}s`
      el.innerHTML = `<div class="mark-ring"></div><div class="mark-dot"></div><div class="mark-label">${mk.text}</div>`
      marksRef.current.push(new mapboxgl.Marker({ element: el, anchor: 'center' })
        .setLngLat([mk.lng, mk.lat]).addTo(map))
    })
  }

  // ---- init ----
  useEffect(() => {
    const map = new mapboxgl.Map({
      container: mapDiv.current, style: 'mapbox://styles/mapbox/dark-v11',
      center: [103.82, 1.35], zoom: 10.55, attributionControl: false,
    })
    mapRef.current = map
    Promise.all(['hexes.geojson', 'report_cards.json', 'twins.json', 'stories.json',
      'ask.json', 'evidence.json'].map(f => fetch('/data/' + f).then(r => r.json())))
      .then(([hexes, cards, twins, stories, ask, evidence]) => {
        setData({ hexes, cards, twins, stories, ask, evidence })
        dataRef.current = { hexes, twins }
        // over slow networks the map 'load' event fires BEFORE the data fetch
        // resolves — registering on('load') then would never run. Handle both.
        const whenReady = (fn) => (map.isStyleLoaded() ? fn() : map.on('load', fn))
        whenReady(() => {
          if (map.getSource('hex')) return
          map.addSource('hex', { type: 'geojson', data: hexes })
          map.addLayer({ id: 'hex-fill', type: 'fill', source: 'hex',
            paint: { 'fill-color': cycleExpr(4.5), 'fill-opacity': 0.78,
              // slow crossfade between keyframe states — the "breathing"
              'fill-color-transition': { duration: 1000 } } })
          map.addLayer({ id: 'hex-line', type: 'line', source: 'hex',
            paint: { 'line-color': '#0b1220', 'line-width': 0.4, 'line-opacity': 0.4 } })
          map.addSource('hl', { type: 'geojson', data: { type: 'FeatureCollection', features: [] } })
          map.addSource('twin-hl', { type: 'geojson', data: { type: 'FeatureCollection', features: [] } })
          map.addSource('twin-lines', { type: 'geojson', data: { type: 'FeatureCollection', features: [] } })
          map.addLayer({ id: 'twin-lines', type: 'line', source: 'twin-lines',
            paint: { 'line-color': '#20b2aa',
              // edge weight = similarity: the closest twin gets the boldest line
              'line-width': ['interpolate', ['linear'], ['coalesce', ['get', 's'], 0.7], 0.5, 1.0, 1, 4.2],
              'line-opacity': ['interpolate', ['linear'], ['coalesce', ['get', 's'], 0.7], 0.5, 0.4, 1, 0.95],
              'line-dasharray': [1.5, 1.5] } })
          map.addLayer({ id: 'twin-hl', type: 'line', source: 'twin-hl',
            paint: { 'line-color': '#20b2aa', 'line-width': 2.6 } })
          map.addLayer({ id: 'hl-line', type: 'line', source: 'hl',
            paint: { 'line-color': '#fcd34d', 'line-width': 3 } })
          map.on('click', 'hex-fill', e => {
            if (tabRef.current === 'Places') return   // place dots own that tab
            const f = e.features[0]
            if (tabRef.current === 'Twins') { drawTwins(f.properties.id); return }
            setSite(f.properties.id)
            map.getSource('hl').setData({ type: 'FeatureCollection', features: [f] })
          })
          map.on('mouseenter', 'hex-fill', () => map.getCanvas().style.cursor = 'pointer')
          map.on('mouseleave', 'hex-fill', () => map.getCanvas().style.cursor = '')
        })
      })
    return () => map.remove()
  }, [])

  // ---- keyframe slideshow: snap to each moment, colours crossfade ----
  const [momIdx, setMomIdx] = useState(0)
  useEffect(() => {
    let seg = 0, elapsed = 0
    const TICK = 250
    const iv = setInterval(() => {
      const map = mapRef.current
      if (!map || !pulseOn.current || !map.getLayer || !map.getLayer('hex-fill')) return
      elapsed += TICK / 1000
      if (elapsed >= MOMENTS[seg].secs) {
        elapsed = 0
        seg = (seg + 1) % MOMENTS.length
        setMomIdx(seg)
        map.setPaintProperty('hex-fill', 'fill-color', cycleExpr(MOMENTS[seg].h))
        setClock(MOMENTS[seg].clock)
      }
    }, TICK)
    return () => clearInterval(iv)
  }, [])

  const phase = MOMENTS[momIdx]

  const setMetric = (metric, reverse = false) => {
    pulseOn.current = false
    const map = mapRef.current
    if (map?.getLayer('hex-fill')) map.setPaintProperty('hex-fill', 'fill-color', colorExpr(metric, reverse))
    setLegend({ kind: 'ramp', reverse, ...(LEGENDS[metric] || { title: metric, lo: 'low', hi: 'high', unit: '' }) })
  }
  const startPulse = () => { pulseOn.current = true; setLegend({ kind: 'pulse' }) }
  const clearHl = () => mapRef.current?.getSource('hl')?.setData({ type: 'FeatureCollection', features: [] })

  const highlight = (hexId) => {
    const f = data.hexes?.features.find(x => x.properties.id === hexId)
    if (f) mapRef.current.getSource('hl').setData({ type: 'FeatureCollection', features: [f] })
  }

  // ---- the micrograph, drawn ON the map ------------------------------
  const placesGeo = useRef(null)
  const EMPTY = { type: 'FeatureCollection', features: [] }
  const circlePoly = (lng, lat, rM) => {
    const k = 111320, ring = []
    for (let i = 0; i <= 64; i++) {
      const a = (i / 64) * 2 * Math.PI
      ring.push([lng + (rM * Math.cos(a)) / (k * Math.cos(lat * Math.PI / 180)),
                 lat + (rM * Math.sin(a)) / k])
    }
    return ring
  }
  const distM = (a, b) => {
    const k = 111320
    const dx = (a[0] - b[0]) * k * Math.cos(a[1] * Math.PI / 180)
    const dy = (a[1] - b[1]) * k
    return Math.hypot(dx, dy)
  }
  const clearMicrograph = () => {
    const map = mapRef.current
    for (const s of ['mg-rings', 'mg-spokes', 'mg-dots'])
      map?.getSource(s)?.setData(EMPTY)
  }
  const drawMicrograph = (props, center) => {
    const map = mapRef.current
    if (!map || !placesGeo.current) return
    const near = placesGeo.current.features
      .map(f => ({ f, d: distM(center, f.geometry.coordinates) }))
      .filter(x => x.d > 1 && x.d <= 420)
    const rivals = near.filter(x => x.f.properties.cat === props.cat)
      .sort((a, b) => a.d - b.d).slice(0, 14)
    const anchors = near.filter(x => x.f.properties.m && x.f.properties.cat !== props.cat)
      .sort((a, b) => a.d - b.d).slice(0, 10)
    const compl = near.filter(x => !x.f.properties.m && x.f.properties.cat !== props.cat)
      .slice(0, 90)
    map.getSource('mg-rings').setData({ type: 'FeatureCollection', features:
      [400, 800].map(r => ({ type: 'Feature', properties: { r },
        geometry: { type: 'LineString', coordinates: circlePoly(center[0], center[1], r) } })) })
    map.getSource('mg-spokes').setData({ type: 'FeatureCollection', features: [
      ...rivals.map(x => ({ type: 'Feature', properties: { kind: 'rival' },
        geometry: { type: 'LineString', coordinates: [center, x.f.geometry.coordinates] } })),
      ...anchors.map(x => ({ type: 'Feature', properties: { kind: 'anchor' },
        geometry: { type: 'LineString', coordinates: [center, x.f.geometry.coordinates] } })),
    ] })
    map.getSource('mg-dots').setData({ type: 'FeatureCollection',
      features: compl.map(x => ({ type: 'Feature', properties: {},
        geometry: x.f.geometry })) })
    map.flyTo({ center, zoom: 15.2, duration: 1400 })
  }

  // ---- places layer (lazy: fetched on first Places visit) ----
  const ensurePlaces = async () => {
    const map = mapRef.current
    if (placesLoaded.current || !map) return
    placesLoaded.current = true
    const pj = await fetch('/data/places.geojson').then(r => r.json())
    placesGeo.current = pj
    map.addSource('places', { type: 'geojson', data: pj })
    for (const s of ['mg-rings', 'mg-spokes', 'mg-dots'])
      map.addSource(s, { type: 'geojson', data: EMPTY })
    map.addLayer({ id: 'mg-dots', type: 'circle', source: 'mg-dots',
      paint: { 'circle-radius': 3.2, 'circle-color': '#20b2aa',
        'circle-opacity': 0.85, 'circle-stroke-color': '#0d1f21', 'circle-stroke-width': 1 } })
    map.addLayer({ id: 'mg-spokes', type: 'line', source: 'mg-spokes',
      paint: { 'line-color': ['match', ['get', 'kind'], 'anchor', '#fcd34d', '#f87171'],
        'line-width': ['match', ['get', 'kind'], 'anchor', 2.4, 1.4],
        'line-opacity': 0.85 } })
    map.addLayer({ id: 'mg-rings', type: 'line', source: 'mg-rings',
      paint: { 'line-color': '#20b2aa', 'line-width': 1.4, 'line-opacity': 0.65,
        'line-dasharray': [2, 2] } })
    map.addLayer({ id: 'place-dots', type: 'circle', source: 'places',
      layout: { visibility: 'none' },
      paint: {
        'circle-color': ['match', ['get', 'g'],
          ...Object.entries(PCOLOR).flat(), '#64748b'],
        'circle-radius': ['interpolate', ['linear'], ['zoom'],
          10, ['case', ['get', 'm'], 2.2, 1.1],
          14, ['case', ['get', 'm'], 7, 3.5]],
        'circle-opacity': 0.85,
      } })
    map.on('click', 'place-dots', e => {
      const f = e.features[0]
      setPlace(f.properties)
      drawMicrograph(f.properties, f.geometry.coordinates)
      e.originalEvent.cancelBubble = true
    })
    map.on('mouseenter', 'place-dots', () => map.getCanvas().style.cursor = 'pointer')
  }
  const showPlaces = (on) => {
    const map = mapRef.current
    if (map?.getLayer('place-dots'))
      map.setLayoutProperty('place-dots', 'visibility', on ? 'visible' : 'none')
  }

  // places category filter
  useEffect(() => {
    const map = mapRef.current
    if (!map?.getLayer('place-dots')) return
    map.setFilter('place-dots', pcat ? ['==', ['get', 'g'], pcat] : null)
  }, [pcat])

  // ---- tab side effects ----
  useEffect(() => {
    tabRef.current = tab
    setSite(null); setAskSel(null); setTyped(''); setPlace(null); clearHl(); clearMarks()
    clearMicrograph(); clearTwinViz(); setTwinSel(null)
    if (tab === 'Twins') {
      pulseOn.current = false
      setLegend({ kind: 'twins' })
      const map = mapRef.current
      if (map?.getLayer('hex-fill'))
        map.setPaintProperty('hex-fill', 'fill-color', '#11302e')   // quiet stage
      // land on a known archetype so the tab opens already telling its story
      const toa = data.hexes?.features.filter(f =>
        f.properties.parent_subzone_name === 'TOA PAYOH CENTRAL')
        .sort((a, b) => (b.properties.pop_resident || 0) - (a.properties.pop_resident || 0))[0]
      if (toa) setTimeout(() => drawTwins(toa.properties.id), 400)
    }
    showPlaces(tab === 'Places')
    if (tab === 'Pulse') { startPulse(); mapRef.current?.flyTo({ center: [103.82, 1.35], zoom: 10.55 }) }
    if (tab === 'Stories') { setStoryIdx(0); setScene(0) }
    if (tab === 'Places') {
      pulseOn.current = false
      setLegend({ kind: 'none' })   // the category chips ARE the legend here
      ensurePlaces().then(() => showPlaces(true))
      const map = mapRef.current
      if (map?.getLayer('hex-fill')) map.setPaintProperty('hex-fill', 'fill-color', NODATA)
      map?.flyTo({ center: [103.845, 1.295], zoom: 13.4 })
    } else if (mapRef.current?.getLayer('hex-fill') && tab !== 'Pulse') {
      // restore hex coloring handled by each tab below
    }
    if (tab === 'Sites') { setMetric('cap_cafe_coffee') }
    if (tab === 'Future') { setMetric('pipe_mrt_dist_m', true); mapRef.current?.flyTo({ center: [103.72, 1.35], zoom: 11.2 }) }
  }, [tab, data.hexes])

  // ---- story scene effects ----
  const story = data.stories?.[storyIdx]
  useEffect(() => {
    if (tab !== 'Stories' || !story) { clearMarks(); return }
    const sc = story.scenes[scene]
    if (!sc) return
    mapRef.current?.flyTo({ ...sc.view, duration: 2400 })
    if (sc.pulse) startPulse(); else setMetric(sc.metric)
    if (sc.highlight) highlight(sc.highlight); else clearHl()
    setMarks(sc.marks)
  }, [tab, storyIdx, scene, data.stories])

  // ---- ask typing ----
  useEffect(() => {
    if (askSel === null || !data.ask) return
    const a = data.ask[askSel]
    setMetric(a.metric, !!a.reverse)
    mapRef.current?.flyTo({ ...a.view, duration: 2200 })
    setTyped(''); let i = 0
    const iv = setInterval(() => {
      i += 3; setTyped(a.a.slice(0, i))
      if (i >= a.a.length) clearInterval(iv)
    }, 24)
    return () => clearInterval(iv)
  }, [askSel])

  const card = site && data.cards ? data.cards[site] : null
  const siteTwins = site && data.twins ? data.twins[site] : []

  return (
    <div className="app">
      <div ref={mapDiv} className="map" />

      {!entered && (
        <div className="launch" onClick={() => setEntered(true)}>
          <img className="launch-logo" src="/propheus.svg" alt="Propheus" />
          <div className="launch-inner">
            <h1>SG <span className="hot">Pulse</span></h1>
            <p>Singapore, as a living system. Watch it breathe.</p>
            <button className="cta">Explore →</button>
          </div>
          <div className="phase-banner">
            <span className="phase-clock">{clock}</span>
            <span>
              <span className={'phase-label ' + phase.cls}>{phase.label}</span>
              <span className="phase-sub">{phase.sub}</span>
            </span>
          </div>
          <div className="live-tiles" key={momIdx}>
            {phase.tiles.map(t => (
              <div className="ltile" key={t.name}>
                <span className="ltile-name">{t.name}</span>
                <b>{t.big}</b>
                <span className="ltile-sub">{t.sub}</span>
              </div>
            ))}
          </div>
          <div className="launch-foot">190,591 places · 2,735 validated measurements · every number checked before it shipped
            <div className="src" style={{ border: 'none', marginTop: 4, textAlign: 'center' }}>
              ATLAS · breathing = pop_resident (SingStat) → dt_pop (LTA OD flows) → nl_2024 (VIIRS night lights), blended by time of day
            </div>
          </div>
        </div>
      )}

      {entered && legend.kind !== 'none' && tab !== 'Evidence' && (
        <div className={'maplegend' + (['Stories', 'Twins'].includes(tab) ? ' right' : '')}>
          {legend.kind === 'pulse' && <>
            <div className="leg-title">People present right now</div>
            <div className="leg-ramp" />
            <div className="leg-ends"><span>few</span><span>26k+ per hex</span></div>
            <div className="leg-note">live blend: residents · daytime workers · evening commercial glow</div>
          </>}
          {legend.kind === 'ramp' && <>
            <div className="leg-title">{legend.title}</div>
            <div className={'leg-ramp' + (legend.reverse ? ' rev' : '')} />
            <div className="leg-ends"><span>{legend.lo}</span><span>{legend.hi}</span></div>
            {legend.unit && <div className="leg-note">{legend.unit}</div>}
          </>}
          {legend.kind === 'twins' && <>
            <div className="leg-title">Functional twins</div>
            <div className="leg-swatches">
              <span><i className="sw" style={{ background: '#fcd34d' }} />your pick</span>
              <span><i className="sw ring" style={{ borderColor: '#20b2aa' }} />its 5 twins</span>
              <span><i className="sw dash" />similarity link — thicker = more alike</span>
            </div>
            <div className="leg-note">found by the trained 256-d embedding — not by distance</div>
          </>}
          <div className="leg-na"><i className="sw" style={{ background: NODATA }} />no data / not scored</div>
        </div>
      )}

      {entered && <>
        <header className="bar">
          <button className="brand" title="Back to start" onClick={() => {
            setEntered(false); setTab('Pulse'); startPulse()
            mapRef.current?.flyTo({ center: [103.82, 1.35], zoom: 10.55 })
          }}>SG <b className="hot">Pulse</b></button>
          {TABS.map(t => (
            <button key={t} className={'tab' + (tab === t ? ' on' : '')} onClick={() => setTab(t)}>{t}</button>
          ))}
          <span className="bar-right">
            <span className="byline">powered by the Plexis Atlas v5</span>
            <img className="bar-logo" src="/propheus.svg" alt="Propheus" />
          </span>
        </header>

        {tab === 'Pulse' && (
          <div className="caption">
            <span className="clock-inline">{clock}</span>
            <b style={{ color: '#fff', marginRight: 8 }}>{phase.label}</b>
            {phase.sub} — five pivotal moments of one day.
            <Src text="pop_resident (SingStat) · dt_pop (LTA OD, S3) · nl_2024 (VIIRS) blended by time of day" />
          </div>
        )}

        {tab === 'Stories' && story && (
          <div className="panel left">
            <div className="panel-tag">Story · {storyIdx + 1} of {data.stories.length}</div>
            <div className="story-nav">
              {data.stories.map((s, i) => (
                <button key={s.id} className={'chip' + (i === storyIdx ? ' on' : '')}
                  onClick={() => { setStoryIdx(i); setScene(0) }}>{s.title}</button>
              ))}
            </div>
            <div className="story-text" key={storyIdx + '-' + scene}>{story.scenes[scene].text}</div>
            {scene === story.scenes.length - 1 && (
              <div className="punchline">“{story.punchline}”</div>
            )}
            <div className="story-controls">
              <button disabled={scene === 0} onClick={() => setScene(s => s - 1)}>←</button>
              <span className="scene-dots">
                {story.scenes.map((_, i) => (
                  <i key={i} className={'sdot' + (i === scene ? ' on' : i < scene ? ' done' : '')}
                    onClick={() => setScene(i)} />
                ))}
              </span>
              <button disabled={scene === story.scenes.length - 1} onClick={() => setScene(s => s + 1)}>→</button>
            </div>
            <Src k={story.scenes[scene].pulse ? 'dt_pop' : story.scenes[scene].metric} />
          </div>
        )}

        {tab === 'Places' && (
          <div className="caption">
            <div className="plegend">
              <button className={'chip' + (pcat === null ? ' on' : '')} onClick={() => setPcat(null)}>All</button>
              {Object.keys(PCOLOR).filter(g => g !== 'other').map(g => (
                <button key={g} className={'chip' + (pcat === g ? ' on' : '')}
                  style={{ borderColor: pcat === g ? PCOLOR[g] : undefined }}
                  onClick={() => setPcat(pcat === g ? null : g)}>
                  <i className="dot" style={{ background: PCOLOR[g] }} />{PLABEL[g]}
                </button>
              ))}
            </div>
            50,231 rated places · bigger dots are demand magnets · click one for its micrograph
            <Src text="places dataset — 190,591 venues, 24-category taxonomy, brand + quality enriched (shown: reviews ≥ 25 or demand magnets)" />
          </div>
        )}
        {tab === 'Places' && place && (
          <aside className="panel right">
            <div className="panel-tag">Place micrograph</div>
            <div className="card-head">
              <div>
                <div className="card-title">{place.n}</div>
                <div className="verdict">
                  <i className="dot" style={{ background: PCOLOR[place.g] }} />
                  {PLABEL[place.g]}{place.m === true || place.m === 'true' ? ' · demand magnet' : ''}
                  {place.r ? ` · ★ ${place.r} (${Number(place.v).toLocaleString()} reviews)` : ''}
                </div>
              </div>
              <button className="x" onClick={() => { setPlace(null); clearMicrograph() }}>×</button>
            </div>
            <div className="twins-h" style={{ marginTop: 6 }}>Micrograph — this venue's 400 m world</div>
            <div className="mg-legend">
              <span><i className="lg-line rival" />same-type rivals</span>
              <span><i className="lg-line anchor" />demand anchors</span>
              <span><i className="lg-dot" />complements</span>
              <span><i className="lg-ring" />400 / 800 m</span>
            </div>
            <div className="vrow"><span><b>Competition</b></span>
              <span className="vtext">{place.c4 ?? 0} same-type venue{place.c4 === 1 ? '' : 's'} within 400 m
                {place.cd ? `; nearest just ${place.cd} m away` : ''}
                {place.cr ? ` (their avg rating ★ ${place.cr})` : ''}</span></div>
            <div className="vrow"><span><b>Support</b></span>
              <span className="vtext">{place.p4 ?? 0} complementary businesses feeding it footfall</span></div>
            <div className="vrow"><span><b>Anchors</b></span>
              <span className="vtext">{place.a4 ?? 0} demand magnet{place.a4 === 1 ? '' : 's'} (malls, hubs) within 400 m</span></div>
            <div className="vrow"><span><b>Transit</b></span>
              <span className="vtext">{place.mrt ? `${place.mrt} m walk to the nearest MRT (~${Math.round(place.mrt / 80)} min)` : 'no MRT in walking range'}</span></div>
            <div className="small" style={{ marginTop: 10, color: '#64748b' }}>
              Every one of 190,591 places carries this fingerprint — it is what the site models are built on.
            </div>
            <Src text="places + per-place micrograph pmg_* — competitors, complements, anchors within 400 m (stage 10p)" />
          </aside>
        )}

        {tab === 'Ask' && data.ask && (
          <div className="ask">
            {askSel !== null && <div className="answer">{typed}
              {typed === data.ask[askSel].a && <Src k={data.ask[askSel].metric} />}
            </div>}
            <div className="chips">
              {data.ask.map((a, i) => (
                <button key={i} className={'chip' + (askSel === i ? ' on' : '')}
                  onClick={() => setAskSel(i)}>{a.q}</button>
              ))}
            </div>
            <div className="small">Demo build uses curated answers · live Ask runs on the Plexis-Mind engine</div>
          </div>
        )}

        {tab === 'Sites' && (
          <div className="caption">Click any hex for its site report card. Colour = cafe opportunity.</div>
        )}
        {tab === 'Sites' && card && (
          <aside className="panel right">
            <div className="panel-tag">Site report card</div>
            <div className="card-head">
              <div>
                <div className="card-title">{card.name?.toLowerCase()}</div>
                {!card.na && <div className="verdict">{card.verdict}</div>}
              </div>
              <button className="x" onClick={() => { setSite(null); clearHl() }}>×</button>
            </div>
            {card.na ? (
              <div className="story-text">This area is {card.zone} — not scored for consumer site selection.</div>
            ) : <>
              {card.rows.map(r => (
                <div className="vrow" key={r.label}>
                  <span>{BAND[r.band]} <b>{r.label}</b></span><span className="vtext">{r.text}</span>
                </div>
              ))}
              <div className="ucs">
                {Object.entries(card.usecases).map(([k, u]) => (
                  <div className="vrow" key={k}><span>{BAND[u.band]} <b>{k}</b></span><span className="vtext">{u.text}</span></div>
                ))}
              </div>
              <div className="twins">
                <div className="twins-h">Functional twins</div>
                {siteTwins.map(t => (
                  <button key={t.id} className="chip" onClick={() => {
                    setSite(t.id); highlight(t.id)
                    const f = data.hexes.features.find(x => x.properties.id === t.id)
                    let c = f.geometry.coordinates[0][0]
                    mapRef.current.flyTo({ center: c, zoom: 12.8 })
                  }}>{t.name?.toLowerCase()}</button>
                ))}
                <Src text="twins from the plexis-e1 256-d hex embedding (validated similarity space)" />
              </div>
              <Src text="catchment iso_walk10_* (S2a) · exit taps vis_* (S7) · rents URA (S8) · risk ACRA (S4) · capture Huff (S1) · outlook MP2019+FAR (S9)" />
            </>}
          </aside>
        )}

        {tab === 'Twins' && (
          <div className="caption">Click any hex — its five <b style={{ color: '#20b2aa' }}>functional twins</b> light up, found by the trained embedding. <span style={{ color: '#fcd34d' }}>yellow = your pick</span> · teal = its twins.</div>
        )}
        {tab === 'Twins' && data.evidence?.embedding && (
          <div className="panel left">
            <div className="panel-tag">Contrastive training — how twins are found</div>
            {twinSel && <>
              <div className="card-title">{twinSel.name?.toLowerCase()}</div>
              <div className="twins" style={{ marginTop: 4 }}>
                {twinSel.twins.map(t => (
                  <button key={t.id} className="chip" onClick={() => drawTwins(t.id)}>
                    {t.name?.toLowerCase()}</button>
                ))}
              </div>
            </>}
            <p className="emb-p" style={{ marginTop: 12 }}>
              Every hex's 801 measurements are compressed into a 256-number fingerprint
              by a neural network trained with <b style={{ color: '#fff' }}>contrastive learning</b>:
              two corrupted views of the same hex must match; other hexes must not.
              A second task — predict a hex's shops and flows from its people and
              buildings — teaches the fingerprint how supply follows demand.
            </p>
            <p className="emb-p">
              The pure neural model scored highest — and <b style={{ color: '#f87171' }}>failed
              the locked 13-check exam</b>: it quietly pulled opposites (Tuas, Orchard)
              closer together. What shipped is a hybrid: 160 classical + 96 learned
              dimensions. It passes every check, and it is what you are clicking right now.
            </p>
            <table className="emb-table">
              <thead><tr><th></th>{data.evidence.embedding.scoreboard.cols.map(c =>
                <th key={c} className={c.includes('hybrid') ? 'hot' : ''}>{c.replace('Classical (PCA)', 'Classical').replace('Shipped hybrid', 'Hybrid ✓')}</th>)}</tr></thead>
              <tbody>
                {data.evidence.embedding.scoreboard.rows.map(r => (
                  <tr key={r.metric}><td>{r.metric}</td>
                    {r.vals.map((v, i) => <td key={i}
                      className={r.fail.includes(i) ? 'fail' : (i === 2 ? 'hot' : '')}>{v}</td>)}
                  </tr>))}
              </tbody>
            </table>
            <a className="report-link" href="/data/plexis_e1_report.md" target="_blank" rel="noreferrer">
              Full training report (plexis-e1) →</a>
            <Src text="plexis-e1 256-d hex embedding — trained on-server in 8 min; 13-check harness locked before training; eval logs validate_embedding_e1.json" />
          </div>
        )}
        {tab === 'Twins' && twinSel && twinSel.twins?.length > 0 && (
          <aside className="panel rightw">
            <div className="panel-tag">Why these five?</div>
            <div className="card-title">{twinSel.name?.toLowerCase()} — its twins at a glance</div>
            {twinSel.twins.map(t => {
              const open = twinOpen === t.id
              const phrase = (w) => {
                const L = TWIN_LBL[w.k]
                return L ? ((w.pa + w.pb) / 2 >= 50 ? L.hi : L.lo) : null
              }
              return (
                <div className={'why-block' + (open ? ' open' : ' mini')} key={t.id}
                  onClick={() => setTwinOpen(open ? null : t.id)}>
                  <div className="why-head">
                    <span className="why-name">{t.name?.toLowerCase()}</span>
                    <span className="why-sim">{open ? <>closer than <b>{t.sim}%</b> of SG</> : <b>{t.sim}%</b>}</span>
                  </div>
                  <div className="why-bar"><i style={{ width: Math.round((t.s || 0) * 100) + '%' }} /></div>
                  {!open && (
                    <div className="why-minirow">
                      {(t.why || []).slice(0, 2).map(phrase).filter(Boolean).join(' · ')
                        || 'matched on the full 256-number fingerprint'}
                    </div>
                  )}
                  {open && <>
                    {t.why?.length ? t.why.map(w => {
                      const L = TWIN_LBL[w.k]
                      if (!L) return null
                      return (
                        <div className="why-row" key={w.k}>
                          <span className="why-phrase">{phrase(w)}</span>
                          <span className="why-vals">{L.t}: <b>{twinVal(w.k, w.a)}</b> vs <b>{twinVal(w.k, w.b)}</b></span>
                          <div className="pbar">
                            <i className="pa" style={{ width: w.pa + '%' }} />
                            <i className="pb" style={{ width: w.pb + '%' }} />
                          </div>
                        </div>
                      )
                    }) : <div className="why-row"><span className="why-vals">no single headline trait — these match across the whole 256-number fingerprint</span></div>}
                    {t.dif && TWIN_LBL[t.dif.k] && (
                      <div className="why-dif">where they differ — {TWIN_LBL[t.dif.k].t}: {twinVal(t.dif.k, t.dif.a)} vs {twinVal(t.dif.k, t.dif.b)}</div>
                    )}
                    <button className="chip whychip" onClick={(e) => { e.stopPropagation(); drawTwins(t.id) }}>
                      show ITS twins ↗</button>
                  </>}
                </div>
              )
            })}
            <Src text="% = share of all scored hexes farther away in embedding space · bar = closeness vs the best twin · tap a box for the full story (yellow/teal bars = national percentile)" />
          </aside>
        )}

        {tab === 'Future' && (
          <div className="caption">Brighter = closer to a FUTURE rail station (JRL + Keppel extension, 37 stations). The western arc is the next decade.
            <Src k="pipe_mrt_dist_m" />
          </div>
        )}

        {tab === 'Evidence' && data.evidence && (
          <div className="evidence">
            <h2>We test the atlas against published science</h2>
            <div className="tiles">
              {data.evidence.replications.map(r => (
                <div className="tile" key={r.paper}>
                  <span className={'status ' + r.status.replace(' ', '')}>{r.status}</span>
                  <b>{r.paper}</b><p>{r.note}</p>
                </div>
              ))}
            </div>
            {data.evidence.novel && <>
              <h2>{data.evidence.novel.title}</h2>
              <p className="emb-p">{data.evidence.novel.intro}</p>
              <div className="star-row">
                {data.evidence.novel.stars.map(s => (
                  <div className="star-card" key={s.col}>
                    <div className="star-corr"><b>{s.corr}</b><span>overlap with everything before it</span></div>
                    <b className="star-name">⭐ {s.name}</b>
                    <code className="star-col">{s.col}</code>
                    <p>{s.text}</p>
                  </div>
                ))}
              </div>
              <ul className="fam-list">
                {data.evidence.novel.families.map(f => <li key={f}>{f}</li>)}
              </ul>
            </>}

            <h2>{data.evidence.validation.headline}</h2>
            <ul>{data.evidence.validation.items.map(x => <li key={x}>{x}</li>)}</ul>

            {data.evidence.embedding && (() => {
              const E = data.evidence.embedding
              return <>
                <h2>{E.title}</h2>
                {E.intro.map((p, i) => <p className="emb-p" key={i}>{p}</p>)}
                <div className="emb-facts">
                  {E.facts.map(f => <span className="chip" key={f}>{f}</span>)}
                </div>
                <table className="emb-table">
                  <thead><tr><th></th>{E.scoreboard.cols.map(c =>
                    <th key={c} className={c.includes('hybrid') ? 'hot' : ''}>{c}</th>)}</tr></thead>
                  <tbody>
                    {E.scoreboard.rows.map(r => (
                      <tr key={r.metric}>
                        <td>{r.metric}</td>
                        {r.vals.map((v, i) => (
                          <td key={i} className={r.fail.includes(i) ? 'fail' :
                            (i === 2 ? 'hot' : '')}>{v}</td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
                <Src text={E.src} />
              </>
            })()}
          </div>
        )}
      </>}
    </div>
  )
}
