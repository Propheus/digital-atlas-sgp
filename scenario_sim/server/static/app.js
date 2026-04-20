// scenario_sim — simplified flow UI

mapboxgl.accessToken = 'MAPBOX_TOKEN_PLACEHOLDER';

const CAT_LABEL = { grocery: 'FairPrice', clinic: 'CHAS Clinic' };
const CAT_LABEL_SHORT = { grocery: 'FairPrice', clinic: 'clinic' };

const state = {
  // data
  catalog: null,
  baselineRows: null,
  byCode: {},
  subzonesGeojson: null,
  world: null,          // /api/world response
  inspectData: null,    // /api/inspect response (current)

  // ui state
  category: 'grocery',
  uiState: 'idle',      // idle | inspect | pick | result
  action: null,         // add | remove | transit
  picks: [],            // list of subzone_codes
  showResult: false,
  resultRows: null,
  resultPayload: null,
};

// ================================================================
// Color helpers
// ================================================================
const SEQ = ['#1a2e2a','#11503b','#097854','#0a9d63','#4bc577','#abe25a','#f4dc3e','#ffae1f','#ef5f1b','#c01b2c'];
const DIV = ['#c01b2c','#e8606a','#f2a38d','#eedab8','#e8e8e8','#c2e6c9','#86c9a0','#41a572','#1c8752','#0f5a38'];

function scaleSeq(v, vmin, vmax) {
  if (v == null || isNaN(v) || vmax === vmin) return '#1a2e2a';
  const t = Math.max(0, Math.min(1, (v - vmin) / (vmax - vmin)));
  return SEQ[Math.min(SEQ.length - 1, Math.floor(t * SEQ.length))];
}
function scaleDiv(v, vabs) {
  if (v == null || isNaN(v)) return '#e8e8e8';
  if (vabs === 0) return '#e8e8e8';
  const t = 0.5 + (v / vabs) * 0.5;
  return DIV[Math.max(0, Math.min(DIV.length - 1, Math.floor(t * DIV.length)))];
}

const fmtInt = n => Number(n).toLocaleString();
const fmt    = (n, d=1) => Number(n).toFixed(d);

// ================================================================
// Boot
// ================================================================
async function boot() {
  const [cat, sz, st, world] = await Promise.all([
    fetch('/api/catalog').then(r => r.json()),
    fetch('/api/subzones.geojson').then(r => r.json()),
    fetch('/api/state').then(r => r.json()),
    fetch('/api/world').then(r => r.json()),
  ]);
  state.catalog = cat;
  state.subzonesGeojson = sz;
  state.baselineRows = st.subzones;
  state.world = world;
  for (const r of st.subzones) state.byCode[r.subzone_code] = r;

  document.getElementById('stats').innerHTML =
    `β<sub>c</sub>=<strong>${fmt(cat.calibrated_beta.clinic, 2)}</strong> · ` +
    `β<sub>g</sub>=<strong>${fmt(cat.calibrated_beta.grocery, 2)}</strong> · ` +
    `click any subzone to inspect`;

  renderWorldStrip();
  attachHandlers();
  updateCategoryLabels();
  initMap();
}

function fmtCompact(n) {
  if (n == null || isNaN(n)) return '—';
  const abs = Math.abs(n);
  if (abs >= 1e6) return (n / 1e6).toFixed(1) + 'M';
  if (abs >= 1e3) return (n / 1e3).toFixed(0) + 'K';
  return Math.round(n).toString();
}

function renderWorldStrip(worldOverride, deltaLine) {
  const w = worldOverride || state.world;
  if (!w) return;
  const cat = state.category;
  const c = w.categories[cat];
  const lbl = c.label;
  const nFacilities = c.facilities;
  const trips = c.monthly_visits;
  const el = document.getElementById('world-strip');
  el.innerHTML =
    `<div class="w-label">World state</div>` +
    `<div class="world-line"><b>${fmtInt(w.n_active)}</b> active subzone agents / ${w.n_subzones}  ·  ` +
    `<b>${fmtCompact(w.total_population)}</b> residents</div>` +
    `<div class="world-line"><b>${fmtInt(nFacilities)}</b> ${lbl} agents  ·  ` +
    `generating <b>${fmtCompact(trips)}</b> trips/mo</div>` +
    (deltaLine ? `<div class="world-line" style="color:#22c55e">${deltaLine}</div>` : '');
}

// ================================================================
// Handlers
// ================================================================
function attachHandlers() {
  // Category pills
  document.querySelectorAll('.pill').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.pill').forEach(p => p.classList.remove('active'));
      btn.classList.add('active');
      state.category = btn.dataset.cat;
      updateCategoryLabels();
      renderWorldStrip();
      if (state.uiState === 'result') renderResult();
      if (state.uiState === 'inspect' && state.inspectData) {
        openInspect(state.inspectData.subzone_code);  // refresh for new category
      }
      renderMap();
    });
  });

  // Action buttons in idle state
  document.querySelectorAll('#state-idle .action').forEach(btn => {
    btn.addEventListener('click', () => {
      state.action = btn.dataset.act;
      state.picks = [];
      setUIState('pick');
    });
  });

  // Quick-action buttons in inspect state (targets the currently inspected subzone)
  document.querySelectorAll('#state-inspect .action').forEach(btn => {
    btn.addEventListener('click', () => {
      if (!state.inspectData) return;
      state.action = btn.dataset.act;
      state.picks = [state.inspectData.subzone_code];
      setUIState('pick');
      refreshPickedFeatureStates();
    });
  });

  document.getElementById('btn-back').addEventListener('click', () => {
    state.inspectData = null;
    setUIState('idle');
    refreshPickedFeatureStates();
  });

  document.getElementById('btn-run').addEventListener('click', runScenario);
  document.getElementById('btn-cancel').addEventListener('click', () => {
    state.action = null;
    state.picks = [];
    setUIState('idle');
  });
  document.getElementById('btn-again').addEventListener('click', () => {
    state.action = null;
    state.picks = [];
    state.resultRows = null;
    state.resultPayload = null;
    state.showResult = false;
    setUIState('idle');
    renderMap();
  });

  document.getElementById('btn-toggle-view').addEventListener('click', () => {
    state.showResult = !state.showResult;
    document.getElementById('badge-mode').textContent = state.showResult ? 'scenario' : 'baseline';
    document.getElementById('btn-toggle-view').textContent =
      state.showResult ? 'show baseline' : 'show scenario';
    renderMap();
  });
}

function updateCategoryLabels() {
  document.querySelectorAll('.cat-lbl').forEach(el => el.textContent = CAT_LABEL[state.category]);
}

function setUIState(s) {
  state.uiState = s;
  for (const id of ['idle', 'inspect', 'pick', 'result']) {
    document.getElementById(`state-${id}`).classList.toggle('hidden', id !== s);
  }

  if (s === 'pick') {
    const instr = {
      add: `Click a subzone on the map to place the new ${CAT_LABEL[state.category]}`,
      remove: `Click a subzone with an existing ${CAT_LABEL[state.category]} to close one`,
      transit: `Click 2+ subzones on the map in order to define a transit corridor`,
    }[state.action];
    document.getElementById('pick-instr').textContent = instr;
    updatePickList();
  }

  if (s === 'idle' || s === 'pick') {
    document.getElementById('map-badge').classList.add('hidden');
  }
}

function updatePickList() {
  const el = document.getElementById('pick-list');
  el.innerHTML = state.picks.map((code, i) => {
    const row = state.byCode[code] || {};
    return `<div class="pick-item">
      <span><span class="nm">${row.subzone_name || code}</span>
      <span class="pa">${row.planning_area || ''}</span></span>
      <span class="rm" data-i="${i}">✕</span>
    </div>`;
  }).join('');
  el.querySelectorAll('.rm').forEach(btn => {
    btn.addEventListener('click', () => {
      const i = +btn.dataset.i;
      state.picks.splice(i, 1);
      updatePickList();
      updateRunButton();
      renderMap();
    });
  });
  updateRunButton();
}

function updateRunButton() {
  const need = state.action === 'transit' ? 2 : 1;
  document.getElementById('btn-run').disabled = state.picks.length < need;
}

// ================================================================
// Inspect a clicked subzone
// ================================================================
async function openInspect(code) {
  try {
    const data = await fetch(`/api/inspect?code=${code}&category=${state.category}&top_k=5`).then(r => r.json());
    if (data.error) { return; }
    state.inspectData = data;
    setUIState('inspect');
    renderInspect();
    refreshPickedFeatureStates();
  } catch (e) { console.error(e); }
}

function renderInspect() {
  const d = state.inspectData;
  if (!d) return;
  const cat = state.category;
  const catLabel = CAT_LABEL[cat];
  const catLabelShort = CAT_LABEL_SHORT[cat];
  const host = document.getElementById('inspect-content');

  // Header + key stats
  let html = `
    <div class="inspect-header">
      <div class="nm">${d.subzone_name}</div>
      <div class="sub">${d.planning_area} · ${fmtInt(d.population)} residents</div>
      <div class="stats">
        <div class="k">${catLabel}</div><div class="v">${d.supply}</div>
        <div class="k">Adequacy</div><div class="v">${fmt(d.adequacy, 0)}/100</div>
        <div class="k">Demand</div><div class="v">${fmtCompact(d.monthly_demand_generated)}/mo</div>
        <div class="k">Served</div><div class="v">${fmtCompact(d.monthly_load_served)}/mo</div>
      </div>
    </div>
  `;

  // Outflows — where residents go
  if (d.included && d.monthly_demand_generated > 0) {
    const local = d.local_capture_share || 0;
    html += `<div class="flow-section">
      <div class="title">What residents are doing</div>
      <div class="lead">
        Generating <b>${fmtCompact(d.monthly_demand_generated)}</b> ${catLabelShort} trips / month.
        ${local > 0.01 ? `<b>${fmt(local*100,0)}%</b> stay inside ${d.subzone_name}; the rest travel out.` : 'Nearly all travel out to other subzones.'}
      </div>
      ${d.top_destinations.map(t => `
        <div class="flow-item ${t.is_local ? 'local' : ''}">
          <span class="pct">${fmt(t.share*100, 0)}%</span>
          <span class="nm">${t.subzone_name}<span class="pa">${t.is_local ? 'local' : t.planning_area}</span></span>
          <span class="meta">${t.supply} store${t.supply===1?'':'s'} · ${fmt(t.travel_min, 0)} min</span>
        </div>
      `).join('')}
    </div>`;
  } else if (!d.included) {
    html += `<div class="flow-section"><div class="lead">This subzone has no active population (low residents, military, water, etc.) — no agent activity.</div></div>`;
  }

  // Inflows — where this subzone's facilities get visitors from
  if (d.top_origins && d.top_origins.length > 0) {
    html += `<div class="flow-section">
      <div class="title">What local facilities are serving</div>
      <div class="lead">
        This subzone's <b>${d.supply}</b> ${catLabel} ${d.supply===1?'is':'are'} receiving
        <b>${fmtCompact(d.monthly_load_served)}</b> visits / month.
      </div>
      ${d.top_origins.map(o => `
        <div class="flow-item ${o.is_local ? 'local' : ''}">
          <span class="pct">${fmt(o.share*100, 0)}%</span>
          <span class="nm">${o.subzone_name}<span class="pa">${o.is_local ? 'local' : o.planning_area}</span></span>
          <span class="meta">${fmtCompact(o.visits)}/mo · ${fmt(o.travel_min, 0)} min</span>
        </div>
      `).join('')}
    </div>`;
  }

  host.innerHTML = html;

  // Toggle remove button availability — only if there's something to remove
  const removeBtn = document.getElementById('inspect-remove');
  if (d.supply > 0) {
    removeBtn.style.display = 'flex';
  } else {
    removeBtn.style.display = 'none';
  }
}

// ================================================================
// Run scenario
// ================================================================
async function runScenario() {
  const mutations = [];
  if (state.action === 'transit') {
    mutations.push({ kind: 'transit_link', corridor: state.picks, corridor_speed_kmh: 40, corridor_stop_min: 1 });
  } else if (state.action === 'add') {
    mutations.push({ kind: 'add_facility', subzone_code: state.picks[0], category: state.category, count: 1 });
  } else if (state.action === 'remove') {
    mutations.push({ kind: 'remove_facility', subzone_code: state.picks[0], category: state.category, count: 1 });
  }

  const btn = document.getElementById('btn-run');
  btn.disabled = true;
  btn.textContent = 'Running…';

  try {
    const res = await fetch('/api/scenario', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ mutations, category: state.category, lam: 0 }),
    });
    const data = await res.json();
    state.resultPayload = data;
    state.resultRows = {};
    for (const r of data.rows) state.resultRows[r.subzone_code] = r;
    state.showResult = true;
    setUIState('result');
    renderResult();
    // Update world strip with post-scenario totals + delta summary
    if (data.world_delta) {
      const wd = data.world_delta.categories[state.category];
      const deltaLine = [];
      if (wd.facilities !== 0) deltaLine.push(`${wd.facilities > 0 ? '+' : ''}${wd.facilities} ${CAT_LABEL[state.category]}`);
      if (Math.abs(wd.mean_A_included) > 0.01) deltaLine.push(`mean access ${wd.mean_A_included > 0 ? '+' : ''}${fmt(wd.mean_A_included, 2)} min`);
      renderWorldStrip(null, deltaLine.length ? 'Δ ' + deltaLine.join(' · ') : null);
    }
    document.getElementById('map-badge').classList.remove('hidden');
    document.getElementById('badge-mode').textContent = 'scenario';
    document.getElementById('btn-toggle-view').textContent = 'show baseline';
    renderMap();
  } catch (e) {
    alert('Error: ' + e.message);
    setUIState('idle');
  } finally {
    btn.textContent = 'Run →';
  }
}

// ================================================================
// Result rendering
// ================================================================
function renderResult() {
  const data = state.resultPayload;
  if (!data) return;
  const cat = state.category;
  const lines = [];

  // MAIN LINE — what the user targeted
  const targetCode = state.picks[0];
  if (state.action === 'transit' && state.picks.length >= 2) {
    // Sum up the biggest movers along the corridor
    let totalDelta = 0;
    let beneficiaries = 0;
    let corrA0 = 0, corrA1 = 0;
    for (const code of state.picks) {
      const row = state.resultRows[code];
      if (!row) continue;
      corrA0 += row.A_base;
      corrA1 += row.A_post;
    }
    for (const row of data.rows) {
      if (row.dA > 0.01) beneficiaries++;
      totalDelta += row.dA;
    }
    const avgCorridor = (corrA1 - corrA0) / state.picks.length;
    lines.push({
      cls: 'main',
      k: 'Transit corridor',
      v: `${state.picks.length} subzones · corridor accessibility ${cmp(avgCorridor, 'min')}` +
         ` · <b>${beneficiaries}</b> subzones see improvement`,
    });
  } else if (state.action === 'add' && targetCode) {
    const row = state.resultRows[targetCode];
    const byCode = state.byCode[targetCode];
    if (row && byCode) {
      lines.push({
        cls: 'main',
        k: `New ${CAT_LABEL[cat]} at ${byCode.subzone_name}`,
        v: `Adequacy <b>${fmt(row.adq_base, 0)}</b> → <b>${fmt(row.adq_post, 0)}</b> ` +
           ` (${cmp(row.dadq, 'pts')}) · ${fmtInt(byCode.population)} residents`,
      });
    }
  } else if (state.action === 'remove' && targetCode) {
    const row = state.resultRows[targetCode];
    const byCode = state.byCode[targetCode];
    if (row && byCode) {
      lines.push({
        cls: 'main',
        k: `Closed ${CAT_LABEL[cat]} at ${byCode.subzone_name}`,
        v: `Adequacy <b>${fmt(row.adq_base, 0)}</b> → <b>${fmt(row.adq_post, 0)}</b> ` +
           `(${cmp(row.dadq, 'pts')})`,
      });
    }
  }

  // NEXT BEST MOVE — top opportunity
  if (data.top_opportunities && data.top_opportunities.length) {
    const top = data.top_opportunities[0];
    lines.push({
      cls: '',
      k: 'Best next move',
      v: `Open a <b>${CAT_LABEL[cat]}</b> at <b>${top.subzone_name}</b> ` +
         `<span class="muted">(${top.planning_area}, ${fmtInt(top.population)})</span>`,
    });
  }

  // WARNING — redundancy, if any
  if (data.top_redundant && data.top_redundant.length) {
    const r = data.top_redundant[0];
    lines.push({
      cls: '',
      k: 'Watch out',
      v: `<b>${r.subzone_name}</b> store may lose <span class="neg">${fmt(r.loss_frac*100, 0)}%</span> ` +
         `of its load`,
    });
  }

  // Only show if zero mutation changes (edge case)
  if (lines.length === 0) {
    lines.push({ cls: '', k: '—', v: '<span class="muted">No measurable change.</span>' });
  }

  document.getElementById('result-lines').innerHTML = lines.map(l => `
    <div class="result-line ${l.cls}">
      <div class="k">${l.k}</div>
      <div class="v">${l.v}</div>
    </div>
  `).join('');
}

function cmp(delta, unit='') {
  if (delta == null || isNaN(delta)) return '—';
  const cls = delta > 0.01 ? 'pos' : (delta < -0.01 ? 'neg' : 'muted');
  const sym = delta > 0 ? '+' : '';
  const u = unit ? ' ' + unit : '';
  return `<span class="${cls}">${sym}${fmt(delta, 1)}${u}</span>`;
}

// ================================================================
// Map
// ================================================================
let map = null;

function initMap() {
  map = new mapboxgl.Map({
    container: 'map',
    style: 'mapbox://styles/mapbox/dark-v11',
    center: [103.82, 1.35],
    zoom: 10.3,
    maxZoom: 14.5,
    minZoom: 9.5,
  });
  map.on('load', () => {
    map.addSource('subzones', { type: 'geojson', data: state.subzonesGeojson, generateId: true });
    map.addLayer({
      id: 'sz-fill', type: 'fill', source: 'subzones',
      paint: { 'fill-color': '#1a2e2a', 'fill-opacity': 0.78 },
    });
    map.addLayer({
      id: 'sz-outline', type: 'line', source: 'subzones',
      paint: { 'line-color': '#0a1719', 'line-width': 0.5 },
    });
    map.addLayer({
      id: 'sz-hover', type: 'line', source: 'subzones',
      paint: {
        'line-color': '#ffc32b',
        'line-width': ['case', ['boolean', ['feature-state', 'hover'], false], 2.5, 0],
      },
    });
    map.addLayer({
      id: 'sz-picked', type: 'line', source: 'subzones',
      paint: {
        'line-color': '#20b2aa',
        'line-width': ['case', ['boolean', ['feature-state', 'picked'], false], 3, 0],
      },
    });

    let hoveredId = null;
    map.on('mousemove', 'sz-fill', e => {
      if (!e.features.length) return;
      if (hoveredId !== null) map.setFeatureState({ source: 'subzones', id: hoveredId }, { hover: false });
      hoveredId = e.features[0].id;
      map.setFeatureState({ source: 'subzones', id: hoveredId }, { hover: true });
      showTooltip(e.point, e.features[0].properties);
    });
    map.on('mouseleave', 'sz-fill', () => {
      if (hoveredId !== null) map.setFeatureState({ source: 'subzones', id: hoveredId }, { hover: false });
      hoveredId = null;
      document.getElementById('tooltip').classList.add('hidden');
    });
    map.on('click', 'sz-fill', e => {
      if (!e.features.length) return;
      const code = e.features[0].properties.subzone_code;

      if (state.uiState === 'pick') {
        // For add/remove we replace; for transit we append (skip dup)
        if (state.action === 'transit') {
          if (state.picks.includes(code)) return;
          state.picks.push(code);
        } else {
          state.picks = [code];
        }
        refreshPickedFeatureStates();
        updatePickList();
        renderMap();
      } else if (state.uiState === 'idle' || state.uiState === 'inspect') {
        openInspect(code);
      }
    });

    renderMap();
  });
}

function refreshPickedFeatureStates() {
  if (!map || !map.getSource('subzones')) return;
  const picked = new Set(state.picks);
  const inspectedCode = state.inspectData && state.uiState === 'inspect' ? state.inspectData.subzone_code : null;
  state.subzonesGeojson.features.forEach((f, i) => {
    const code = f.properties.subzone_code;
    map.setFeatureState(
      { source: 'subzones', id: i },
      { picked: picked.has(code) || code === inspectedCode }
    );
  });
}

function renderMap() {
  if (!map || !map.getSource('subzones')) return;
  const cat = state.category;

  // Decide: are we showing baseline or result-delta?
  const resultMode = state.uiState === 'result' && state.showResult && state.resultRows;

  const rows = state.baselineRows;
  const values = {};
  let vmin = Infinity, vmax = -Infinity;

  if (resultMode) {
    // Delta mode
    for (const r of rows) {
      const pr = state.resultRows[r.subzone_code];
      const v = pr ? pr.dadq : 0;
      values[r.subzone_code] = v;
      if (r.included) {
        if (v < vmin) vmin = v;
        if (v > vmax) vmax = v;
      }
    }
  } else {
    // Baseline adequacy mode
    const key = `adq_${cat}`;
    for (const r of rows) {
      const v = r[key];
      values[r.subzone_code] = v;
      if (r.included && v != null) {
        if (v < vmin) vmin = v;
        if (v > vmax) vmax = v;
      }
    }
  }

  if (!isFinite(vmin)) { vmin = 0; vmax = 100; }

  // Build paint expression
  const matchExpr = ['match', ['get', 'subzone_code']];
  for (const f of state.subzonesGeojson.features) {
    const code = f.properties.subzone_code;
    const v = values[code];
    const color = resultMode
      ? scaleDiv(v, Math.max(Math.abs(vmin), Math.abs(vmax), 0.5))
      : scaleSeq(v, vmin, vmax);
    matchExpr.push(code, color);
  }
  matchExpr.push('#1a2e2a');
  map.setPaintProperty('sz-fill', 'fill-color', matchExpr);

  // Dim excluded
  const opExpr = ['match', ['get', 'subzone_code']];
  for (const r of rows) opExpr.push(r.subzone_code, r.included ? 0.82 : 0.12);
  opExpr.push(0.4);
  map.setPaintProperty('sz-fill', 'fill-opacity', opExpr);

  // Legend
  const title = resultMode
    ? `Δ ${CAT_LABEL_SHORT[cat]} adequacy`
    : `${CAT_LABEL_SHORT[cat]} adequacy (0–100)`;
  document.getElementById('legend-title').textContent = title;
  const scale = resultMode ? DIV : SEQ;
  document.getElementById('legend-scale').innerHTML =
    `<span>${resultMode ? fmt(vmin, 0) : fmt(vmin, 0)}</span>` +
    scale.map(c => `<div class="bar" style="background:${c}"></div>`).join('') +
    `<span>${resultMode ? '+' + fmt(vmax, 0) : fmt(vmax, 0)}</span>`;
}

function showTooltip(point, props) {
  const row = state.byCode[props.subzone_code];
  if (!row) return;
  const cat = state.category;
  const supplyKey = cat === 'clinic' ? 'chas_clinics' : 'fairprice';
  const catLabel = cat === 'clinic' ? 'clinic visits' : 'grocery trips';
  const adq = row[`adq_${cat}`];
  const L = row[`L_${cat}`];
  const pr = state.resultRows ? state.resultRows[props.subzone_code] : null;
  const d = pr ? pr.dadq : null;

  const tip = document.getElementById('tooltip');
  tip.innerHTML = `
    <h3>${row.subzone_name}</h3>
    <div class="row-t"><span class="k">${row.planning_area}</span><span></span></div>
    <div class="row-t"><span class="k">Residents</span><span class="v">${fmtInt(row.population)}</span></div>
    <div class="row-t"><span class="k">${cat === 'clinic' ? 'CHAS clinics' : 'FairPrice'}</span><span class="v">${row.supply[supplyKey]}</span></div>
    <div class="row-t"><span class="k">Adequacy</span><span class="v">${adq != null ? fmt(adq, 0) : '—'}</span></div>
    <div class="row-t"><span class="k">${catLabel} served/mo</span><span class="v">${L != null ? fmtCompact(L) : '—'}</span></div>
    ${d != null ? `<div class="row-t"><span class="k">Δ scenario</span><span class="v ${d>0?'pos':(d<0?'neg':'')}">${d>0?'+':''}${fmt(d,1)}</span></div>` : ''}
    ${state.uiState === 'idle' || state.uiState === 'inspect' ? '<div class="row-t" style="color:#20b2aa;font-size:0.66rem;padding-top:4px">click to inspect agent activity →</div>' : ''}
  `;
  tip.style.left = (point.x + 14) + 'px';
  tip.style.top  = (point.y + 14) + 'px';
  tip.classList.remove('hidden');
}

boot();
