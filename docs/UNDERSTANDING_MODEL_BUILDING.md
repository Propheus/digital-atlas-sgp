# Understanding Model Building — the plain-English version

*How the Digital Atlas embeddings were built and proven, with zero jargon.
Saved 2026-06-13. The technical versions live in `EMBEDDING_V5_DESIGN.md`,
`PLACE_EMBEDDING_DESIGN.md` and the two training reports.*

---

## "Exam first" — the locked exam

Normally when people train an AI model, they train it first, then look around
for ways to show it works. The danger is obvious: you unconsciously pick the
tests your model happens to pass — like a student writing the exam questions
*after* seeing their own answers.

We did the opposite. **Before training anything**, we wrote down the full
list of tests and pass marks — "it must find hidden chain outlets 70% of the
time", "retrain it three times and it must come out 95% the same" — and froze
that list. Then training happened, and the model shipped only because it
passed every test on the pre-written list.

The proof it isn't theatre: for the neighbourhood model, the version with the
*best scores* failed one of the locked tests — it quietly pulled opposite
districts (Tuas and Orchard) closer together — and we threw it away and
shipped a different one. **The exam decided, not us.**

## The "forbidden probe" — a test the model must FAIL

One of the pre-written tests is unusual: the model has to fail it on purpose.

The rule was: no star ratings, no review counts — a place's fingerprint should
describe what a place **is**, not how popular it is. We excluded all of that
from the inputs. But how do you know popularity didn't sneak in through a back
door (popular places might leave subtle traces in the other data)?

You check by trying to cheat: take the finished fingerprints and try as hard
as possible to predict each place's star rating from them.

- If you **can** → popularity leaked in. Fail.
- If you **can't** → the rule held. Pass.

We tried, and it fails badly — almost nothing about ratings can be recovered.
That deliberate failure is the proof the no-rating promise is real, not just
a claim in a slide.

## The "chain-sibling test" — a fair test nobody can argue with

During training we hid 20% of every chain's outlets from the model. Afterwards
we asked: given one hidden McDonald's, can you find another McDonald's among
all 190,591 places, using nothing but structure? It can — **81% of the time**.
It's fair because the model was never told those outlets were related; it had
to learn what "the same kind of place" means well enough to rediscover them.

## Two more words you'll hear

- **Baselines** — running other people's published methods on our data, so
  "ours works better" comes with numbers attached, not vibes.
- **Ablations** — removing one ingredient at a time (say, the chain-matching
  trick) and re-running the exam, to show every ingredient earns its place.

---

## The whole philosophy in one line

**Write the test before the student studies, include one question they must
get wrong on purpose, and let the marks decide.** Everything else is
logistics.
