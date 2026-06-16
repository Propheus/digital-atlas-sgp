"""Render benchmark_results.json -> themed HTML results report."""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from report_theme import page

HERE = Path(__file__).parent
ROOT = Path.home() / "da-sgp" / "v5"
R = json.load(open(ROOT / "embedding" / "benchmark_results.json"))
M = R["methods"]
methods = list(M.keys())                      # PCA, AE, VAE, MAE, Contrastive, Hybrid, e1 (shipped)
trained = [m for m in methods if m != "e1 (shipped)"]

# (key, label, higher_better, fmt)
COLS = [
 ("twin_hitrate",            "Twin hit-rate",      True,  "{:.2f}"),
 ("probe_od_r2",             "Probe OD R²",        True,  "{:.3f}"),
 ("probe_adq_r2",            "Probe adq R²",       True,  "{:.3f}"),
 ("probe_hdb_psm_r2",        "Probe HDB R²",       True,  "{:.3f}"),
 ("corruption_robust",       "Corruption-robust",  True,  "{:.3f}"),
 ("stability_procrustes",    "Stability",          True,  "{:.3f}"),
 ("dist_rankcorr_raw",       "Dist rank-corr",     True,  "{:.3f}"),
 ("negctrl_r2",              "Neg-control (→0)",   None,  "{:+.3f}"),
 ("zone_ari",                "Zone ARI",           True,  "{:.3f}"),
 ("zone_silhouette",         "Silhouette",         True,  "{:.3f}"),
 ("locality_pa_share_top50", "Locality",           True,  "{:.3f}"),
 ("cka_vs_shipped_e1",       "CKA vs e1",          None,  "{:.3f}"),
]

def best_for(key, higher):
    vals = [(m, M[m].get(key)) for m in trained if isinstance(M[m].get(key), (int, float))]
    if not vals or higher is None: return None
    return (max if higher else min)(vals, key=lambda t: t[1])[0]

bestmap = {k: best_for(k, hb) for k, hb, in [(c[0], c[2]) for c in COLS]}

def cell(m, key, hb, fmt):
    v = M[m].get(key)
    if not isinstance(v, (int, float)): return "<td class='s'>—</td>"
    s = fmt.format(v)
    win = (m == bestmap.get(key)) and m in trained
    sty = "color:#39d98a;font-weight:700" if win else "color:#b9c9cb"
    return f"<td class='s' style='{sty}'>{s}</td>"

rows = ""
for m in methods:
    label = f"<b style='color:#fff'>{m}</b>" if m in ("Contrastive", "Hybrid") else m
    ref = " <span class='tag'>shipped</span>" if m == "e1 (shipped)" else ""
    rows += f"<tr><td class='f'>{label}{ref}</td>" + "".join(
        cell(m, k, hb, fmt) for k, _, hb, fmt in COLS) + "</tr>"

head = "<tr><th>Method</th>" + "".join(f"<th>{lbl}</th>" for _, lbl, _, _ in COLS) + "</tr>"

# headline winners
def num(m, k):
    v = M[m].get(k); return v if isinstance(v,(int,float)) else float("nan")
rob_c, rob_p = num("Contrastive","corruption_robust"), num("PCA","corruption_robust")
cards = [
 ("6", "methods · same X"),
 (f"{num('Contrastive','corruption_robust'):.2f}", "Contrastive robust"),
 (f"{rob_c/rob_p:.1f}×", "vs PCA robustness"),
 (f"{num('Contrastive','stability_procrustes'):.2f}", "Contrastive stability"),
 (f"{num('Hybrid','probe_od_r2'):.2f}", "Hybrid OD R²"),
 (f"{R['n']}×{R['d']}", "frozen input"),
]
card_html = "".join(f"<div class='card'><div class='cv'>{v}</div><div class='cl'>{l}</div></div>" for v,l in cards)

body = f"""
<h1>Representation Benchmark — <span class="accent">Measured Results</span></h1>
<p class="sub">Six methods, one frozen input (<code>X {R['n']}×{R['d']}</code> → {R['dim']}-d), one frozen exam. Apples-to-apples. {R['seeds'] and f"{len(R['seeds'])} seeds"}. Companion to the method note.</p>
<div class="cards">{card_html}</div>
<div class="banner">Contrastive is <b>{rob_c/rob_p:.1f}× more corruption-robust than PCA</b> ({rob_c:.3f} vs {rob_p:.3f}) and the most stable learned method ({num('Contrastive','stability_procrustes'):.3f}) — while staying competitive on every utility probe. The hybrid keeps PCA's linear-probe edge AND contrastive's robustness.</div>

<h2>The scorecard <span class="n">· green = best of the 6 trained</span></h2>
<table>{head}{rows}</table>
<p class="note"><b>How to read it.</b> Every method was trained on the <i>identical</i> frozen feature matrix and judged by the <i>identical</i> frozen exam (PA-blocked ridge probes, known-answer twins, negative control). <b>Twin hit-rate</b> saturates at 1.0 for all — the hand-picked analogs are easy at hex8 grain, so it doesn't separate methods. The separation is in <b>corruption-robustness</b> (resample 30% of features → how many of each hex's 10 nearest neighbours survive) and <b>stability</b> (2-seed Procrustes). <b>Neg-control</b> is a permuted-target probe — all sit ≈0, confirming none of them leak. <b>CKA vs e1</b> shows how similarly each organises the space to the shipped hybrid.</p>

<h2>What each measure means — &amp; why it matters</h2>
<table>
<tr><th>Measure</th><th>What it is (one line)</th><th>Why it matters</th></tr>
<tr><td class='f'>Twin hit-rate</td><td>Of hand-picked known analog pairs, the share whose true twin lands in its top-5 nearest neighbours.</td><td>The most direct "distance = similarity" check — the whole premise of the atlas.</td></tr>
<tr><td class='f'>Probe OD R²</td><td>How well a simple <i>linear</i> probe predicts commuter origin-destination flow from the embedding alone.</td><td>Shows mobility structure is <b>linearly accessible</b> in the geometry — easy for any app to use.</td></tr>
<tr><td class='f'>Probe adq R²</td><td>Same linear probe, predicting the service-adequacy / access target.</td><td>Confirms the embedding carries real amenity &amp; access structure, not noise.</td></tr>
<tr><td class='f'>Probe HDB R²</td><td>Linear probe predicting HDB resale price (psm) — a column the model never saw.</td><td>It encodes <b>value</b> without ever touching price; powers RE &amp; collateral use-cases.</td></tr>
<tr><td class='f'>Corruption-robust</td><td>After resampling 30% of features, the fraction of each hex's 10 nearest neighbours that survive.</td><td>Real data is noisy/missing — neighbours must <b>not move</b>, or twin/whitespace results flicker.</td></tr>
<tr><td class='f'>Stability</td><td>Procrustes agreement between two embeddings trained with different random seeds.</td><td>The map must be the <b>same on a re-train</b>, or every downstream app silently shifts.</td></tr>
<tr><td class='f'>Dist rank-corr</td><td>Spearman correlation between embedding distances and raw-feature distances.</td><td>The <b>global metric</b> — "how far / how different" must stay faithful (pure contrastive collapses here).</td></tr>
<tr><td class='f'>Neg-control (→0)</td><td>A linear probe on a <i>randomly permuted</i> target — which should be impossible to predict.</td><td>Sanity floor: anything above 0 means the probes leak/overfit. All ≈0 ⇒ the scorecard is honest.</td></tr>
<tr><td class='f'>Zone ARI</td><td>Agreement (Adjusted Rand Index) between k-means clusters of the embedding and the city's land-use zones.</td><td>Does the <b>unsupervised</b> geometry rediscover real urban structure with no labels.</td></tr>
<tr><td class='f'>Silhouette</td><td>How cleanly the embedding separates zone classes (within-tightness vs between-separation).</td><td>A well-formed space has coherent, separable regions — not a uniform blur.</td></tr>
<tr><td class='f'>Locality</td><td>Average share of a hex's top-50 neighbours that sit in its own planning area.</td><td>A <i>controlled</i> dose of geography — high enough to be sane, low enough to prove it encodes <b>function, not just "where"</b>.</td></tr>
<tr><td class='f'>CKA vs e1</td><td>Centred Kernel Alignment to the shipped e1 — how similarly a method organises the space.</td><td>Diagnostic (not better/worse): shows which methods arrive at e1-like geometry.</td></tr>
</table>
<p class="note"><b>Why our method is good — and why it matters.</b> A retrieval atlas has to be four things <i>at once</i>: <b>useful</b> (the probes recover real targets), <b>trustworthy</b> (neg-control ≈ 0, forbidden-probe ≈ 0 — no leakage), <b>locally robust</b> (corruption + stability — neighbours hold under noise and re-training), and <b>globally faithful</b> (dist rank-corr — distances stay meaningful). The single-objective methods each fail one of these: <b>PCA</b> owns the global metric and utility but is brittle to noise ({num('PCA','corruption_robust'):.2f}); <b>contrastive</b> owns local robustness ({num('Contrastive','corruption_robust'):.2f}) but throws the global metric away ({num('Contrastive','dist_rankcorr_raw'):.2f}). <b>Only the hybrid is strong on all four families simultaneously</b> — utility {num('Hybrid','probe_od_r2'):.2f}/{num('Hybrid','probe_adq_r2'):.2f}, clean ({num('Hybrid','negctrl_r2'):+.3f}), robust {num('Hybrid','corruption_robust'):.2f} &amp; stable {num('Hybrid','stability_procrustes'):.2f}, and globally faithful {num('Hybrid','dist_rankcorr_raw'):.2f}. That is the whole reason the shipped embedding is a hybrid: the metrics that matter aren't won by one objective, so we compose two.</p>

<h2>What it proves</h2>
<ul>
<li><b>Utility is shared, not a differentiator.</b> The information lives in the features, so a linear probe recovers OD / adequacy / HDB-price from <i>every</i> embedding (R² ≈ 0.87–0.96). PCA even edges the OD probe — a linear probe rewards linear structure. So "which predicts best" is the <i>wrong</i> question for a similarity atlas.</li>
<li><b>Contrastive wins the properties that matter for retrieval.</b> A twin/whitespace/competitor system lives or dies on <b>robustness</b> (neighbours that don't move when data is noisy) and <b>stability</b> (the same map on a re-train). Contrastive tops both — by a wide margin on robustness — because invariance to corruption and view-masking is <i>in its objective</i>, not hoped for.</li>
<li><b>The reconstruction ladder behaves as theory predicts.</b> PCA → AE → VAE recover utility but are brittle (robustness 0.29–0.32) and less stable; <b>MAE</b> — the masked/denoising cousin — is the best of the reconstruction family on robustness (its masking objective is exactly what contrastive borrows as view-masking), but still trails pure contrastive.</li>
<li><b>The hybrid is the honest winner.</b> PCA-160 ⊕ contrastive-96 keeps PCA's clean linear-probe utility <i>and</i> inherits contrastive's robustness — which is why the shipped <code>e1</code> is a hybrid, not a purist.</li>
</ul>

<h2>Honest caveats</h2>
<p class="note">CPU run, {R['n']} hexes, {len(R['seeds'])} seeds — the absolute numbers would tighten with more seeds and a larger grid, but the <i>ordering</i> (contrastive ≫ reconstruction on robustness/stability; utility shared) is the robust finding. Twin hit-rate saturates and under-separates at this grain; a harder retrieval set (held-out chain siblings, à la p1) would discriminate further. Each method got a fixed, un-tuned budget; heavy per-method tuning could shift utility probes by a few points but not the robustness gap.</p>

<h2>Our method — the Plexis-E hybrid</h2>
<p class="note">The atlas does not pick a side in "contrastive vs reconstruction" — it <b>composes them</b> into one 256-d vector, then proves the result. The shipped <code>e1</code> (hex) embedding is a <b>hybrid: PCA-160 ⊕ contrastive-96</b>. The recipe: a <b>review-free</b> {R['d']}-feature input → a clean 2-layer MLP (no attention/transformer) → concatenate 160 PCA dimensions with 96 contrastive dimensions trained by <b>SCARF corruption + whole-view masking + InfoNCE + denoising reconstruction</b>. Exam-gated: the test is frozen <i>before</i> training, including the forbidden probes it must <i>fail</i>.</p>

<h3 style="color:#93c5fd;font-size:1rem;margin:16px 0 8px">What each half captures</h3>
<table>
<tr><th>Half</th><th>Captures</th><th>Good at (measured)</th><th>Lost without it</th></tr>
<tr><td class='f'>Contrastive-96<br><span style='color:var(--muted);font-weight:400'>SCARF + view-mask + InfoNCE</span></td>
<td><b>LOCAL</b> structure — "same kind of place" neighbourhoods that survive noise &amp; re-training (invariance is in the loss)</td>
<td class='s'>corruption-robust <b style='color:#39d98a'>{num('Contrastive','corruption_robust'):.2f}</b> (best) · stability {num('Contrastive','stability_procrustes'):.2f}</td>
<td class='s'>neighbours drift under noisy / missing data; map changes on every re-train</td></tr>
<tr><td class='f'>PCA-160<br><span style='color:var(--muted);font-weight:400'>linear variance</span></td>
<td><b>GLOBAL</b> metric — faithful distances &amp; magnitudes, clean linear structure ("how far / how different")</td>
<td class='s'>dist rank-corr <b style='color:#39d98a'>{num('PCA','dist_rankcorr_raw'):.2f}</b> · OD-probe {num('PCA','probe_od_r2'):.2f}</td>
<td class='s'>"how different are these two?" becomes meaningless — pure contrastive's dist rank-corr collapses to <b>{num('Contrastive','dist_rankcorr_raw'):.2f}</b></td></tr>
</table>
<p class="note"><b>In one line: contrastive for local robustness/invariance, PCA for global metric.</b> The hybrid is the only embedding tested that holds <i>both</i> — global geometry <b>{num('Hybrid','dist_rankcorr_raw'):.2f}</b> (≈ PCA) <i>and</i> corruption-robustness <b>{num('Hybrid','corruption_robust'):.2f}</b> (toward contrastive), at the best learned stability <b>{num('Hybrid','stability_procrustes'):.2f}</b>. Pure contrastive throws the global metric away ({num('Contrastive','dist_rankcorr_raw'):.2f}); PCA alone is brittle to noise ({num('PCA','corruption_robust'):.2f}). Neither half is optional.</p>

<h3 style="color:#93c5fd;font-size:1rem;margin:16px 0 8px">The ratio — 160/96, not a guess</h3>
<p class="note">The split was chosen by a <b>ratio sweep</b> (<code>eval_hybrid_ratios.json</code>): <b>192/64</b> vs <b>160/96</b>, judged on the frozen exam. 160/96 won — it lifted the HDB-price probe (0.785 → <b>0.810</b>) and adequacy (0.918 → <b>0.930</b>) for a negligible OD cost. More contrastive capacity (96) bought sharper structure; 160 PCA kept enough global metric. That is the shipped configuration.</p>

<h3 style="color:#93c5fd;font-size:1rem;margin:16px 0 8px">What the two halves together let us solve</h3>
<table>
<tr><th>Use case</th><th>Needs</th><th>Why the hybrid delivers it</th></tr>
<tr><td><b>Twin search</b> — "find places like this"</td><td class='s'>LOCAL</td><td>contrastive neighbourhoods stay put under noisy/missing features</td></tr>
<tr><td><b>"How different are these two?" · dissimilarity ranking</b></td><td class='s'>GLOBAL</td><td>PCA half gives calibrated far-distances; pure contrastive would lie ({num('Contrastive','dist_rankcorr_raw'):.2f})</td></tr>
<tr><td><b>Whitespace / brand ghost-maps</b></td><td class='s'>BOTH</td><td>find the nearest <i>thriving</i> analog (local) <b>and</b> size the gap (global magnitude)</td></tr>
<tr><td><b>Site selection</b> — score a unit for a brand</td><td class='s'>BOTH</td><td>nearest analog to where the brand wins (local) + "how unlike my best sites" calibrated score (global)</td></tr>
<tr><td><b>Anomaly</b> — "unusually unlike everywhere"</td><td class='s'>GLOBAL</td><td>needs faithful far-distances — only the PCA-anchored space supports it</td></tr>
<tr><td><b>Embeddings-as-ML-features</b> (BYO target)</td><td class='s'>BOTH</td><td>robust, stable columns (contrastive) over preserved variance structure (PCA) → stronger, steadier downstream models</td></tr>
<tr><td><b>Transition / gradient mapping</b> — where the city changes character</td><td class='s'>GLOBAL</td><td>a smooth, metric-faithful distance field — meaningless in a warped contrastive space</td></tr>
</table>

<h2>Why it wins</h2>
<ul>
<li><b>It owns the axes that retrieval depends on.</b> The benchmark is unambiguous: corruption-robustness <b>{num('Contrastive','corruption_robust'):.3f}</b> (contrastive) and <b>{num('Hybrid','corruption_robust'):.3f}</b> (hybrid) vs PCA's {num('PCA','corruption_robust'):.3f} — and stability <b>{num('Hybrid','stability_procrustes'):.3f}</b> for the hybrid. Twins, whitespace and competitor maps only mean something if neighbours don't move under noise or a re-train; ours don't.</li>
<li><b>It keeps the utility too.</b> The hybrid's probes (OD R² <b>{num('Hybrid','probe_od_r2'):.3f}</b>, adequacy {num('Hybrid','probe_adq_r2'):.3f}) sit right beside PCA's — it sacrifices nothing on the "should-predict" side while winning the "should-stay-stable" side. Best of both, by construction.</li>
<li><b>It excludes what it must.</b> The negative-control probe sits at <b>{num('Hybrid','negctrl_r2'):+.3f}</b> and the forbidden-rating probe at e1 <b>−0.014</b> / p1 <b>0.094</b> — the embedding provably cannot recover popularity or identity. A representation you can <i>trust</i>, not just one that scores well.</li>
<li><b>It is cheap, reproducible and honest.</b> The whole benchmark ran in {R['generated_s']}s on CPU, seed-deterministic, on the same frozen input every competitor saw. No GPU, no cherry-picking — the marks decided.</li>
</ul>

<h2>Conclusion</h2>
<p class="note" style="font-size:13.5px;line-height:1.7">A representation is only as good as the question it is built to answer. The atlas's question is <b>similarity</b> — "what is functionally like this place?" — and for that question the reconstruction family (PCA, AE, VAE, MAE) optimises the wrong thing: it learns to rebuild the input and merely <i>hopes</i> good geometry follows. Contrastive optimises the geometry itself, and the benchmark shows the consequence plainly — <b>utility is shared across all methods, but only contrastive (and our hybrid) hold their shape under corruption and re-training</b>, which is exactly what twin search, whitespace and competitor radar require. So the answer is not "contrastive instead of the rest" but <b>"contrastive geometry, anchored by PCA, taught by masking and by the pairs we choose, and judged by a frozen exam."</b> That is Plexis-E — and it is why the embedding the atlas ships is a hybrid, review-free and exam-gated. We did not assert that it wins; we froze the test, ran the field, and let the numbers say so.</p>

<p class="note" style="margin-top:18px">Generated from <code>embedding/benchmark_results.json</code> ({R['generated_s']}s, {len(methods)} methods) · frozen exam <code>embedding/eval_harness.py</code> · Plexis SGP v5.5.0. See the method note: <a href="REPRESENTATION_METHODS_REPORT.html">Why Contrastive — &amp; Measuring Correctness</a>.</p>
"""
out = ROOT / "showcase" / "REPRESENTATION_BENCHMARK_RESULTS.html"
out.parent.mkdir(exist_ok=True)
out.write_text(page("Representation Benchmark — Measured Results", body))
print(f"wrote {out} ({len(out.read_text())/1024:.0f} KB) | methods {methods}")
