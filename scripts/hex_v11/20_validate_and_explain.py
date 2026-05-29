"""For EVERY scored hex (+ data-shown), validate the computation deterministically
and generate a 1–2 sentence plain-English explanation via Haiku 4.5.

Outputs:
  data/hex_v11/hex8_explainability.jsonl
    {hex8_id, subzone, availability_score, adequacy_score, primary_factor,
     primary_factor_value, validated, validation_issues, explanation}

  data/hex_v11/hex8_validation_summary.md  — % validation pass per check

Budget: < $5 (Haiku 4.5 at $0.80/M input, $4/M output, ~$0.001 per hex × 500 = $0.50)
"""

import json, os, sys, time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
import numpy as np
import urllib.request
import threading

OUT_JSONL = Path('data/hex_v11/hex8_explainability.jsonl')
OUT_SUMMARY = Path('data/hex_v11/hex8_validation_summary.md')

API_KEY = Path('~/notes/openrouter-batch5-key.txt').expanduser().read_text().strip()
MODEL = 'anthropic/claude-haiku-4.5'
# Cost guard — hard stop if we exceed
MAX_BUDGET_USD = 5.0

# Pricing (USD per 1M tokens) — Haiku 4.5
PRICE_IN  = 0.80
PRICE_OUT = 4.00

cost_lock = threading.Lock()
total_cost = [0.0]
total_calls = [0]

SYSTEM_PROMPT = (
    "You write short plain-English explanations for transport adequacy scores in Singapore. "
    "Rules: (1) Exactly one or two sentences, max 220 chars. (2) Plain English, no jargon. "
    "(3) Address a Singapore resident. (4) Specifically explain WHY the score is what it is — "
    "name the dominant factor. (5) Do not use the words 'availability' or 'adequacy' — describe "
    "the experience instead. (6) Don't say 'this hex' — refer to the area by name."
)

def band(v):
    if v < 0.30: return 'Excellent'
    if v < 0.50: return 'Good'
    if v < 0.70: return 'Moderate'
    if v < 0.85: return 'Poor'
    return 'Critical'

def to_score(gap):
    """Convert 0..1 gap to 0..100 score (100 = best)."""
    if pd.isna(gap): return None
    return int(100 - round(float(gap) * 100))

def validate_hex(r):
    """Deterministically validate the math. Return (passed, issues_list)."""
    issues = []
    # Pop sums
    nr_sum = sum(float(r.get(k, 0) or 0) for k in
                 ['pop_nr_dorm','pop_nr_fdw','pop_nr_ep','pop_nr_sp','pop_nr_wp_other'])
    nr_stored = float(r.get('pop_non_resident', 0) or 0)
    if abs(nr_sum - nr_stored) > 1: issues.append(f'NR sum mismatch: {nr_sum} vs {nr_stored}')
    tot = float(r.get('pop_resident', 0) or 0) + nr_stored
    if abs(tot - float(r.get('pop_total', 0) or 0)) > 1:
        issues.append(f'pop_total mismatch')

    # Availability composite
    avail_replay = (0.30 * float(r['f_distance']) + 0.25 * float(r['f_accessibility'])
                    + 0.25 * float(r['f_last_mile']) + 0.20 * float(r['f_connectivity']))
    if abs(avail_replay - float(r['availability_adequacy_gap'])) > 0.005:
        issues.append(f'availability mismatch: {avail_replay:.3f} vs {float(r["availability_adequacy_gap"]):.3f}')

    # Quality_only composite
    q_replay = (0.42 * float(r['frequency_adequacy_gap']) + 0.33 * float(r['reach_adequacy_gap'])
                + 0.17 * float(r['crowding_adequacy_gap']) + 0.08 * float(r['resilience_adequacy_gap']))
    if 'quality_only_gap' in r and abs(q_replay - float(r['quality_only_gap'])) > 0.005:
        issues.append(f'quality_only mismatch: {q_replay:.3f} vs {float(r["quality_only_gap"]):.3f}')

    # adequacy_core = max(availability, quality_only)
    core_replay = max(avail_replay, q_replay)
    if abs(core_replay - float(r['adequacy_core'])) > 0.005:
        issues.append(f'adequacy_core mismatch: {core_replay:.3f} vs {float(r["adequacy_core"]):.3f}')

    # Floor enforcement
    if float(r['adequacy_default']) < float(r['availability_adequacy_gap']) - 0.005:
        issues.append('adequacy_default < availability (FLOOR VIOLATION)')

    return (len(issues) == 0), issues

def identify_primary_driver(r):
    """Which factor dominates the gap?"""
    factors = {
        'f_distance':          float(r['f_distance']),
        'f_accessibility':     float(r['f_accessibility']),
        'f_last_mile':         float(r['f_last_mile']),
        'f_connectivity':      float(r['f_connectivity']),
        'frequency_gap':       float(r['frequency_adequacy_gap']),
        'reach_gap':           float(r['reach_adequacy_gap']),
        'crowding_gap':        float(r['crowding_adequacy_gap']),
        'resilience_gap':      float(r['resilience_adequacy_gap']),
    }
    worst = max(factors.items(), key=lambda x: x[1])
    return worst[0], worst[1]

def build_prompt(r, primary_factor, primary_value):
    avail = to_score(float(r['availability_adequacy_gap']))
    adeq  = to_score(float(r['adequacy_default']))
    sz = r.get('parent_subzone') or r.get('parent_pa') or 'this area'
    pa = r.get('parent_pa') or ''
    zt = r.get('zone_type', 'residential')

    # Compact factual brief
    facts = []
    facts.append(f'Subzone: {sz}{" (" + pa + ")" if pa and pa != sz else ""}, zone_type: {zt}')
    facts.append(f'Population total: {float(r.get("pop_total", 0)):,.0f} '
                 f'(residents {float(r.get("pop_resident", 0)):,.0f}, NR {float(r.get("pop_non_resident", 0)):,.0f})')
    facts.append(f'Availability score: {avail}/100 (band: {band(float(r["availability_adequacy_gap"]))})')
    facts.append(f'Adequacy score: {adeq}/100 (band: {band(float(r["adequacy_default"]))})')
    facts.append(f'Nearest MRT: {float(r.get("dist_nearest_mrt_m", 0)):.0f} m | nearest bus: {float(r.get("dist_bus_m", 0)):.0f} m')
    facts.append(f'Bus routes nearby: {int(r.get("bus_routes_count", 0))} | MRT lines reachable: {int(r.get("mrt_lines_count", 0))}')
    if 'peak_wait_min' in r:
        facts.append(f'Peak wait: {float(r["peak_wait_min"]):.1f} min')
    if 'time_to_cbd_min' in r and not pd.isna(r['time_to_cbd_min']):
        facts.append(f'Time to CBD via MRT: {float(r["time_to_cbd_min"]):.0f} min')
    if 'pct_dest_within_45min' in r:
        facts.append(f'% destinations within 45 min: {float(r["pct_dest_within_45min"]):.0f}%')
    if 'n_lines_to_cbd' in r:
        facts.append(f'CBD-serving lines reachable: {int(r["n_lines_to_cbd"])}')
    facts.append(f'Dominant gap driver: {primary_factor} ({primary_value:.2f})')

    return (
        f"Hex facts:\n" + "\n".join(f"- {f}" for f in facts) +
        "\n\nWrite one or two sentences (max 220 chars) explaining the experience."
    )

def call_openrouter(prompt):
    """Call Haiku 4.5 via OpenRouter. Return (text, in_tokens, out_tokens) or (None, 0, 0)."""
    body = json.dumps({
        'model': MODEL,
        'messages': [
            {'role': 'system', 'content': SYSTEM_PROMPT},
            {'role': 'user', 'content': prompt},
        ],
        'max_tokens': 200,
        'temperature': 0.3,
    }).encode()
    req = urllib.request.Request(
        'https://openrouter.ai/api/v1/chat/completions',
        data=body,
        headers={
            'Authorization': f'Bearer {API_KEY}',
            'Content-Type': 'application/json',
            'HTTP-Referer': 'https://sgp-mobility.digitalatlaspropheus.com',
            'X-Title': 'SG Transport Adequacy',
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.loads(r.read())
        text = data['choices'][0]['message']['content'].strip()
        usage = data.get('usage', {})
        in_tok  = usage.get('prompt_tokens', 0)
        out_tok = usage.get('completion_tokens', 0)
        return text, in_tok, out_tok
    except Exception as e:
        return f'(LLM error: {e})', 0, 0

def process_hex(r_dict):
    r = pd.Series(r_dict)
    passed, issues = validate_hex(r)
    primary_factor, primary_value = identify_primary_driver(r)
    avail_score = to_score(float(r['availability_adequacy_gap']))
    adeq_score = to_score(float(r['adequacy_default']))

    prompt = build_prompt(r, primary_factor, primary_value)

    # Cost guard
    with cost_lock:
        if total_cost[0] > MAX_BUDGET_USD:
            return {
                'hex8_id': r['hex8_id'],
                'subzone': r.get('parent_subzone'),
                'availability_score': avail_score,
                'adequacy_score': adeq_score,
                'primary_factor': primary_factor,
                'primary_factor_value': round(primary_value, 3),
                'validated': passed,
                'validation_issues': issues,
                'explanation': '(skipped — budget exceeded)',
            }
    text, in_tok, out_tok = call_openrouter(prompt)
    cost = in_tok / 1_000_000 * PRICE_IN + out_tok / 1_000_000 * PRICE_OUT
    with cost_lock:
        total_cost[0] += cost
        total_calls[0] += 1

    return {
        'hex8_id': r['hex8_id'],
        'subzone': r.get('parent_subzone'),
        'pa':      r.get('parent_pa'),
        'zone_type': r.get('zone_type'),
        'pop_total': float(r.get('pop_total', 0) or 0),
        'availability_score': avail_score,
        'adequacy_score': adeq_score,
        'primary_factor': primary_factor,
        'primary_factor_value': round(primary_value, 3),
        'validated': passed,
        'validation_issues': issues,
        'explanation': text,
        'cost_usd': round(cost, 6),
    }

def main():
    # Merge feature + bands so we have everything per hex
    h_feat = pd.read_parquet('data/hex_v11/hex8_adequacy_features.parquet')
    h_band = pd.read_parquet('data/hex_v11/hex8_adequacy.parquet')
    extra = [c for c in h_band.columns if c not in h_feat.columns and c != 'hex8_id']
    h = h_feat.merge(h_band[['hex8_id'] + extra], on='hex8_id', how='left')

    # Process scored + data-shown
    target = h[(h['is_scored'] == True) | (h.get('is_data_shown', False) == True)].copy()
    print(f'Target hexes: {len(target)} (scored + data-shown)')

    # Resume support
    seen = set()
    if OUT_JSONL.exists():
        for line in OUT_JSONL.open():
            try:
                rec = json.loads(line)
                seen.add(rec['hex8_id'])
            except Exception:
                pass
        print(f'Resuming — {len(seen)} hexes already processed.')

    todo = target[~target['hex8_id'].isin(seen)].copy()
    print(f'Hexes still to process: {len(todo)}')
    if len(todo) == 0:
        print('Nothing to do.')
        return

    rows = todo.to_dict('records')

    write_lock = threading.Lock()
    out_fh = OUT_JSONL.open('a')

    n_done = 0
    n_validated = 0
    started = time.time()
    with ThreadPoolExecutor(max_workers=8) as ex:
        futures = {ex.submit(process_hex, r): r['hex8_id'] for r in rows}
        for fut in as_completed(futures):
            try:
                rec = fut.result()
                with write_lock:
                    out_fh.write(json.dumps(rec) + '\n')
                    out_fh.flush()
                n_done += 1
                if rec.get('validated'): n_validated += 1
                if n_done % 25 == 0 or n_done == len(rows):
                    elapsed = time.time() - started
                    rate = n_done / max(elapsed, 1)
                    eta = (len(rows) - n_done) / max(rate, 0.1)
                    print(f'  {n_done}/{len(rows)} | validated {n_validated}/{n_done} '
                          f'| cost ${total_cost[0]:.3f} | rate {rate:.1f}/s | eta {eta:.0f}s',
                          flush=True)
            except Exception as e:
                print(f'  ⚠ worker error: {e}')
    out_fh.close()

    # Final summary
    print(f'\nDone. {n_done} hexes processed.')
    print(f'  Validated:       {n_validated}/{n_done} ({100*n_validated/max(n_done,1):.1f}%)')
    print(f'  Total LLM cost:  ${total_cost[0]:.3f} (budget ${MAX_BUDGET_USD})')

    # Write summary markdown
    all_recs = [json.loads(l) for l in OUT_JSONL.open()]
    total = len(all_recs)
    val = sum(1 for r in all_recs if r['validated'])
    OUT_SUMMARY.write_text(f"""# Hex Validation Summary

**Built:** 2026-05-29
**Hexes processed:** {total}
**Passed all checks:** {val} ({100*val/max(total,1):.1f}%)
**Failed (issues recorded):** {total - val}

## Per-check pass rates

| Check | Pass | Fail |
|---|---|---|
| Population sum (NR buckets) | {sum(1 for r in all_recs if not any('NR sum' in i for i in r["validation_issues"]))} | {sum(1 for r in all_recs if any('NR sum' in i for i in r["validation_issues"]))} |
| pop_total = resident + NR | {sum(1 for r in all_recs if not any('pop_total' in i for i in r["validation_issues"]))} | {sum(1 for r in all_recs if any('pop_total' in i for i in r["validation_issues"]))} |
| Availability composite | {sum(1 for r in all_recs if not any('availability mismatch' in i for i in r["validation_issues"]))} | {sum(1 for r in all_recs if any('availability mismatch' in i for i in r["validation_issues"]))} |
| Quality composite | {sum(1 for r in all_recs if not any('quality_only mismatch' in i for i in r["validation_issues"]))} | {sum(1 for r in all_recs if any('quality_only mismatch' in i for i in r["validation_issues"]))} |
| adequacy_core formula | {sum(1 for r in all_recs if not any('adequacy_core mismatch' in i for i in r["validation_issues"]))} | {sum(1 for r in all_recs if any('adequacy_core mismatch' in i for i in r["validation_issues"]))} |
| Floor (adeq ≥ avail) | {sum(1 for r in all_recs if not any('FLOOR VIOLATION' in i for i in r["validation_issues"]))} | {sum(1 for r in all_recs if any('FLOOR VIOLATION' in i for i in r["validation_issues"]))} |

## Total LLM cost
**${total_cost[0]:.3f}** (budget: ${MAX_BUDGET_USD}, model: {MODEL})

## Output
- Per-hex records: `data/hex_v11/hex8_explainability.jsonl`
""")
    print(f'Summary written to {OUT_SUMMARY}')

if __name__ == '__main__':
    main()
