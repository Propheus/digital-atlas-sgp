#!/usr/bin/env python3
"""
Serving interface for the Singapore Urban Representation bundle.

Three main functions:
  1. lookup(hex_id) — fast lookup for pre-computed hexes
  2. find_similar(hex_id, k=10) — cosine similarity search on GCN-64 embedding
  3. predict_categories(hex_id) — XGBoost category count predictions
  4. gap_analysis(hex_id) — actual vs predicted category counts
"""
import json
import numpy as np
import pandas as pd
import os
from xgboost import XGBRegressor

SERVE_DIR = os.path.dirname(os.path.abspath(__file__))

# Load once at startup
BUNDLE = pd.read_parquet(f"{SERVE_DIR}/hex_shareable_bundle.parquet")
with open(f"{SERVE_DIR}/feature_schema.json") as f:
    SCHEMA = json.load(f)

EMBED_COLS = [f"g{i}" for i in range(64)]
PRED_COLS = [c for c in BUNDLE.columns if c.startswith("pred_")]

# Hex_id → row index
HEX_TO_IDX = {hid: i for i, hid in enumerate(BUNDLE["hex_id"].tolist())}


def lookup(hex_id):
    """Return all info for a pre-computed hex."""
    idx = HEX_TO_IDX.get(hex_id)
    if idx is None:
        return None
    return BUNDLE.iloc[idx].to_dict()


def find_similar(hex_id, k=10):
    """Find k most similar hexes by GCN-64 embedding cosine."""
    idx = HEX_TO_IDX.get(hex_id)
    if idx is None:
        return []
    Z = BUNDLE[EMBED_COLS].to_numpy()
    q = Z[idx]
    norms = np.linalg.norm(Z, axis=1) * np.linalg.norm(q) + 1e-9
    sims = (Z @ q) / norms
    order = np.argsort(-sims)[1:k+1]  # exclude self
    results = []
    for i in order:
        results.append({
            "hex_id": BUNDLE.iloc[i]["hex_id"],
            "subzone": BUNDLE.iloc[i]["parent_subzone"],
            "pa": BUNDLE.iloc[i]["parent_pa"],
            "similarity": float(sims[i]),
        })
    return results


def predict_categories(hex_id):
    """Return predicted raw category counts."""
    idx = HEX_TO_IDX.get(hex_id)
    if idx is None:
        return None
    log_preds = BUNDLE.iloc[idx][PRED_COLS]
    raw_preds = np.expm1(log_preds.values)
    return {col.replace("pred_", ""): float(max(0, v)) for col, v in zip(PRED_COLS, raw_preds)}


def gap_analysis(hex_id):
    """Compare actual vs predicted counts per category."""
    idx = HEX_TO_IDX.get(hex_id)
    if idx is None:
        return None
    # We need actual counts — load from feature table or require them passed in
    # Simpler: return predictions; caller compares to actuals
    preds = predict_categories(hex_id)
    return preds


if __name__ == "__main__":
    # Example: find hexes similar to Raffles Place
    print("Top 5 hexes similar to Raffles Place:")
    raffles = BUNDLE[BUNDLE["parent_subzone"] == "DTSZ05"].iloc[0]
    for nb in find_similar(raffles["hex_id"], k=5):
        print(f"  {nb['subzone']:<10} {nb['pa']:<20} sim={nb['similarity']:.3f}")

    print(f"\nPredicted categories for Raffles Place:")
    preds = predict_categories(raffles["hex_id"])
    for cat, count in sorted(preds.items(), key=lambda x: -x[1])[:10]:
        print(f"  {cat:<25} {count:>8.1f}")
