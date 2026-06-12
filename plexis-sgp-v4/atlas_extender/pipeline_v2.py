"""Atlas Extender — Multi-Round Deep Pipeline (v2).

9 stages with streaming events. Each LLM stage uses extended thinking
(budget 4-8K tokens) for genuine depth. Adversarial loop = 2 rounds of
synthesizer ↔ debater. Then 3-persona expert panel in parallel. Finally
a decision agent that synthesizes everything.

Use:
  for evt in extend_v2_stream("use case text"):
      handle_event(evt)
"""
import json, time, traceback
from pathlib import Path
import pandas as pd

from .agents.reasoner import reason
from .agents.synthesizer import synthesize
from .agents.debater import debate
from .agents.refiner import refine
from .agents.critic_r2 import critique_r2
from .agents.expert_panel import expert_panel
from .agents.decision import decide
from .agents.builder import build, ROOT
from .pipeline import catalog_summary, render_md_report, update_catalogs


def extend_v2_stream(use_case_text: str, output_dir: Path = None):
    """Yields events as a streaming generator. Each event is a dict with:
       {stage, status, payload, t_elapsed_s}
    """
    t0 = time.time()
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    output_dir = output_dir or (ROOT / "extensions" / f"v2-{timestamp}")
    output_dir.mkdir(parents=True, exist_ok=True)

    def evt(stage, status, payload=None):
        return {
            "stage": stage,
            "status": status,
            "elapsed_s": round(time.time() - t0, 1),
            "payload": payload,
        }

    # Find current version
    versions = sorted(ROOT.glob("CHECKPOINT_v*.json"))
    base_version = versions[-1].stem.replace("CHECKPOINT_v", "") if versions else "unknown"
    parts = base_version.split(".")
    parts[-1] = str(int(parts[-1]) + 1) if parts[-1].isdigit() else "1"
    new_version = ".".join(parts)

    yield evt("init", "ok", {
        "use_case": use_case_text,
        "base_version": base_version,
        "new_version": new_version,
        "output_dir": str(output_dir),
    })

    try:
        # === STAGE 1: Reasoning ===
        yield evt("reasoner", "start")
        ucs = reason(use_case_text)
        (output_dir / "1_ucs.json").write_text(json.dumps(ucs, indent=2))
        yield evt("reasoner", "done", ucs)

        scale = ucs.get("scale", "hex9")
        cs_text, cols_at_scale = catalog_summary(scale=scale)

        # === STAGE 2: Synthesizer R1 ===
        yield evt("synthesizer_r1", "start")
        syn_r1 = synthesize(ucs, cs_text, cols_at_scale)
        proposals_r1 = syn_r1.get("proposed_features", [])
        (output_dir / "2_proposals_r1.json").write_text(json.dumps(syn_r1, indent=2))
        yield evt("synthesizer_r1", "done", {
            "n": len(proposals_r1),
            "proposals": proposals_r1,
        })

        # === STAGE 3: Debater R1 ===
        yield evt("debater_r1", "start")
        deb_r1 = debate(proposals_r1, cs_text)
        critiques_r1 = deb_r1.get("critiques", [])
        (output_dir / "3_debates_r1.json").write_text(json.dumps(deb_r1, indent=2))
        yield evt("debater_r1", "done", {
            "n": len(critiques_r1),
            "critiques": critiques_r1,
        })

        # === STAGE 4: Refiner (Synthesizer R2) ===
        yield evt("refiner_r2", "start")
        ref = refine(proposals_r1, critiques_r1, ucs, cols_at_scale)
        refined = ref.get("refined_proposals", [])
        new_proposals = ref.get("new_proposals", [])
        # Merge into final proposal set, keeping non-rejected refinements
        all_r2 = []
        for r in refined:
            if r.get("action") in ("REVISE", "DEFEND", "REPLACE"):
                all_r2.append(r)
        all_r2.extend(new_proposals)
        (output_dir / "4_refinement.json").write_text(json.dumps(ref, indent=2))
        yield evt("refiner_r2", "done", {
            "n_refined": len(refined),
            "n_new": len(new_proposals),
            "n_total": len(all_r2),
            "refinements": refined,
            "new_proposals": new_proposals,
        })

        # === STAGE 5: Debater R2 ===
        yield evt("debater_r2", "start")
        deb_r2 = critique_r2(all_r2, critiques_r1, cs_text)
        critiques_r2 = deb_r2.get("critiques", [])
        panel_note = deb_r2.get("overall_panel_note", "")
        (output_dir / "5_debates_r2.json").write_text(json.dumps(deb_r2, indent=2))
        yield evt("debater_r2", "done", {
            "n": len(critiques_r2),
            "critiques": critiques_r2,
            "overall_note": panel_note,
        })

        # === STAGE 6: Expert Panel (3 personas in parallel) ===
        yield evt("expert_panel", "start")
        panel = expert_panel(all_r2, critiques_r2)
        (output_dir / "6_expert_panel.json").write_text(json.dumps(panel, indent=2))
        yield evt("expert_panel", "done", panel)

        # === STAGE 7: Decision (synthesizes everything) ===
        yield evt("decision", "start")
        # Pack all evidence into the decision agent
        evidence = {
            "round1_critiques": critiques_r1,
            "round2_critiques": critiques_r2,
            "panel": panel,
            "panel_note": panel_note,
        }
        # decide() expects (proposals, debates) — pass r2 critiques as the debates
        # but include a richer context via the proposals' rationale
        for p in all_r2:
            p_critique_r1 = next((c for c in critiques_r1 if c.get("feature") == p.get("name") or c.get("feature") == p.get("original_name")), None)
            p_critique_r2 = next((c for c in critiques_r2 if c.get("feature") == p.get("name")), None)
            panel_verdicts = []
            for persona, panel_data in panel.items():
                if "verdicts" in panel_data:
                    v = next((x for x in panel_data["verdicts"] if x.get("feature") == p.get("name")), None)
                    if v:
                        panel_verdicts.append(f"{persona}: {v.get('verdict')} - {v.get('reasoning')}")
            p["_evidence_r1"] = p_critique_r1
            p["_evidence_r2"] = p_critique_r2
            p["_panel"] = panel_verdicts
        dec = decide(all_r2, critiques_r2)
        decisions = dec.get("decisions", [])
        (output_dir / "7_decisions.json").write_text(json.dumps(dec, indent=2))
        n_keep = sum(1 for d in decisions if d.get("decision") == "KEEP")
        n_rev  = sum(1 for d in decisions if d.get("decision") == "REVISE")
        n_rej  = sum(1 for d in decisions if d.get("decision") == "REJECT")
        yield evt("decision", "done", {
            "decisions": decisions,
            "keep": n_keep, "revise": n_rev, "reject": n_rej,
        })

        # Merge proposals with decisions for builder
        proposals_by = {p.get("name"): p for p in all_r2}
        for d in decisions:
            p = proposals_by.get(d["feature"], {})
            d.setdefault("code", p.get("code", ""))
            d.setdefault("dependencies", p.get("dependencies", []))
            d.setdefault("scale", p.get("scale", scale))
            d.setdefault("description", p.get("description", ""))

        # === STAGE 8: Builder ===
        yield evt("builder", "start")
        build_res = build(decisions, scale=scale)
        df = build_res.pop("df")
        extended_path = output_dir / f"{scale}_extended.parquet"
        df.to_parquet(extended_path, index=False)
        (output_dir / "8_build.json").write_text(json.dumps(build_res, indent=2, default=str))
        yield evt("builder", "done", {
            "added": build_res["added"],
            "failed": build_res["failed"],
            "extended_path": str(extended_path),
            "shape": list(df.shape),
        })

        # === STAGE 9: Reporter ===
        yield evt("reporter", "start")
        rep = {
            "timestamp": timestamp,
            "use_case": use_case_text,
            "base_version": base_version,
            "new_version": new_version,
            "scale": scale,
            "n_proposed": len(all_r2),
            "n_proposed_r1": len(proposals_r1),
            "n_proposed_r2_new": len(new_proposals),
            "n_kept": n_keep,
            "n_revised": n_rev,
            "n_rejected": n_rej,
            "n_added": len(build_res["added"]),
            "n_failed": len(build_res["failed"]),
            "added_features": build_res["added"],
            "failed_features": build_res["failed"],
            "extended_parquet": str(extended_path),
            "elapsed_s": round(time.time() - t0, 1),
            "panel_note": panel_note,
        }
        # Render md (compatible with v1)
        md = render_md_report(rep, ucs, all_r2, critiques_r2, decisions)
        (output_dir / "0_report.md").write_text(md)
        (output_dir / "0_report.json").write_text(json.dumps(rep, indent=2, default=str))
        update_catalogs(output_dir, build_res["added"], ucs, new_version, scale)
        yield evt("reporter", "done", rep)

        yield evt("done", "ok", {"output_dir": str(output_dir), "elapsed_s": rep["elapsed_s"]})

    except Exception as e:
        yield evt("error", "fail", {"error": str(e), "trace": traceback.format_exc()[-1000:]})
