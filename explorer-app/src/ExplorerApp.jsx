import React, { useEffect, useRef, useState, useMemo } from 'react'
import mapboxgl from 'mapbox-gl'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

mapboxgl.accessToken = import.meta.env.VITE_MAPBOX_TOKEN || ''

// sequential (teal->yellow->red) and diverging (blue<->orange) palettes
const SEQ = ['#0b3b3a', '#0f766e', '#14b8a6', '#fcd34d', '#f97316', '#ef4444']
const DIV = ['#2563eb', '#60a5fa', '#1e293b', '#fbbf24', '#f97316']
const DIVERGING = new Set(['od_net', 'breathing', 'latent_demand'])
const NODATA = '#1f2937'

const fmt = (v, unit) => {
  if (v === null || v === undefined) return '—'
  if (typeof v === 'string') return v
  if (typeof v === 'boolean') return v ? 'yes' : 'no'   // pipe_new_mrt_within_800m
  if (unit === 'ppl' || unit === 'trips/mo') return Math.round(v).toLocaleString()
  if (unit === '$/m2') return '$' + Math.round(v).toLocaleString()
  if (unit === 'frac') return (v * 100).toFixed(1) + '%'
  if (unit === '%') return v.toFixed(1) + '%'
  return Math.abs(v) >= 1000 ? Math.round(v).toLocaleString() : v.toFixed(v % 1 === 0 ? 0 : 2)
}

function colorExpr(metric) {
  const [lo, hi] = metric.domain
  let pal = DIVERGING.has(metric.id) ? DIV : SEQ
  if (metric.reverse) pal = [...pal].reverse()   // e.g. future-MRT distance: closer = hotter
  const stops = []
  const n = pal.length
  for (let i = 0; i < n; i++) {
    const t = i / (n - 1)
    stops.push(lo + t * (hi - lo), pal[i])
  }
  return ['case',
    ['==', ['get', metric.col], null], NODATA,
    ['interpolate', ['linear'], ['to-number', ['get', metric.col], 0], ...stops],
  ]
}

export default function ExplorerApp() {
  const mapRef = useRef(null)
  const mapDiv = useRef(null)
  const [manifest, setManifest] = useState(null)
  const [level, setLevel] = useState('hex8')        // hex8 | subzone
  const [metricId, setMetricId] = useState('commercial_activity')
  const [selected, setSelected] = useState(null)
  const [search, setSearch] = useState('')
  const [help, setHelp] = useState(false)
  const [mrt, setMrt] = useState(false)
  const [category, setCategory] = useState('Commercial')
  const dataRef = useRef({ hex8: null, subzone: null })

  const metric = useMemo(
    () => manifest?.metrics.find(m => m.id === metricId) || manifest?.metrics[0],
    [manifest, metricId])
  const metricsInCat = useMemo(
    () => manifest ? manifest.metrics.filter(m => m.group === category) : [],
    [manifest, category])
  const selectCategory = c => {
    setCategory(c)
    const ms = manifest.metrics.filter(m => m.group === c)
    if (ms.length && !ms.some(m => m.id === metricId)) setMetricId(ms[0].id)
  }

  // ---- init map + load data ----
  useEffect(() => {
    const map = new mapboxgl.Map({
      container: mapDiv.current,
      style: 'mapbox://styles/mapbox/dark-v11',
      center: [103.82, 1.352], zoom: 10.6, attributionControl: false,
    })
    mapRef.current = map
    map.addControl(new mapboxgl.NavigationControl({ showCompass: false }), 'bottom-right')

    Promise.all([
      fetch('/data/layers.json').then(r => r.json()),
      fetch('/data/hex8_explore.geojson').then(r => r.json()),
      fetch('/data/subzone_explore.geojson').then(r => r.json()).catch(() => null),
      fetch('/data/mrt_lines.geojson').then(r => r.json()).catch(() => null),
      fetch('/data/mrt_stations.geojson').then(r => r.json()).catch(() => null),
    ]).then(([man, hex8, subzone, lines, stations]) => {
      dataRef.current = { hex8, subzone }
      setManifest(man)
      map.on('load', () => {
        map.addSource('hex8', { type: 'geojson', data: hex8 })
        map.addSource('subzone', { type: 'geojson', data: subzone || { type: 'FeatureCollection', features: [] } })
        map.addSource('sel', { type: 'geojson', data: { type: 'FeatureCollection', features: [] } })
        const m0 = man.metrics.find(x => x.id === 'commercial_activity') || man.metrics[0]
        map.addLayer({ id: 'hex8-fill', type: 'fill', source: 'hex8',
          paint: { 'fill-color': colorExpr(m0), 'fill-opacity': 0.72 } })
        map.addLayer({ id: 'hex8-line', type: 'line', source: 'hex8',
          paint: { 'line-color': '#0f172a', 'line-width': 0.4, 'line-opacity': 0.5 } })
        map.addLayer({ id: 'sz-fill', type: 'fill', source: 'subzone', layout: { visibility: 'none' },
          paint: { 'fill-color': colorExpr(m0), 'fill-opacity': 0.7 } })
        map.addLayer({ id: 'sz-line', type: 'line', source: 'subzone', layout: { visibility: 'none' },
          paint: { 'line-color': '#334155', 'line-width': 0.6 } })
        map.addLayer({ id: 'sel-line', type: 'line', source: 'sel',
          paint: { 'line-color': '#fcd34d', 'line-width': 2.4 } })
        if (lines) { map.addSource('mrt', { type: 'geojson', data: lines })
          map.addLayer({ id: 'mrt', type: 'line', source: 'mrt', layout: { visibility: 'none' },
            paint: { 'line-color': '#67e8f9', 'line-width': 1.4, 'line-opacity': 0.6 } }) }
        if (stations) { map.addSource('stn', { type: 'geojson', data: stations })
          map.addLayer({ id: 'stn', type: 'circle', source: 'stn', layout: { visibility: 'none' },
            paint: { 'circle-radius': 2.5, 'circle-color': '#a5f3fc', 'circle-opacity': 0.8 } }) }

        const onClick = e => {
          const f = e.features[0]
          setSelected(f.properties)
          map.getSource('sel').setData({ type: 'FeatureCollection', features: [f] })
        }
        map.on('click', 'hex8-fill', onClick)
        map.on('click', 'sz-fill', onClick)
        for (const lyr of ['hex8-fill', 'sz-fill']) {
          map.on('mouseenter', lyr, () => map.getCanvas().style.cursor = 'pointer')
          map.on('mouseleave', lyr, () => map.getCanvas().style.cursor = '')
        }
      })
    })
    return () => map.remove()
  }, [])

  // ---- recolor on metric change ----
  useEffect(() => {
    const map = mapRef.current
    if (!map || !map.isStyleLoaded() || !metric) return
    const expr = colorExpr(metric)
    if (map.getLayer('hex8-fill')) map.setPaintProperty('hex8-fill', 'fill-color', expr)
    if (map.getLayer('sz-fill')) map.setPaintProperty('sz-fill', 'fill-color', expr)
  }, [metric])

  // ---- level toggle ----
  useEffect(() => {
    const map = mapRef.current
    if (!map || !map.getLayer || !map.getLayer('hex8-fill')) return
    const h = level === 'hex8' ? 'visible' : 'none'
    const s = level === 'subzone' ? 'visible' : 'none'
    map.setLayoutProperty('hex8-fill', 'visibility', h)
    map.setLayoutProperty('hex8-line', 'visibility', h)
    map.setLayoutProperty('sz-fill', 'visibility', s)
    map.setLayoutProperty('sz-line', 'visibility', s)
  }, [level])

  // ---- mrt toggle ----
  useEffect(() => {
    const map = mapRef.current
    if (!map || !map.getLayer || !map.getLayer('mrt')) return
    const v = mrt ? 'visible' : 'none'
    map.setLayoutProperty('mrt', 'visibility', v)
    if (map.getLayer('stn')) map.setLayoutProperty('stn', 'visibility', v)
  }, [mrt])

  // ---- search ----
  const doSearch = e => {
    e.preventDefault()
    const q = search.trim().toLowerCase()
    if (!q) return
    const fc = dataRef.current[level]
    if (!fc) return
    const f = fc.features.find(ft => {
      const p = ft.properties
      return (p.hex8_id || '').toLowerCase() === q
        || (p.parent_subzone_name || p.SUBZONE_N || p.name || '').toLowerCase().includes(q)
        || (p.parent_pa || p.PLN_AREA_N || '').toLowerCase().includes(q)
        || (p.subzone_c || p.SUBZONE_C || '').toLowerCase() === q
    })
    if (f) {
      setSelected(f.properties)
      mapRef.current.getSource('sel').setData({ type: 'FeatureCollection', features: [f] })
      let c = f.geometry.coordinates
      while (Array.isArray(c) && Array.isArray(c[0])) c = c[0]   // dig to first [lng,lat]
      mapRef.current.flyTo({ center: c, zoom: 13.5 })
    }
  }

  return (
    <div className="app">
      <div ref={mapDiv} className="map" />

      {/* top bar */}
      <header className="topbar">
        <div className="brand"><img src="/propheus.svg" className="logo-img" alt="Propheus" /><span className="brand-name">Digital&nbsp;<b>Atlas</b></span><span className="sub">Singapore · hex8 atlas v5.0.0</span></div>
        <div className="levels">
          <span className="lbl">LEVEL</span>
          {['hex8', 'subzone'].map(l =>
            <button key={l} className={'pill ' + (level === l ? 'on' : '')} onClick={() => setLevel(l)}>{l === 'hex8' ? 'Hex8' : 'Subzone'}</button>)}
        </div>
        {manifest && <div className="levels cats">
          <span className="lbl">LAYERS</span>
          {manifest.categories.map(c =>
            <button key={c} className={'pill ' + (category === c ? 'on' : '')} onClick={() => selectCategory(c)}>{c}</button>)}
        </div>}
        <button className="help-btn" onClick={() => setHelp(true)}>?</button>
      </header>

      {/* metric pills for the active category */}
      {manifest && <div className="metricbar">
        <span className="glabel">METRIC</span>
        {metricsInCat.map(m =>
          <button key={m.id} className={'pill ' + (metricId === m.id ? 'on' : '')} onClick={() => setMetricId(m.id)}>{m.label}</button>)}
        <div className="mbspacer" />
        <span className="glabel">OVERLAY</span>
        <button className={'pill ' + (mrt ? 'on' : '')} onClick={() => setMrt(v => !v)}>MRT/LRT</button>
      </div>}

      {/* left search */}
      <form className="search" onSubmit={doSearch}>
        <input value={search} onChange={e => setSearch(e.target.value)}
          placeholder={level === 'hex8' ? 'Search hex8 id / planning area…' : 'Search subzone / planning area…'} />
        <button type="submit">↵</button>
      </form>

      {/* legend */}
      {metric && <div className="legend">
        <div className="leg-title">{metric.label} <span className="unit">{metric.unit}</span></div>
        <div className="leg-bar" style={{ background: `linear-gradient(to right, ${(metric.reverse ? [...(DIVERGING.has(metric.id) ? DIV : SEQ)].reverse() : (DIVERGING.has(metric.id) ? DIV : SEQ)).join(',')})` }} />
        <div className="leg-ends"><span>{fmt(metric.domain[0], metric.unit)}</span><span>{fmt(metric.domain[1], metric.unit)}</span></div>
      </div>}

      {/* right detail panel */}
      <aside className={'panel ' + (selected ? 'open' : '')}>
        {selected && manifest && <DetailPanel p={selected} manifest={manifest} onClose={() => { setSelected(null); mapRef.current.getSource('sel').setData({ type: 'FeatureCollection', features: [] }) }} />}
      </aside>

      {help && <HelpModal manifest={manifest} onClose={() => setHelp(false)} />}
    </div>
  )
}

function DetailPanel({ p, manifest, onClose }) {
  const title = p.parent_subzone_name || p.SUBZONE_N || p.name || p.hex8_id || 'Selected'
  const pa = p.parent_pa || p.PLN_AREA_N || ''
  const idtail = p.hex8_id ? ' · ' + p.hex8_id : (p.SUBZONE_C ? ' · ' + p.SUBZONE_C : '')
  const unitOf = col => manifest.metrics.find(m => m.col === col)?.unit
  return (
    <div className="panel-inner">
      <div className="panel-head">
        <div><div className="panel-title">{title}</div>
          <div className="panel-sub">{pa}{p.archetype_label ? ' · ' + p.archetype_label : ''}{idtail}</div></div>
        <button className="x" onClick={onClose}>×</button>
      </div>
      <div className="panel-body">
        {Object.entries(manifest.detail_groups).map(([grp, cols]) => {
          const rows = cols.filter(c => p[c] !== undefined && p[c] !== null && c !== 'parent_pa' && c !== 'parent_subzone_name' && c !== 'archetype_label')
          if (!rows.length) return null
          return <div className="dgroup" key={grp}>
            <div className="dgroup-h">{grp}</div>
            {rows.map(c => <div className="drow" key={c}><span>{c}</span><b>{fmt(p[c], unitOf(c))}</b></div>)}
          </div>
        })}
      </div>
    </div>
  )
}

function HelpModal({ manifest, onClose }) {
  const md = useMemo(() => {
    if (!manifest) return ''
    let s = '# Digital Atlas — layer guide\n\nEvery hex8 (~0.74 km²) carries 687 features from the Plexis v5.0.0 atlas, including the validation-gated site-selection layers (Opportunity / Catchment / Business / Future). Pick a metric up top to color the map; click any hex for the full breakdown. Singapore total population 6.04M (SingStat Jun-2024). Site-selection metrics are hex8-only (gray at subzone level, like the OD group).\n\n'
    const g = {}
    manifest.metrics.forEach(m => { (g[m.group] = g[m.group] || []).push(m) })
    for (const [grp, ms] of Object.entries(g)) {
      s += `\n## ${grp}\n\n`
      for (const m of ms) s += `**${m.label}** \`${m.col}\` — ${m.desc}\n\n`
    }
    return s
  }, [manifest])
  return <div className="modal-bg" onClick={onClose}>
    <div className="modal" onClick={e => e.stopPropagation()}>
      <button className="x" onClick={onClose}>×</button>
      <div className="modal-body"><ReactMarkdown remarkPlugins={[remarkGfm]}>{md}</ReactMarkdown></div>
    </div>
  </div>
}
