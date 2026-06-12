# SG Pulse — Digital Atlas Showcase App (Spec v0)

**Date:** 2026-06-10 · **Status:** Concept locked, outline approved-pending
**Working name:** **SG Pulse** (alt: xPlorer, CityLens SG, Atlas One) — "SG Pulse,
powered by the Plexis Atlas" (the engine keeps the technical brand).
**Audience:** urban planners, government, investors, managers — NOT technical.
**Nature:** fully static demo app. No backend, no live model calls. Every number,
answer and animation precomputed from the v5 atlas
(`azold-test-server:/home/azureuser/da-sgp/v5/`, hex8 grain only — hex9 is internal).

## Design principles (non-negotiable)

1. **Answers, not layers.** No column names anywhere. Questions, stories, verdicts.
2. **Verdicts, not numbers.** 🟢🟡🔴 bands with one plain sentence each; numbers are
   the supporting cast (proven pattern from the adequacy app).
3. **Every claim traceable.** Each verdict/story has a "How we know this" expander →
   source dataset + validation result. Gov audiences probe trust first; we uniquely
   have a signed validation log to show.
4. **One launch point.** A single hero screen; everything else is one tap away.
5. **Demo-first.** Built to be presented in 5 minutes and explored in 30.

---

## Information architecture

```
LAUNCH (hero)                       ← the breathing map, title, one CTA
 └─ Tab bar (persistent, 6 tabs)
    1. PULSE      — the living-city animation (also the launch backdrop)
    2. STORIES    — 5 guided scrollytelling tours
    3. ASK        — scripted Q&A (canned questions, typed-out answers)
    4. SITES      — click-anywhere Site Report Card + Compare/Twins
    5. FUTURE     — JRL + development-capacity outlook
    6. EVIDENCE   — paper replications + layer validation (the trust tab)
```

Nav model: tab bar along the top (same pill language as the explorer); stories are
also deep-linkable (`/story/breathing`) so a presenter can jump straight in.
Persona lens (Plan / Invest / Govern) is a small toggle in the header — it only
re-orders story tiles and re-weights report-card emphasis, nothing else.

---

## 1 · PULSE (launch screen)

Full-bleed dark Mapbox. A 24-hour loop morphs hex fill between night population and
daytime population (precomputed keyframes from `pop_resident` ↔ `dt_pop`); CBD
inflates ~20×, Sengkang/Punggol drain. Time-of-day dial sweeps; soft glow accent
(#fcd34d). Title + one line — "Singapore, as a living system. 190,591 places ·
2,485 measurements · every hex validated." Single CTA: **Explore** → reveals tab bar.

Quiet flex at the bottom: counters ticking (places, transit taps, businesses).

## 2 · STORIES (the demo magnet)

Five tiles → each a scroll-driven tour (scroll advances scenes; camera + layers +
copy per scene; "next story" chaining). All camera paths and layer states are
hardcoded JSON — pure playback.

| # | Story | Beats (scenes) | Data binding |
|---|---|---|---|
| 1 | **Singapore breathes** | night map → day map morph → CBD zoom (+87K daytime) → Sengkang drain → "two cities, same map" | dt_pop, dt_net, dt_class |
| 2 | **The 800-metre lie** | perfect circle around a Toa Payoh hex → morph to true walk catchment → PIE slices it → severance ranking flyover | iso_walk10 vs iso_euclid800, severance_ratio |
| 3 | **Where the next supermarket goes** | national capture heat → fly to Yunnan (60K unserved) → punchline: "the model never saw the FairPrice study — and found the same desert" → top-10 sites list | cap_supermarket, unserved pop |
| 4 | **The bus city nobody sees** | rail-distance view (Yishun East looks poor) → flip to 15-min reach (190K!) → interchange constellation | iso_transit15_pop vs dist_mrt |
| 5 | **The city that registers itself** | ACRA layer → Chinatown shophouse registration belt → virtual-office towers called out → mortality heat ("where businesses die") | biz_live_robust, biz_per_address, biz_recent_dead_share |

Each story ends with a verdict card ("So what: …" one-liner per persona) + the
"How we know this" expander.

### Emergence shelf (second story collection)

Stories tab is organized as two shelves: **City Stories** (the 5 above) and
**Emergence** ("nobody designed this — the data found it"):

| # | Story | Core emergent property | Data binding | Punchline |
|---|---|---|---|---|
| E1 | **The city plans itself** | self-organized clustering beyond zoning: bar→bar 3.0, hotel→bar 2.75, industrial→residential 0.50, and cafes DON'T follow offices (0.87) | colo_lift_matrix; fly-to Keong Saik | "Zoning draws the boxes. The city writes its own rules inside them." |
| E2 | **Hungry corners** | demand self-organizes faster than supply: high activity, lagging retail | latent_demand + cap_* naming the prize | "Crowds arrive before commerce. This is the gap — while it's still open." |
| E3 | **The city can't keep secrets** | emergent proxies: condo%→income, gov preschools→private markets, structure→FairPrice desert re-derived | cross-layer reveal carousel | "Measure enough of a city and it starts confessing." |
| E4 | **Gravity has moved** | network topology creates a different centre than the skyline: 45-min labour shed peaks at Little India/Bendemeer (1.9–2.1M), not Raffles; coda: more-trains-more-jam feedback loop | labor_pool_45m, congestion findings | "The CBD is where the money sits. The centre is where the people can get to." |

Evidence-tab crossover: running the Bettencourt urban-scaling replication (ready)
yields a combined emergence-story + replication tile: "Singapore's neighbourhoods
obey the same mathematical law as world cities."

Curation: E1 and E3 are the flagship emergence stories (best visual / best
sales argument); E5 (transit-congestion loop) folded into E4 as a coda.

## 3 · ASK (scripted, looks live)

A chat-style panel with **8 pre-scripted questions as tappable chips** (typing
animation on answers; map reacts). Static = zero risk on stage, and the presenter
can hand the device to the audience to pick a chip.

Canned set (answers precomputed with map states):
1. Where should a clinic chain expand next?
2. Which neighbourhoods are underserved for groceries?
3. Where do I find the biggest lunch crowds without the CBD rents?
4. Which town centres can absorb another gym?
5. Where can workers reach my office within 45 minutes?
6. Which areas are growing fastest right now?
7. Where will the JRL change everything?
8. Is Orchard saturated for cafes? *(answer: yes — p03 capture; here's where isn't)*

Footer note: "Live natural-language Ask is powered by the Plexis-Mind engine —
demo build uses curated answers." Honest, and it plants the roadmap.

## 4 · SITES (the tool they'll reuse)

Click any hex (or search a neighbourhood) → **Site Report Card**, precomputed for
all 1,191 hexes into one JSON:

> **Bedok North** · hex 8865…
> 🟢 **Catchment** — 14,200 people within a 10-min walk; holds steady by day
> 🟡 **Competition** — 3 cafes in reach; room for ~0.8 more outlets
> 🟢 **Footfall** — single-exit MRT, ~28K taps/day past the door
> 🔴 **Cost** — rents in the top quartile for the east
> 🟡 **Outlook** — no new rail coming; modest build-out headroom
> **Verdict: strong for F&B · weak for large-format retail**

Verdict rules (computed at build time, per use-case F&B / retail / clinic / gym /
office):
- Catchment: iso_walk10_pop ≥12K 🟢 · 4–12K 🟡 · <4K 🔴 (office uses labor_pool_45m)
- Competition: cap_{usecase} ≥1.0 🟢 ("supports ~N outlets") · 0.4–1.0 🟡 · <0.4 🔴
- Footfall: vis_exit_footfall + od_throughput percentile bands
- Cost: rent_resi_psf_med percentile (framed "premium / mid / value", not good/bad)
- Outlook: pipe_new_mrt_within_800m OR dev_capacity ≥ p75 🟢; nl decline 🔴
- Risk: biz_recent_dead_share bands
- Overall: rule template per use-case (e.g., F&B = catchment∧footfall weighted)

Two actions: **Compare** (side-by-side vs Toa Payoh Central / Orchard / a second
click) and **Find twins** (top-5 nearest in the normalized feature space —
precomputed neighbor lists). Plus the "How we know this" expander per row.

## 5 · FUTURE

One screen, three toggles: future rail (37 MP19-delta stations pulse on, year
labels), FAR-headroom glow (Matilda/Bidadari/Tengah), night-light growth corridors.
Copy: "Where the next decade lands." Investor-lens default tile order starts here.

## 6 · EVIDENCE (the trust tab — and the differentiator for gov/planners)

Two sections:

**A. Replication Lab — "We test the atlas against published science."**
Tiles per paper: claim → what we ran on Singapore data → result → verdict chip
(✅ Replicated / 🔁 Ready to run / 🧪 In progress).

| Paper / theory | Claim | Atlas test | Status |
|---|---|---|---|
| **Rise of the Creative Class (2022 revisit)** | creative-occupation share predicts economic vitality | persona occupation mix × commercial activity by area | ✅ Replicated |
| **Huff (1963) retail gravity** | store patronage decays with distance, splits by attractiveness | S1 capture model; behavioral validity tested | ✅ Replicated (it IS our S1) |
| **Moreno 15-minute city (2021)** | most needs reachable in 15 min active travel | min15 scores (hex_v11), calibrated Toa Payoh 100 / Lim Chu Kang 13 | ✅ Replicated |
| **Jacobs vitality (Death & Life, quantified à la De Nadai 2016)** | small blocks + mixed use + density → street vitality | road topology × place diversity × footfall | ✅ Replicated (suite) |
| **Active School Travel friendliness (Land 2024, 13(8):1319)** | built environment predicts walk-to-school friendliness | 179 SGP primary schools | 🧪 In progress |
| **MRT capitalization into housing prices** (SG hedonic literature) | rail proximity is priced into homes | 227K HDB resale × dist_mrt hedonic | 🔁 Ready (data in place) |
| **Bettencourt urban scaling (2013)** | amenities scale super-linearly with population | subzone pop vs place counts across 326 subzones | 🔁 Ready |
| **Schläpfer universal visitation law (Nature 2021)** | visits ∝ 1/(distance×frequency)² | LTA OD matrix (hex8×hex8 flows) | 🔁 Ready |
| **Cervero & Kockelman 3Ds (1997)** | density/diversity/design drive ridership | taps vs 3D measures per hex | 🔁 Ready |
| **Alonso bid-rent gradient (1964)** | rents decay from the centre | rent surface vs CBD distance | 🔁 Ready |
| **Night lights ≈ economic activity (Henderson 2012)** | luminosity proxies output | VIIRS vs commercial-activity index | 🔁 Ready |

**B. Validation ledger.** One row per atlas layer: what was checked, the
archetype results (Yunnan p96, Toa Payoh conservation +0.2%, …), link-out to the
full `SITE_SELECTION_VALIDATION.md` rendered as a page. Headline: "50 machine
checks · 10 layers · every gate passed before shipping."

---

## Tech sketch (static = cheap + bulletproof)

- Fork of `explorer-app` (Vite + React + Mapbox GL, same dark theme, #fcd34d
  accents, labels at --t2 — house style rules apply).
- `public/data/`: hex8 geojson (already exists) + `report_cards.json` (1,191
  precomputed cards) + `stories/*.json` (camera/layer/copy scenes) + `ask.json`
  (8 Q&A + map states) + `twins.json` + `evidence.json`.
- One build script in plexis: `build_showcase_data.py` → emits all of the above
  from the v5 masters. No server component; deployable as static files behind
  nginx like the other atlas apps.
- Scroll engine: simple IntersectionObserver per scene (no heavy scrolly lib).

## Build phases

- **v0 (demo-ready):** Launch/Pulse animation · Stories 1+3 · Report card (F&B +
  retail verdicts) · Ask with 4 chips · Evidence tab static table.
- **v1:** remaining stories, Compare/Twins, persona lenses, Future tab polish,
  remaining Ask chips, evidence tiles with mini-charts.
- **v2 (post-demo):** wire Ask to the live Plexis agent; run the 6 "ready"
  replications and flip their chips to ✅.

## The 5-minute demo script

1. Launch → breathing map. Say nothing for 15 seconds.
2. Hand over: "ask it something" → tap a chip.
3. Story 3 (supermarket) → end on the FairPrice punchline.
4. Click the audience member's neighbourhood → report card → Compare vs Orchard.
5. Future tab → JRL lights up → close: "every number you saw is validated —
   that's the Evidence tab."
