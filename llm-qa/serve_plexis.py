#!/usr/bin/env python3
"""
Plexis-Mind inference server — FastAPI, streaming, auto context-injection.

base google/gemma-4-12b-it (4-bit) + LoRA adapter, tokenizer FROM the adapter dir.
Auto-RAG: scan the user message for a known subzone / planning-area, inject a compact
atlas profile as `Context:` -> runs the model in its 88% reason-in-context production mode.

Run:  HF_TOKEN=... python3 serve_plexis.py            # binds 0.0.0.0:8080
Env:  PORT (8080), ADAPTER (/root/plexis-mind-sft-lora), ATLAS (/root/atlas)
"""
import os, json, threading, re
import torch
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
from transformers import (AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig,
                          TextIteratorStreamer)
from peft import PeftModel

BASE    = os.environ.get("BASE", "google/gemma-4-12b-it")
ADAPTER = os.environ.get("ADAPTER", "/root/plexis-mind-sft-lora")
PORT    = int(os.environ.get("PORT", "8080"))

import atlas_tools as A
A.ATLAS = os.environ.get("ATLAS", "/root/atlas")

SYS = (
 "You are Alchemy, a candid, knowledgeable local who really knows Singapore's neighbourhoods.\n\n"
 "WHEN A \"Context:\" BLOCK OF ATLAS FACTS IS PROVIDED, write a genuine, thoughtful assessment of that "
 "area — like a smart friend's honest read, not a brochure or a stat dump:\n"
 "• Open with a clear, opinionated verdict.\n"
 "• Then ANALYSE: weave the Context's figures into what life there is genuinely like — getting around, "
 "food and errands, raising kids or the social scene, the character and feel of the place — and say "
 "what each figure IMPLIES (e.g. a high HDB share points to a down-to-earth heartland; many nearby "
 "schools and hawker stalls mean easy school runs and cheap meals; far from an MRT but bus-rich means "
 "you'll lean on buses). Cite the Context's figures as evidence; don't just list them.\n"
 "• Be balanced about TRADE-OFFS — who it suits, who might not love it. Close with a nuanced bottom line.\n\n"
 "HARD RULES ABOUT NUMBERS (critical):\n"
 "• Use ONLY numbers that literally appear in the Context block. NEVER invent or estimate populations, "
 "counts, percentages, scores or distances, and NEVER make up hypothetical example areas with numbers.\n"
 "• If there is NO Context block (a general or conceptual question), answer QUALITATIVELY and "
 "conceptually — explain the reasoning in words, citing NO specific figures at all.\n"
 "• Walkability and vibrancy are scores from 0 to 1 (e.g. 0.72 is fairly walkable); shares are percentages.\n"
 "• If the atlas doesn't track something (crime, weather, real-time conditions, exact income, future "
 "prices), say so honestly instead of guessing.\n\n"
 "READING THE LOCATION-INTELLIGENCE METRICS (when present):\n"
 "• 'regional draws' (anchor strength) = the DEMAND GENERATOR — how much footfall the area pulls in for that "
 "category. A POSITIVE catchment signal (proven demand), NOT saturation.\n"
 "• 'under-served (gap)' — higher = more unmet provision for that category.\n"
 "• 'provided per 1k' (saturation) high = already well/over-served; 'avg competitors' high = crowded market.\n"
 "• 'accessibility/pull' higher = more central/connected; lower 'walk to MRT' is better.\n"
 "• For an OPPORTUNITY / siting question, reason like an analyst — do NOT recite a formula:\n"
 "   (a) consider only categories RELEVANT to the question (for F&B, ignore non-food gaps like beauty/fitness);\n"
 "   (b) target the LARGEST relevant unmet gap, sanity-checking saturation/competitors so you don't pick a crowded one;\n"
 "   (c) SYNTHESISE with who is actually there — local jobs/workers (wp_pop), demographics, family-index, vibrancy — "
 "to say WHO the customer is and when they show up;\n"
 "   (d) propose a SPECIFIC concept (e.g. 'a grab-and-go bakery-café for the lunchtime office crowd'), not just a "
 "category name. Demand (anchors/footfall) and provision (gap/saturation) are separate axes. It's a reasoned "
 "estimate, not a fact.\n"
 "• 'livability index' and 'family-friendliness index' (0-1) are the atlas's own overall scores — cite them "
 "and explain what's driving them (e.g. walkability + amenities up, density pressure down). Reason ACROSS "
 "layers: connect who lives there (demographics, affluence) with how they move (transit, commute), what's "
 "nearby (places, gaps) and the area's pulse (vibrancy, commercial) into one coherent read.\n\n"
 "Write with VOICE and CHARACTER — like a sharp local friend painting a picture of what daily life there "
 "actually feels like, not a report. Use evocative, specific phrasing (the morning kopi run, grandparents "
 "and toddlers in the void deck, the school-run rhythm) and WEAVE the figures into that story rather than "
 "listing them. Have a point of view. About 2–4 flowing paragraphs — never a spec sheet or a dry stat dump.")

# ---------------------------------------------------------------- model
# Base in bf16 + LoRA adapter, NOT merged — so the adapter is TOGGLEABLE at inference:
#   adapter on               -> Alchemy (fine-tuned)
#   model.disable_adapter()  -> raw base Gemma   (powers the Compare panel)
print("loading tokenizer (from adapter)…", flush=True)
tok = AutoTokenizer.from_pretrained(ADAPTER)
print("loading base bf16 + adapter (sdpa, toggleable)…", flush=True)
model = AutoModelForCausalLM.from_pretrained(BASE, dtype=torch.bfloat16,
        device_map="auto", attn_implementation="sdpa")
model = PeftModel.from_pretrained(model, ADAPTER)
model.eval()
print("model ready (bf16 + sdpa, base+adapter toggleable)", flush=True)

# ---------------------------------------------------------------- context injection
sz, _g = A._load()
# longest-first so "Tampines East" wins over "Tampines"
_SUBZ = sorted(sz.index.tolist(), key=len, reverse=True)
_PAS  = sorted({p for p in sz["pa"].dropna().unique()}, key=len, reverse=True)
print(f"context index: {len(_SUBZ)} subzones, {len(_PAS)} planning areas", flush=True)

def _num(v, nd=0):
    try:
        v = float(v)
        if v != v: return None
        return int(round(v)) if nd == 0 else round(v, nd)
    except Exception:
        return None

def _find_entities(text, limit=2):
    """Find up to `limit` distinct atlas entities mentioned, longest-name-first,
    skipping spans already claimed (so 'Tampines East' beats 'Tampines')."""
    low = text.lower()
    found, claimed = [], []
    def overlaps(s, e):
        return any(not (e <= cs or s >= ce) for cs, ce in claimed)
    for name, scale in [(n, "subzone") for n in _SUBZ] + [(p, "pa") for p in _PAS]:
        m = re.search(r"\b" + re.escape(name.lower()) + r"\b", low)
        if m and not overlaps(m.start(), m.end()):
            found.append((name, scale)); claimed.append((m.start(), m.end()))
            if len(found) >= limit: break
    return found

def _pct(v, nd=0):
    n = _num(v, nd);  return None if n is None else n

# category domains — so an "F&B" question never surfaces a beauty/fitness gap as the opportunity
FOOD_CATS = {"cafe_coffee", "restaurant", "hawker", "fast_food", "bakery", "supermarket"}
DOMAINS = {"food": FOOD_CATS}
def _domain_of(text):
    t = (text or "").lower()
    if any(w in t for w in ("f&b", "f & b", "food", "dining", "restaurant", "cafe", "café", "coffee",
                            "hawker", "bakery", "baker", "fast food", "supermarket", "grocery", "eatery",
                            "eateries", "meal", "brunch", "cuisine", "drink", "snack")):
        return "food"
    return None

def _top_by(r, prefix, suffix, n=3, thresh=None, cats=None):
    """Top-n (category, value) over columns prefix..suffix, desc. `cats`=restrict to these raw categories."""
    items = []
    for c in sz.columns:
        if c.startswith(prefix) and c.endswith(suffix):
            raw = c[len(prefix):len(c) - len(suffix)] if suffix else c[len(prefix):]
            if cats is not None and raw not in cats:
                continue
            v = r[c]
            if v == v and (thresh is None or float(v) >= thresh):
                items.append((raw.replace("_", " "), float(v)))
    items.sort(key=lambda x: -x[1])
    return items[:n]

def _loc_intel(r, domain=None):
    """Compact 'location-intelligence' line. `domain` restricts the gap/saturation list to that
    category family (e.g. an F&B question only sees food gaps, never a beauty gap)."""
    cats = DOMAINS.get(domain)
    dlbl = f" {domain}" if domain else ""
    li = []
    anc = _top_by(r, "mg_", "_anchor_strength", 3)
    if anc: li.append("strongest regional draws: " + ", ".join(f"{c} ({int(v)})" for c, v in anc))
    gap = _top_by(r, "gap_", "", 3, thresh=0.25, cats=cats)
    if gap: li.append(f"most under-served{dlbl} (gap, +1=under-served): " + ", ".join(f"{c} ({v:.2f})" for c, v in gap))
    sat = _top_by(r, "sat_", "_per_1k", 2, cats=cats)
    if sat: li.append("most provided per 1k residents: " + ", ".join(f"{c} ({v:.1f})" for c, v in sat))
    g = lambda c: r[c] if c in sz.columns else None
    pc = _num(g("pull_composite"), 2); dp = _num(g("density_pressure"), 2)
    ci = _num(g("commercial_intensity"), 2); comp = _num(g("mg_avg_competitors_400m"), 0)
    wd = _num(g("mg_avg_walk_dist_mrt_m"), 0)
    extra = []
    if pc is not None: extra.append(f"accessibility/pull {pc}")
    if comp is not None: extra.append(f"avg competitors/400m {comp}")
    if wd is not None: extra.append(f"avg walk to MRT {wd}m")
    if dp is not None: extra.append(f"density-pressure {dp}")
    if ci is not None: extra.append(f"commercial-intensity {ci}")
    if extra: li.append("; ".join(extra))
    return (" Location-intelligence — " + "; ".join(li) + ".") if li else ""

def _subzone_ctx(name, domain=None):
    r = sz.loc[name]
    g = lambda c: r[c] if c in sz.columns else None
    bits = [f"{name} ({g('pa')}, {g('region')})"]
    def add(label, col, nd=0, suffix=""):
        v = _num(g(col), nd)
        if v is not None: bits.append(f"{label} {v}{suffix}")
    def add_share(label, col):  # column already 0-1
        v = g(col)
        p = _pct(None if v is None or v != v else float(v) * 100, 0)
        if p is not None: bits.append(f"{label} {p}%")
    # size & people
    add("population", "pop_resident")
    add("density", "pop_density", suffix="/km²")
    add_share("share of children (0-14)", "child_share")
    add_share("share of elderly (65+)", "elder_share")
    add_share("HDB-housed", "pop_hdb_share")
    # getting around
    add("walkability (0-1)", "walkability_score", 2)
    add("MRT stations", "mrt_station_count")
    add("metres to nearest MRT", "dist_mrt_m")
    add("bus stops", "bus_stop_count")
    add("amenities within 400m walk", "walk_amenities_400m")
    # education
    add("schools", "school_count_total")
    add("primary schools within 1km", "primary_schools_within_1km")
    add("preschools", "preschool_count")
    # food & life
    add("hawker eateries", "pc_cat_hawker")
    add("hawker centres", "hawker_centre_count")
    add("vibrancy (0-1)", "vibrancy_index", 2)
    add("commercial land-use", "lu_commercial_pct", suffix="%")
    add("total places/POIs", "pc_total")
    # cross-layer signals: outcome indices · affluence · transit usage · jobs · land-use mix
    add("livability index (0-1)", "livability_index", 2)
    add("family-friendliness index (0-1)", "family_index", 2)
    add("transit score (0-1)", "max_transit_score", 2)
    add("daily bus taps", "daily_bus_taps")
    add("local jobs (workplace pop)", "wp_pop")
    add("land-use diversity (0-1 entropy)", "lu_entropy", 2)
    rps = _num(g("hdb_resale_median_psm"))
    if rps: bits.append(f"HDB resale median ~${rps:,}/m²")
    dom = g("pc2_dominant_category")
    if isinstance(dom, str) and dom not in ("", "other", "nan"):
        bits.append(f"dominant place type {dom.replace('_',' ')}")
    ctx = "; ".join(str(b) for b in bits) + "."
    # weekday OD top destinations
    try:
        o = A.od(name, "top_dest", 3)
        d = o.get("top_destinations") or []
        if d:
            ctx += " Top weekday commuter destinations: " + ", ".join(
                f"{x['dest']} ({x['trips']:,})" for x in d) + "."
        sc = A.od(name, "self_containment").get("self_containment_pct")
        if sc is not None: ctx += f" Self-containment {sc}%."
    except Exception:
        pass
    try:
        ctx += _loc_intel(r, domain)
    except Exception as e:
        print("loc_intel err", e, flush=True)
    return ctx

def _pa_loc_intel(sub, domain=None):
    """Aggregated demand-supply intelligence for a planning area (mean over its subzones)."""
    cats = DOMAINS.get(domain); dlbl = f" {domain}" if domain else ""
    def aggtop(prefix, suffix, n, thresh=None, allow=None):
        items = []
        for c in sz.columns:
            if c.startswith(prefix) and c.endswith(suffix):
                raw = c[len(prefix):len(c) - len(suffix)] if suffix else c[len(prefix):]
                if allow is not None and raw not in allow: continue
                v = sub[c].mean()
                if v == v and (thresh is None or float(v) >= thresh):
                    items.append((raw.replace("_", " "), float(v)))
        items.sort(key=lambda x: -x[1]); return items[:n]
    li = []
    anc = aggtop("mg_", "_anchor_strength", 3)
    if anc: li.append("strongest demand generators (anchor): " + ", ".join(f"{c} ({int(v)})" for c, v in anc))
    gap = aggtop("gap_", "", 3, thresh=0.2, allow=cats)
    if gap: li.append(f"most under-served{dlbl} (avg gap, +1=under-served): " + ", ".join(f"{c} ({v:.2f})" for c, v in gap))
    sat = aggtop("sat_", "_per_1k", 2, allow=cats)
    if sat: li.append("most provided per 1k: " + ", ".join(f"{c} ({v:.1f})" for c, v in sat))
    if "mg_avg_competitors_400m" in sz.columns:
        comp = _num(sub["mg_avg_competitors_400m"].mean())
        if comp is not None: li.append(f"avg competitors/400m {comp}")
    return (" Location-intelligence (planning-area average) — " + "; ".join(li) + ".") if li else ""

def _pa_ctx(pa, domain=None):
    sub = sz[sz["pa"] == pa]
    if not len(sub): return None
    region = sub.iloc[0]["region"]
    bits = [f"{pa} planning area ({region}); {len(sub)} subzones"]
    def addsum(label, col, suffix=""):
        if col in sz.columns:
            v = _num(sub[col].sum())
            if v is not None: bits.append(f"{label} {v}{suffix}")
    def addmean(label, col, nd=2):
        if col in sz.columns:
            v = _num(sub[col].mean(), nd)
            if v is not None: bits.append(f"{label} {v}")
    addsum("total population", "pop_resident")
    addmean("avg walkability (0-1)", "walkability_score")
    addmean("avg livability (0-1)", "livability_index")
    addmean("avg family index (0-1)", "family_index")
    addmean("avg vibrancy (0-1)", "vibrancy_index")
    addmean("avg transit score (0-1)", "max_transit_score")
    addsum("hawker eateries", "pc_cat_hawker")
    addsum("hawker centres", "hawker_centre_count")
    addsum("MRT stations", "mrt_station_count")
    addsum("bus stops", "bus_stop_count")
    addsum("schools", "school_count_total")
    addsum("local jobs", "wp_pop")
    addsum("total places", "pc_total")
    if "hdb_resale_median_psm" in sz.columns:
        vals = [float(v) for v in sub["hdb_resale_median_psm"] if v == v and float(v) > 0]
        if vals: bits.append(f"HDB resale ~${int(sum(vals)/len(vals)):,}/m²")
    return "; ".join(str(b) for b in bits) + "." + _pa_loc_intel(sub, domain)

def build_context(text):
    ents = _find_entities(text)
    if not ents: return None, None
    domain = _domain_of(text)
    parts, names = [], []
    for name, scale in ents:
        try:
            c = _subzone_ctx(name, domain) if scale == "subzone" else _pa_ctx(name, domain)
            if c: parts.append(c); names.append(name)
        except Exception as e:
            print("ctx err", e, flush=True)
    if not parts: return None, None
    return " ".join(parts), (names[0] if len(names) == 1 else " & ".join(names))

# ---------------------------------------------------------------- api
app = FastAPI(title="Plexis-Mind")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

class Msg(BaseModel):
    role: str
    content: str

class ChatReq(BaseModel):
    messages: list[Msg]
    max_tokens: int = 600
    temperature: float = 0.55
    raw: bool = False          # raw=True -> disable adapter (base Gemma)

@app.get("/health")
def health():
    return {"status": "ok", "model": "plexis-mind-v0", "base": BASE,
            "subzones": len(_SUBZ), "planning_areas": len(_PAS)}

def _prep(req: ChatReq):
    msgs = [m.model_dump() for m in req.messages]
    last = next((m for m in reversed(msgs) if m["role"] == "user"), None)
    ctx, entity = (None, None)
    if last:
        ctx, entity = build_context(last["content"])
        if ctx:
            last["content"] = f"Context: {ctx}\n\nQuestion: {last['content']}"
        else:
            last["content"] = (last["content"] +
                "\n\n[No atlas data was retrieved for this question. Answer conceptually, in words — "
                "do NOT cite specific numbers, scores or distances, and do not invent example areas with figures.]")
    chat = [{"role": "system", "content": SYS}] + msgs
    text = tok.apply_chat_template(chat, add_generation_prompt=True, tokenize=False)
    enc = tok(text, return_tensors="pt", add_special_tokens=False, truncation=True,
              max_length=1536).to(model.device)
    return enc, ctx, entity

_SSE_HEADERS = {"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}

def _start_gen(enc, max_tokens, temperature, raw=False):
    """Kick off generation in a thread; raw=True disables the LoRA (base Gemma). Returns the streamer."""
    streamer = TextIteratorStreamer(tok, skip_prompt=True, skip_special_tokens=True)
    kw = dict(**enc, max_new_tokens=min(max_tokens, 768), streamer=streamer,
              do_sample=(temperature > 0), temperature=max(temperature, 1e-4),
              pad_token_id=tok.eos_token_id)
    def _run():
        try:
            with torch.inference_mode():
                if raw:
                    with model.disable_adapter():
                        model.generate(**kw)
                else:
                    model.generate(**kw)
        except Exception as e:
            print("generate error:", repr(e), flush=True)
            streamer.end()
    threading.Thread(target=_run, daemon=True).start()
    return streamer

@app.post("/chat")
def chat(req: ChatReq):
    enc, ctx, entity = _prep(req)
    streamer = _start_gen(enc, req.max_tokens, req.temperature, raw=req.raw)
    def gen():
        yield f"data: {json.dumps({'meta': {'entity': entity, 'grounded': bool(ctx)}})}\n\n"
        for piece in streamer:
            if piece:
                yield f"data: {json.dumps({'token': piece})}\n\n"
        yield "data: [DONE]\n\n"
    return StreamingResponse(gen(), media_type="text/event-stream", headers=_SSE_HEADERS)

@app.post("/compare")
def compare(req: ChatReq):
    """Same prompt + atlas context to BOTH; stream Alchemy (adapter on) then raw Gemma (adapter off)."""
    enc, ctx, entity = _prep(req)
    def gen():
        yield f"data: {json.dumps({'meta': {'entity': entity, 'grounded': bool(ctx)}})}\n\n"
        for label, raw in (("alchemy", False), ("raw", True)):
            streamer = _start_gen(enc, req.max_tokens, req.temperature, raw=raw)
            for piece in streamer:
                if piece:
                    yield f"data: {json.dumps({'model': label, 'token': piece})}\n\n"
            yield f"data: {json.dumps({'model': label, 'done': True})}\n\n"
        yield "data: [DONE]\n\n"
    return StreamingResponse(gen(), media_type="text/event-stream", headers=_SSE_HEADERS)

if __name__ == "__main__":
    import uvicorn
    print(f"serving on 0.0.0.0:{PORT}", flush=True)
    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="info")
