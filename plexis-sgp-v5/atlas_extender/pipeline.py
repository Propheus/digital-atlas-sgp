"""Atlas Extender pipeline — reason → synthesize → debate → decide → build → report."""
import json, time
from pathlib import Path
import pandas as pd

from .agents.reasoner import reason
from .agents.synthesizer import synthesize
from .agents.debater import debate
from .agents.decision import decide
from .agents.builder import build, ROOT


def catalog_summary(scale: str = None) -> tuple[str, list]:
    """Return (compact summary text, list of column names at the target scale)."""
    fc_path = ROOT / "catalog/feature_catalog.json"
    if not fc_path.exists():
        return "(catalog not available)", []
    fc = json.load(open(fc_path))

    by_family = {}
    cols_at_scale = []
    for f in fc["features"]:
        s = f.get("scale", "?")
        col = f.get("column", "")
        if not col: continue
        # Family by leading underscore-prefix
        parts = col.split("_")
        family = parts[0] if len(parts) == 1 else f"{parts[0]}_{parts[1][:6]}"
        key = f"{s}/{family}"
        by_family.setdefault(key, []).append(col)
        if scale and s == scale:
            cols_at_scale.append(col)

    lines = []
    for key, cols in sorted(by_family.items(), key=lambda x: (x[0].split("/")[0], -len(x[1]))):
        sample = ", ".join(cols[:3]) + (", ..." if len(cols) > 3 else "")
        lines.append(f"  {key} ({len(cols)}): {sample}")
    return "\n".join(lines), cols_at_scale


def render_md_report(rep, ucs, proposals, critiques, decisions) -> str:
    proposals_by = {p["name"]: p for p in proposals}
    critiques_by = {c["feature"]: c for c in critiques}

    lines = [
        f"# Atlas Extender Report",
        f"",
        f"**Use case:** {rep['use_case']}",
        f"**Generated:** {rep['timestamp']}",
        f"**Atlas version (base):** {rep['base_version']}",
        f"**New version:** {rep['new_version']}",
        f"",
        f"## Summary",
        f"",
        f"| | Count |",
        f"|---|---|",
        f"| Proposed | {rep['n_proposed']} |",
        f"| KEEP | {rep['n_kept']} |",
        f"| REVISE | {rep['n_revised']} |",
        f"| REJECT | {rep['n_rejected']} |",
        f"| **Successfully added** | **{rep['n_added']}** |",
        f"| Build-failed | {rep['n_failed']} |",
        f"",
        f"## Use Case Spec",
        f"",
        f"```json",
        json.dumps(ucs, indent=2),
        f"```",
        f"",
        f"## Per-feature decisions",
        f"",
    ]
    for d in sorted(decisions, key=lambda x: (x.get("priority") or 99, x.get("feature", ""))):
        feat = d["feature"]
        p = proposals_by.get(feat, {})
        c = critiques_by.get(feat, {})
        decision = d.get("decision", "?")
        emoji = {"KEEP": "✅", "REVISE": "🔧", "REJECT": "❌"}.get(decision, "•")
        lines += [
            f"### {emoji} `{feat}` — {decision}  *(priority {d.get('priority','?')})*",
            f"",
            f"**Description:** {p.get('description','')}",
            f"",
            f"**Type:** {p.get('derivation_type','?')}  · **Scale:** {p.get('scale','?')}  · **Dtype:** {p.get('dtype','?')}",
            f"",
            f"**Rationale:** {p.get('rationale','')}",
            f"",
            f"**Decision justification:** {d.get('justification','')}",
            f"",
        ]
        if p.get("derivation_type") == "derive":
            code = d.get("revised_code") or p.get("code", "")
            lines += [f"**Code:**", f"```python", code, f"```", f""]
            lines += [f"**Dependencies:** `{', '.join(p.get('dependencies', []))}`", f""]
        if c:
            lines += [
                f"**Strengths:** {', '.join(c.get('strengths',[]))}",
                f"",
                f"**Weaknesses:** {', '.join(c.get('weaknesses',[]))}",
                f"",
                f"**Redundancy:** {c.get('redundancy_with') or 'none'}  · "
                f"**Risk:** {c.get('implementation_risk','?')}  · "
                f"**Confidence:** {c.get('confidence','?')}",
                f"",
            ]

    if rep["added_features"]:
        lines += [f"## Added to atlas", f""]
        lines += [f"| Feature | dtype | non-null | median | min | max |"]
        lines += [f"|---|---|---|---|---|---|"]
        for f in rep["added_features"]:
            lines.append(
                f"| `{f['feature']}` | {f['dtype']} | {f['non_null']:,} | "
                f"{f.get('median','—')} | {f.get('min','—')} | {f.get('max','—')} |"
            )
        lines.append("")

    if rep["failed_features"]:
        lines += [f"## Build failures", f""]
        for f in rep["failed_features"]:
            lines.append(f"- `{f['feature']}` — {f['reason']}")
        lines.append("")

    return "\n".join(lines)


def update_catalogs(extension_dir: Path, added_features: list, ucs: dict,
                    new_version: str, scale: str) -> None:
    """Write extension-local feature_catalog.json + dataset_catalog.json so the
    extended state is documented separately from the main atlas catalog."""
    extension_dir.mkdir(parents=True, exist_ok=True)
    feature_rows = []
    for f in added_features:
        feature_rows.append({
            "dataset": f"extension_{new_version}",
            "scale": scale,
            "column": f["feature"],
            "dtype": f["dtype"],
            "null_pct": f.get("null_pct", 0),
            "min": f.get("min"),
            "max": f.get("max"),
            "median": f.get("median"),
            "source_stage": "atlas_extender",
            "source_use_case": ucs.get("use_case", ""),
        })
    (extension_dir / "feature_catalog.json").write_text(
        json.dumps({"version": new_version, "scale": scale, "features": feature_rows}, indent=2)
    )

    ds_row = {
        "dataset": f"extension_{new_version}",
        "scale": scale,
        "description": f"Atlas extension for use case: {ucs.get('use_case','')}",
        "owner_stage": "atlas_extender",
        "n_cols_added": len(added_features),
        "use_case": ucs.get("use_case", ""),
        "version": new_version,
    }
    (extension_dir / "dataset_catalog.json").write_text(json.dumps({"datasets": [ds_row]}, indent=2))


def extend(use_case_text: str, output_dir: Path = None) -> dict:
    t0 = time.time()
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    output_dir = output_dir or (ROOT / "extensions" / timestamp)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Find current atlas version
    versions = sorted(ROOT.glob("CHECKPOINT_v*.json"))
    base_version = versions[-1].stem.replace("CHECKPOINT_v", "") if versions else "unknown"
    # Bump patch by 1 (e.g. 4.8.0 → 4.8.1) for extensions
    parts = base_version.split(".")
    parts[-1] = str(int(parts[-1]) + 1) if parts[-1].isdigit() else "1"
    new_version = ".".join(parts)

    print(f"=== ATLAS EXTENDER ===")
    print(f"Use case: {use_case_text}")
    print(f"Base version: {base_version}  →  New version: {new_version}")
    print(f"Output: {output_dir}")

    # 1. Reason
    print("\n[1/5] REASONER (Opus)...")
    ucs = reason(use_case_text)
    (output_dir / "1_ucs.json").write_text(json.dumps(ucs, indent=2))
    print(f"  target: {ucs.get('target_variable')}")
    print(f"  scale:  {ucs.get('scale')}")
    print(f"  concepts ({len(ucs.get('key_concepts', []))}): {ucs.get('key_concepts')}")

    # 2. Synthesize
    scale = ucs.get("scale", "hex9")
    print(f"\n[2/5] SYNTHESIZER (Opus)...")
    cs_text, cols_at_scale = catalog_summary(scale=scale)
    syn = synthesize(ucs, cs_text, cols_at_scale)
    (output_dir / "2_proposals.json").write_text(json.dumps(syn, indent=2))
    proposals = syn.get("proposed_features", [])
    print(f"  proposed {len(proposals)} features")
    for p in proposals:
        print(f"    • {p['name']} ({p.get('derivation_type','?')})")

    # 3. Debate
    print(f"\n[3/5] DEBATER (Opus)...")
    deb = debate(proposals, cs_text)
    (output_dir / "3_debates.json").write_text(json.dumps(deb, indent=2))
    critiques = deb.get("critiques", [])
    avg_conf = sum(c.get("confidence", 0) for c in critiques) / max(len(critiques), 1)
    print(f"  {len(critiques)} critiques, avg confidence {avg_conf:.2f}")

    # 4. Decide
    print(f"\n[4/5] DECISION (Opus)...")
    dec = decide(proposals, critiques)
    (output_dir / "4_decisions.json").write_text(json.dumps(dec, indent=2))
    decisions = dec.get("decisions", [])
    n_keep = sum(1 for d in decisions if d.get("decision") == "KEEP")
    n_rev  = sum(1 for d in decisions if d.get("decision") == "REVISE")
    n_rej  = sum(1 for d in decisions if d.get("decision") == "REJECT")
    print(f"  KEEP: {n_keep}  REVISE: {n_rev}  REJECT: {n_rej}")

    # Merge proposals into decisions (so builder has code + dependencies)
    proposals_by = {p["name"]: p for p in proposals}
    for d in decisions:
        p = proposals_by.get(d["feature"], {})
        d.setdefault("code", p.get("code", ""))
        d.setdefault("dependencies", p.get("dependencies", []))
        d.setdefault("scale", p.get("scale", scale))
        d.setdefault("description", p.get("description", ""))

    # 5. Build
    print(f"\n[5/5] BUILDER...")
    build_res = build(decisions, scale=scale)
    df = build_res.pop("df")
    (output_dir / "5_build.json").write_text(json.dumps(build_res, indent=2, default=str))
    print(f"  added: {len(build_res['added'])}  failed: {len(build_res['failed'])}")
    if build_res["failed"]:
        for f in build_res["failed"]:
            print(f"    ✗ {f['feature']}: {f['reason']}")

    # Write extended bundle (separate, doesn't overwrite main)
    extended_path = output_dir / f"{scale}_extended.parquet"
    df.to_parquet(extended_path, index=False)
    print(f"  wrote {extended_path.name}: {df.shape[0]:,} rows × {df.shape[1]} cols")

    # Update catalogs (extension-local)
    update_catalogs(output_dir, build_res["added"], ucs, new_version, scale)

    # Final report
    rep = {
        "timestamp": timestamp,
        "use_case": use_case_text,
        "base_version": base_version,
        "new_version": new_version,
        "scale": scale,
        "n_proposed": len(proposals),
        "n_kept": n_keep,
        "n_revised": n_rev,
        "n_rejected": n_rej,
        "n_added": len(build_res["added"]),
        "n_failed": len(build_res["failed"]),
        "added_features": build_res["added"],
        "failed_features": build_res["failed"],
        "extended_parquet": str(extended_path),
        "elapsed_s": round(time.time() - t0, 1),
    }
    (output_dir / "0_report.json").write_text(json.dumps(rep, indent=2, default=str))
    md = render_md_report(rep, ucs, proposals, critiques, decisions)
    (output_dir / "0_report.md").write_text(md)

    print(f"\n=== DONE ({rep['elapsed_s']}s) ===")
    print(f"Report: {output_dir}/0_report.md")
    return rep
