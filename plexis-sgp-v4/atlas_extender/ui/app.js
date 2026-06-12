// Atlas Extender UI — SSE consumer + stage rendering

const STAGE_LABELS = {
  init:           "🌱 Initialize",
  reasoner:       "1. 🧠 Reasoner",
  synthesizer_r1: "2. 💡 Synthesizer R1",
  debater_r1:     "3. ⚔️ Debater R1",
  refiner_r2:     "4. 🔧 Refiner R2",
  debater_r2:     "5. ⚔️ Debater R2 (deeper)",
  expert_panel:   "6. 👥 Expert Panel",
  decision:       "7. ⚖️ Decision",
  builder:        "8. 🏗️ Builder",
  reporter:       "9. 📋 Reporter",
  done:           "✅ Done",
  error:          "❌ Error",
};

const stageOrder = Object.keys(STAGE_LABELS);
let currentRunId = null;
let runEvents = {};

const useCaseEl = document.getElementById("useCase");
const runBtn = document.getElementById("runBtn");
const contentEl = document.getElementById("content");
const headerTitle = document.getElementById("header-title");
const headerMeta = document.getElementById("header-meta");
const runsList = document.getElementById("runsList");

// Examples
document.querySelectorAll(".example").forEach(el => {
  el.addEventListener("click", () => useCaseEl.value = el.dataset.uc);
});

runBtn.addEventListener("click", async () => {
  const uc = useCaseEl.value.trim();
  if (!uc) return;
  runBtn.disabled = true;
  runBtn.textContent = "Starting...";
  try {
    const r = await fetch("/run", {method: "POST", headers: {"Content-Type": "application/json"},
                                   body: JSON.stringify({use_case: uc})});
    const d = await r.json();
    currentRunId = d.run_id;
    runEvents[currentRunId] = [];
    initView(uc);
    streamEvents(currentRunId);
    refreshRunsList();
  } finally {
    runBtn.disabled = false;
    runBtn.textContent = "Run pipeline";
  }
});

function initView(uc) {
  headerTitle.textContent = uc;
  headerMeta.textContent = `Run ${currentRunId} · in progress`;
  contentEl.innerHTML = stageOrder.map(s => `
    <div class="stage" id="stage-${s}">
      <div class="stage-header" onclick="toggleStage('${s}')">
        <span class="dot" id="dot-${s}"></span>
        <span class="stage-name">${STAGE_LABELS[s]}</span>
        <span class="stage-time" id="time-${s}"></span>
      </div>
      <div class="stage-body" id="body-${s}">
        <em>waiting...</em>
      </div>
    </div>
  `).join("");
}

function toggleStage(s) {
  document.getElementById(`stage-${s}`).classList.toggle("expanded");
}

function streamEvents(run_id) {
  const es = new EventSource(`/stream/${run_id}`);
  es.onmessage = (msg) => {
    const evt = JSON.parse(msg.data);
    runEvents[run_id].push(evt);
    handleEvent(evt);
    if (evt.stage === "done" || evt.stage === "error") es.close();
  };
  es.onerror = () => es.close();
}

function handleEvent(evt) {
  const s = evt.stage;
  const dot = document.getElementById(`dot-${s}`);
  const body = document.getElementById(`body-${s}`);
  const time = document.getElementById(`time-${s}`);
  if (!dot || !body) {
    if (s === "done") {
      headerMeta.textContent = `Run ${currentRunId} · ${evt.payload?.elapsed_s}s · ${evt.payload?.output_dir || ""}`;
    }
    return;
  }
  if (evt.status === "start") {
    dot.className = "dot running";
    body.innerHTML = "<em>running...</em>";
  } else if (evt.status === "done" || evt.status === "ok") {
    dot.className = "dot done";
    time.textContent = `${evt.elapsed_s}s`;
    body.innerHTML = renderStageBody(s, evt.payload);
    document.getElementById(`stage-${s}`).classList.add("expanded");
  } else if (evt.status === "fail") {
    dot.className = "dot error";
    body.innerHTML = `<pre style="color:#f85149">${evt.payload?.error || ""}\n\n${evt.payload?.trace || ""}</pre>`;
    document.getElementById(`stage-${s}`).classList.add("expanded");
  }
}

function renderStageBody(s, p) {
  if (!p) return "";
  if (s === "init") {
    return `<div class="kpi-l">Use case</div><div style="margin-top:4px;color:#c9d1d9">${p.use_case}</div>
            <div style="margin-top:8px;color:#8b949e;font-size:12px">
              ${p.base_version} → <strong style="color:#79c0ff">${p.new_version}</strong> · ${p.output_dir}</div>`;
  }
  if (s === "reasoner") {
    return `
      <div class="summary">
        <div class="kpi"><div class="kpi-l">Target</div><div style="font-size:13px;margin-top:4px">${p.target_variable || ""}</div></div>
        <div class="kpi"><div class="kpi-l">Scale</div><div class="kpi-v" style="font-size:18px">${p.scale || ""}</div></div>
        <div class="kpi"><div class="kpi-l">Decision type</div><div style="font-size:13px;margin-top:4px">${p.decision_type || ""}</div></div>
        <div class="kpi"><div class="kpi-l">Stakeholder</div><div style="font-size:11px;margin-top:4px">${p.stakeholder || ""}</div></div>
      </div>
      <div style="margin-top:10px"><strong>Key concepts (${(p.key_concepts||[]).length}):</strong></div>
      <ul style="margin-top:6px;padding-left:20px;font-size:13px;color:#c9d1d9">
        ${(p.key_concepts||[]).map(c => `<li>${c}</li>`).join("")}
      </ul>
      ${p.constraints && p.constraints.length ? `<div style="margin-top:8px"><strong>Constraints:</strong> ${p.constraints.join(', ')}</div>` : ""}
      <div style="margin-top:8px;color:#8b949e;font-size:12px"><em>${p.evaluation_metric || ''}</em></div>
    `;
  }
  if (s === "synthesizer_r1") {
    return `<div class="summary">
              <div class="kpi"><div class="kpi-v">${p.n}</div><div class="kpi-l">proposed</div></div>
            </div>
            ${(p.proposals||[]).map(prop => renderFeatureCard(prop)).join("")}`;
  }
  if (s === "debater_r1") {
    return `<div class="summary">
              <div class="kpi"><div class="kpi-v">${p.n}</div><div class="kpi-l">critiques</div></div>
            </div>
            ${(p.critiques||[]).map(renderCritique).join("")}`;
  }
  if (s === "refiner_r2") {
    return `<div class="summary">
              <div class="kpi"><div class="kpi-v">${p.n_refined}</div><div class="kpi-l">refined</div></div>
              <div class="kpi"><div class="kpi-v">${p.n_new}</div><div class="kpi-l">new</div></div>
              <div class="kpi"><div class="kpi-v">${p.n_total}</div><div class="kpi-l">total in R2</div></div>
            </div>
            <h4 style="margin-top:10px;font-size:13px;color:#79c0ff">Refinements:</h4>
            ${(p.refinements||[]).map(renderRefinement).join("")}
            <h4 style="margin-top:10px;font-size:13px;color:#79c0ff">New (gaps from debate):</h4>
            ${(p.new_proposals||[]).map(renderFeatureCard).join("")}`;
  }
  if (s === "debater_r2") {
    return `<div class="summary">
              <div class="kpi"><div class="kpi-v">${p.n}</div><div class="kpi-l">critiques R2</div></div>
            </div>
            ${p.overall_note ? `<div style="background:#0d1117;border-left:3px solid #ffc107;padding:10px;margin-bottom:10px;font-size:13px;font-style:italic">${p.overall_note}</div>` : ""}
            ${(p.critiques||[]).map(renderCritiqueR2).join("")}`;
  }
  if (s === "expert_panel") {
    const personas = ["revenue_manager", "data_scientist", "domain_engineer"];
    return `<div class="persona-grid">
      ${personas.map(k => {
        const data = p[k] || {};
        const verdicts = data.verdicts || [];
        return `<div class="persona">
          <div class="persona-name">${k.replace("_", " ")}</div>
          ${verdicts.map(v => `
            <div class="verdict-row ${v.verdict}">
              <strong>${v.feature}</strong> · ${v.verdict} · conf ${v.confidence}
              <div style="font-size:10px;margin-top:2px">${v.reasoning || ""}</div>
            </div>
          `).join("")}
        </div>`;
      }).join("")}
    </div>`;
  }
  if (s === "decision") {
    return `<div class="summary">
              <div class="kpi"><div class="kpi-v" style="color:#28a745">${p.keep}</div><div class="kpi-l">KEEP</div></div>
              <div class="kpi"><div class="kpi-v" style="color:#ffc107">${p.revise}</div><div class="kpi-l">REVISE</div></div>
              <div class="kpi"><div class="kpi-v" style="color:#dc3545">${p.reject}</div><div class="kpi-l">REJECT</div></div>
            </div>
            ${(p.decisions||[]).map(d => renderDecision(d)).join("")}`;
  }
  if (s === "builder") {
    return `<div class="summary">
              <div class="kpi"><div class="kpi-v" style="color:#28a745">${(p.added||[]).length}</div><div class="kpi-l">added</div></div>
              <div class="kpi"><div class="kpi-v" style="color:#dc3545">${(p.failed||[]).length}</div><div class="kpi-l">failed</div></div>
              <div class="kpi"><div class="kpi-v">${(p.shape||[])[0] || "?"}×${(p.shape||[])[1] || "?"}</div><div class="kpi-l">shape</div></div>
            </div>
            <h4 style="margin-top:10px;font-size:13px;color:#7ce38b">Added:</h4>
            <table style="width:100%;font-size:12px;border-collapse:collapse">
              <tr style="background:#21262d"><th style="padding:6px;text-align:left">Feature</th><th>dtype</th><th>median</th><th>range</th></tr>
              ${(p.added||[]).map(f => `<tr style="border-top:1px solid #30363d">
                <td style="padding:6px"><code>${f.feature}</code></td>
                <td>${f.dtype}</td>
                <td>${f.median ?? "—"}</td>
                <td>${f.min ?? "—"} → ${f.max ?? "—"}</td>
              </tr>`).join("")}
            </table>
            ${p.failed && p.failed.length ? `<h4 style="margin-top:10px;color:#f85149">Failed:</h4>${p.failed.map(f => `<div class="feature-card reject">${f.feature}: ${f.reason}</div>`).join("")}` : ""}
            <div style="margin-top:8px;color:#6e7681;font-size:11px">${p.extended_path}</div>`;
  }
  if (s === "reporter") {
    return `<div class="summary">
              <div class="kpi"><div class="kpi-v">${p.n_proposed}</div><div class="kpi-l">proposed</div></div>
              <div class="kpi"><div class="kpi-v" style="color:#28a745">${p.n_added}</div><div class="kpi-l">shipped</div></div>
              <div class="kpi"><div class="kpi-v">${p.elapsed_s}s</div><div class="kpi-l">total</div></div>
              <div class="kpi"><div class="kpi-v">${p.new_version}</div><div class="kpi-l">version</div></div>
            </div>
            <a href="/artifact/${currentRunId}/0_report.md" target="_blank" style="color:#58a6ff">→ open full report</a>`;
  }
  if (s === "done") {
    return `<div style="color:#7ce38b">Pipeline complete in ${p.elapsed_s}s. Output: <code>${p.output_dir}</code></div>`;
  }
  return `<pre>${JSON.stringify(p, null, 2)}</pre>`;
}

function renderFeatureCard(p) {
  const ext = p.derivation_type === "external" ? " 🌐" : p.derivation_type === "learned" ? " 🧠" : "";
  return `<div class="feature-card">
    <span class="feature-name">${p.name}</span>${ext}
    <span style="font-size:11px;color:#8b949e">· ${p.derivation_type} · ${p.dtype || ""}</span>
    <div class="feature-desc">${p.description || ""}</div>
    ${p.code ? `<pre>${p.code}</pre>` : ""}
    <div class="feature-detail"><em>${p.rationale || ""}</em></div>
    ${(p.dependencies||[]).length ? `<div class="feature-detail" style="font-size:11px;color:#6e7681">deps: ${(p.dependencies).map(c => `<code>${c}</code>`).join(", ")}</div>` : ""}
  </div>`;
}

function renderCritique(c) {
  const risk_color = {low:"#7ce38b", medium:"#f0d264", high:"#f85149"}[c.implementation_risk] || "#8b949e";
  return `<div class="feature-card">
    <span class="feature-name">${c.feature}</span>
    <span style="font-size:11px;color:${risk_color}">· risk: ${c.implementation_risk} · conf ${c.confidence}</span>
    ${c.redundancy_with ? `<div style="font-size:11px;color:#f85149;margin-top:3px">⚠ Redundant with <code>${c.redundancy_with}</code></div>` : ""}
    <div class="feature-detail"><strong>+</strong> ${(c.strengths||[]).join('. ')}</div>
    <div class="feature-detail"><strong>−</strong> ${(c.weaknesses||[]).join('. ')}</div>
  </div>`;
}

function renderCritiqueR2(c) {
  const ship = c.should_ship ? "✓" : "✗";
  return `<div class="feature-card ${c.should_ship ? '' : 'reject'}">
    <span class="feature-name">${c.feature}</span> ${ship}
    <span style="font-size:11px;color:#8b949e">· risk: ${c.remaining_risk} · conf ${c.confidence}</span>
    ${c.redundancy_with ? `<div style="font-size:11px;color:#f85149">⚠ Redundant with <code>${c.redundancy_with}</code></div>` : ""}
    <div class="feature-detail">${(c.round_2_concerns||[]).join(' · ')}</div>
  </div>`;
}

function renderRefinement(r) {
  const action_color = {REVISE:"#ffc107", DEFEND:"#28a745", REPLACE:"#58a6ff"}[r.action] || "#8b949e";
  return `<div class="feature-card" style="border-color:${action_color}">
    <span class="feature-name">${r.original_name || r.name}</span>
    <span style="font-size:11px;color:${action_color}">· ${r.action}</span>
    ${r.action === "REPLACE" && r.new_name ? ` → <code>${r.new_name}</code>` : ""}
    <div class="feature-desc">${r.description || ""}</div>
    ${r.code ? `<pre>${r.code}</pre>` : ""}
    <div class="feature-detail"><em>${r.justification || r.addresses_critique || ""}</em></div>
  </div>`;
}

function renderDecision(d) {
  const cls = (d.decision || "").toLowerCase();
  return `<div class="feature-card ${cls}">
    <span class="feature-name">${d.feature}</span>
    <span style="font-size:11px">· ${d.decision} · prio ${d.priority || "?"}</span>
    <div class="feature-desc">${d.justification || ""}</div>
    ${d.revised_code ? `<pre>${d.revised_code}</pre>` : ""}
  </div>`;
}

async function refreshRunsList() {
  try {
    const r = await fetch("/runs");
    const runs = await r.json();
    if (!runs.length) {
      runsList.innerHTML = '<div class="empty" style="padding:30px 0;">No runs yet</div>';
      return;
    }
    runsList.innerHTML = runs.slice(0, 30).map(rn => {
      const cls = (rn.run_id === currentRunId) ? "run active" : "run";
      const status = {running:"🔵", done:"✅", error:"❌"}[rn.status] || "•";
      const t = new Date(rn.started * 1000).toLocaleTimeString();
      return `<div class="${cls}" onclick="loadRun('${rn.run_id}')">
        <div class="run-uc">${status} ${rn.use_case}</div>
        <div class="run-meta">${rn.run_id.substring(0,8)} · ${t} · ${rn.n_added != null ? rn.n_added + ' added' : ''}</div>
      </div>`;
    }).join("");
  } catch(e) { console.error(e); }
}

async function loadRun(run_id) {
  currentRunId = run_id;
  const r = await fetch(`/runs/${run_id}`);
  const data = await r.json();
  initView(data.use_case);
  // Replay events
  for (const evt of (data.events || [])) handleEvent(evt);
  // If saved-on-disk only (no events): render report card directly
  if (data.events?.length === 0 && data.output_dir) {
    try {
      const rep = await fetch(`/artifact/${run_id}/0_report.json`).then(r => r.json());
      handleEvent({stage: "init", status: "ok", elapsed_s: 0, payload: {use_case: rep.use_case, base_version: rep.base_version, new_version: rep.new_version, output_dir: data.output_dir}});
      handleEvent({stage: "reporter", status: "done", elapsed_s: rep.elapsed_s, payload: rep});
    } catch (e) { /* nope */ }
  }
  refreshRunsList();
}

// Initial state + periodic refresh
refreshRunsList();
setInterval(refreshRunsList, 5000);
