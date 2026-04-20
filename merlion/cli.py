"""
Merlion CLI — quick-test the intent layer and use-case routing.

Usage:
  python -m merlion "find 20 sites like tanjong pagar for a cafe brand"
  python -m merlion --llm "where is starbucks missing in the heartland?"
  python -m merlion --list            # show all use cases
  python -m merlion --run archetype_clustering k=15
"""
import argparse
import json
import os
import sys

# Allow running via `python -m merlion` from the repo root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from merlion import Merlion  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description="Merlion — SGP urban intelligence CLI")
    ap.add_argument("query", nargs="?", help="Natural-language query")
    ap.add_argument("--llm", action="store_true", help="Enable Claude Sonnet intent backend")
    ap.add_argument("--list", action="store_true", help="List registered use cases")
    ap.add_argument("--audit", action="store_true",
                    help="Audit use case → model → dataset chain; verify paths")
    ap.add_argument("--run", metavar="USE_CASE",
                    help="Run a use case directly (skip intent layer)")
    ap.add_argument("params", nargs="*",
                    help="key=value pairs for --run")
    ap.add_argument("--json", action="store_true", help="Raw JSON output")

    args = ap.parse_args()

    # Load .env if present (for ANTHROPIC_API_KEY).
    # Check merlion/.env first (package-local), then repo root .env.
    for env_path in [
        os.path.join(os.path.dirname(__file__), ".env"),
        os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"),
    ]:
        if os.path.exists(env_path):
            for line in open(env_path):
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
            break

    m = Merlion(use_llm=args.llm)

    if args.audit:
        from merlion.models.registry import MODELS, validate_paths
        report = validate_paths()
        ucs = m.use_cases()

        print(f"\n\033[1;36m=== MERLION AUDIT ===\033[0m\n")
        print(f"\033[1;33m[1] Use case → Model → Dataset chain\033[0m\n")
        print(f"{'Use case':<22} {'Primary':<12} {'Augment':<18} {'Dataset':<40} {'Status':<8}")
        print("─" * 102)

        any_missing = False
        for uc in ucs:
            pm = uc["primary_model"]
            aug = ",".join(uc["augment_models"]) or "-"
            spec_info = report.get(pm, {"path": "n/a", "exists": False})
            status = "✓" if spec_info["exists"] else "✗ MISSING"
            if not spec_info["exists"]:
                any_missing = True
            path_short = spec_info["path"].replace(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) + "/", "")
            color = "\033[0;32m" if spec_info["exists"] else "\033[0;31m"
            print(f"{uc['name']:<22} {pm:<12} {aug:<18} {path_short[:40]:<40} {color}{status}\033[0m")

        print(f"\n\033[1;33m[2] Model dataset inventory\033[0m\n")
        print(f"{'Model':<20} {'Kind':<14} {'Dims':<6} {'Path exists':<14}")
        print("─" * 70)
        for name, info in report.items():
            mark = "\033[0;32m✓" if info["exists"] else "\033[0;31m✗"
            print(f"{name:<20} {info['kind']:<14} {info['dims']:<6} {mark}\033[0m")

        print(f"\n\033[1;33m[3] Empirical evidence (from 260-test head-to-head)\033[0m\n")
        for name in ["gcn", "node2vec", "umap", "xgboost"]:
            spec = MODELS.get(name)
            if spec:
                print(f"  \033[1;36m{name}\033[0m — {spec.empirical_evidence}\n")

        if any_missing:
            print("\033[0;31m⚠  Some model datasets are missing locally. Run:\n")
            print("  rsync -az rwm-server:/home/azureuser/digital-atlas-sgp/data/hex_v10/ \\")
            print("       /Users/sumanth/propheus-projs/da-sgp/digital-atlas-sgp/data/hex_v10/\033[0m")
        else:
            print("\033[0;32m✓ All model datasets present locally.\033[0m")
        return

    if args.list:
        ucs = m.use_cases()
        if args.json:
            print(json.dumps(ucs, indent=2))
        else:
            print(f"\nRegistered use cases ({len(ucs)}):\n")
            for uc in ucs:
                print(f"  {uc['name']:<24} → primary:{uc['primary_model']:<12} "
                      f"strategy:{uc['strategy']:<18} {uc['description']}")
        return

    if args.run:
        # Parse key=value params
        params = {}
        for p in args.params:
            if "=" in p:
                k, v = p.split("=", 1)
                # Try to cast
                try:
                    v_cast = json.loads(v)
                except Exception:
                    v_cast = v
                params[k] = v_cast
        result = m.run(args.run, **params)
        print(json.dumps(result, indent=2, default=str))
        return

    if not args.query:
        ap.print_help()
        return

    out = m.ask(args.query)
    if args.json:
        print(json.dumps(out, indent=2, default=str))
        return

    # Pretty human output
    print(f"\n\033[1;36mQuery:\033[0m {args.query}\n")
    print("\033[1;36mParsed intents:\033[0m")
    for i, it in enumerate(out.get("intents", [])):
        marker = "→" if i == 0 else " "
        print(f"  {marker} {it['use_case']:<22} conf={it['confidence']:.2f} "
              f"strategy={it['strategy']}")
    chosen = out.get("chosen")
    if chosen:
        print(f"\n\033[1;32mChosen:\033[0m {chosen['use_case']}")
        if chosen.get("entities"):
            print("\033[1;32mEntities:\033[0m")
            for k, v in chosen["entities"].items():
                print(f"    {k}: {v}")
    result = out.get("result", {})
    print(f"\n\033[1;33mRouting result:\033[0m")
    print(f"  Primary model : {result.get('meta',{}).get('primary_model')}")
    print(f"  Augment models: {result.get('meta',{}).get('augment_models')}")
    print(f"  Strategy      : {result.get('meta',{}).get('strategy')}")
    print(f"  Status        : {result.get('status','n/a')}")
    if result.get("message"):
        print(f"  \033[2m{result['message']}\033[0m")


if __name__ == "__main__":
    main()
