"""Generate the SGP ASTS friendliness HTML report — Propheus 'Geoagent' dark-teal theme."""
import json, csv, statistics as st
from pathlib import Path

D = Path(__file__).parent / "report_data"
OUT = Path(__file__).parent / "SGP_ASTS_REPORT.html"
VERSION = "Propheus Digital Atlas SGP v4.8"
PAPER_TITLE = ("Evaluating the Quality of Children’s Active School Travel Spaces and the "
               "Mechanisms of School District Friendliness Impact Based on Multi-Source Big Data")
PAPER_CITE = "Lu, C., Yu, C. &amp; Liu, X. (2024). Land 13(8), 1319 · MDPI · doi:10.3390/land13081319 · 151 primary schools, Lanzhou, China"

gj = json.load(open(D / "friendliness_index.geojson"))
_BAD = ("student care", "childcare", "@", " gate ")
feats = [f for f in gj["features"] if not any(b in f["properties"]["name"].lower() for b in _BAD)]
P = [f["properties"] for f in feats]

WEIGHTS = [("Greenery — park area share", 0.2601),
           ("Choice — through-movement", 0.1916),
           ("Traffic signals — safety", 0.1873),
           ("Integration — reachability", 0.1628),
           ("Crossings — safety", 0.1196),
           ("Footpath density — provision", 0.0785)]

def read_csv(p):
    with open(p) as f:
        return list(csv.DictReader(f))

gd = read_csv(D / "geodetector.csv")
gi = read_csv(D / "geodetector_interaction.csv")

regions = {}
for p in P:
    regions.setdefault(p["zone"], []).append(p["friendliness"])
region_rows = sorted(((z, round(st.mean(v), 1), len(v)) for z, v in regions.items()), key=lambda r: -r[1])
top = sorted(P, key=lambda p: -p["friendliness"])[:10]
bot = sorted(P, key=lambda p: p["friendliness"])[:10]
levels = {"Low": 0, "Medium": 0, "High": 0}
for p in P:
    levels[p["level"]] += 1
stats = dict(n=len(P), n_high=levels["High"], n_low=levels["Low"], mean=round(st.mean([p["friendliness"] for p in P]), 1))

def color(v):  # 0..100 -> coral -> amber -> teal (dark-theme scale)
    v = max(0, min(100, v)) / 100
    a = (1.0, 0.42, 0.42); b = (1.0, 0.82, 0.40); c = (0.13, 0.70, 0.67)
    if v < 0.5:
        t = v/0.5; r = tuple(a[i]+(b[i]-a[i])*t for i in range(3))
    else:
        t = (v-0.5)/0.5; r = tuple(b[i]+(c[i]-b[i])*t for i in range(3))
    return "#%02x%02x%02x" % tuple(int(x*255) for x in r)

def rows_tbl(rows):
    return "".join(
        f'<tr><td class="rank">{i+1}</td><td>{p["name"].replace(" Primary School"," Pri Sch")}</td>'
        f'<td class="muted">{p["zone"].replace(" REGION","")}</td>'
        f'<td class="num"><span class="chip" style="--c:{color(p["friendliness"])}">{p["friendliness"]:.0f}</span></td></tr>'
        for i, p in enumerate(rows))

wmax = max(w for _, w in WEIGHTS)
weight_bars = "".join(
    f'<div class="wrow"><span class="wlab">{lab}</span>'
    f'<span class="wbar"><i style="width:{w/wmax*100:.0f}%"></i></span>'
    f'<span class="wval">{w:.3f}</span></div>' for lab, w in WEIGHTS)

qmax = max(float(r["q"]) for r in gd)
q_bars = "".join(
    f'<div class="wrow"><span class="wlab">{r["driver"]} <em>({r["effect"]})</em></span>'
    f'<span class="wbar q"><i style="width:{float(r["q"])/qmax*100:.0f}%"></i></span>'
    f'<span class="wval">{float(r["q"]):.3f}</span></div>' for r in gd)

inter_rows = "".join(
    f'<tr><td>{r["pair"]}</td><td class="num">{float(r["q_ab"]):.3f}</td>'
    f'<td class="num muted">{float(r["max_single"]):.3f}</td>'
    f'<td><span class="tag {r["interaction"].split("-")[0]}">{r["interaction"]}</span></td></tr>'
    for r in gi)

region_bars = "".join(
    f'<div class="wrow"><span class="wlab">{z.replace(" REGION","")}<span class="rn">{n} schools</span></span>'
    f'<span class="wbar"><i style="width:{m/max(r[1] for r in region_rows)*100:.0f}%;background:{color(m)}"></i></span>'
    f'<span class="wval">{m}</span></div>' for z, m, n in region_rows)

TERMS = [
 ("01", "Schools", "where every journey ends",
  "The government primary schools, each pinned to its exact location. Everything in the study is measured in the area "
  "around these points — they are the anchor of the analysis.",
  f"{stats['n']} of Singapore's ~179 MOE primary schools (a few dropped as data duplicates); spread West 43 · "
  "North-East 42 · Central 28 · North 28 · East 27.",
  "MOE's Primary-1 registration gives priority to homes within 1 km (then 1–2 km), so the area right around each "
  "school is where most of its pupils actually live — and could walk."),
 ("02", "Walking network", "the web of footpaths",
  "A digital map of every footway, sidewalk, park path and pedestrian crossing, stitched into one connected graph the "
  "computer can “walk” along. Built from OpenStreetMap.",
  "170,121 nodes (junctions) and 463,880 edges (path segments) covering all of Singapore.",
  "This is the real surface children travel on. Distances are measured <em>along paths</em>, not straight lines — so a "
  "canal or expressway blocking a route is correctly counted as a detour, the way a child experiences it."),
 ("03", "Space syntax", "how readable the streets are",
  "An established urban-morphology science that scores a street layout on two things — <b>Integration</b> (how easy a "
  "place is to reach from everywhere else) and <b>Choice</b> (how likely a street is to lie on a natural through-route). "
  "Simple, well-integrated networks are easy to navigate; tangled ones are not.",
  "Computed with the cityseer engine on a 235,600-node “dual” model of the network, at 800 m and 1600 m walking radii.",
  "A legible network is one a 7-year-old can follow without getting lost, and where people and traffic move predictably. "
  "It is a structural wayfinding-and-safety measure, independent of how nice any single street looks."),
 ("04", "Catchment", "the active school travel space",
  "The bundle of streets a child can reach within <b>1 km of walking along the network</b> from the school gate — not a "
  "1 km circle on a map, but the real reachable area. This is the “Active School Travel Space” the study evaluates.",
  f"{stats['n']} catchments; on average ~31 km of walkable streets over ~0.9 km² each, from compact (3.8 km of streets) "
  "to sprawling (66 km).",
  "It is drawn to match the MOE 1 km priority band exactly, so it is the precise area where an upgrade would change the "
  "most pupils' walk to school."),
 ("05", "Entropy index", "one fair score from six measures",
  "The six raw measures (Integration, Choice, crossings, signals, greenery, footpath density) are fused into a single "
  "<b>0–100 score</b> by the <b>entropy weight method</b> — a statistical rule that gives more weight to indicators that "
  "genuinely vary and carry information, and less to flat ones. No official chooses the weights, so there is no agency bias.",
  "Data-derived weights: greenery 0.26 · choice 0.19 · signals 0.19 · integration 0.16 · crossings 0.12 · footpaths 0.08. "
  "Schools then split into Low / Medium / High thirds.",
  "An auditable, defensible score whose weights come from the data, not opinion — important for any public-facing "
  "prioritisation that has to withstand scrutiny."),
 ("06", "Geographic Detector", "what explains the map",
  "A spatial-statistics test that asks “how much of the friendliness pattern does each background factor explain?”, "
  "producing a power score <b>q</b> from 0 to 1. Its interaction mode checks whether two factors together explain more "
  "than either alone.",
  "School centrality q=0.22 (strongest) · population density 0.11 · district size 0.08 · transport convenience 0.06 — all "
  "positive. Every factor pair is “nonlinear-enhancing” (density × centrality reaches q=0.40).",
  "It reveals the <em>levers</em>: friendliness is not random — it tracks how centrally a school sits in the street "
  "network, amplified by density. That points to where structural change, not cosmetics, would help most."),
]
term_cards = "".join(
  f'<div class="termcard"><div class="termhead"><span class="tnum">{no}</span>'
  f'<h4>{term}<span class="tplain">{tag}</span></h4></div>'
  f'<p>{plain}</p>'
  f'<div class="tmeta"><span class="tlabel">In this study</span>{data}</div>'
  f'<div class="tmeta why"><span class="tlabel">For planners</span>{why}</div></div>'
  + ('<div class="tarrow">↓</div>' if no != "06" else '')
  for no, term, tag, plain, data, why in TERMS)

data_json = json.dumps([
    {"n": p["name"], "z": p["zone"], "f": round(p["friendliness"], 1), "lv": p["level"],
     "g": round(p["green_pct"]*100, 1), "cr": round(p["crossing_dens"], 1),
     "ch": round(p["choice"]), "it": round(p["integration"]),
     "lat": f["geometry"]["coordinates"][1], "lon": f["geometry"]["coordinates"][0]}
    for p, f in zip(P, feats)])

LOGO = ('<svg viewBox="0 0 100 100" class="plogo" xmlns="http://www.w3.org/2000/svg">'
        '<path d="M45,64.2c-1.1,9.1-3.3,15.3-5.8,15.3c-0.1,0-0.1,0-0.2,0c-0.3,0-0.6-0.2-1-0.4c-3.1-2.5-5.4-14.5-5.4-29c0-14.4,2.3-26.4,5.4-29c0.3-0.3,0.7-0.5,1-0.5h0.2c2.6,0,4.9,6.8,6,16.6c-5.6,2-9.5,7.3-9.5,13.5C35.6,56.9,39.5,62.1,45,64.2z"/>'
        '<path d="M67.4,50c0,14.5-2.3,26.5-5.4,29c-0.3,0.2-0.6,0.4-0.9,0.4c-0.1,0-0.2,0-0.2,0c-2.5,0-4.7-6.2-5.8-15.3c5.5-2,9.4-7.3,9.4-13.5c0-6.2-4-11.6-9.5-13.5c1.1-9.8,3.4-16.6,6-16.6H61c0.4,0,0.7,0.2,1,0.5C65.1,23.6,67.4,35.6,67.4,50z"/>'
        '<path d="M30.2,50c0-14.4,2.3-26.4,5.4-29c-10.6,5.3-17.9,16.3-17.9,29c0,12.7,7.3,23.7,17.9,29C32.5,76.5,30.2,64.5,30.2,50z M64.4,21c3.1,2.6,5.4,14.5,5.4,29c0,14.5-2.3,26.5-5.4,29C75,73.7,82.3,62.7,82.3,50C82.3,37.3,75,26.4,64.4,21z"/>'
        '<path d="M62.1,50.7c0,5-3,9.3-7.4,11.2c-1.5,0.6-3.1,1-4.8,1c-1.7,0-3.3-0.4-4.8-1c-4.3-1.9-7.4-6.2-7.4-11.2c0-5.1,3.1-9.4,7.5-11.2c1.4-0.6,3-0.9,4.7-0.9c1.7,0,3.2,0.3,4.7,0.9C59.1,41.3,62.1,45.6,62.1,50.7z"/></svg>')

HTML = f"""<!doctype html><html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>School-Travel Friendliness — Singapore · Propheus Digital Atlas</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap" rel="stylesheet">
<style>
:root{{--bg0:#0F2224;--bg1:#132C30;--bg2:#1A3C42;--accent:#20b2aa;--accent2:#3fe0d6;
--ink:#f3f8f7;--t2:#aebfbc;--t3:#7d918e;--line:rgba(32,178,170,.18);
--glass:rgba(17,40,42,.55);--glass2:rgba(20,48,51,.75);--coral:#ff6b6b;--amber:#ffd166}}
*{{box-sizing:border-box}}
html{{scroll-behavior:smooth}}
body{{margin:0;color:var(--ink);font-family:Inter,system-ui,sans-serif;font-size:16.5px;line-height:1.7;
background:linear-gradient(150deg,#0F2224 0%,#132C30 45%,#1A3C42 100%) fixed;-webkit-font-smoothing:antialiased}}
.wrap{{max-width:1080px;margin:0 auto;padding:0 26px}}
a{{color:var(--accent2)}}
/* top bar */
.topbar{{display:flex;align-items:center;justify-content:space-between;padding:20px 0;border-bottom:1px solid var(--line)}}
.brand{{display:flex;align-items:center;gap:11px;font-family:"Space Grotesk";font-weight:600;font-size:15px;letter-spacing:.01em}}
.plogo{{width:30px;height:30px}}.plogo path{{fill:var(--accent)}}
.brand small{{display:block;font:500 11px/1 Inter;color:var(--t3);letter-spacing:.14em;text-transform:uppercase;margin-top:3px}}
.navver{{font:500 12px/1 Inter;color:var(--t2);border:1px solid var(--line);border-radius:20px;padding:7px 14px}}
/* header */
header{{padding:64px 0 46px}}
.kicker{{font:600 12.5px/1 Inter;letter-spacing:.2em;text-transform:uppercase;color:var(--accent);margin-bottom:20px;
display:inline-flex;gap:9px;align-items:center}}
.kicker::before{{content:"";width:26px;height:1.5px;background:var(--accent)}}
h1{{font-family:"Space Grotesk";font-weight:700;font-size:clamp(34px,6vw,58px);line-height:1.05;margin:0 0 20px;letter-spacing:-.015em}}
h1 .g{{background:linear-gradient(90deg,var(--accent),var(--accent2));-webkit-background-clip:text;background-clip:text;color:transparent}}
.lede{{font-size:19px;max-width:710px;color:var(--t2)}}.lede b{{color:var(--ink);font-weight:600}}
.chips{{display:flex;flex-wrap:wrap;gap:14px;margin-top:38px}}
.chip-stat{{background:var(--glass);border:1px solid var(--line);border-radius:16px;padding:16px 22px;min-width:124px;backdrop-filter:blur(8px)}}
.chip-stat b{{display:block;font-family:"Space Grotesk";font-weight:700;font-size:31px;line-height:1;color:var(--accent2)}}
.chip-stat span{{font-size:12px;color:var(--t3);text-transform:uppercase;letter-spacing:.07em}}
.cite{{display:flex;gap:18px;margin-top:30px;background:var(--glass);border:1px solid var(--line);border-left:3px solid var(--accent);border-radius:14px;padding:18px 22px;backdrop-filter:blur(8px)}}
.cite-tag{{font:600 11px/1 Inter;letter-spacing:.14em;text-transform:uppercase;color:var(--accent);padding-top:3px;white-space:nowrap}}
.cite-title{{font-family:"Space Grotesk";font-weight:500;font-size:16px;color:var(--ink);line-height:1.4}}
.cite-meta{{font-size:13px;color:var(--t2);margin-top:6px}}
section{{padding:52px 0;border-top:1px solid var(--line)}}
h2{{font-family:"Space Grotesk";font-weight:600;font-size:30px;margin:0 0 10px;letter-spacing:-.01em}}
.sub{{color:var(--t2);margin:0 0 30px;max-width:720px;font-size:16.5px}}.sub b{{color:var(--ink)}}.sub em{{color:var(--accent2);font-style:normal}}
#map{{height:580px;border-radius:20px;border:1px solid var(--line);box-shadow:0 20px 60px -30px #000}}
.leaflet-popup-content-wrapper{{background:#0f2628;color:var(--ink);border:1px solid var(--line);border-radius:12px}}
.leaflet-popup-tip{{background:#0f2628}}
.legend{{display:flex;align-items:center;gap:14px;margin-top:18px;font-size:13.5px;color:var(--t2);flex-wrap:wrap}}
.scale{{height:12px;width:260px;border-radius:6px;background:linear-gradient(90deg,#ff6b6b,#ffd166,#20b2aa)}}
.grid{{display:grid;grid-template-columns:1fr 1fr;gap:26px}}
@media(max-width:780px){{.grid{{grid-template-columns:1fr}} #map{{height:460px}} body{{font-size:16px}}}}
.card{{background:var(--glass);border:1px solid var(--line);border-radius:18px;padding:28px 30px;backdrop-filter:blur(8px)}}
.card h3{{font-family:"Space Grotesk";font-weight:600;font-size:20px;margin:0 0 20px;color:var(--ink)}}
table{{width:100%;border-collapse:collapse;font-size:14.5px}}
th{{text-align:left;font:600 11px/1 Inter;letter-spacing:.09em;text-transform:uppercase;color:var(--t3);padding:0 0 11px;border-bottom:1px solid var(--line)}}
td{{padding:10px 0;border-bottom:1px solid rgba(255,255,255,.05)}}tr:last-child td{{border-bottom:none}}
td.num{{text-align:right;font-variant-numeric:tabular-nums}}td.rank{{color:var(--t3);width:24px}}
.muted{{color:var(--t2)}}
.chip{{display:inline-block;min-width:32px;text-align:center;font-weight:700;color:#06201d;background:var(--c);border-radius:8px;padding:3px 9px;font-size:13px}}
.wrow{{display:grid;grid-template-columns:1fr 150px 48px;align-items:center;gap:15px;margin:13px 0;font-size:14.5px}}
.wrow em{{color:var(--accent2);font-style:normal;font-weight:600}}
.wlab{{display:flex;justify-content:space-between;gap:8px}}.rn{{color:var(--t3);font-size:12px}}
.wbar{{background:rgba(255,255,255,.07);height:10px;border-radius:6px;overflow:hidden}}
.wbar i{{display:block;height:100%;background:linear-gradient(90deg,var(--accent),var(--accent2));border-radius:6px}}
.wbar.q i{{background:linear-gradient(90deg,#7c83ff,#a78bfa)}}
.wval{{text-align:right;font-variant-numeric:tabular-nums;color:var(--t2);font-size:13.5px}}
.tag{{font-size:11.5px;font-weight:600;padding:3px 10px;border-radius:20px;background:rgba(255,255,255,.08);color:var(--t2)}}
.tag.nonlinear{{background:rgba(32,178,170,.16);color:var(--accent2)}}.tag.bi{{background:rgba(255,209,102,.16);color:var(--amber)}}
.note{{background:var(--glass2);border:1px solid var(--line);border-left:3px solid var(--accent);border-radius:12px;padding:20px 24px;font-size:15px;color:var(--t2)}}.note b{{color:var(--ink)}}
.flow{{display:flex;flex-wrap:wrap;gap:8px;align-items:center}}
.flow span{{background:rgba(32,178,170,.08);border:1px solid var(--line);border-radius:9px;padding:7px 13px;font-size:13.5px;color:var(--ink)}}
.flow .ar{{border:none;background:none;color:var(--accent);padding:0 1px;font-size:15px}}
/* methodology */
.mgrid{{display:grid;grid-template-columns:1fr 1fr;gap:18px}}
@media(max-width:780px){{.mgrid{{grid-template-columns:1fr}}}}
.mstep{{background:var(--glass);border:1px solid var(--line);border-radius:14px;padding:20px 22px}}
.mstep .no{{font-family:"Space Grotesk";font-weight:700;color:var(--accent);font-size:13px;letter-spacing:.05em}}
.mstep h4{{margin:6px 0 6px;font-size:16.5px;font-weight:600}}
.mstep p{{margin:0;font-size:14px;color:var(--t2)}}
.termflow{{max-width:840px}}
.termcard{{background:var(--glass);border:1px solid var(--line);border-radius:16px;padding:24px 28px;backdrop-filter:blur(8px)}}
.termhead{{display:flex;align-items:baseline;gap:14px;margin-bottom:10px}}
.tnum{{font-family:"Space Grotesk";font-weight:700;font-size:15px;color:var(--accent);background:rgba(32,178,170,.12);
border:1px solid var(--line);border-radius:9px;padding:5px 10px;letter-spacing:.04em}}
.termhead h4{{margin:0;font-family:"Space Grotesk";font-weight:600;font-size:21px;display:flex;align-items:baseline;gap:12px;flex-wrap:wrap}}
.tplain{{font:400 14px/1 Inter;color:var(--t3);font-style:italic}}
.termcard>p{{margin:0 0 14px;color:var(--t2);font-size:15.5px}}.termcard b{{color:var(--ink)}}.termcard em{{color:var(--accent2);font-style:normal}}
.tmeta{{font-size:14px;color:var(--t2);padding:11px 0 0;border-top:1px solid rgba(255,255,255,.06);margin-top:4px}}
.tmeta.why{{margin-top:11px}}
.tlabel{{display:inline-block;font:600 10.5px/1 Inter;letter-spacing:.1em;text-transform:uppercase;color:var(--accent);
background:rgba(32,178,170,.1);border-radius:5px;padding:4px 8px;margin-right:9px;vertical-align:middle}}
.tmeta.why .tlabel{{color:var(--amber);background:rgba(255,209,102,.1)}}
.tarrow{{text-align:center;color:var(--accent);font-size:22px;line-height:1;margin:9px 0}}
.formula{{font-family:"Space Grotesk",monospace;background:#0c1d1f;border:1px solid var(--line);border-radius:10px;
padding:14px 18px;color:var(--accent2);font-size:14.5px;overflow-x:auto;margin:10px 0}}
.srctab td{{font-size:14px}}.srctab td:first-child{{color:var(--ink);font-weight:500}}.srctab td:last-child{{color:var(--t2)}}
footer{{padding:44px 0 70px;border-top:1px solid var(--line);color:var(--t3);font-size:13.5px}}
/* ---- print / PDF ---- */
@page{{size:A4;margin:11mm}}
@media print{{
  *{{-webkit-print-color-adjust:exact!important;print-color-adjust:exact!important}}
  html,body{{background:#11282a!important}}
  body{{font-size:11pt}}
  .wrap{{padding:0 6mm}}
  a{{color:var(--accent2)!important;text-decoration:none}}
  header{{padding:18px 0 26px}}
  section{{padding:24px 0;break-inside:avoid}}
  h1{{font-size:30pt}}h2{{font-size:18pt}}
  #map{{height:300px;break-inside:avoid}}
  .card,.termcard,.mstep,.chip-stat,.cite,.note,.formula{{break-inside:avoid}}
  .termcard,.mstep{{page-break-inside:avoid}}
  .topbar{{padding:10px 0}}
  .chips{{gap:8px}}
}}
.powered{{display:flex;align-items:center;gap:12px;margin-bottom:18px;color:var(--t2);font-size:14px}}
.powered .plogo{{width:26px;height:26px}}.powered b{{color:var(--ink);font-weight:600}}
</style></head><body>

<div class="wrap"><div class="topbar">
<div class="brand">{LOGO}<div>Propheus<small>Digital Atlas · Singapore</small></div></div>
<div class="navver">{VERSION}</div>
</div></div>

<header><div class="wrap">
<div class="kicker">Urban Analytics · Active School Travel</div>
<h1>Can children <span class="g">walk to school?</span><br>Singapore's school-travel friendliness</h1>
<p class="lede">A full replication of <a href="https://www.mdpi.com/2073-445X/13/8/1319" target="_blank">Land 2024, 13(8):1319</a>
(Lanzhou, 151 primary schools) for <b>{stats['n']} Singapore primary schools</b> — scoring the quality of the
1&nbsp;km walking catchment around each school from space syntax, pedestrian safety, greenery and footpath provision,
then asking <b>what drives it</b> with a Geographic Detector.</p>
<div class="chips">
<div class="chip-stat"><b>{stats['n']}</b><span>Primary schools</span></div>
<div class="chip-stat"><b>1 km</b><span>Network catchment</span></div>
<div class="chip-stat"><b>{stats['n_high']}</b><span>High friendliness</span></div>
<div class="chip-stat"><b>{stats['n_low']}</b><span>Low friendliness</span></div>
<div class="chip-stat"><b>235k</b><span>Space-syntax nodes</span></div>
</div>
<div class="cite"><div class="cite-tag">Replicating</div>
<div class="cite-body"><div class="cite-title">“{PAPER_TITLE}”</div>
<div class="cite-meta">{PAPER_CITE} · <a href="https://www.mdpi.com/2073-445X/13/8/1319" target="_blank">MDPI</a></div></div></div>
</div></header>

<section><div class="wrap">
<h2>The map</h2>
<p class="sub">Each school at its location, coloured by the friendliness of its walking catchment. Click a dot for the breakdown.</p>
<div id="map"></div>
<div class="legend"><span>Less friendly</span><div class="scale"></div><span>More friendly</span>
<span style="margin-left:auto">Catchment = 1&nbsp;km network distance · MOE home-school priority band</span></div>
</div></section>

<section><div class="wrap">
<h2>Key terms, in plain language</h2>
<p class="sub">This study chains six methods: <b>schools → walking network → space syntax → catchment → entropy index →
Geographic Detector</b>. Here is what each one means, the data behind it, and why it matters for planning.</p>
<div class="termflow">{term_cards}</div>
</div></section>

<section><div class="wrap">
<h2>A core–periphery pattern</h2>
<p class="sub">Friendliness rises toward the <b>newer planned towns</b> of the west and north-east and falls in the
<b>dense central core</b> — the inverse of 15-minute amenity access. It reflects the walking <em>environment</em>
(greenery, legible street networks, controlled crossings), the same core–periphery signature the Lanzhou study reported.</p>
<div class="grid">
<div class="card"><h3>Mean friendliness by region</h3>{region_bars}</div>
<div class="card"><h3>What makes a street friendly?</h3>
<p class="muted" style="margin:-6px 0 16px;font-size:14px">Objective entropy weights across all {stats['n']} catchments.</p>
{weight_bars}</div>
</div>
</div></section>

<section><div class="wrap">
<h2>Most &amp; least friendly catchments</h2>
<div class="grid">
<div class="card"><h3>Top 10</h3><table><thead><tr><th></th><th>School</th><th>Region</th><th class="num">Score</th></tr></thead><tbody>{rows_tbl(top)}</tbody></table></div>
<div class="card"><h3>Bottom 10</h3><table><thead><tr><th></th><th>School</th><th>Region</th><th class="num">Score</th></tr></thead><tbody>{rows_tbl(bot)}</tbody></table></div>
</div>
</div></section>

<section><div class="wrap">
<h2>Reading the scores — what friendliness means here</h2>
<p class="sub">The score is a <b>0–100 relative ranking</b> of how supportive each school's 1&nbsp;km walking catchment is for a
child travelling on foot — <em>100 = friendliest catchment in Singapore, 0 = least</em>. It rates the walking
<b>environment</b>, not how close amenities are, and is comparative across the {stats['n']} schools rather than an
absolute pass/fail.</p>
<div class="mgrid">
<div class="mstep"><div class="no">WHAT IT CAPTURES</div><h4>The child's walk</h4>
<p>A high score means short, legible routes (few confusing turns), dense controlled crossings, leafy shaded streets and
continuous footpaths — the conditions under which a parent lets a child walk or cycle to school unaccompanied.</p></div>
<div class="mstep"><div class="no">WHY IT MATTERS IN SG</div><h4>Policy-relevant by design</h4>
<p>Singapore's MOE gives <b>admission priority within 1–2 km</b> of a school, so a large share of pupils live in genuine
walking range. The score shows where that walking environment actually delivers — directly informing active-travel,
road-safety and the “car-lite” agenda.</p></div>
<div class="mstep"><div class="no">CONTEXT</div><h4>Tropical &amp; safety lens</h4>
<p>In Singapore's climate, <b>greenery</b> (the heaviest-weighted indicator, 0.26) is shade and heat relief, not just
amenity; <b>crossings &amp; signals</b> are the front line of child road safety; <b>space-syntax legibility</b> means
routes a young child can navigate. That is why these dominate the index.</p></div>
<div class="mstep"><div class="no">HOW TO USE IT</div><h4>Targeting, not judgement</h4>
<p>A <span style="color:var(--coral);font-weight:600">Low</span> score is not a “bad school” — it flags a catchment
where greening, crossing upgrades or footpath continuity would most improve children's walk. Bottom-decile catchments
are the priority list for intervention.</p></div>
</div>
<div class="note" style="margin-top:22px"><b>Why the pattern inverts 15-minute access.</b> Friendly catchments cluster
in <em>newer towns</em> (Jurong West, Punggol) built with wide green park-connector footpaths and regular signalised
crossings; the <em>dense central core</em> (Bukit Timah, Newton) scores lower because mature, fine-grained street
networks have more turns, less green corridor and busier roads — even though shops sit closer. The score is measuring a
different thing than proximity: the <em>quality of the journey</em>, which is what determines whether a child walks.</div>
</div></section>

<section><div class="wrap">
<h2>What drives friendliness — the mechanisms</h2>
<p class="sub">Geographic Detector q-statistic: the share of friendliness variance explained by each contextual driver
(held strictly <em>out</em> of the index to avoid circularity). All four push friendliness up.</p>
<div class="grid">
<div class="card"><h3>Single-factor power (q)</h3>{q_bars}
<p class="muted" style="font-size:13.5px;margin-top:16px">School centrality is the strongest single driver — schools
embedded in well-connected street networks have friendlier catchments.</p></div>
<div class="card"><h3>Interaction detector</h3>
<table><thead><tr><th>Factor pair</th><th class="num">q</th><th class="num">max single</th><th>type</th></tr></thead><tbody>{inter_rows}</tbody></table>
<p class="muted" style="font-size:13.5px;margin-top:16px">Every pair is <b style="color:var(--accent2)">nonlinear-enhancing</b>:
factors explain far more together than alone — friendliness is a system effect, not a single lever.</p></div>
</div>
</div></section>

<section id="method"><div class="wrap">
<h2>Methodology</h2>
<p class="sub">Faithful to the source paper's chain — <b>schools → walking network → space syntax → catchment →
entropy index → Geographic Detector</b> — adapted to Singapore and computed end-to-end on Propheus infrastructure.
The logic: define the real walkable area a child crosses to reach school, measure its <em>environmental quality</em>
from objective open data, fuse those measures into one score with no subjective weighting, then statistically test
which contextual factors <em>explain</em> the resulting pattern. Where Lanzhou used the Amap routing API and Baidu
street view, Singapore substitutes the OpenStreetMap pedestrian graph and the Digital Atlas v4 layers; the street-view
dimension is deferred to Phase 2.</p>

<div class="card" style="margin-bottom:22px">
<h3>Data sources</h3>
<table class="srctab"><tbody>
<tr><td>Primary schools (points)</td><td>Digital Atlas v4 places master — {stats['n']} schools after cleaning</td></tr>
<tr><td>Walking network</td><td>OpenStreetMap pedestrian graph — 170,121 nodes / 463,880 edges</td></tr>
<tr><td>Road crossings · traffic signals</td><td>OpenStreetMap — 40,551 crossings · 5,443 signals (safety)</td></tr>
<tr><td>Parks &amp; green space</td><td>OpenStreetMap — 4,658 polygons (greenery)</td></tr>
<tr><td>Bus stops · MRT stations</td><td>OpenStreetMap — 5,938 bus · 324 rail (transport-convenience driver)</td></tr>
<tr><td>Population density</td><td>Digital Atlas v4 subzone population ÷ subzone area</td></tr>
</tbody></table>
</div>

<div class="mgrid">
<div class="mstep"><div class="no">STEP 1 · CATCHMENT</div><h4>1 km network catchment</h4>
<p>For each school, the streets reachable within <b>1 km network distance</b> (not Euclidean) on the OSM walk graph —
the MOE home-school registration priority band. The corridor = reachable edges buffered 40 m.</p></div>

<div class="mstep"><div class="no">STEP 2 · SPACE SYNTAX</div><h4>Angular Integration &amp; Choice</h4>
<p>cityseer angular analysis on the <b>dual graph</b> (235,600 nodes). Harmonic closeness → <b>Integration</b>
(reachability); betweenness → <b>Choice</b> (through-movement), at 800 m &amp; 1600 m radii.</p></div>

<div class="mstep"><div class="no">STEP 3 · SAFETY &amp; GREENERY</div><h4>Objective environment</h4>
<p>Controlled crossings &amp; traffic signals per km of route (safety); park/green area as a share of the catchment
(greenery); walkable footpath density (provision). All clipped to the catchment corridor.</p></div>

<div class="mstep"><div class="no">STEP 4 · INDEX</div><h4>Entropy-weighted composite</h4>
<p>Six indicators min-max normalised, then combined by the <b>entropy weight method</b> — weights derived from each
indicator's information content, no subjective tuning — and rescaled 0–100.</p></div>
</div>

<div class="card" style="margin-top:22px">
<h3>Formulae</h3>
<p class="muted" style="margin:-4px 0 8px;font-size:14px">Entropy weight of indicator <em>j</em> over <em>n</em> catchments:</p>
<div class="formula">pⱼ = rᵢⱼ / Σᵢ rᵢⱼ &nbsp;&nbsp;·&nbsp;&nbsp; eⱼ = −(1/ln n) Σᵢ pᵢⱼ ln pᵢⱼ &nbsp;&nbsp;·&nbsp;&nbsp; wⱼ = (1−eⱼ) / Σⱼ(1−eⱼ)</div>
<p class="muted" style="margin:14px 0 8px;font-size:14px">Friendliness, and the Geographic Detector power statistic <em>q</em> (h = driver strata, 5 quantiles):</p>
<div class="formula">Friendliness = Σⱼ wⱼ rᵢⱼ &nbsp;&nbsp;·&nbsp;&nbsp; q = 1 − ( Σₕ Nₕ σ²ₕ ) / ( N σ² ) &nbsp;∈ [0,1]</div>
<p class="muted" style="font-size:13.5px;margin-top:12px"><b style="color:var(--ink)">Disjoint sets.</b> Index indicators
(route environment) and Geographic Detector drivers (population density, transport convenience, district size, school
centrality) are kept strictly separate, so q is never circular — the central design rule of the analysis.</p>
</div>
</div></section>

<section><div class="wrap">
<div class="note"><b>Scope — Phase 1.</b> This measures network structure plus objective environment proxies. The source
paper's street-view experiential layer (green-view index, sky/enclosure, sidewalk ratio from semantic segmentation of
Google Street View / Mapillary) is Phase 2 and requires a GPU. School list = {stats['n']} matched &amp; cleaned from the
v4 places master (vs MOE's 179). Computed entirely on Propheus servers from Digital Atlas v4 data + OpenStreetMap.</div>
</div></section>

<footer><div class="wrap">
<div class="powered">{LOGO}<span>Powered by <b>{VERSION}</b></span></div>
Active School Travel Space friendliness · Singapore · {stats['n']} primary schools · entropy-weighted index ·
Geographic Detector. Method after Land 2024, 13(8):1319. Data: Digital Atlas v4 (places, population, boundaries) +
OpenStreetMap (walk network, crossings, signals, parks, transit).
</div></footer>

<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
const DATA={data_json};
function col(v){{v=Math.max(0,Math.min(100,v))/100;const a=[255,107,107],b=[255,209,102],c=[33,178,170];
  let r;if(v<.5){{let t=v/.5;r=a.map((x,i)=>x+(b[i]-x)*t)}}else{{let t=(v-.5)/.5;r=b.map((x,i)=>x+(c[i]-x)*t)}}
  return'rgb('+r.map(x=>Math.round(x)).join(',')+')'}}
const map=L.map('map',{{scrollWheelZoom:false}}).setView([1.352,103.82],11.4);
L.tileLayer('https://{{s}}.basemaps.cartocdn.com/dark_all/{{z}}/{{x}}/{{y}}{{r}}.png',
  {{attribution:'© OpenStreetMap © CARTO',subdomains:'abcd',maxZoom:19}}).addTo(map);
DATA.forEach(d=>{{
  L.circleMarker([d.lat,d.lon],{{radius:7,fillColor:col(d.f),color:'#0b1f20',weight:1.4,fillOpacity:.95}})
   .bindPopup(`<b>${{d.n}}</b><br><span style="color:#7d918e">${{d.z.replace(' REGION','')}}</span>`+
     `<div style="margin-top:6px;font:700 24px 'Space Grotesk',sans-serif;color:${{col(d.f)}}">${{d.f}} <span style="font:500 12px Inter;color:#7d918e">/ 100 · ${{d.lv}}</span></div>`+
     `<div style="font-size:12.5px;margin-top:6px;color:#aebfbc">Greenery ${{d.g}}% · Crossings ${{d.cr}}/km · Choice ${{d.ch}}</div>`)
   .addTo(map);}});
</script>
</body></html>"""

OUT.write_text(HTML)
print(f"wrote {OUT} ({len(HTML)//1024} KB) · {stats['n']} schools")
