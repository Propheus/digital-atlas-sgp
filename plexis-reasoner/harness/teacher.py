"""
Teacher client — talks to a tool-calling LLM (OpenRouter now, local vLLM later).
Same interface for both so we validate cheaply on the API, then scale on the box.
"""
import json
import os
import time
import urllib.request
from pathlib import Path

# endpoint is configurable: defaults to OpenRouter, override for local vLLM
# (set PLEXIS_TEACHER_URL=http://localhost:8000/v1/chat/completions on the box)
OR_URL = os.environ.get("PLEXIS_TEACHER_URL",
                        "https://openrouter.ai/api/v1/chat/completions")
_keyfile = Path.home().joinpath("notes/openrouter-llm-build-key.txt")
OR_KEY = os.environ.get("PLEXIS_TEACHER_KEY",
                        _keyfile.read_text().strip() if _keyfile.exists() else "local")

# tool schemas the model sees (OpenAI/Qwen function-call format)
def tool_schemas():
    P = {"type": "object", "properties": {}, "required": []}
    def t(name, desc, props, req):
        return {"type": "function", "function": {
            "name": name, "description": desc,
            "parameters": {"type": "object", "properties": props, "required": req}}}
    s = lambda d="": {"type": "string", "description": d}
    i = lambda d="": {"type": "integer", "description": d}
    arr = lambda d="": {"type": "array", "items": {"type": "string"}, "description": d}
    return [
        t("resolve", "Match a place name to an atlas entity (subzone/PA/region).",
          {"name": s("e.g. 'Tampines', 'Bishan'")}, ["name"]),
        t("lookup", "Get atlas field values for one entity.",
          {"entity": s(), "fields": arr("column names or aliases like population, rent"),
           "scale": s("subzone|pa|region|hex8 (default subzone)")}, ["entity", "fields"]),
        t("filter", "Filter entities by a condition. where is a pandas expr.",
          {"scope": s("a region/PA name or 'all'"), "scale": s(),
           "where": s("e.g. 'pop_resident > 20000'"), "return_fields": arr(), "limit": i()},
          ["where"]),
        t("rank", "Filter (optional) then rank entities by a metric. The filter-then-rank skill.",
          {"metric": s("a column like gap_health_medical, cap_supermarket"),
           "scope": s(), "scale": s(), "where": s(), "order": s("desc|asc"), "k": i()}, ["metric"]),
        t("compare", "Compare two entities on given dimensions.",
          {"a": s(), "b": s(), "dims": arr(), "scale": s()}, ["a", "b", "dims"]),
        t("capture", "Huff capture: demand a NEW outlet of a category would win here.",
          {"category": s(), "entity": s(), "scale": s()}, ["category", "entity"]),
        t("gap", "Demand-supply gap for a category (higher=underserved). entities=list.",
          {"category": s(), "entities": arr(), "scale": s()}, ["category", "entities"]),
        t("colocation", "How well the surrounding mix fits where a category thrives (>1 good).",
          {"category": s(), "entity": s(), "scale": s()}, ["category", "entity"]),
        t("saturation", "Existing outlets per 1,000 residents for a category (crowding).",
          {"category": s(), "entity": s(), "scale": s()}, ["category", "entity"]),
        t("micrograph", "Per-category demand pressure / supply support / anchor strength @400m.",
          {"category": s(), "entity": s(), "scale": s()}, ["category", "entity"]),
        t("synergy", "Interaction signals (pop x walk, office x transit, ...).",
          {"entity": s(), "scale": s()}, ["entity"]),
        t("find_twins", "Functional twin neighbourhoods via the plexis-e1 embedding.",
          {"entity": s(), "k": i(), "scale": s()}, ["entity"]),
        t("isochrone", "10-min walk catchment stats for an entity.",
          {"entity": s(), "scale": s()}, ["entity"]),
        t("od_flow", "Outbound commuting profile (origin-destination) for an entity.",
          {"entity": s(), "scale": s()}, ["entity"]),
        t("places_in", "List/count places in an entity, optional category filter.",
          {"entity": s(), "category": s(), "scale": s(), "limit": i()}, ["entity"]),
        t("place_resolve", "Find a specific venue by name -> its id + basics.",
          {"name": s()}, ["name"]),
        t("place_twins", "Functional siblings of a venue via the plexis-p1 embedding.",
          {"name": s("venue name"), "k": i()}, ["name"]),
        t("brand_dna", "A chain's siting DNA -> subzones that best match it (expansion map).",
          {"brand": s(), "k": i()}, ["brand"]),
        t("brand_info", "Where a chain operates: outlet count, category, region.",
          {"brand": s()}, ["brand"]),
        t("can_answer", "Check if the atlas covers a topic (use before answering or to abstain).",
          {"topic": s()}, ["topic"]),
        t("list_categories", "The 11 place categories the capture/gap tools understand.", {}, []),
    ]


def chat(messages, model, tools=None, temperature=0.7, max_retries=4):
    """One chat completion with tool-calling. Returns the assistant message dict."""
    body = {"model": model, "messages": messages, "temperature": temperature}
    if tools:
        body["tools"] = tools
        body["tool_choice"] = "auto"
    data = json.dumps(body).encode()
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(OR_URL, data=data, headers={
                "Authorization": f"Bearer {OR_KEY}", "Content-Type": "application/json",
                "HTTP-Referer": "https://propheus.ai", "X-Title": "plexis-reasoner"})
            r = json.load(urllib.request.urlopen(req, timeout=120))
            return r["choices"][0]["message"]
        except Exception as e:
            if attempt == max_retries - 1:
                return {"role": "assistant", "content": f"[teacher error: {str(e)[:200]}]"}
            time.sleep(2 * (attempt + 1))
