import { useState, useEffect, useCallback, useMemo, useRef } from 'react'
import mapboxgl from 'mapbox-gl'
import 'mapbox-gl/dist/mapbox-gl.css'
import './App.css'

mapboxgl.accessToken = 'MAPBOX_TOKEN_PLACEHOLDER'

const METRICS = {
  density_gap:   { label: 'Supply Gap',    key: 'density_gap',       fmt: v => v != null ? (Number(v) > 0 ? `+${v}` : `${v}`) : '—', stops: [[-50,'#7f1d1d'],[-15,'#dc2626'],[0,'#374151'],[15,'#059669'],[50,'#10b981']] },
  population:    { label: 'Population',    key: 'population',        fmt: v => v ? Number(v).toLocaleString() : '—',     stops: [[0,'#0a2e1f'],[5000,'#134e3a'],[15000,'#15803d'],[30000,'#22c55e'],[60000,'#86efac']] },
  total_places:  { label: 'Places',        key: 'total_places',      fmt: v => v ? Number(v).toLocaleString() : '—',     stops: [[0,'#1a1a0a'],[50,'#3b3a00'],[200,'#a16207'],[500,'#f59e0b'],[1500,'#fde68a']] },
  pop_density:   { label: 'Density',       key: 'pop_density',       fmt: v => v ? `${Math.round(Number(v)).toLocaleString()}/km²` : '—', stops: [[0,'#1a1a2e'],[5000,'#2d1b69'],[15000,'#7c3aed'],[30000,'#c084fc'],[50000,'#f0abfc']] },
  median_hdb_psf:{ label: 'HDB $/psf',    key: 'median_hdb_psf',    fmt: v => v ? `$${Math.round(Number(v))}` : '—',    stops: [[300,'#1e3a5f'],[450,'#1e40af'],[550,'#3b82f6'],[650,'#93c5fd'],[900,'#dbeafe']] },
  category_entropy:{ label: 'Diversity',   key: 'category_entropy',  fmt: v => v ? Number(v).toFixed(2) : '—',           stops: [[0,'#7f1d1d'],[1.0,'#dc2626'],[1.8,'#fca5a5'],[2.3,'#bbf7d0'],[3.0,'#15803d']] },
}

const REGION_COLORS = { 'CENTRAL REGION':'#14b8a6', 'EAST REGION':'#60A5FA', 'NORTH REGION':'#34D399', 'NORTH-EAST REGION':'#F59E0B', 'WEST REGION':'#EC4899' }
const TIER_META = { 1:{label:'Transit',color:'#8B5CF6'}, 2:{label:'Competitors',color:'#EF4444'}, 3:{label:'Complementary',color:'#22C55E'}, 4:{label:'Demand Magnets',color:'#F59E0B'} }

const CAT_COLORS = {
  'Shopping Retail':'#F59E0B','Restaurant':'#EF4444','Business':'#6366F1','Education':'#3B82F6',
  'Beauty Personal Care':'#EC4899','Cafe Coffee':'#F97316','Convenience Daily Needs':'#14B8A6',
  'Hawker Street Food':'#FBBF24','Fitness Recreation':'#22C55E','Health Medical':'#EF4444',
  'Bar Nightlife':'#A855F7','Services':'#6B7280','Transport':'#9CA3AF','Automotive':'#78716C',
  'Fast Food Qsr':'#FB923C','Office Workspace':'#6366F1','Culture Entertainment':'#A78BFA',
  'Hospitality':'#0EA5E9','Bakery Pastry':'#F472B6','General':'#6B7280','Religious':'#C084FC',
  'Civic Government':'#64748B','Ngo':'#94A3B8','Residential':'#475569',
}
const CAT_LABELS = {
  'Automotive':'Auto','Bakery Pastry':'Bakery','Bar Nightlife':'Bars','Beauty Personal Care':'Beauty',
  'Business':'Business','Cafe Coffee':'Cafes','Civic Government':'Civic','Convenience Daily Needs':'Convenience',
  'Culture Entertainment':'Culture','Education':'Education','Fast Food Qsr':'QSR','Fitness Recreation':'Fitness',
  'General':'General','Hawker Street Food':'Hawker','Health Medical':'Health','Hospitality':'Hotels',
  'Ngo':'NGO','Office Workspace':'Office','Religious':'Religious','Residential':'Residential',
  'Restaurant':'Restaurant','Services':'Services','Shopping Retail':'Shopping','Transport':'Transport',
}

function parseProps(raw) {
  const p = { ...raw }
  for (const k of ['counts','top_anchors','demand_drivers']) {
    if (typeof p[k]==='string') try{p[k]=JSON.parse(p[k])}catch{p[k]=k==='counts'?{}:[]}
  }
  if (!p.counts) p.counts = {}
  for (const k of Object.keys(p)) {
    if (typeof p[k]==='string'&&p[k]!==''&&!isNaN(Number(p[k]))&&!['id','name','planning_area','region','subzone_name'].includes(k)) p[k]=Number(p[k])
  }
  return p
}

// DNA Tags — the personality of this subzone
function getDNATags(p) {
  const tags = []
  // Commercial character
  if (p.lu_commercial_pct > 40) tags.push({ label: 'CBD', color: '#6366F1', bg: '#6366F122' })
  else if (p.lu_commercial_pct > 20) tags.push({ label: 'Commercial Hub', color: '#818CF8', bg: '#818CF822' })
  if (p.lu_industrial_pct > 30) tags.push({ label: 'Industrial', color: '#78716C', bg: '#78716C22' })

  // Transit
  if (p.mrt_stations_1km >= 3) tags.push({ label: 'Transit Nexus', color: '#8B5CF6', bg: '#8B5CF622' })
  else if (p.mrt_stations_1km >= 1) tags.push({ label: 'MRT Connected', color: '#A78BFA', bg: '#A78BFA22' })
  else if (p.dist_nearest_mrt > 2000) tags.push({ label: 'Transit Gap', color: '#F87171', bg: '#F8717122' })

  // Food culture
  if (p.hawkers_within_1km >= 5) tags.push({ label: 'Hawker Haven', color: '#FBBF24', bg: '#FBBF2422' })
  if (p.fnb_coverage_ratio > 0.5) tags.push({ label: 'F&B Hub', color: '#F97316', bg: '#F9731622' })

  // Commerce DNA
  if (p.category_entropy > 2.6) tags.push({ label: 'Diverse Economy', color: '#14B8A6', bg: '#14B8A622' })
  if (p.branded_pct > 25) tags.push({ label: 'Brand Central', color: '#EC4899', bg: '#EC489922' })
  if (p.branded_pct < 3 && p.total_places > 100) tags.push({ label: 'Independent', color: '#10B981', bg: '#10B98122' })
  if (p.place_density > 3000) tags.push({ label: 'Ultra Dense', color: '#F97316', bg: '#F9731622' })

  // Supply (band-based)
  const gb = p.gap_band || ''
  if (gb === 'high_oversupply') tags.push({ label: 'Oversaturated', color: '#F87171', bg: '#F8717122' })
  if (gb === 'high_opportunity') tags.push({ label: 'Opportunity Zone', color: '#10B981', bg: '#10B98122' })

  // Living
  if (p.green_ratio > 0.4) tags.push({ label: 'Green Lung', color: '#22C55E', bg: '#22C55E22' })
  if (p.elderly_pct > 20) tags.push({ label: 'Silver Zone', color: '#9CA3AF', bg: '#9CA3AF22' })
  if (p.median_hdb_psf > 750) tags.push({ label: 'Premium Estate', color: '#A78BFA', bg: '#A78BFA22' })
  if (p.population === 0 && p.total_places > 100) tags.push({ label: 'Work-Only Zone', color: '#6366F1', bg: '#6366F122' })

  return tags.slice(0, 6)
}

const DETAIL_SECTIONS = [
  { title: 'Demographics & Housing', items: [
    ['area_km2','Area',v=>`${v} km²`],['pop_density','Density',v=>`${Math.round(v).toLocaleString()}/km²`],
    ['elderly_pct','Elderly',v=>`${v}%`],['male_pct','Male',v=>`${v}%`],
    ['median_hdb_psf','HDB $/psf',v=>`$${Math.round(v)}`],['hdb_price_yoy','HDB YoY',v=>`${v}%`],
    ['condominiums_and_other_apartments_pct','Condo',v=>`${v}%`],['landed_properties_pct','Landed',v=>`${v}%`],
  ]},
  { title: 'Land Use', items: [
    ['lu_residential_pct','Residential',v=>`${v}%`],['lu_commercial_pct','Commercial',v=>`${v}%`],
    ['lu_industrial_pct','Industrial',v=>`${v}%`],['lu_open_space_pct','Open Space',v=>`${v}%`],
    ['green_ratio','Green Ratio',v=>v.toFixed(3)],['avg_gpr','Plot Ratio',v=>v.toFixed(2)],
  ]},
  { title: 'Transport & Access', items: [
    ['dist_nearest_mrt','MRT',v=>`${v}m`],['mrt_stations_1km','MRT ≤1km',v=>v],
    ['bus_stop_count_1km','Bus Stops',v=>v],['dist_nearest_hawker','Hawker',v=>`${v}m`],
    ['hawkers_within_1km','Hawkers ≤1km',v=>v],['dist_nearest_park','Park',v=>`${v}m`],
    ['road_density','Road Density',v=>v.toFixed(1)],
  ]},
  { title: 'Commerce & Quality', items: [
    ['place_density','Place/km²',v=>Math.round(v).toLocaleString()],['branded_count','Branded',v=>Math.round(v)],
    ['unique_brand_count','Brands',v=>Math.round(v)],['avg_rating','Rating',v=>`★ ${v.toFixed(1)}`],
    ['total_reviews','Reviews',v=>Math.round(v).toLocaleString()],['fnb_coverage_ratio','F&B Coverage',v=>v.toFixed(2)],
    ['sfa_eating_count','SFA Eateries',v=>v],
  ]},
  { title: 'Personas (NVIDIA Nemotron)', items: [
    ['persona_count','Personas',v=>v.toLocaleString()],['p_median_age','Median Age',v=>v],
    ['p_pct_university','University',v=>`${v}%`],['p_pct_professional','Professional',v=>`${v}%`],
    ['p_pct_finance','Finance',v=>`${v}%`],['p_pct_tech','Tech',v=>`${v}%`],
    ['p_hobby_food','Food Interest',v=>`${v}%`],['p_affluence','Affluence',v=>v.toFixed(3)],
  ]},
]

function DetailSection({ title, items, data }) {
  const [open, setOpen] = useState(false)
  const rows = items.map(([k,l,f])=>{const v=data[k];if(v==null||v===0)return null;try{return{label:l,val:String(f(v))}}catch{return null}}).filter(Boolean)
  if (!rows.length) return null
  return (
    <div className="dsec">
      <button className="dsec-h" onClick={()=>setOpen(!open)}>
        <span>{title}</span>
        <span className="dsec-m">{rows.length} <span className={`ch ${open?'open':''}`}>&#9656;</span></span>
      </button>
      {open && <div className="dsec-b">{rows.map(r=><div key={r.label} className="dr"><span className="dl">{r.label}</span><span className="dv">{r.val}</span></div>)}</div>}
    </div>
  )
}

function AnchorGroup({ tier, label, color, anchors }) {
  const [showAll, setShowAll] = useState(false)
  const visible = showAll ? anchors : anchors.slice(0, 4)
  return (
    <div className="ag">
      <div className="ag-h"><span className="adot" style={{background:color}}/> T{tier} {label} <span className="ag-c">{anchors.length}</span></div>
      {visible.map((a,i)=>(
        <div key={i} className="ai">
          <span className="adot-s" style={{background:color}}/>
          <span className="ai-n">{a[0]}</span>
          {a[2] && <span className="ai-t">{a[2]}</span>}
          <div className="ai-bar"><div className="ai-fill" style={{width:`${Math.min(a[3]*120,100)}%`,background:color}}/></div>
        </div>
      ))}
      {anchors.length>4&&<button className="more" onClick={()=>setShowAll(!showAll)}>{showAll?'Less':`+${anchors.length-4} more`}</button>}
    </div>
  )
}

function SubzonePanel({ sz, onClose }) {
  if (!sz) return null
  const p = sz, counts = p.counts||{}, regionColor = REGION_COLORS[p.region]||'#666'
  const [tab, setTab] = useState('overview')
  const tags = getDNATags(p)
  const drivers = (Array.isArray(p.demand_drivers)?p.demand_drivers:[]).filter(d=>d[0])
  const anchors = (Array.isArray(p.top_anchors)?p.top_anchors:[]).filter(a=>a[0])
  const anchorGroups = {}; anchors.forEach(a=>{const t=a[1];if(!anchorGroups[t])anchorGroups[t]=[];anchorGroups[t].push(a)})
  const topCats = Object.entries(counts).filter(([,v])=>v>0).sort((a,b)=>b[1]-a[1]).slice(0,8)
  const band = p.gap_band || 'balanced'
  const bandMeta = {
    high_opportunity: { color: '#10B981', label: 'High Opportunity' },
    moderate_opportunity: { color: '#6EE7B7', label: 'Opportunity' },
    balanced: { color: 'var(--text3)', label: 'Balanced' },
    moderate_oversupply: { color: '#FCA5A5', label: 'Saturated' },
    high_oversupply: { color: '#F87171', label: 'Oversaturated' },
    not_applicable: { color: '#374151', label: 'N/A' },
  }
  const gapColor = (bandMeta[band] || bandMeta.balanced).color
  const gapLabel = (bandMeta[band] || bandMeta.balanced).label

  return (
    <div className="panel">
      <button className="panel-close" onClick={onClose}>&times;</button>
      {/* Header */}
      <div className="ph">
        <div className="ph-top">
          <span className="ph-code">{p.id}</span>
          <span className="ph-region" style={{color:regionColor,borderColor:`${regionColor}66`,background:`${regionColor}15`}}>{p.region?.replace(' REGION','')}</span>
        </div>
        <h2 className="ph-name">{p.subzone_name||p.name}</h2>
        <span className="ph-pa">{p.planning_area}</span>
        {tags.length>0&&<div className="dna-tags">{tags.map(t=><span key={t.label} className="dna-tag" style={{color:t.color,borderColor:`${t.color}55`,background:t.bg}}>{t.label}</span>)}</div>}
      </div>

      {/* Hero */}
      <div className="hero">
        <div className="hc"><div className="hv">{p.population?p.population.toLocaleString():'—'}</div><div className="hl">Population</div></div>
        <div className="hc"><div className="hv">{p.total_places?p.total_places.toLocaleString():'0'}</div><div className="hl">Places</div></div>
        <div className="hc">
          <div className="hv" style={{color:gapColor}}>{p.density_gap!=null?(p.density_gap>0?`+${p.density_gap}`:p.density_gap):'—'}</div>
          <div className="hl" style={{color:gapColor}}>{gapLabel}</div>
        </div>
        <div className="hc"><div className="hv">{p.category_entropy?.toFixed(2)??'—'}</div><div className="hl">Diversity</div></div>
      </div>

      {/* Tabs */}
      <div className="ptabs">
        <button className={`pt ${tab==='overview'?'active':''}`} onClick={()=>setTab('overview')}>Overview</button>
        <button className={`pt ${tab==='anchors'?'active':''}`} onClick={()=>setTab('anchors')}>Anchors{anchors.length>0?` (${anchors.length})`:''}</button>
        <button className={`pt ${tab==='data'?'active':''}`} onClick={()=>setTab('data')}>All Data</button>
      </div>

      <div className="ptab-body">
        {tab==='overview'&&<>
          {/* Demand Drivers */}
          {drivers.length>0&&<div className="sec">
            <div className="st">Demand Drivers</div>
            <div className="chips">{drivers.slice(0,6).map(([dt,c],i)=>{
              const icons={Gym:'💪',Hotel:'🏨',Hospital:'🏥','Shopping Mall':'🛍️',University:'🎓',School:'🏫',Park:'🌳'}
              return <span key={i} className="chip">{icons[dt]||'📍'} {dt} <b>{Number(c).toLocaleString()}</b></span>
            })}</div>
          </div>}

          {/* Top Categories with colored bars */}
          {topCats.length>0&&<div className="sec">
            <div className="st">Top Categories</div>
            <div className="cbars">{topCats.map(([cat,count])=>{
              const max=topCats[0][1], color=CAT_COLORS[cat]||'#20B2AA'
              return <div key={cat} className="cbar">
                <span className="cbar-l">{CAT_LABELS[cat]||cat}</span>
                <div className="cbar-t"><div className="cbar-f anim-bar" style={{width:`${(count/max)*100}%`,background:color}}/></div>
                <span className="cbar-v" style={{color}}>{count}</span>
              </div>
            })}</div>
          </div>}

          {/* Context Vector */}
          {p.micro_count>0&&<div className="sec">
            <div className="st">Context Vector <span className="st-sub">{Number(p.micro_count).toLocaleString()} micrographs</span></div>
            <div className="cvs">{[['Transit',p.cv_transit,'#8B5CF6'],['Competitor',p.cv_competitor,'#EF4444'],['Complementary',p.cv_complementary,'#22C55E'],['Demand',p.cv_demand,'#F59E0B']].map(([l,v,c])=>(
              <div key={l} className="cvr"><span className="cvl">{l}</span><div className="cvt"><div className="cvf anim-bar" style={{width:`${Math.min((v||0)*100,100)}%`,background:c}}/></div><span className="cvp" style={{color:c}}>{v?`${(v*100).toFixed(0)}%`:'—'}</span></div>
            ))}</div>
          </div>}

          {/* Detail sections (collapsed) */}
          {DETAIL_SECTIONS.map(s=><DetailSection key={s.title} title={s.title} items={s.items} data={p}/>)}
        </>}

        {tab==='anchors'&&<>
          {[1,2,3,4].map(t=>{const g=anchorGroups[t];if(!g?.length)return null;const m=TIER_META[t];return<AnchorGroup key={t} tier={t} label={m.label} color={m.color} anchors={g}/>})}
          {anchors.length===0&&<div className="empty">No anchor data</div>}
        </>}

        {tab==='data'&&<div className="data-tab">
          {Object.entries(counts).filter(([,v])=>v>0).length>0&&<div className="sec">
            <div className="st">All Place Counts ({Object.entries(counts).filter(([,v])=>v>0).length} categories)</div>
            {Object.entries(counts).filter(([,v])=>v>0).sort((a,b)=>b[1]-a[1]).map(([k,v])=><div key={k} className="dr"><span className="dl">{CAT_LABELS[k]||k}</span><span className="dv">{v}</span></div>)}
          </div>}
          {DETAIL_SECTIONS.map(sec=>{
            const rows=sec.items.map(([k,l,f])=>{const v=p[k];if(v==null||v===0)return null;try{return{label:l,val:String(f(v))}}catch{return null}}).filter(Boolean)
            if(!rows.length)return null
            return <div key={sec.title} className="sec"><div className="st">{sec.title}</div>{rows.map(r=><div key={r.label} className="dr"><span className="dl">{r.label}</span><span className="dv">{r.val}</span></div>)}</div>
          })}
        </div>}
      </div>
    </div>
  )
}

function PlanningAreaHighlights({ features, paName }) {
  if (!features.length||!paName) return null
  const props = features.map(f=>f.properties)
  const totalPop = props.reduce((s,p)=>s+(Number(p.population)||0),0)
  const totalPlaces = props.reduce((s,p)=>s+(Number(p.total_places)||0),0)
  return (
    <div className="area-hl">
      <h3 className="area-hl-name">{paName}</h3>
      <span className="area-hl-sub">{features.length} subzones &middot; {totalPop.toLocaleString()} pop &middot; {totalPlaces.toLocaleString()} places</span>
    </div>
  )
}

function getCentroid(f){const c=[];function ex(a){if(typeof a[0]==='number'){c.push(a);return}a.forEach(ex)}ex(f.geometry.coordinates);if(!c.length)return null;return[c.reduce((s,x)=>s+x[0],0)/c.length,c.reduce((s,x)=>s+x[1],0)/c.length]}

export default function App() {
  const mapContainer=useRef(null),mapRef=useRef(null),popupRef=useRef(null),metricRef=useRef('density_gap')
  const [geojson,setGeojson]=useState(null),[metric,setMetric]=useState('density_gap'),[selected,setSelected]=useState(null)
  const [search,setSearch]=useState(''),[paFilter,setPaFilter]=useState(null),[regionFilter,setRegionFilter]=useState(null)
  const [showAllPA,setShowAllPA]=useState(false),[mapReady,setMapReady]=useState(false),[view,setView]=useState('map')

  useEffect(()=>{metricRef.current=metric},[metric])
  useEffect(()=>{fetch('/subzones.geojson?v=4').then(r=>r.json()).then(d=>{console.log(`Loaded ${d.features.length}`);setGeojson(d)}).catch(e=>console.error(e))},[])

  const{planningAreas,regions}=useMemo(()=>{if(!geojson)return{planningAreas:[],regions:[]};const m={},r=new Set();geojson.features.forEach(f=>{if(f.properties.planning_area)m[f.properties.planning_area]=(m[f.properties.planning_area]||0)+1;if(f.properties.region)r.add(f.properties.region)});return{planningAreas:Object.entries(m).sort((a,b)=>b[1]-a[1]).map(([n,c])=>({name:n,count:c})),regions:[...r].sort()}},[geojson])

  const filterExpr=useMemo(()=>{const c=[];if(paFilter)c.push(['==',['get','planning_area'],paFilter]);if(regionFilter)c.push(['==',['get','region'],regionFilter]);if(search){const s=search.toLowerCase();c.push(['any',['in',s,['downcase',['coalesce',['get','name'],'']]],['in',s,['downcase',['coalesce',['get','subzone_name'],'']]],['in',s,['downcase',['coalesce',['get','planning_area'],'']]]]);} return c.length===0?null:c.length===1?c[0]:['all',...c]},[paFilter,regionFilter,search])

  const filteredFeatures=useMemo(()=>{if(!geojson)return[];return geojson.features.filter(f=>{const p=f.properties;if(paFilter&&p.planning_area!==paFilter)return false;if(regionFilter&&p.region!==regionFilter)return false;if(search){const s=search.toLowerCase();if(!((p.name||'').toLowerCase().includes(s)||(p.subzone_name||'').toLowerCase().includes(s)||(p.planning_area||'').toLowerCase().includes(s)))return false}return true})},[geojson,paFilter,regionFilter,search])

  const stats=useMemo(()=>{if(!filteredFeatures.length)return null;return{z:filteredFeatures.length,p:filteredFeatures.reduce((s,f)=>s+(Number(f.properties.population)||0),0),pl:filteredFeatures.reduce((s,f)=>s+(Number(f.properties.total_places)||0),0)}},[filteredFeatures])

  const sortedZones=useMemo(()=>{const m=METRICS[metric];return[...filteredFeatures].sort((a,b)=>(Number(b.properties[m.key])||0)-(Number(a.properties[m.key])||0))},[filteredFeatures,metric])

  useEffect(()=>{if(!mapContainer.current||mapRef.current)return;const map=new mapboxgl.Map({container:mapContainer.current,style:'mapbox://styles/mapbox/dark-v11',center:[103.8198,1.3521],zoom:11.2,attributionControl:false});map.addControl(new mapboxgl.NavigationControl(),'bottom-right');popupRef.current=new mapboxgl.Popup({closeButton:false,closeOnClick:false,className:'sz-popup',offset:10});map.on('load',()=>setMapReady(true));mapRef.current=map;return()=>{map.remove();mapRef.current=null}},[])

  useEffect(()=>{const map=mapRef.current;if(!mapReady||!geojson||!map||map.getSource('sz'))return;map.addSource('sz',{type:'geojson',data:geojson});const m=METRICS[metric];map.addLayer({id:'sz-fill',type:'fill',source:'sz',paint:{'fill-color':['interpolate',['linear'],['coalesce',['to-number',['get',m.key]],0],...m.stops.flat()],'fill-opacity':0.75}});map.addLayer({id:'sz-line',type:'line',source:'sz',paint:{'line-color':'rgba(32,178,170,0.3)','line-width':0.5}});map.addLayer({id:'sz-hl',type:'line',source:'sz',paint:{'line-color':'#fff','line-width':2.5,'line-opacity':1},filter:['==',['get','id'],'__']});
    map.on('mousemove','sz-fill',e=>{map.getCanvas().style.cursor='pointer';const f=e.features?.[0];if(f&&popupRef.current){const p=f.properties,cm=METRICS[metricRef.current],v=typeof p[cm.key]==='string'?parseFloat(p[cm.key]):p[cm.key];popupRef.current.setLngLat(e.lngLat).setHTML(`<b>${p.subzone_name||p.name}</b><br/>${cm.label}: ${cm.fmt(v)}`).addTo(map)}});
    map.on('mouseleave','sz-fill',()=>{map.getCanvas().style.cursor='';popupRef.current?.remove()});
    map.on('click','sz-fill',e=>{if(e.features?.[0])setSelected(parseProps(e.features[0].properties))})
  },[mapReady,geojson])

  useEffect(()=>{const map=mapRef.current;if(!mapReady||!map?.getLayer('sz-fill'))return;const m=METRICS[metric];map.setPaintProperty('sz-fill','fill-color',['interpolate',['linear'],['coalesce',['to-number',['get',m.key]],0],...m.stops.flat()])},[metric,mapReady])
  useEffect(()=>{const map=mapRef.current;if(!mapReady||!map?.getLayer('sz-fill'))return;map.setFilter('sz-fill',filterExpr);map.setFilter('sz-line',filterExpr)},[filterExpr,mapReady])
  useEffect(()=>{const map=mapRef.current;if(!mapReady||!map?.getLayer('sz-hl'))return;map.setFilter('sz-hl',selected?['==',['get','id'],selected.id]:['==',['get','id'],'__'])},[selected,mapReady])
  useEffect(()=>{const map=mapRef.current;if(!mapReady||!geojson||!map)return;if(paFilter||regionFilter||search){if(filteredFeatures.length){const b=new mapboxgl.LngLatBounds();filteredFeatures.forEach(f=>{const c=getCentroid(f);if(c)b.extend(c)});if(!b.isEmpty())map.fitBounds(b,{padding:60,duration:800})}}else map.flyTo({center:[103.8198,1.3521],zoom:11.2,duration:800})},[paFilter,regionFilter,search,filteredFeatures,mapReady,geojson])

  const selectFromList=useCallback(f=>{setSelected(parseProps(f.properties));const c=getCentroid(f);if(c)mapRef.current?.flyTo({center:c,zoom:14,duration:600})},[])

  return (
    <div className="app">
      <div className="view-tabs">
        {[['map','Map'],['features','Features'],['categories','Categories'],['satellite','Satellite'],['anomalies','Anomalies'],['nightlight','Night Light']].map(([k,l])=>(
          <button key={k} className={`vt ${view===k?'active':''}`} onClick={()=>setView(k)}>{l}</button>
        ))}
      </div>

      {view==='map'?<>
        <div className="sidebar">
          <div className="sb-header">
            <div className="logo-row">
              <img src="/propheus-logo.svg" alt="Propheus" className="logo" />
            </div>
            <h1 className="sb-title">SGP <span className="accent">Explorer</span></h1>
            <p className="sb-sub">332 Subzones &middot; 174,713 Places</p>
          </div>
          <input className="search" type="text" placeholder="Search subzones..." value={search} onChange={e=>setSearch(e.target.value)}/>

          <div className="fs"><div className="fl">Region</div>
            <div className="zf">
              <button className={`zb ${regionFilter===null?'active':''}`} onClick={()=>setRegionFilter(null)}>All</button>
              {regions.map(r=><button key={r} className={`zb ${regionFilter===r?'active':''}`} style={regionFilter===r?{background:`${REGION_COLORS[r]}22`,color:REGION_COLORS[r],borderColor:REGION_COLORS[r]}:{}} onClick={()=>setRegionFilter(regionFilter===r?null:r)}>{r.replace(' REGION','')}</button>)}
            </div>
          </div>

          <div className="fs"><div className="fl">Planning Area</div>
            <div className="af">
              {planningAreas.slice(0,showAllPA?999:10).map(a=>(
                <button key={a.name} className={`ab ${paFilter===a.name?'active':''}`} onClick={()=>setPaFilter(paFilter===a.name?null:a.name)}>{a.name} <span className="ac">{a.count}</span></button>
              ))}
              {planningAreas.length>10&&!showAllPA&&<button className="ab" onClick={()=>setShowAllPA(true)}>+{planningAreas.length-10} more</button>}
            </div>
          </div>

          <div className="ms">
            {Object.entries(METRICS).map(([k,v])=><button key={k} className={`mb ${metric===k?'active':''}`} onClick={()=>setMetric(k)}>{v.label}</button>)}
          </div>

          {stats&&<div className="ss"><span><b className="ss-num">{stats.z}</b> subzones</span><span><b className="ss-num">{stats.p.toLocaleString()}</b> pop</span><span><b className="ss-num">{stats.pl.toLocaleString()}</b> places</span></div>}

          <div className="wl">{sortedZones.slice(0,100).map(w=>{const p=w.properties,m=METRICS[metric],val=typeof p[m.key]==='string'?parseFloat(p[m.key]):p[m.key]
            const rc=REGION_COLORS[p.region]||'#666'
            const gb=p.gap_band||''
            const gapC=gb.includes('opportunity')?'#10B981':gb.includes('oversupply')?'#F87171':'var(--border)'
            const metricColor=metric==='density_gap'?(val>0?'#10B981':val<0?'#F87171':'var(--text3)'):metric==='category_entropy'?(val>2.3?'#10B981':val<1.2?'#F87171':'var(--accent)'):metric==='median_hdb_psf'?(val>650?'#A78BFA':val>500?'#60A5FA':'var(--accent)'):'var(--accent)'
            return <div key={p.id} className={`wr ${selected?.id===p.id?'sel':''}`} style={{borderLeft:`3px solid ${selected?.id===p.id?'var(--accent)':gapC}`}} onClick={()=>selectFromList(w)}>
              <div className="wr-l">
                <div className="wr-top"><span className="wr-dot" style={{background:rc}}/><span className="wr-n">{p.subzone_name||p.name}</span></div>
                <span className="wr-pa">{p.planning_area} &middot; {Number(p.total_places||0).toLocaleString()} places</span>
              </div>
              <span className="wr-v" style={{color:metricColor}}>{m.fmt(val)}</span>
            </div>
          })}</div>
        </div>

        <div className="map-area">
          <div ref={mapContainer} className="map"/>
          <div className="legend"><div className="lg-t">{METRICS[metric].label}</div><div className="lg-bar">{METRICS[metric].stops.map(([,c],i)=><div key={i} style={{background:c,flex:1}}/>)}</div><div className="lg-l"><span>Low</span><span>High</span></div></div>
          {paFilter&&<PlanningAreaHighlights features={filteredFeatures} paName={paFilter}/>}
          <SubzonePanel sz={selected} onClose={()=>setSelected(null)}/>
        </div>
      </>:(
        <div className="report-view"><iframe src={view==='features'?'/feature_inventory.html':view==='categories'?'/category_intelligence.html':view==='satellite'?'/satellite_insights.html':view==='anomalies'?'/deep_anomalies.html':'/night_light_growth.html'} className="report-iframe" title={view}/></div>
      )}
    </div>
  )
}
