"""
Plexis SGP — checkpoint publisher.

Generates a versioned manifest documenting the full atlas state:
  - VERSION
  - dataset inventory with sha256 + sizes + row counts
  - pipeline run timings (latest)
  - validator pass-rate roll-up
  - per-stage stats

Outputs:
  CHECKPOINT_v4.0.0.json
  CHECKPOINT_v4.0.0.md
"""
import hashlib, json, time, os
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).parent
VERSION = "5.4.0"
PLEXIS_VERSION = f"plexis-sgp-v{VERSION}"


def sha256_file(p, blocksize=4*1024*1024):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while True:
            b = f.read(blocksize)
            if not b: break
            h.update(b)
    return h.hexdigest()


def main():
    t0 = time.time()
    print(f"Plexis SGP {VERSION} — generating checkpoint...")

    # Catalog
    catalog = pd.read_parquet(ROOT / "catalog/dataset_catalog.parquet")
    feature_catalog = pd.read_parquet(ROOT / "catalog/feature_catalog.parquet")

    # Pipeline log
    pipeline_log = json.load(open(ROOT / "logs/pipeline_run.json")) if (ROOT / "logs/pipeline_run.json").exists() else {}

    # Validator JSONs
    validators = []
    for vp in (ROOT / "hex").glob("*_validation.json"):
        try:
            v = json.load(open(vp))
            checks = v.get("checks", [])
            n_pass = sum(1 for c in checks if c.get("status") == "PASS")
            validators.append({
                "validator": vp.stem,
                "checks_total": len(checks),
                "checks_pass": n_pass,
                "checks_warn": sum(1 for c in checks if c.get("status") == "WARN"),
                "checks_fail": sum(1 for c in checks if c.get("status") == "FAIL"),
            })
        except Exception:
            pass

    # Compute hashes for all parquets + key files
    print("  Hashing parquet files...")
    files_indexed = []
    total_bytes = 0
    for sub in ["hex", "places", "boundaries", "catalog", "logs"]:
        for p in sorted((ROOT / sub).glob("**/*")):
            if not p.is_file(): continue
            sz = p.stat().st_size
            entry = {
                "path": str(p.relative_to(ROOT)),
                "size_bytes": sz,
                "size_mb": round(sz / 1e6, 3),
            }
            # Only hash large outputs (parquet/json) to save time
            if p.suffix in (".parquet", ".json", ".geojson"):
                entry["sha256"] = sha256_file(p)
            files_indexed.append(entry)
            total_bytes += sz

    # Stage roll-up from pipeline log
    stage_summary = {}
    for s in pipeline_log.get("stages", []):
        stage_summary[s["stage"]] = {
            "status": s.get("status"),
            "wall_clock_s": round(s.get("secs", 0), 2),
        }

    # Manifest
    manifest = {
        "version": VERSION,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "pipeline_total_secs": pipeline_log.get("total_secs"),
        "pipeline_run_at": pipeline_log.get("generated_at"),
        "stages": stage_summary,
        "validators": validators,
        "catalog": {
            "datasets": int(len(catalog)),
            "features": int(len(feature_catalog)),
            "features_with_curated_description": int((feature_catalog["description"] != "").sum()),
        },
        "datasets": catalog.to_dict("records"),
        "files_indexed": files_indexed,
        "totals": {
            "files": len(files_indexed),
            "size_bytes": total_bytes,
            "size_mb": round(total_bytes / 1e6, 1),
        },
    }

    # Write JSON
    out_json = ROOT / f"CHECKPOINT_v{VERSION}.json"
    with open(out_json, "w") as f:
        json.dump(manifest, f, indent=2)

    # Write Markdown summary
    md = []
    md.append(f"# Plexis SGP — Checkpoint v{VERSION}")
    md.append("")
    md.append(f"**Generated:** {manifest['generated_at']}  ")
    md.append(f"**Pipeline total:** {manifest['pipeline_total_secs']:.0f}s = {manifest['pipeline_total_secs']/60:.1f} min  ")
    md.append(f"**Datasets:** {manifest['catalog']['datasets']} (in catalog) · **Features:** {manifest['catalog']['features']} ({manifest['catalog']['features_with_curated_description']} with curated descriptions)  ")
    md.append(f"**Files indexed:** {manifest['totals']['files']:,} · **Total size:** {manifest['totals']['size_mb']:,} MB")
    md.append("")

    # Stages
    md.append("## Pipeline stages")
    md.append("")
    md.append("| Stage | Status | Time (s) |")
    md.append("|---|---|---|")
    for sid, s in stage_summary.items():
        md.append(f"| {sid} | {s['status']} | {s['wall_clock_s']:.1f} |")
    md.append("")

    # Validator summary
    md.append("## Validators")
    md.append("")
    md.append("| Validator | Pass | Warn | Fail | Total |")
    md.append("|---|---|---|---|---|")
    for v in validators:
        md.append(f"| `{v['validator']}` | {v['checks_pass']} | {v['checks_warn']} | {v['checks_fail']} | {v['checks_total']} |")
    md.append("")

    # Datasets
    md.append("## Datasets in catalog")
    md.append("")
    md.append("| Dataset | Scale | Rows × Cols | Owner | Description |")
    md.append("|---|---|---|---|---|")
    for d in sorted(manifest["datasets"], key=lambda r: (r["scale"], r["dataset"])):
        md.append(f"| `{d['dataset']}` | {d['scale']} | {d['n_rows']:,} × {d['n_cols']} | {d['owner_stage']} | {d['description']} |")
    md.append("")

    # Top files by size
    big_files = sorted([f for f in files_indexed if "size_mb" in f], key=lambda r: -r["size_mb"])[:15]
    md.append("## Top 15 files by size")
    md.append("")
    md.append("| Path | Size (MB) |")
    md.append("|---|---|")
    for f in big_files:
        md.append(f"| `{f['path']}` | {f['size_mb']:.1f} |")
    md.append("")

    md.append(f"---")
    md.append(f"")
    md.append(f"_Checkpoint manifest: `{out_json.name}`. Atlas-1 backup: `{PLEXIS_VERSION}.tar.gz`._")

    out_md = ROOT / f"CHECKPOINT_v{VERSION}.md"
    out_md.write_text("\n".join(md))

    print(f"\n=== Manifest written ===")
    print(f"  {out_json}")
    print(f"  {out_md}")
    print(f"  size: {os.path.getsize(out_json)/1024:.1f} KB JSON, {os.path.getsize(out_md)/1024:.1f} KB Markdown")
    print(f"\nNext step: tar+gzip the entire plexis-sgp-v4/ to backup")
    print(f"  Wall clock: {time.time()-t0:.1f}s")


if __name__ == "__main__":
    main()
