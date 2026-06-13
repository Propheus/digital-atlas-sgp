import React, { useEffect, useRef, useState } from 'react'
import mapboxgl from 'mapbox-gl'

mapboxgl.accessToken = import.meta.env.VITE_MAPBOX_TOKEN || ''

const SEQ = ['#0b3b3a', '#0f766e', '#14b8a6', '#fcd34d', '#f97316', '#ef4444']
const NODATA = '#142c2b'
const DOMAINS = { cap_supermarket: [0, 2.6], rent_resi_psf_med: [1.5, 7], min15_score: [10, 100] }

const GROUPS = [
  { tag: 'NEIGHBOURHOODS', sub: 'hex8 fingerprint · plexis-e1 · 256 numbers', emb: 'plexis-e1 (hex8 · 256-d)', entries: [
    { id: 'e1', t: 'Pilot here, roll out there', s: 'a trial’s rollout list IS its functional twins' },
    { id: 'e2', t: 'Is this rent fair?', s: 'benchmark any number against the twins' },
    { id: 'e3', t: 'What’s missing here?', s: 'gaps appear where a hex trails its twins' },
    { id: 'e4', t: 'What is Tengah becoming?', s: 'a new town’s trajectory through the space' },
    { id: 'e5', t: 'Fuel for every model', s: '256 columns of city structure, probe-tested' },
  ] },
  { tag: 'PLACES', sub: 'venue fingerprint · plexis-p1 · 64 numbers', emb: 'plexis-p1 (place · 64-d)', entries: [
    { id: 'e6', t: 'Find me 12 more like this one', s: 'expansion scouting by structure, not stars' },
    { id: 'e7', t: 'Where does FairPrice go next?', s: 'brand siting DNA → a ghost map' },
    { id: 'e8', t: 'What should fill this corner?', s: 'archetypes its twins host — and it lacks' },
    { id: 'e9', t: 'The misfit detector', s: 'venues unlike their own street' },
    { id: 'e10', t: 'The market’s real segments', s: '48 functional clusters on the real map' },
  ] },
]

// plain-language phrasing for shared twin traits (subset used in twins.json)
const PHRASE = {
  pop_resident: ['densely lived-in', 'lightly lived-in'], dt_pop: ['fills up by day', 'quiet by day'],
  cap_total: ['demand to spare', 'fully served'], iso_walk10_pop: ['walk-dense', 'walk-sparse'],
  iso_transit15_pop: ['superbly connected', 'transit-isolated'], rent_resi_psf_med: ['expensive', 'affordable'],
  biz_live_robust: ['business-dense streets', 'business-thin'], biz_recent_dead_share: ['high-churn', 'low-churn'],
  vis_exit_footfall: ['heavy MRT footfall', 'little MRT footfall'], od_throughput: ['major transit node', 'off the grid'],
  labor_pool_45m: ['can staff anything', 'hard to staff'], labor_jobs_balance_45m: ['job-rich', 'bedroom community'],
  min15_score: ['complete neighbourhood', 'amenity-poor'], time_to_cbd_min: ['far from centre', 'close to centre'],
  nl_2024: ['bright at night', 'dark at night'], pipe_mrt_dist_m: ['missed by new rail', 'near coming rail'],
  pipe_dev_capacity_res: ['growth headroom', 'built out'], pc_total: ['packed with places', 'place-sparse'],
  pc_cat_restaurant: ['eating street', 'thin on food'], pc_cat_shopping_retail: ['retail-heavy', 'light on retail'],
  pop_hdb_share: ['HDB heartland', 'private housing'], lu_residential_pct: ['housing-dominated', 'little housing'],
  lu_business_pct: ['working district', 'not office country'], lu_entropy: ['mixed-use', 'single-use'],
  est_built_far: ['dense and tall', 'low-rise'], n_highrise_bldgs: ['high-rise skyline', 'low-rise'],
}
const phrase = (w) => { const p = PHRASE[w.k]; return p ? ((w.pa + w.pb) / 2 >= 50 ? p[0] : p[1]) : null }
const CATC = { cafe_coffee: '#fcd34d', restaurant: '#f97316', bakery: '#fde68a', bar_nightlife: '#c084fc',
  hawker: '#fb923c', supermarket: '#7dd3fc', health_medical: '#34d399', shopping_retail: '#38bdf8' }

const Emb = ({ which }) => (
  <div className="emb-badge"><span className="hexglyph">⬢</span> FROM THE EMBEDDINGS — this answer is
    distance in <b>{which}</b> fingerprint space. No hand-made rule produced it.</div>
)
const Src = ({ text }) => <div className="src">ATLAS · {text}</div>

export default function App() {
  const mapRef = useRef(null)
  const mapDiv = useRef(null)
  const [data, setData] = useState(null)
  const [active, setActive] = useState('e1')
  const [pick, setPick] = useState(null)       // entry-local selection
  const hprop = useRef({})
  const centroid = useRef({})

  useEffect(() => {
    const map = new mapboxgl.Map({
      container: mapDiv.current, style: 'mapbox://styles/mapbox/dark-v11',
      center: [103.82, 1.35], zoom: 10.3, attributionControl: false,
    })
    map.on('error', () => {})
    mapRef.current = map
    Promise.all(['hexes.geojson', 'twins.json', 'diary.json']
      .map(f => fetch('/data/' + f).then(r => r.json())))
      .then(([hexes, twins, diary]) => {
        hexes.features.forEach(f => {
          hprop.current[f.properties.id] = f.properties
          const ring = f.geometry.coordinates[0], n = ring.length - 1
          centroid.current[f.properties.id] =
            [ring.slice(0, n).reduce((s, c) => s + c[0], 0) / n,
             ring.slice(0, n).reduce((s, c) => s + c[1], 0) / n]
        })
        const ready = (fn) => (map.isStyleLoaded() ? fn() : map.on('load', fn))
        ready(() => {
          if (map.getSource('hex')) return
          map.addSource('hex', { type: 'geojson', data: hexes })
          map.addLayer({ id: 'hex-fill', type: 'fill', source: 'hex',
            paint: { 'fill-color': NODATA, 'fill-opacity': 0.55,
              'fill-color-transition': { duration: 600 } } })
          map.addLayer({ id: 'hex-line', type: 'line', source: 'hex',
            paint: { 'line-color': '#0b1220', 'line-width': 0.4, 'line-opacity': 0.4 } })
          for (const s of ['hl', 'twin-hl', 'lines', 'dots'])
            map.addSource(s, { type: 'geojson', data: { type: 'FeatureCollection', features: [] } })
          map.addLayer({ id: 'twin-hl', type: 'line', source: 'twin-hl',
            paint: { 'line-color': '#20b2aa', 'line-width': 2.4 } })
          map.addLayer({ id: 'lines', type: 'line', source: 'lines',
            paint: { 'line-color': '#20b2aa', 'line-dasharray': [1.6, 1.4],
              'line-width': ['coalesce', ['get', 'w'], 1.6],
              'line-opacity': 0.85 } })
          map.addLayer({ id: 'hl', type: 'line', source: 'hl',
            paint: { 'line-color': '#fcd34d', 'line-width': 3 } })
          map.addLayer({ id: 'dots', type: 'circle', source: 'dots',
            paint: { 'circle-radius': ['coalesce', ['get', 'r'], 6],
              'circle-color': ['coalesce', ['get', 'c'], '#20b2aa'],
              'circle-stroke-color': '#ffffff', 'circle-stroke-width': 1.4,
              'circle-emissive-strength': 1 } })
          map.on('click', 'hex-fill', e => {
            const id = e.features[0].properties.id
            if (['e1', 'e2'].includes(activeRef.current)) setPick(id)
          })
          map.on('mouseenter', 'hex-fill', () => map.getCanvas().style.cursor = 'pointer')
          map.on('mouseleave', 'hex-fill', () => map.getCanvas().style.cursor = '')
          setData({ hexes, twins, diary })
        })
      })
    return () => map.remove()
  }, [])
  const activeRef = useRef('e1')
  useEffect(() => { activeRef.current = active }, [active])

  const setSrc = (id, feats) =>
    mapRef.current?.getSource(id)?.setData({ type: 'FeatureCollection', features: feats })
  const clearAll = () => ['hl', 'twin-hl', 'lines', 'dots'].forEach(s => setSrc(s, []))
  const hexFeat = (id) => data.hexes.features.find(f => f.properties.id === id)
  const fill = (expr) => mapRef.current?.setPaintProperty('hex-fill', 'fill-color', expr)
  const metricExpr = (m) => {
    const [lo, hi] = DOMAINS[m]
    const stops = SEQ.flatMap((c, i) => [lo + (i / (SEQ.length - 1)) * (hi - lo), c])
    return ['case', ['==', ['get', m], null], NODATA,
      ['interpolate', ['linear'], ['to-number', ['get', m], 0], ...stops]]
  }
  const segLoaded = useRef(false)

  const drawTwinStar = (anchor) => {
    const tws = data.twins[anchor] || []
    if (!tws.length) { clearAll(); setSrc('hl', [hexFeat(anchor)]); return }
    setSrc('hl', [hexFeat(anchor)])
    setSrc('twin-hl', tws.map(t => hexFeat(t.id)).filter(Boolean))
    const c0 = centroid.current[anchor]
    setSrc('lines', tws.map(t => ({ type: 'Feature',
      properties: { w: 1 + (t.s || 0.7) * 3 },
      geometry: { type: 'LineString', coordinates: [c0, centroid.current[t.id]] } })))
    setSrc('dots', [])
    mapRef.current.flyTo({ center: c0, zoom: 10.8, duration: 1400 })
  }

  // ---- per-entry map state ----
  useEffect(() => {
    if (!data) return
    const map = mapRef.current
    const d = data.diary
    clearAll()
    if (map.getLayer('segments')) map.setLayoutProperty('segments', 'visibility', 'none')
    map.setLayoutProperty('hex-fill', 'visibility', active === 'e10' ? 'none' : 'visible')
    fill(NODATA)

    if (active === 'e1') { const a = pick || d.e1.anchor; drawTwinStar(a) }
    if (active === 'e2') {
      fill(metricExpr('rent_resi_psf_med'))
      const a = pick || d.e2.default; drawTwinStar(a)
    }
    if (active === 'e3') {
      fill(metricExpr('cap_supermarket'))
      const g = d.e3.gaps[pick ?? 0] || d.e3.gaps[0]
      if (g) drawTwinStar(g.hex)
    }
    if (active === 'e4') {
      setSrc('hl', d.e4.hexes.map(hexFeat).filter(Boolean))
      const tws = [...new Set(d.e4.hexes.flatMap(h => (data.twins[h] || []).map(t => t.id)))]
      setSrc('twin-hl', tws.map(hexFeat).filter(Boolean))
      map.flyTo({ center: [103.73, 1.36], zoom: 11.3, duration: 1400 })
    }
    if (active === 'e5') {
      fill(metricExpr('min15_score'))
      map.flyTo({ center: [103.82, 1.35], zoom: 10.3, duration: 1200 })
    }
    if (active === 'e6') {
      const a = d.e6.anchors[pick ?? 0] || d.e6.anchors[0]
      if (a) {
        setSrc('dots', [
          { type: 'Feature', properties: { c: '#fcd34d', r: 9 },
            geometry: { type: 'Point', coordinates: [a.anchor.lng, a.anchor.lat] } },
          ...a.sibs.map(s => ({ type: 'Feature',
            properties: { c: CATC[s.cat] || '#20b2aa', r: 6 },
            geometry: { type: 'Point', coordinates: [s.lng, s.lat] } }))])
        setSrc('lines', a.sibs.map(s => ({ type: 'Feature',
          properties: { w: 1.4 },
          geometry: { type: 'LineString',
            coordinates: [[a.anchor.lng, a.anchor.lat], [s.lng, s.lat]] } })))
        map.flyTo({ center: [103.82, 1.35], zoom: 10.6, duration: 1400 })
      }
    }
    if (active === 'e7') {
      setSrc('dots', d.e7.outlets.map(o => ({ type: 'Feature',
        properties: { c: '#94a3b8', r: 2.6 },
        geometry: { type: 'Point', coordinates: o } })))
      setSrc('twin-hl', d.e7.ghosts.map(g => hexFeat(g.hex)).filter(Boolean))
      setSrc('hl', [])
      map.flyTo({ center: [103.82, 1.35], zoom: 10.4, duration: 1400 })
    }
    if (active === 'e8') {
      const c = d.e8.corners[pick ?? 0] || d.e8.corners[0]
      if (c) drawTwinStar(c.hex)
    }
    if (active === 'e9') {
      setSrc('dots', d.e9.misfits.map((m, i) => ({ type: 'Feature',
        properties: { c: i === (pick ?? -1) ? '#fcd34d' : '#ef4444', r: i === (pick ?? -1) ? 9 : 5 },
        geometry: { type: 'Point', coordinates: [m.lng, m.lat] } })))
      const m = d.e9.misfits[pick ?? -1]
      if (m) map.flyTo({ center: [m.lng, m.lat], zoom: 13.5, duration: 1400 })
      else map.flyTo({ center: [103.82, 1.35], zoom: 10.4, duration: 1200 })
    }
    if (active === 'e10') {
      const show = () => map.setLayoutProperty('segments', 'visibility', 'visible')
      if (!segLoaded.current) {
        segLoaded.current = true
        fetch('/data/segments.geojson').then(r => r.json()).then(seg => {
          map.addSource('segments', { type: 'geojson', data: seg })
          map.addLayer({ id: 'segments', type: 'circle', source: 'segments',
            paint: { 'circle-radius': 2.2, 'circle-color': ['get', 'c'],
              'circle-opacity': 0.75, 'circle-emissive-strength': 1 } })
        })
      } else show()
      map.flyTo({ center: [103.82, 1.35], zoom: 10.6, duration: 1400 })
    }
  }, [active, pick, data])

  const d = data?.diary
  const group = GROUPS.find(g => g.entries.some(e => e.id === active))
  const entry = group.entries.find(e => e.id === active)
  const name = (h) => hprop.current[h]?.parent_subzone_name?.toLowerCase() || h

  // ---- right-panel content per entry ----
  const right = () => {
    if (!data) return <p className="dim">opening the diary…</p>
    const tw = (a) => data.twins[a] || []
    if (active === 'e1') {
      const a = pick || d.e1.anchor
      return <>
        <p>Run a pilot in <b>{name(a)}</b> and the findings transfer to the places that
          <i> function</i> like it — not the places next door. The teal hexes are its five
          twins; that's the rollout list. <span className="hint">click any hex to re-anchor</span></p>
        {tw(a).map(t => (
          <div className="row" key={t.id}>
            <b>{t.name.toLowerCase()}</b>
            <span className="dim">{(t.why || []).slice(0, 2).map(phrase).filter(Boolean).join(' · ') || 'matches across the whole fingerprint'}</span>
            <span className="simtag">closer than {t.sim}% of SG</span>
          </div>))}
      </>
    }
    if (active === 'e2') {
      const a = pick || d.e2.default
      const r0 = hprop.current[a]?.rent_resi_psf_med
      const tws = tw(a).map(t => ({ n: t.name, r: hprop.current[t.id]?.rent_resi_psf_med })).filter(x => x.r)
      const mean = tws.length ? tws.reduce((s, x) => s + x.r, 0) / tws.length : null
      const mx = Math.max(r0 || 0, ...tws.map(x => x.r), 0.01)
      return <>
        <p>Is <b>{name(a)}</b>'s rent high? Wrong question. Is it high <i>for what it is</i>?
          Compare it only to its functional twins: <span className="hint">click any hex</span></p>
        {r0 && <div className="bar-row you"><span>{name(a)} (you)</span>
          <div className="bar"><i style={{ width: (r0 / mx) * 100 + '%', background: '#fcd34d' }} /></div>
          <b>S${r0.toFixed(2)}</b></div>}
        {tws.map(x => <div className="bar-row" key={x.n}><span>{x.n.toLowerCase()}</span>
          <div className="bar"><i style={{ width: (x.r / mx) * 100 + '%' }} /></div>
          <b>S${x.r.toFixed(2)}</b></div>)}
        {r0 && mean && <p className="verdict">{r0 > mean * 1.15 ? `≈${Math.round((r0 / mean - 1) * 100)}% ABOVE its twins — expensive for what it is`
          : r0 < mean * 0.85 ? `≈${Math.round((1 - r0 / mean) * 100)}% BELOW its twins — a relative bargain` : 'in line with its twins — fairly priced for its function'}</p>}
      </>
    }
    if (active === 'e3') {
      const g = d.e3.gaps[pick ?? 0] || d.e3.gaps[0]
      return <>
        <p>The twins supply the <i>expectation</i>. <b>{g.name.toLowerCase()}</b> could sustain
          just <b>{g.self}</b> new supermarket-equivalents — its five twins average <b>{g.twin_mean}</b>.
          Same kind of place, half the provision: that shortfall is a shortlist entry, not trivia.</p>
        <div className="chips">{d.e3.gaps.map((x, i) => (
          <button key={x.hex} className={'chip' + ((pick ?? 0) === i ? ' on' : '')}
            onClick={() => setPick(i)}>{x.name.toLowerCase()}</button>))}</div>
        {g.twins.map(t => <div className="row slim" key={t.name}><b>{t.name.toLowerCase()}</b>
          <span className="dim">capture {t.cap ?? '—'}</span></div>)}
      </>
    }
    if (active === 'e4') {
      return <>
        <p>Tengah is still being built — so <i>what is it turning into?</i> Ask where its hexes'
          twins live today. The answer is its functional forecast: borrow that town's amenity
          timeline and school pressure as Tengah's preview.</p>
        {d.e4.towns.map(([t, v]) => (
          <div className="bar-row" key={t}><span>{t.toLowerCase()}</span>
            <div className="bar"><i style={{ width: (v / d.e4.towns[0][1]) * 100 + '%' }} /></div>
            <b>{v}</b></div>))}
        <p className="dim">votes = how often each town appears among the twins of Tengah's {d.e4.hexes.length} scored hexes</p>
      </>
    }
    if (active === 'e5') {
      return <>
        <p>The quiet workhorse: any downstream model starts from the 256-number fingerprint
          instead of 801 raw columns. Probe-tested on held-out data:</p>
        <div className="row slim"><b>housing prices</b><span className="dim">read back at</span><span className="simtag">R² 0.81</span></div>
        <div className="row slim"><b>transit throughput</b><span className="dim">read back at</span><span className="simtag">R² 0.90</span></div>
        <div className="row slim"><b>adequacy score</b><span className="dim">read back at</span><span className="simtag">R² 0.93</span></div>
        <p className="dim">map shows one example signal (15-minute-city score) the fingerprint carries.
          House rule: use the vectors RAW — never re-standardise per dimension.</p>
      </>
    }
    if (active === 'e6') {
      const a = d.e6.anchors[pick ?? 0] || d.e6.anchors[0]
      return <>
        <p>Your best outlet is <b>{a.anchor.name}</b> — {a.label}. Its 12 nearest fingerprints
          are the same <i>kind</i> of venue, island-wide. The model found same-brand siblings
          and same-trade rivals it was never told about.</p>
        <div className="chips">{d.e6.anchors.map((x, i) => (
          <button key={x.anchor.name} className={'chip' + ((pick ?? 0) === i ? ' on' : '')}
            onClick={() => setPick(i)}>{x.anchor.name.split('(')[0]}</button>))}</div>
        {a.sibs.slice(0, 9).map(s => <div className="row slim" key={s.rank}>
          <b>#{s.rank} {s.name}</b><span className="dim">{s.sz?.toLowerCase()}</span></div>)}
      </>
    }
    if (active === 'e7') {
      return <>
        <p><b>{d.e7.n_outlets} FairPrice outlets</b> (grey dots) define the brand's home turf.
          Now: which hexes are functional twins of those homes — but have <i>no FairPrice</i>?
          The teal hexes are the ghost map. Note who's on it: <b>Yunnan</b> — the
          government-confirmed supermarket desert — surfaces a third independent way.</p>
        {d.e7.ghosts.map(g => <div className="row slim" key={g.hex}>
          <b>{g.name.toLowerCase()}</b>
          <span className="dim">{g.votes} of its FairPrice-twin hexes vote for it</span></div>)}
      </>
    }
    if (active === 'e8') {
      const c = d.e8.corners[pick ?? 0] || d.e8.corners[0]
      return <>
        <p>What should fill an empty unit in <b>{c.name.toLowerCase()}</b>? Look at what its
          five twins host that it doesn't. If most twins support an archetype, this corner
          probably can too — with the twins as the evidence.</p>
        <div className="chips">{d.e8.corners.map((x, i) => (
          <button key={x.hex} className={'chip' + ((pick ?? 0) === i ? ' on' : '')}
            onClick={() => setPick(i)}>{x.name.toLowerCase()}</button>))}</div>
        {c.wants.map(w => <div className="row slim" key={w.cat}>
          <b>{w.cat.replace(/_/g, ' ')}</b>
          <span className="dim">present in {w.votes} of 5 twins, absent here</span></div>)}
      </>
    }
    if (active === 'e9') {
      return <>
        <p>Every red dot is the venue that least belongs to its own street — its fingerprint
          sits farthest from its hex's crowd. Sometimes a contrarian bet; often a tenant in
          the wrong place. Cross-reference with the atlas's business-mortality layer for an
          early-warning score.</p>
        {d.e9.misfits.slice(0, 12).map((m, i) => (
          <button className={'row btn' + ((pick ?? -1) === i ? ' on' : '')} key={i}
            onClick={() => setPick(i)}>
            <b>{m.name}</b>
            <span className="dim">{m.cat.replace(/_/g, ' ')} · {m.sz?.toLowerCase()} · unlike its {m.crowd} neighbours</span>
          </button>))}
      </>
    }
    if (active === 'e10') {
      return <>
        <p>Forget categories — colour every venue by its <b>functional cluster</b> ({d.e10.n_clusters} of
          them, learned from structure). Orchard retail, industrial canteens and void-deck
          services each form their own colour, and the colours interleave across the island:
          the market's real segments don't follow district lines.</p>
        <p className="dim">{d.e10.n_shown.toLocaleString()} venues shown (sampled from 190,591).
          Fly the full space in <a href="http://10.0.2.25:16096" target="_blank" rel="noreferrer">Places Constellation →</a></p>
      </>
    }
    return null
  }

  return (
    <div className="app">
      <header className="bar">
        <span className="brand">Atlas <span className="hot">Diary</span></span>
        <span className="bar-sub">ten things you can ask a city, answered live</span>
        <span className="powered">powered by Digital Atlas</span>
        <img className="logo" src="/propheus.svg" alt="Propheus" />
      </header>

      <aside className="left">
        {GROUPS.map(g => (
          <div key={g.tag} className="group">
            <div className="gtag">{g.tag}<span>{g.sub}</span></div>
            {g.entries.map(e => (
              <button key={e.id} className={'acc' + (active === e.id ? ' on' : '')}
                onClick={() => { setActive(e.id); setPick(null) }}>
                <b>{e.t}</b>
                {active === e.id && <span className="accsub">{e.s}</span>}
              </button>
            ))}
          </div>
        ))}
        <Src text="hex twins: plexis-e1 · place siblings/misfits/segments: plexis-p1 · capture/rents/15-min: atlas v5 layers" />
      </aside>

      <div ref={mapDiv} className="map" />

      <aside className="right">
        <div className="panel-tag">{entry.t}</div>
        {right()}
        <Emb which={group.emb} />
      </aside>
    </div>
  )
}
