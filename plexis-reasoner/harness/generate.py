"""
Generation driver — sample questions, run rollouts through the teacher in
parallel, verify each, write KEPT traces to a jsonl (resumable). This is the
SFT dataset builder. Same script runs against OpenRouter or a local vLLM teacher.

Usage:
  python3 generate.py --n 500 --model google/gemma-4-31b-it --out ../traces/sft.jsonl
"""
import argparse
import json
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import curriculum  # noqa: E402
import rollout  # noqa: E402
import verify  # noqa: E402

_lock = threading.Lock()
_stats = {"done": 0, "kept": 0, "by_tier": {}}


def one(rec, model, out_f):
    t = rollout.run(rec["question"], model, temperature=0.7, max_turns=8)
    ok, reward, reason = verify.grade(t, rec["gold"])
    with _lock:
        _stats["done"] += 1
        tier = rec["tier"]
        d = _stats["by_tier"].setdefault(tier, [0, 0])
        d[0] += 1; d[1] += ok
        if ok:
            _stats["kept"] += 1
            # the training record: chat messages + provenance
            sample = {"question": rec["question"], "tier": tier,
                      "messages": t["messages"], "reward": reward,
                      "n_calls": len(t["calls"]), "gold": rec["gold"]}
            out_f.write(json.dumps(sample) + "\n")
            out_f.flush()
        if _stats["done"] % 20 == 0:
            kr = _stats["kept"] / _stats["done"] * 100
            print(f"  {_stats['done']} done | {_stats['kept']} kept ({kr:.0f}%) | "
                  + " ".join(f"{k}:{v[1]}/{v[0]}" for k, v in sorted(_stats['by_tier'].items())),
                  flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=500)
    ap.add_argument("--model", default="google/gemma-4-31b-it")
    ap.add_argument("--out", default=str(Path(__file__).parents[1] / "traces/sft.jsonl"))
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    qs = curriculum.sample(args.n, seed=args.seed)
    print(f"generating {len(qs)} trajectories with {args.model} "
          f"({args.workers} workers) -> {args.out}", flush=True)

    with open(args.out, "a") as out_f:
        with ThreadPoolExecutor(max_workers=args.workers) as ex:
            list(ex.map(lambda r: one(r, args.model, out_f), qs))

    kr = _stats["kept"] / max(1, _stats["done"]) * 100
    print(f"\nDONE: {_stats['kept']}/{_stats['done']} kept ({kr:.0f}%)", flush=True)
    print("by tier:", {k: f"{v[1]}/{v[0]}" for k, v in _stats["by_tier"].items()})


if __name__ == "__main__":
    main()
