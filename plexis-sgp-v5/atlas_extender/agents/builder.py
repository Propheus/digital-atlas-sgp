"""Builder — execute KEEP/REVISE features against the master parquet (sandboxed)."""
from pathlib import Path
import pandas as pd
import numpy as np

ROOT = Path("/home/azureuser/plexis-sgp-v4")


def build(decisions: list, scale: str = "hex9") -> dict:
    """Apply KEEP and REVISE decisions to the master bundle. Returns
    {df, added, failed, source_path}."""
    source_path = ROOT / "hex" / f"{scale}_all_features.parquet"
    if not source_path.exists():
        # Fallback for places scale
        source_path = ROOT / "places" / "sgp_places_final.parquet"
    df = pd.read_parquet(source_path)
    n_cols_before = len(df.columns)

    added, failed = [], []

    for d in decisions:
        if d.get("decision") not in ("KEEP", "REVISE"):
            continue
        feat = d["feature"]
        code = d.get("revised_code") or d.get("code") or ""
        if not code:
            failed.append({"feature": feat, "reason": "no code provided"})
            continue

        # Sandboxed namespace — only df + np + pd
        safe_ns = {"df": df, "pd": pd, "np": np, "__builtins__": {
            "min": min, "max": max, "abs": abs, "len": len, "round": round,
            "int": int, "float": float, "str": str, "bool": bool, "list": list,
            "dict": dict, "tuple": tuple, "set": set, "range": range, "True": True,
            "False": False, "None": None,
        }}

        try:
            exec(code, safe_ns)
        except Exception as e:
            failed.append({"feature": feat, "reason": f"exec error: {str(e)[:200]}"})
            continue

        df = safe_ns["df"]
        if feat not in df.columns:
            failed.append({"feature": feat, "reason": f"code did not create column '{feat}'"})
            continue

        col = df[feat]
        if col.isna().all():
            failed.append({"feature": feat, "reason": "all NaN"})
            df = df.drop(columns=[feat])
            continue

        info = {
            "feature": feat,
            "dtype": str(col.dtype),
            "non_null": int(col.notna().sum()),
            "null_pct": round(col.isna().mean() * 100, 2),
        }
        if pd.api.types.is_numeric_dtype(col):
            info.update({
                "median": float(col.median()) if col.notna().any() else None,
                "min": float(col.min()) if col.notna().any() else None,
                "max": float(col.max()) if col.notna().any() else None,
            })
        added.append(info)

    return {
        "df": df,
        "added": added,
        "failed": failed,
        "source_path": str(source_path),
        "n_cols_before": n_cols_before,
        "n_cols_after": len(df.columns),
    }
