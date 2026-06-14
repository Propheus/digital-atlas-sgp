"""
SFT prep — convert verified trajectories into Qwen chat-format training rows,
with an HONEST split: hold out entire subzones so eval measures generalization
to places never seen in training (the v0 discipline).

In:  /workspace/traces/sft_v1.jsonl  (+ optional sft_prod.jsonl)
Out: /workspace/traces/sft_train.jsonl, sft_eval.jsonl  (messages-only chat rows)
"""
import json
import re
import sys
from pathlib import Path

TRACES = sys.argv[1] if len(sys.argv) > 1 else "/workspace/traces/sft_v1.jsonl"
OUT = Path("/workspace/traces")

# hold out ~12% of subzones entirely -> eval questions about them are unseen
HOLDOUT_HASH_MOD = 8          # subzone hashes %8 == 0 -> eval (~12.5%)


def subzone_of(question):
    # pull a capitalised place phrase from the question for the holdout split
    m = re.findall(r"\b([A-Z][a-z]+(?: [A-Z][a-z]+)*)\b", question)
    return (m[0].upper() if m else "")


def to_chat(rec):
    """Keep the message list as-is (system/user/assistant/tool) — it's already
    the chat format. Strip nothing: the tool-call turns ARE the training signal."""
    msgs = rec["messages"]
    # drop a trailing forced 'Give your final answer' user turn if present,
    # merging so the last assistant turn is the clean answer
    out = []
    for m in msgs:
        role = m["role"]
        if role == "user" and m.get("content", "").startswith("Give your final answer"):
            continue
        keep = {"role": role}
        if m.get("content") is not None:
            keep["content"] = m["content"]
        if m.get("tool_calls"):
            # Qwen's chat template wants arguments as a dict (mapping), not the
            # OpenAI/Gemma JSON-string form -> parse each tool_call's arguments
            tcs = []
            for tc in m["tool_calls"]:
                fn = dict(tc.get("function", {}))
                a = fn.get("arguments")
                if isinstance(a, str):
                    try:
                        fn["arguments"] = json.loads(a) if a.strip() else {}
                    except Exception:
                        fn["arguments"] = {}
                tcs.append({"type": "function", "function": fn})
            keep["tool_calls"] = tcs
        if role == "tool":
            keep["name"] = m.get("name")
            keep["tool_call_id"] = m.get("tool_call_id", m.get("name"))
        out.append(keep)
    return out


def main():
    rows = [json.loads(l) for l in open(TRACES)]
    # also fold in the earlier prod traces if present (pre-fix but correct)
    extra = OUT / "sft_prod.jsonl"
    if extra.exists():
        rows += [json.loads(l) for l in open(extra)]
    print(f"loaded {len(rows)} verified traces")

    train, ev = [], []
    n_holdout_sz = set()
    for r in rows:
        q = r["question"]
        sz = subzone_of(q)
        is_eval = sz and (hash(sz) % HOLDOUT_HASH_MOD == 0)
        row = {"messages": to_chat(r), "tier": r["tier"]}
        if is_eval:
            ev.append(row); n_holdout_sz.add(sz)
        else:
            train.append(row)

    # dedup-lite: cap any identical (question) to <=4 copies in train
    from collections import Counter
    cap, kept = Counter(), []
    for row in train:
        key = row["messages"][1]["content"] if len(row["messages"]) > 1 else id(row)
        if cap[key] < 4:
            kept.append(row); cap[key] += 1
    train = kept

    with open(OUT / "sft_train.jsonl", "w") as f:
        for r in train:
            f.write(json.dumps(r) + "\n")
    with open(OUT / "sft_eval.jsonl", "w") as f:
        for r in ev:
            f.write(json.dumps(r) + "\n")
    print(f"train: {len(train)} | eval: {len(ev)} "
          f"(held-out from {len(n_holdout_sz)} subzones)")


if __name__ == "__main__":
    main()
