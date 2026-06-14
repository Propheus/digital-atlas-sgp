"""
Rollout — run one agentic trajectory: model emits tool calls, we execute them
against the atlas, feed observations back, until it answers. Returns the full
message trace (the training sample) + metadata.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import atlas_tools as AT  # noqa: E402
from teacher import chat, tool_schemas  # noqa: E402

SYSTEM = """You are Plexis, a senior urban analyst for Singapore. You answer by \
REASONING over the Digital Atlas through tools — never invent numbers, never \
recall figures from memory; always fetch them.

How to work:
- Think briefly, then call the tools you need. Chain them: resolve names, filter \
and rank to find candidates, fetch the deciding metric, confirm the winner.
- Ground every claim in a tool result. Cite the fields you used.
- If the atlas does not cover something (crime, weather, income, future prices), \
say so plainly and stop — do not guess.
- When you have enough, give a concise analyst answer.

The 11 place categories: beauty_personal, cafe_coffee, convenience, education, \
fast_food, fitness_recreation, hawker, health_medical, restaurant, \
shopping_retail, supermarket.

REAL atlas field names (use these exactly — do NOT invent fields like \
'pop_worker' or 'employment_rate'):
- people: pop_resident, pop_0_14, pop_65plus, pop_hdb_share, pop_dorm, dt_pop \
(daytime population), nonres_share
- movement: dist_mrt_m, time_to_cbd_min, min15_score, walkability_score, \
od_out_trips, od_out_am (use od_flow for the commuting picture)
- housing/price: rent_resi_psf_med, hdb_resale_4r_median_psm
- vitality: biz_live_robust, biz_recent_dead_share, nl_2024 (night lights)
- per-category metrics (suffix one of the 11 categories): cap_<cat> (Huff \
capture), gap_<cat> (under-supply), sat_<cat>_per_1k, colo_fit_<cat>
Geography is parent_region / parent_pa / parent_subzone_name (not 'region'). \
For 'job centre vs dormitory', use od_flow + dt_pop vs pop_resident. \
Scope can be a region name like 'North' or 'East Region'."""

MAX_TURNS = 8


def run(question, model, temperature=0.7, max_turns=MAX_TURNS):
    """Execute one trajectory. Returns dict(messages, calls, answer, ok)."""
    tools = tool_schemas()
    messages = [{"role": "system", "content": SYSTEM},
                {"role": "user", "content": question}]
    calls = []
    for turn in range(max_turns):
        msg = chat(messages, model, tools=tools, temperature=temperature)
        tc = msg.get("tool_calls")
        # normalise assistant message into the trace
        messages.append({k: v for k, v in msg.items() if k in
                         ("role", "content", "tool_calls")})
        if not tc:
            # no tool call -> this is the final answer
            return {"question": question, "messages": messages, "calls": calls,
                    "answer": msg.get("content", ""), "turns": turn + 1,
                    "tool_error": any(c.get("error") for c in calls)}
        # execute every tool call this turn
        for call in tc:
            fn = call["function"]["name"]
            try:
                args = json.loads(call["function"].get("arguments") or "{}")
            except Exception:
                args = {}
            result = AT.call(fn, **args)
            calls.append({"tool": fn, "args": args,
                          "error": isinstance(result, dict) and "error" in result})
            messages.append({"role": "tool", "tool_call_id": call.get("id", fn),
                             "name": fn, "content": json.dumps(result)[:4000]})
    # ran out of turns -> force a final answer
    messages.append({"role": "user", "content": "Give your final answer now, grounded in what you found."})
    msg = chat(messages, model, temperature=temperature)
    messages.append({"role": "assistant", "content": msg.get("content", "")})
    return {"question": question, "messages": messages, "calls": calls,
            "answer": msg.get("content", ""), "turns": max_turns,
            "tool_error": any(c.get("error") for c in calls), "truncated": True}


def render(trace):
    """Pretty-print a trajectory for inspection."""
    out = []
    for m in trace["messages"]:
        r = m["role"]
        if r == "system":
            continue
        if r == "user":
            out.append(f"USER: {m['content']}")
        elif r == "assistant":
            if m.get("tool_calls"):
                for c in m["tool_calls"]:
                    out.append(f"  → {c['function']['name']}({c['function'].get('arguments','')})")
            if m.get("content"):
                out.append(f"ASSISTANT: {m['content']}")
        elif r == "tool":
            out.append(f"  ← {m['name']}: {m['content'][:160]}")
    return "\n".join(out)
