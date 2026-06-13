# The Digital Atlas Use-Case Diary

*What the embeddings are, why contrastive training matters, and the many ways
to actually use this thing — written for anyone, 2026-06-12.*

---

## Part 0 — One idea underneath everything

The Digital Atlas measures Singapore exhaustively: 801 measurements for every
neighbourhood hex, 190,591 places each with its own micro-world. But raw
measurements answer narrow questions. The unlock is turning each unit — a
neighbourhood, a venue — into a **fingerprint**: a short list of numbers where
**distance means functional similarity**.

Two fingerprints exist today, both validated before shipping:

| | **plexis-e1** (neighbourhoods) | **plexis-p1** (places) |
|---|---|---|
| Unit | 1,191 hex8 cells (~0.7 km²) | 190,591 venues |
| Size | 256 numbers | 64 numbers |
| Built from | all 801 atlas measurements | what it is + its micrograph + its context |
| Deliberately excludes | — | star ratings, reviews, popularity (audited: R²=0.09) |
| Exam | 13-check locked harness | 9/9, incl. hidden-sibling test 81% |

### What "contrastive training" is, in one paragraph

Nobody told the network what "similar" means. It learned by playing a matching
game millions of times: *recognise yourself* (two distorted copies of the same
unit must match), *recognise your siblings* (two outlets of the same chain —
or two corrupted views of the same hex — must land together), *agree with your
context* (a place's fingerprint must match a second network's reading of its
surroundings). Lookalike decoys — same category, different world — make the
game hard enough that "all cafes are alike" is a losing strategy. What
survives is a geometry where **closeness = plays the same role in the city**.

And the honesty rule that makes everything below trustworthy: the exams were
locked *before* training, the models shipped only on passing, and similarity
is provably **not** geography (distance-leak ρ = 0.08) and **not** popularity.

---

## Part 1 — Diary at the NEIGHBOURHOOD level (hex8, plexis-e1)

### Entry 1 · "Pilot here, roll out there" — the policy planner
You're trialling a new active-mobility scheme in Toa Payoh Central. Where will
the results transfer? Ask for its twins: Tiong Bahru Station, Townsville,
Upper Paya Lebar, Bendemeer, Bishan East — places with the same density, the
same MRT footfall, the same street-business intensity. **A pilot's findings
travel along embedding distance, not along the MRT line.** The twins ARE your
rollout list, and the "why" panel in SG Pulse shows the shared traits in plain
language.

### Entry 2 · "Is this rent fair?" — the benchmark
Any number attached to a hex — rent, business mortality, capture potential —
becomes more meaningful next to its twins. A hex whose rent sits 30% above
its five functional twins is expensive *for what it is*; the same rent in a
one-off hex is just... its price. Twin-relative comparison removes the
apples-to-oranges problem that plagues every district-level league table.

### Entry 3 · "What's missing here?" — gap detection by expectation
If a hex is functionally identical to five others and four of them support a
supermarket, a clinic, and three enrichment centres — and this one doesn't —
that's not trivia, that's a shortlist. The embedding supplies the *expected*
amenity profile; the gap between expected and actual is an opportunity map
nobody can compute from category counts alone.

### Entry 4 · "What is Tengah becoming?" — new-town trajectory
A growing estate moves through embedding space year by year. Re-embed with
updated data and watch which existing fabric Tengah drifts toward — Punggol's?
Sengkang's? That tells you which town's amenity timeline, school pressure, and
commercial mix to expect, with a decade of real history as the forecast.

### Entry 5 · The quiet workhorse — features for any model
Downstream models stop needing 801 columns: the 256-number fingerprint carries
the city's structure (held-out housing-price probe R² = 0.81). Every future
model in the shop — demand, risk, accessibility — starts 256 columns rich.
Rule: **use the vectors RAW; never re-standardise per-dimension** (we have the
scar tissue to prove it).

---

## Part 2 — Diary at the PLACE level (plexis-p1)

### Entry 6 · "Find me twenty more like this one" — the expansion scout
Your best-performing outlet is a kopi bakery in a podium mall. Its 12 nearest
fingerprints are the same *kind* of venue across the whole island — when we
queried Tiong Bahru Bakery, the siblings were other TBB outlets **and
PrimaDéli branches** the model was never told about. The expansion shortlist
writes itself, and it's ranked by structure, not by someone's star ratings.

### Entry 7 · Brand siting DNA — "where does our next outlet go?"
Average the context fingerprints of a chain's existing outlets and you get its
**siting DNA** — the kind of corner it thrives on, as a vector. Score every
hex against that DNA and the top of the list is the next-outlet ghost map.
This composes with the Huff capture layer: **capture says how MUCH demand is
winnable; the embedding says what KIND of operator wins it.**

### Entry 8 · "What should go into this empty unit?" — the landlord's question
Run the context tower on a vacant corner: which place-archetypes sit in
contexts like this elsewhere — and survive? "This corner wants a clinic, a
tuition centre, a minimart" is a defensible answer with lookalike corners as
evidence, not a hunch.

### Entry 9 · The misfit detector — risk before it happens
A place whose own fingerprint sits far from what its context predicts is a
misfit — sometimes a genius contrarian bet, more often a tenant in the wrong
spot. Cross-referenced with the atlas's ACRA mortality layer (which already
names death-zone drivers: thin footfall, rent pressure, crowded trade), misfit
distance becomes an early-warning score for lenders, landlords and the
operators themselves.

### Entry 10 · Seeing the market's real segments — the galaxy
Categories lie: "cafe" contains kopitiams, specialty roasters and mall chains
that share nothing but a word. The UMAP galaxy (Places Constellation) shows
the **actual** functional segments — 48 named clusters like "shopping retail ·
Orchard" and "industrial canteens" — so market sizing, competitor sets and
white-space analysis happen on real structure. The colour toggle is the proof:
paint by geography and the rainbow stays mixed.

---

## Part 3 — The two levels together

The place model literally contains the hex model (its context tower reads the
frozen hex-e1 vector), so the levels compose cleanly:

- **Zoom out**: place misfits aggregate into hex-level fragility scores.
- **Zoom in**: a hex twin-pair disagreement ("alike except retail mix") is
  explained by listing which *place clusters* one has and the other lacks.
- **Full pipeline for a site decision**: hex twins (is this location the kind
  of place where this works?) → capture (how much demand is winnable?) →
  place siblings (who exactly will I be? who are my real competitors?) →
  misfit check (does anything about this pairing look wrong?).

## Part 4 — Where to touch all of this today

| Want to… | Go to |
|---|---|
| Click a neighbourhood, see twins + why | SG Pulse → Twins tab (azold:16095) |
| Fly the place galaxy, walk sibling graphs | Places Constellation (azold:16096) |
| Join fingerprints to your own data | `hex/hex8_embedding_plexis_e1_256d.parquet` · `places/place_embedding_plexis_p1_64d.parquet` |
| Read the proofs | `EMBEDDING_V5_DESIGN.md` + `embedding/PLEXIS_E1_REPORT.md` · `PLACE_EMBEDDING_DESIGN.md` + `embedding_place/PLEXIS_P1_REPORT.md` |
| Everything else the atlas measures | `ATLAS_V5_REPORT.html` · `NEW_METRICS_SUMMARY.md` |

### Not yet built, already possible
Brand-DNA ghost maps and Cast-this-corner (the trained context tower is saved);
quarterly re-embeds for drift detection ("which neighbourhoods changed role
this year?"); embedding-grounded answers in the Plexis-Mind chat; a "find my
twin" API for external partners.

---

*Every claim above traces to a validated artifact: 64/64 atlas gates, 13-check
e1 harness, 9/9 p1 exam — all locked before the things they test were built.*
