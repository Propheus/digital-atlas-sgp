# LLM MoE Spatial Expert — Ideation
## Teaching an LLM to reason about Singapore's urban fabric

**Date:** 2026-04-20  
**Status:** Ideation — no code, pure architecture thinking  
**Depends on:** SGP Digital Atlas (1,794 features across 183K entities)  
**Goal:** A Mixture-of-Experts adapter that activates for spatial-commercial questions about Singapore, giving any base LLM the reasoning depth of a commercial real estate analyst who's memorized the entire atlas.

---

## 1. The Core Idea

We have 1,794 structured features across 183,000+ entities (7,318 hex-9 + 1,191 hex-8 + 326 subzones + 174,711 places). An LLM can't consume parquet files. But if we convert each entity into natural language answering two questions:

- **"What am I?"** — the entity's identity, character, and metrics
- **"Where am I?"** — its spatial context, neighbors, flows, and position

...we create a training corpus that teaches a model to *reason spatially*, not just retrieve data.

**This is not RAG.** RAG gives the model data at query time. This bakes spatial intuition into the model's weights. The model learns what "Dense HDB with high pull_office and low saturation_cafe" *means* — it doesn't need to look it up.

---

## 2. Why This Is Better Than RAG

| Approach | What it does | Limitation |
|---|---|---|
| **RAG** | Retrieves features at query time, asks LLM to interpret | LLM doesn't understand spatial semantics; treats features as arbitrary numbers |
| **Merlion (agent)** | Routes NL → use case → model → result | Brittle routing; can't handle open-ended spatial reasoning |
| **This (MoE fine-tune)** | Model has internalized spatial-commercial reasoning | Needs periodic retraining; can hallucinate plausible-sounding but wrong spatial claims |

The key difference: RAG gives the model data. Training gives the model **intuition**. After training, the model knows that a hex with `net_demand_flow = +0.85` is a captive residential market without needing to look up what that number means.

---

## 3. "What Am I / Where Am I" at Each Level

### Subzone (326 entities)

**What am I:**
> "Toa Payoh Central is a mature HDB estate in the Central Region with 27,340 residents, 23% elderly, high transit connectivity (2 MRT stations, 184K daily taps), 1,573 commercial places dominated by services and beauty, with walkability in the 96th percentile. Ecosystem completeness is 86% — has food, health, transit, convenience but no parks. HDB median PSF is $658, indicating a mid-premium estate."

**Where am I:**
> "Toa Payoh Central sits between Novena (medical hub) to the south and Bishan (residential) to the north. 4.2km from CBD, served by NSL. Gradient position +1.3 (commercial centre of its neighborhood), interface score 0.16 (homogeneous residential), net demand flow +0.75 (strong residential inflow). Neighbors: Toa Payoh West (similar HDB), Bidadari (new development), Braddell (suburban)."

### Hex-8 (1,191 entities)

**What am I:**
> "This hex-8 in Sengkang Town Centre is a Dense HDB archetype — the highest population hex in Singapore (42,312 residents) with 134 HDB blocks averaging 6.8 floors. Vitality index 0.15, accessibility 0.72. FnB is severely undersupplied (saturation 0.18, gap +200 places). Nightlight radiance 45 nW, growing 8% since 2022. Self-containment 0.75."

**Where am I:**
> "Surrounded by Dense HDB hexes (Rivervale, Fernvale) with similar density. Pull_residential is P100 (highest in Singapore). 2 MRT stations, bus headway 28min. Net demand flow +0.85 — massive captive residential demand flowing inward. This is the definition of a captive market for retail."

### Hex-9 (7,318 entities)

Finer grain — a single building cluster. "What am I" describes ~24 places and ~50 buildings in a 174m cell. "Where am I" describes micrograph context vectors, transit accessibility, specific station proximity, density band.

### Place (174,711 entities)

**What am I:**
> "Starbucks at 1 Raffles Place (Cafe & Coffee, premium tier, branded). 15 competitors within 200m, complementary diversity 22/24. Anchor score 0.78 (near MRT + hotels + offices). Synergy_cafe_office fires at P98 — value comes from office worker demand. Survivability 0.03 — heavily saturated market but survives on demand volume."

**Where am I:**
> "CBD core (Downtown Core), archetype Tourist/Commercial. Population 1,940 residents but 7,332 total (74% non-resident workers). Daytime intensity 3.8x. Idx_vitality 0.85, idx_competition 0.95. Saturated for cafes (5.0x) but demand-match is 0.82 — the demand justifies the supply."

---

## 4. MoE Architecture

```
User query: "Is Bukit Timah a good area for a new gym?"
     │
     ▼
┌──────────────────────────┐
│  ROUTER (lightweight)    │  Binary: spatial-SGP question? yes/no
│  Haiku / small classifier │  Triggers on: SGP place names, site selection,
│                          │  transport, competition, demand questions
└───────────┬──────────────┘
            │ yes
            ▼
┌──────────────────────────────────────────────────┐
│  SGP SPATIAL EXPERT (LoRA adapter)               │
│                                                  │
│  Base: Sonnet or Haiku                           │
│  Adapter: trained on 263K "what am I/where am I" │
│  documents + comparisons + QA + reasoning chains │
│                                                  │
│  Knows: archetypes, demand pull, saturation,     │
│  synergies, walkability, ecosystem, competition, │
│  temporal patterns, demographic segments         │
└───────────┬──────────────────────────────────────┘
            │
            ▼
"Bukit Timah is a Suburban Private archetype with 8,200 
residents, 26% elderly (P95). Pull_residential is strong 
(P85) but the high elderly % suggests wellness/rehab demand, 
not competitive gym demand. Saturation_fitness is 1.8 
(slightly oversupplied for generic gyms). The tuition belt 
(13 education places) means parent traffic — morning yoga/
pilates captures an underserved segment. Network walk to 
MRT is 2,188m so customers drive — parking matters more 
than transit access."
```

### Router design

**Positive triggers** (route to SGP expert):
- Singapore place names (Toa Payoh, Orchard, Jurong, Tampines...)
- Site selection / location analysis questions
- Transport / walkability / accessibility for SGP
- Commercial viability / competition / market gap questions
- Population / demographics for SGP areas
- "Where should I..." questions about SGP businesses

**Negative** (pass to base model):
- General Singapore questions (history, politics, culture)
- Other countries
- Non-spatial business questions (pricing, marketing, HR)
- Code / technical questions

**Router training:** ~5K labeled examples, simple binary classification. Can be a Haiku prompt or a small fine-tuned classifier.

---

## 5. Training Corpus Design

### Document Type 1: Entity Profiles (~183K documents)

Template-generated but with enough variation that the model learns patterns, not templates. Each entity gets a structured narrative.

```
[ENTITY: hex-8 | ID: 886520ca17fffff]
[ARCHETYPE: Dense HDB | REGION: West | PA: Jurong West]
[POPULATION: 42,391 residents | 48,363 total | 15% elderly | 13% children]

[WHAT AM I]
This is a Dense HDB neighborhood in Jurong West Central — one of the 
highest-population hexes in Singapore. 135 HDB blocks with average 
8.2 floors create a wall of residential density. The estate has strong 
self-containment (0.75) with a hawker centre, supermarket, and clinics 
present. Transit is served by 1 MRT station and 21 bus stops, though 
GTFS headway is 28 minutes (moderate). The commercial mix is dominated 
by education (31 places) and convenience (18), reflecting the family-
heavy population (13% children). FnB is severely undersupplied — 
saturation at 0.18 means the hex needs approximately 200 more food 
outlets to match Singapore norms. HDB median PSF is $520/sqft 
(mid-market). Nightlights grew 5% from 2022-2024, indicating stable 
commercial activity.

[WHERE AM I]
In western Singapore, 15km from CBD. Surrounded by similar Dense HDB 
hexes (Taman Jurong, Boon Lay). Pull_residential is P99 — nearly 
the strongest residential demand signal in the country. Pull_transit 
is P99 (Jurong East interchange nearby). Pull_office is P87 (Jurong 
Lake District emerging). Net demand flow is +0.75 — overwhelmingly 
a residential demand source. Interface score is 0.16 (internally 
homogeneous — all HDB). The commercial gap here is structural: 
population grew faster than commercial development.

[KEY METRICS]
population=42,391 | pop_total=48,363 | pct_elderly=0.149 | 
hdb_blocks=135 | pc_total=211 | saturation_fnb=0.18 | gap_fnb=+200 |
ecosystem=0.86 | transit_taps=95,376 | gtfs_headway=28min |
pull_residential=P99 | pull_transit=P99 | archetype=Dense_HDB |
nl_2024=38.5 | idx_vitality=0.12 | idx_demand=0.45
```

### Document Type 2: Comparative Pairs (~50K documents)

Teaches relative reasoning.

```
[COMPARE: Sengkang Town Centre vs Raffles Place CBD]

These two hexes represent opposite ends of Singapore's urban spectrum.

POPULATION: Sengkang has 42K residents (P100), Raffles Place has 158 
(P35). But Raffles Place's total population (including workers) is 
7,332 — a 46x daytime amplification.

COMMERCIAL: Sengkang has 312 places serving 42K people (7.4 per 1000). 
Raffles Place has 3,686 places serving 7K (526 per 1000). Completely 
different commercial economics.

DEMAND: Sengkang's demand is captive residential (net_demand_flow 
+0.85). Raffles Place's demand is commercial inflow (-0.43). A cafe 
in Sengkang serves breakfast-to-dinner to the same residents. A cafe 
in Raffles Place serves 8am-6pm to rotating office workers.

SATURATION: Sengkang FnB saturation is 0.18 (needs 200 more outlets). 
Raffles Place is 5.0 (maximum oversupply). Yet Raffles Place cafes 
survive because demand volume is enormous despite saturation.

IMPLICATION: Opening in Sengkang = low competition, captive demand, 
but price-sensitive (HDB population). Opening in Raffles Place = 
intense competition, premium pricing possible, but differentiation 
is the only moat.
```

### Document Type 3: Question-Answer Pairs (~20K documents)

Synthetic QA teaching the model to answer spatial-commercial questions.

```
Q: Where are the best locations for a new hawker centre in Singapore?

A: I'd identify hexes with: high population (>20K), zero hawker_centres, 
long walk_hawker distance (>1.5km), and high pull_residential. 
The top candidates:

1. Woodlands East (40K pop, 0 hawkers, walk_hawker 2.1km, Dense HDB)
   — largest gap, most affected residents
2. Punggol Field (38K pop, 0 hawkers, walk_hawker 1.8km, new town)
   — fast-growing, infrastructure catching up
3. Fernvale (37K pop, 0 hawkers, ecosystem 0.71 — food is the missing piece)

All are Dense HDB new towns where population growth outpaced food 
infrastructure. The common pattern: BTO developments delivered 
thousands of units, but hawker centres (which take 3-5 years to plan 
and build) haven't followed.

Note: Jurong West Central also has gap_fnb = +200 but already has 
1 hawker centre — the gap there is restaurant/cafe, not hawker.
```

### Document Type 4: Reasoning Chains (~10K documents)

Step-by-step spatial reasoning teaching the model HOW to think.

```
[REASONING: Should I open a premium restaurant in Tuas?]

Step 1: POPULATION CHECK
→ Tuas Bay: 0 residents, 13,110 total (100% non-resident workers)
→ Workers are present only during business hours

Step 2: DEMAND TYPE
→ pull_office = P90 (strong business activity)  
→ pull_residential = P51 (no residential demand)
→ This is a purely daytime, worker-driven market

Step 3: PRICE FIT
→ Workers are industrial/blue-collar (bldg_industrial = 126)
→ No HDB PSF data (no housing here)
→ Price sensitivity is HIGH — these workers eat $5-8 meals

Step 4: TEMPORAL
→ daytime_intensity = 100x
→ Demand exists ONLY 7am-6pm weekdays
→ Zero weekend/evening traffic

Step 5: COMPETITION
→ saturation_fnb = 0.19 (severely undersupplied!)
→ Only 46 restaurants for 13K workers
→ HUGE gap — but for budget food, not premium

Step 6: CONCLUSION
→ A BUDGET restaurant (economy rice, mixed veg, $5 sets) = YES
→ A PREMIUM restaurant = NO (wrong price tier for the audience)
→ The gap is real. The opportunity is real. But the format must 
  match the customer: industrial workers need fast, cheap, filling.
```

---

## 6. Corpus Statistics

| Type | Documents | Avg tokens | Total tokens |
|---|---|---|---|
| Entity profiles | ~183,000 | ~500 | ~91M |
| Comparative pairs | ~50,000 | ~400 | ~20M |
| QA pairs | ~20,000 | ~300 | ~6M |
| Reasoning chains | ~10,000 | ~600 | ~6M |
| **Total** | **~263,000** | **~470 avg** | **~123M tokens** |

This is a solid fine-tuning corpus — large enough to generalize, not so large that it becomes noise.

---

## 7. What the Model Learns

### Spatial vocabulary
- `pull_office = P95` means "very strong office worker demand nearby"
- `saturation_fnb = 0.18` means "severely undersupplied for food"
- `net_demand_flow = +0.85` means "residential captive market"
- `archetype = Dense HDB` means "high-rise public housing, family-heavy, price-sensitive"
- `interface_score = 0.6` means "sharp land-use transition — mixed-use edge"
- `gradient_position = -0.5` means "edge of commercial cluster, not centre"

### Reasoning patterns
- "High population + low places = opportunity (but check price sensitivity)"
- "Saturation > 2 doesn't mean no opportunity — if demand_match > 0.7, volume justifies entry"
- "Near-MRT matters for impulse categories (cafe, convenience) but not for destination categories (gym, tuition)"
- "Elderly % > 20% shifts demand: less nightlife, more health, more daytime F&B"
- "Industrial zone = zero residents ≠ zero demand; use population_total not population"

### Geographic knowledge
- Spatial relationships between areas (Toa Payoh is north of Novena, south of Bishan)
- What each archetype "feels like" (Dense HDB = uniform towers, Suburban Private = landed houses)
- How transit connectivity shapes commercial viability
- Where Singapore is growing vs mature vs declining

---

## 8. Evaluation Framework

### Held-out test set
- 500 entities (125 per level) withheld from training
- Test: "Describe this hex" → check factual accuracy against actual features
- Test: "Where should I open X?" → verify the recommended hexes actually have the claimed properties
- Test: "Compare A vs B" → check relative rankings match data

### Benchmark questions (50)
Hand-curated questions with ground-truth answers from the atlas:
- "Which planning area has the most elderly residents?" (Bedok)
- "What's the transit headway in Tuas?" (60 min — effectively no service)
- "Is Orchard Road oversaturated for restaurants?" (Yes, saturation 5.0)
- "Where is nightlight growth highest?" (hexes with nl_growth_corridor = 1)

### Hallucination detection
Compare model output against actual atlas values. Flag when:
- Model claims a metric value that's >20% different from actual
- Model assigns wrong archetype to a known area
- Model recommends a location that doesn't meet its own stated criteria

---

## 9. Technical Implementation Path

### Phase 1: Corpus generation (1-2 days)
- Template engine that converts each entity's features into natural language
- Variability: randomize sentence structure, metric ordering, emphasis
- Quality: spot-check 50 random outputs against actual data

### Phase 2: QA + reasoning synthesis (2-3 days)
- Use Claude to generate QA pairs from the atlas features
- Prompt: "Given this hex's features, generate 3 plausible questions a real estate analyst would ask and answer them using the data"
- Human review 100 samples for quality

### Phase 3: Router training (0.5 day)
- 5K examples of "spatial-SGP question" vs "other"
- Fine-tune a small classifier or write a prompt for Haiku

### Phase 4: Expert fine-tuning (1-2 days)
- LoRA adapter on Haiku or Sonnet
- 263K documents, ~123M tokens
- Evaluate on held-out set

### Phase 5: Integration (1 day)
- Wire router + expert into existing Merlion stack
- OR: standalone API that wraps the MoE

---

## 10. The Hybrid: MoE + Atlas API

The strongest architecture isn't pure MoE or pure RAG — it's both:

```
User query
    │
    ▼
[Router] → SGP spatial? → [MoE Expert generates reasoning]
                                    │
                                    ▼
                          [Atlas API verifies numbers]
                                    │
                                    ▼
                          [Final response with verified data]
```

The MoE provides the **reasoning framework** ("check saturation, then demand-match, then price fit").
The Atlas API provides the **ground truth** ("saturation_fnb for this hex is actually 0.23").

The MoE can hallucinate specific numbers. The API can't reason. Together they produce accurate, reasoned responses.

---

## 11. What This Enables (End State)

A user asks: *"I have $500K to open a bubble tea shop. Where in Singapore should I go?"*

The MoE expert responds (internally reasoning through):
1. Category: Cafe & Coffee / Bubble Tea → demand_match links to pull_transit + pull_residential
2. Budget $500K → rules out CBD (rent too high); targets HDB town centres
3. Checks saturation_cafe across all hex-8 cells with population > 20K
4. Finds undersupplied hexes with high pull_transit (near MRT exits where youth traffic concentrates)
5. Cross-checks: which of these have low competitors_200m for same category?
6. Verifies: GTFS headway < 15min (good frequency = steady foot traffic)
7. Outputs top 3 locations with reasoning for each

This is the spatial reasoning that currently requires a human analyst with a GIS tool, a spreadsheet, and domain knowledge. The MoE makes it conversational.

---

## 12. Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Hallucination of specific numbers | User acts on wrong data | Always verify with Atlas API before surfacing to user |
| Overfitting to training templates | Responses sound templated | Vary templates; include free-form reasoning chains |
| Stale knowledge after atlas update | Recommendations based on old data | Quarterly retraining; or hybrid with RAG for current numbers |
| Router misclassification | Non-spatial queries go to expert (weird outputs) | Conservative router; high-confidence threshold |
| Model memorizes entities not patterns | Can't generalize to new development areas | Include synthetic "new area" examples in training |
| Cost of fine-tuning | LoRA on Haiku should be ~$50-100 | Small investment relative to value |

---

## 13. Comparison to Existing Approaches

| System | Spatial knowledge | Reasoning | Real-time | Cost |
|---|---|---|---|---|
| Google Maps / OneMap | High (visual) | None | Yes | Free |
| Commercial GIS (ArcGIS, QGIS) | High (query) | None (user supplies) | Yes | High |
| ChatGPT with RAG | Low (retrieved) | Good (general) | Yes | Medium |
| Merlion (current) | Structured (routed) | Rule-based | Yes | Low |
| **This MoE** | **Internalized** | **Spatial-specific** | **Near-real-time** | **Low** |

The MoE is the only approach that combines *deep spatial knowledge* with *domain-specific reasoning* in a conversational interface.

---

## 14. Open Questions

1. **Base model size** — Is Haiku sufficient for the expert, or does spatial reasoning need Sonnet's capacity?
2. **Training data quality vs quantity** — Would 50K high-quality documents outperform 263K template-generated ones?
3. **Multi-city extension** — If we build the same for HKG (already have 1,371 features), can one MoE serve both? Or separate experts per city?
4. **Temporal reasoning** — Can the model learn to reason about change over time (nl_growth, wp_pop_growth) meaningfully?
5. **User intent classification** — Some questions need precise numbers (→ API). Some need reasoning (→ MoE). Can the router distinguish?
6. **Competitive moat** — If we publish the corpus, anyone can replicate. The moat is the atlas quality + continuous updating + domain expertise in corpus design.

---

## 15. Why Now

- The atlas is complete: 1,794 features, 4 levels, validated, consistent
- LoRA fine-tuning is cheap ($50-100)
- Claude/OpenAI APIs support MoE-style routing natively
- The commercial real estate / site selection market has no equivalent product
- Singapore is small enough (1,191 hex-8 cells) that the model can memorize geography without needing massive parameters

**The atlas data is the moat. The MoE is the interface. Together they create a product no one else can replicate — because no one else has built the underlying feature stack.**

---

*Ideation v1 — 2026-04-20*  
*Next steps: corpus generation experiment (1K entities), evaluate if model picks up spatial grammar*
