import React, { useEffect, useMemo, useRef, useState } from 'react'
import DeckGL from '@deck.gl/react'
import { OrthographicView, LinearInterpolator } from '@deck.gl/core'
import { ScatterplotLayer, TextLayer } from '@deck.gl/layers'
import mapboxgl from 'mapbox-gl'
import { forceSimulation, forceLink, forceManyBody, forceCenter, forceCollide } from 'd3-force'

mapboxgl.accessToken = import.meta.env.VITE_MAPBOX_TOKEN || ''

const hex2rgb = (h) => [parseInt(h.slice(1, 3), 16), parseInt(h.slice(3, 5), 16), parseInt(h.slice(5, 7), 16)]
const Src = ({ text }) => <div className="src">ATLAS · {text}</div>

export default function App() {
  const [meta, setMeta] = useState(null)
  const [arrays, setArrays] = useState(null)
  const [xy, setXy] = useState(null)            // Float32Array, 2*n
  const [colorMode, setColorMode] = useState('cat')   // cat | geo
  const [center, setCenter] = useState(null)   // row idx -> constellation mode
  const [graph, setGraph] = useState(null)     // {nodes, links} after d3 layout
  const [hover, setHover] = useState(null)
  const [q, setQ] = useState('')
  const [view, setView] = useState({ target: [500, -500, 0], zoom: -1.1 })
  const [tick, setTick] = useState(0)          // drives the twinkle
  const [showHelp, setShowHelp] = useState(false)
  const mapRef = useRef(null)
  const mapDiv = useRef(null)
  const shardCache = useRef({})

  // ---- load static data ----
  useEffect(() => {
    Promise.all([
      fetch('/data/meta.json').then(r => r.json()),
      fetch('/data/arrays.json').then(r => r.json()),
      fetch('/data/galaxy_xy.bin').then(r => r.arrayBuffer()),
    ]).then(([m, a, buf]) => {
      setMeta(m); setArrays(a); setXy(new Float32Array(buf))
      // cinematic arrival: drift from deep space into the galaxy
      setTimeout(() => setView(v => ({ ...v, zoom: 0.22,
        transitionDuration: 3200,
        transitionInterpolator: new LinearInterpolator(['zoom', 'target']) })), 250)
    })
  }, [])

  // twinkle clock (only while the galaxy is on screen)
  useEffect(() => {
    if (center !== null) return
    const iv = setInterval(() => setTick(t => t + 1), 110)
    return () => clearInterval(iv)
  }, [center])

  // ~1,400 stars get a slow shimmer
  const sparkIdx = useMemo(() => {
    if (!meta) return null
    const r = []
    for (let i = 0; i < meta.n; i += Math.floor(meta.n / 1400)) r.push(i)
    return r
  }, [meta])

  // ---- precomputed GPU attributes for the galaxy ----
  const galaxyAttrs = useMemo(() => {
    if (!meta || !arrays || !xy) return null
    const n = meta.n
    const pos = new Float32Array(n * 2)
    for (let i = 0; i < n; i++) { pos[2 * i] = xy[2 * i]; pos[2 * i + 1] = -xy[2 * i + 1] }
    const catCol = new Uint8Array(n * 3)
    const geoCol = new Uint8Array(n * 3)
    const palette = meta.cat_colors.map(hex2rgb)
    let latMin = 1.15, latMax = 1.48, lngMin = 103.6, lngMax = 104.05
    for (let i = 0; i < n; i++) {
      const c = palette[arrays.cat[i]] || [100, 116, 139]
      catCol.set(c, 3 * i)
      // geography rainbow: where you are on the island becomes the colour —
      // if the galaxy still looks mixed, function space ≠ geography (geo-leak .077)
      const u = (arrays.lng[i] - lngMin) / (lngMax - lngMin)
      const v = (arrays.lat[i] - latMin) / (latMax - latMin)
      geoCol.set([40 + 215 * u, 40 + 215 * v, 230 - 160 * u], 3 * i)
    }
    return { pos, catCol, geoCol }
  }, [meta, arrays, xy])

  // ---- search ----
  const results = useMemo(() => {
    if (!q || q.length < 2 || !arrays) return []
    const needle = q.toLowerCase()
    const out = []
    for (let i = 0; i < arrays.name.length && out.length < 8; i++) {
      if (arrays.name[i].toLowerCase().includes(needle)) out.push(i)
    }
    return out
  }, [q, arrays])

  // ---- constellation: fetch neighbours + run d3 layout ----
  const openConstellation = async (idx) => {
    const sh = idx % (meta.shards || 128)
    if (!shardCache.current[sh])
      shardCache.current[sh] = await fetch(`/data/nn/s${sh}.json`).then(r => r.json())
    const nbrs = shardCache.current[sh][idx] || []
    // cosine sims live in a narrow 0.9x band — normalize WITHIN the star so
    // rank differences become visible distances/widths (relative, like hex twins)
    const sims = nbrs.map(([, s]) => s / 1000)
    const lo = Math.min(...sims), hi = Math.max(...sims)
    const rel = (s) => hi > lo ? (s - lo) / (hi - lo) : 1
    const nodes = [{ i: idx, r: 26, fx: 0, fy: 0 },
      ...nbrs.map(([j, s]) => ({ i: j, sim: s / 1000, rel: rel(s / 1000), r: 15 }))]
    const links = nbrs.map(([j, s]) => ({ source: idx, target: j,
      sim: s / 1000, rel: rel(s / 1000) }))
    const sim = forceSimulation(nodes.map(n => ({ ...n, id: n.i })))
      .force('link', forceLink(links.map(l => ({ ...l })))
        .id(d => d.id).distance(l => 260 + (1 - l.rel) * 380).strength(1))
      .force('charge', forceManyBody().strength(-1400))
      .force('center', forceCenter(0, 0))
      .force('collide', forceCollide().radius(d => d.r * 2.1 + 65))
      .stop()
    for (let t = 0; t < 260; t++) sim.tick()
    setGraph({ center: idx, nodes: sim.nodes(), links })
    setCenter(idx)
    setQ('')
  }

  // ---- geo panel (mapbox) ----
  // ONE persistent map for the app's lifetime. The split view is always
  // mounted and merely hidden in galaxy mode (visibility, not unmount) —
  // destroying/recreating Map instances leaks aborted tile fetches
  // ("DOMException: operation was aborted") and churns WebGL contexts.
  useEffect(() => () => { try { mapRef.current?.remove() } catch { /* noop */ } }, [])
  useEffect(() => {
    if (center === null || !arrays || !graph) return
    if (!mapRef.current && mapDiv.current) {
      mapRef.current = new mapboxgl.Map({
        container: mapDiv.current, style: 'mapbox://styles/mapbox/dark-v11',
        center: [103.82, 1.35], zoom: 10, attributionControl: false,
      })
      mapRef.current.on('error', () => {})   // benign aborted-tile noise
    }
    const map = mapRef.current
    if (!map) return
    map.resize()   // container was hidden; recompute size on show
    const draw = () => {
      if (mapRef.current !== map) return   // torn down while style loaded
      const ids = [center, ...graph.links.map(l => l.target)]
      const feats = graph.links.map(l => ({
        type: 'Feature', properties: { w: 1 + (l.rel ?? 0.5) * 4 },
        geometry: { type: 'LineString',
          coordinates: [[arrays.lng[center], arrays.lat[center]],
                        [arrays.lng[l.target], arrays.lat[l.target]]] } }))
      const pts = ids.map((i, k) => ({
        type: 'Feature', properties: { main: k === 0 ? 1 : 0 },
        geometry: { type: 'Point', coordinates: [arrays.lng[i], arrays.lat[i]] } }))
      const setSrc = (id, data, add) => {
        if (map.getSource(id)) map.getSource(id).setData(data)
        else add()
      }
      setSrc('arcs', { type: 'FeatureCollection', features: feats }, () => {
        map.addSource('arcs', { type: 'geojson', data: { type: 'FeatureCollection', features: feats } })
        map.addLayer({ id: 'arcs', type: 'line', source: 'arcs',
          paint: { 'line-color': '#20b2aa', 'line-width': ['max', 0.6, ['get', 'w']],
            'line-opacity': 0.75, 'line-dasharray': [2, 1.5] } })
      })
      setSrc('pts', { type: 'FeatureCollection', features: pts }, () => {
        map.addSource('pts', { type: 'geojson', data: { type: 'FeatureCollection', features: pts } })
        map.addLayer({ id: 'pts', type: 'circle', source: 'pts',
          paint: { 'circle-radius': ['case', ['==', ['get', 'main'], 1], 11, 7],
            'circle-color': ['case', ['==', ['get', 'main'], 1], '#fcd34d', '#20b2aa'],
            'circle-stroke-color': '#ffffff', 'circle-stroke-width': 2,
            'circle-emissive-strength': 1 } })
      })
      const lons = ids.map(i => arrays.lng[i]), lats = ids.map(i => arrays.lat[i])
      map.fitBounds([[Math.min(...lons), Math.min(...lats)],
                     [Math.max(...lons), Math.max(...lats)]],
        { padding: 70, duration: 1200, maxZoom: 13 })
    }
    map.isStyleLoaded() ? draw() : map.once('load', draw)
  }, [center, graph])

  const layers = useMemo(() => {
    if (!galaxyAttrs || center !== null) return []
    const zoom = view.zoom ?? 0.2
    // quiet by default: only the biggest constellations are named; zooming in
    // reveals the rest — everything else speaks on hover
    const nLabels = zoom < 0.45 ? 9 : zoom < 1.1 ? 22 : 48
    const bySize = [...meta.clusters].sort((a, b) => b.size - a.size)
    const labelData = bySize.slice(0, nLabels)
    const clColor = (d) => hex2rgb(meta.cat_colors[meta.cats.indexOf(d.top_cat)] || '#20b2aa')
    // a featured star roams the galaxy, inviting the click
    const feat = sparkIdx[Math.floor(tick / 45) % sparkIdx.length]
    const L = [
      new ScatterplotLayer({   // nebula glow under the major galaxies, breathing
        id: 'cluster-glow',
        data: bySize.slice(0, 16),
        getPosition: d => [d.cx, -d.cy],
        radiusUnits: 'common',
        getRadius: (d, { index }) => Math.sqrt(d.size) * (1.15 + 0.18 * Math.sin(tick * 0.055 + index * 2.1)),
        getFillColor: d => [...clColor(d), 26],
        updateTriggers: { getRadius: tick },
      }),
      new ScatterplotLayer({
        id: 'galaxy',
        data: { length: meta.n, attributes: {
          getPosition: { value: galaxyAttrs.pos, size: 2 },
          getFillColor: { value: colorMode === 'cat' ? galaxyAttrs.catCol : galaxyAttrs.geoCol, size: 3 },
        } },
        radiusUnits: 'pixels', getRadius: 1.4, opacity: 0.55,
        pickable: true,
        onHover: ({ index }) => setHover(index >= 0 ? index : null),
        onClick: ({ index }) => index >= 0 && openConstellation(index),
        updateTriggers: { getFillColor: colorMode },
        transitions: { getFillColor: 600 },
      }),
      new ScatterplotLayer({   // shimmer: a sprinkle of stars slowly breathing
        id: 'twinkle',
        data: sparkIdx,
        getPosition: i => [galaxyAttrs.pos[2 * i], galaxyAttrs.pos[2 * i + 1]],
        radiusUnits: 'pixels',
        getRadius: (i, { index }) => 1.1 + 1.6 * Math.abs(Math.sin(tick * 0.09 + index * 1.7)),
        getFillColor: [255, 248, 220],
        opacity: 0.5,
        updateTriggers: { getRadius: tick },
      }),
      new TextLayer({
        id: 'cluster-labels',
        data: labelData,
        getPosition: d => [d.cx, -d.cy],
        getText: d => d.name.split(' + ')[0].split(' · ')[0],
        getSize: 12.5, getColor: [255, 255, 255, 175],
        fontFamily: '-apple-system, system-ui, sans-serif',
        outlineWidth: 3, outlineColor: [10, 22, 23, 230],
        fontSettings: { sdf: true },
        transitions: { getColor: 400 },
      }),
    ]
    if (hover === null && feat !== undefined) {
      // call-to-action: one star at a time pulses and asks to be clicked
      L.push(new ScatterplotLayer({
        id: 'feat-ring',
        data: [feat],
        getPosition: i => [galaxyAttrs.pos[2 * i], galaxyAttrs.pos[2 * i + 1]],
        radiusUnits: 'pixels',
        getRadius: 10 + 4 * Math.abs(Math.sin(tick * 0.18)),
        filled: false, stroked: true,
        getLineColor: [252, 211, 77, 210], lineWidthUnits: 'pixels', getLineWidth: 2,
        pickable: true,
        onClick: ({ object }) => object !== undefined && openConstellation(object),
        updateTriggers: { getRadius: tick },
      }))
      L.push(new TextLayer({
        id: 'feat-label',
        data: [feat],
        getPosition: i => [galaxyAttrs.pos[2 * i], galaxyAttrs.pos[2 * i + 1]],
        getText: i => `${arrays.name[i]}  ·  click me ✦`,
        getPixelOffset: [0, -26],
        getSize: 13, getColor: [252, 211, 77, 235],
        fontFamily: '-apple-system, system-ui, sans-serif',
        outlineWidth: 4, outlineColor: [10, 22, 23, 245],
        fontSettings: { sdf: true },
      }))
    }
    if (hover !== null) {
      L.push(new ScatterplotLayer({   // hover halo
        id: 'halo',
        data: [hover],
        getPosition: i => [galaxyAttrs.pos[2 * i], galaxyAttrs.pos[2 * i + 1]],
        radiusUnits: 'pixels', getRadius: 9,
        filled: false, stroked: true,
        getLineColor: [252, 211, 77, 230], lineWidthUnits: 'pixels', getLineWidth: 2,
        transitions: { getRadius: { duration: 250, enter: () => [2] } },
      }))
    }
    return L
  }, [galaxyAttrs, colorMode, center, meta, tick, hover, view.zoom, arrays, sparkIdx])

  const catName = (i) => meta.cats[arrays.cat[i]].replace(/_/g, ' ')
  const catColor = (i) => meta.cat_colors[arrays.cat[i]]
  const loaded = meta && arrays && xy

  return (
    <div className="app">
      <header className="bar">
        <span className="brand" onClick={() => { setCenter(null); setGraph(null) }}>
          Places <span className="hot">Constellation</span></span>
        <span className="bar-sub">{loaded ? `${meta.n.toLocaleString()} places · one similarity space` : 'loading the galaxy…'}</span>
        <button className="helpbtn" onClick={() => setShowHelp(true)}>how it works</button>
        <span className="powered">powered by Digital Atlas</span>
        <div className="search">
          <input placeholder="find any place…" value={q} onChange={e => setQ(e.target.value)} />
          {results.length > 0 && (
            <div className="search-drop">
              {results.map(i => (
                <button key={i} onClick={() => openConstellation(i)}>
                  <i className="dot" style={{ background: catColor(i) }} />
                  {arrays.name[i]} <span>{catName(i)}</span>
                </button>
              ))}
            </div>
          )}
        </div>
        <img className="logo" src="/propheus.svg" alt="Propheus" style={{ marginLeft: 0 }} />
      </header>

      {center === null && loaded && (
        <>
          <div className="galaxy-wrap">
            <DeckGL views={new OrthographicView({ flipY: false })}
              viewState={{ ...view, minZoom: -1.5, maxZoom: 6 }}
              onViewStateChange={({ viewState }) => setView(viewState)}
              controller={true} layers={layers}
              getCursor={() => (hover !== null ? 'pointer' : 'grab')} />
          </div>
          <div className="cta-chip" onClick={() => {
            const i = sparkIdx[Math.floor(tick / 45) % sparkIdx.length]
            if (i !== undefined) openConstellation(i)
          }}>✦ click any star — meet its 12 functional siblings</div>
          {hover !== null && (
            <div className="tip">
              <b>{arrays.name[hover]}</b>
              <span style={{ color: catColor(hover) }}>{catName(hover)}</span>
              <em>{meta.clusters[arrays.cluster[hover]]?.name}</em>
            </div>
          )}
          <div className="panel intro">
            <p><b>{meta.n.toLocaleString()} places</b>, arranged by what they <i>are</i> —
              not where they are. Hover to read the stars. <b>Click one</b> to meet its siblings.</p>
            <div className="toggles">
              <button className={colorMode === 'cat' ? 'on' : ''} onClick={() => setColorMode('cat')}>colour = what it is</button>
              <button className={colorMode === 'geo' ? 'on' : ''} onClick={() => setColorMode('geo')}>colour = where it is</button>
            </div>
            {colorMode === 'geo' && <p className="note">if similarity were geography this would form colour blocks —
              it stays a mixed rainbow (leak ρ = 0.077)</p>}
            <Src text="plexis-p1 64d embedding · UMAP · no rating signals" />
          </div>
        </>
      )}

      {showHelp && (
        <div className="help-back" onClick={() => setShowHelp(false)}>
          <div className="help" onClick={e => e.stopPropagation()}>
            <button className="x" onClick={() => setShowHelp(false)}>×</button>
            <div className="panel-tag">How it works</div>
            <h2>Every place becomes 64 numbers — and distance means similarity</h2>

            <p>Each of the <b>190,591 places</b> on this map has been turned into a
              compact fingerprint of 64 numbers. Two places whose fingerprints sit
              close together <i>function</i> the same way — even if they're on
              opposite ends of the island. That's all this app does: it lets you
              fly through that fingerprint space.</p>

            <h3>The fingerprint is purely structural</h3>
            <p>It is built from three things — and <b>nothing else</b>:</p>
            <div className="help-rows">
              <div className="help-row">
                <span className="hr-k">what it is</span>
                <span>its category, whether it's a chain or independent, and how big the brand is</span>
              </div>
              <div className="help-row">
                <span className="hr-k">what surrounds it</span>
                <span>its micrograph — the world within a short walk: rivals at 400/800&nbsp;m,
                  complementary shops, crowd anchors, distance to the MRT</span>
              </div>
              <div className="help-row">
                <span className="hr-k">where it sits</span>
                <span>the character of its neighbourhood, pressed into the fingerprint during
                  training — the place never stores its location; it <i>learned to encode
                  what kind of context it fits</i></span>
              </div>
            </div>
            <p className="help-note">Deliberately excluded: star ratings, review counts, popularity.
              The geometry describes what a place IS, not how loved it is — and we audited that:
              trying to predict a place's rating from its fingerprint fails (R² = 0.09).</p>

            <h3>How the machine learned it — contrastive training</h3>
            <p>The network was never told what "similar" means. Instead it played a
              matching game, millions of rounds, with three rules:</p>
            <ol className="help-list">
              <li><b>Recognise yourself.</b> Show the network two distorted copies of the
                same place (random details hidden) — it must say "same place". Show it
                two different places — "different".</li>
              <li><b>Recognise your siblings.</b> Two outlets of the same chain — a
                Ya Kun in Yew Tee and a Ya Kun in Admiralty — must land close together.
                That teaches it what "the same kind of place" means across locations.</li>
              <li><b>Agree with your street.</b> A place's own fingerprint must match a
                second network's read of its surroundings — so "fits this kind of
                neighbourhood" is baked into the numbers.</li>
            </ol>
            <p>To make the game hard, every round includes lookalikes — same category,
              completely different context — so the network can't get away with
              "all cafes are alike".</p>

            <h3>How we kept it honest</h3>
            <p>Before training began, we locked a 9-check exam. The model only shipped
              because it passed all nine, including:</p>
            <ul className="help-list">
              <li><b>The hidden-sibling test</b> — we hid 20% of every chain's outlets during
                training; the finished model re-found a sibling for <b>81%</b> of them
                among all 190,591 candidates.</li>
              <li><b>Similar ≠ nearby</b> — correlation between fingerprint distance and
                physical distance is just 0.08. Try the "colour = where it is" toggle.</li>
              <li><b>Stability</b> — retrained from scratch three times, the space comes
                back 98% identical.</li>
            </ul>
            <Src text="plexis-p1 place embedding — two-tower contrastive (SCARF + chain siblings + cross-view), trained on the Digital Atlas; design + 9-check exam locked before training (PLACE_EMBEDDING_DESIGN.md, PLEXIS_P1_REPORT.md)" />
          </div>
        </div>
      )}

      {loaded && (
        <div className={'split' + (center !== null && graph ? '' : ' hide')}>
          <div className="cpane">
            {center !== null && graph && <>
            <svg className="cgraph" viewBox="-900 -760 1800 1520" preserveAspectRatio="xMidYMid meet">
              {graph.links.map((l, k) => {
                const a = graph.nodes[0], b = graph.nodes[k + 1]
                return <line key={k} x1={a.x} y1={a.y} x2={b.x} y2={b.y}
                  stroke="#20b2aa" strokeDasharray="5 4"
                  strokeWidth={1.5 + l.rel * 6}
                  opacity={0.4 + l.rel * 0.55} />
              })}
              {graph.nodes.map((nd, k) => (
                <g key={nd.id} transform={`translate(${nd.x},${nd.y})`}
                  className="cnode" style={{ animationDelay: `${k * 70}ms` }}
                  onClick={() => k > 0 && openConstellation(nd.id)}>
                  <circle r={nd.r * 2.1}
                    fill={k === 0 ? '#fcd34d' : '#0d1f21'}
                    stroke={k === 0 ? '#fcd34d' : catColor(nd.id)} strokeWidth={3} />
                  {k > 0 && <circle r={5} fill={catColor(nd.id)} />}
                  <text y={nd.r * 2.1 + 26} textAnchor="middle" className="nlabel">
                    {arrays.name[nd.id].slice(0, 26)}</text>
                  {k > 0 && <text y={nd.r * 2.1 + 48} textAnchor="middle" className="nsub">
                    {catName(nd.id)} · #{k} of {meta.n.toLocaleString()}</text>}
                </g>
              ))}
            </svg>
            <div className="cfoot">
              <b>{arrays.name[center]}</b> and its 12 functional siblings —
              line thickness = similarity. Click a sibling to walk the graph.
              <Src text="neighbours + similarity from plexis-p1 (64d, contrastive, no rating signals) · kNN-12 cosine" />
            </div>
            <button className="back" onClick={() => { setCenter(null); setGraph(null) }}>← back to the galaxy</button>
            </>}
          </div>
          <div className="gpane">
            <div ref={mapDiv} className="gmap" />
            <div className="gfoot">The same star on the real map — <span className="y">yellow = your place</span>,
              teal = siblings. Function space is NOT geography: siblings span the island.</div>
          </div>
        </div>
      )}
    </div>
  )
}
