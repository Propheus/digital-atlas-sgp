"""
Model Registry — maps model names (as referenced in use_cases/registry.py)
to their backing artifacts on disk.

This is the single source of truth for:
  - which file backs each model
  - which test evidence justifies its use
  - which capabilities it supports (similar, predict, cluster, ...)
"""
import os
from dataclasses import dataclass, field

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA = os.path.join(ROOT, "data", "hex_v10")


@dataclass
class ModelSpec:
    name: str                     # canonical name used in use_cases/registry.py
    kind: str                     # "embedding" | "predictor" | "feature_table" | "graph"
    data_path: str                # parquet/npz/etc backing this model
    dims: int = 0                 # embedding dim if applicable (0 for non-embedding)
    capabilities: list[str] = field(default_factory=list)  # similar, predict, cluster, ...
    empirical_evidence: str = ""  # which test categories this model wins/ties
    description: str = ""


# ============================================================
# Canonical model specs
# Empirical evidence from 260-test head-to-head (EMBEDDING_4WAY_COMPARISON.html)
# ============================================================
MODELS = {

    "gcn": ModelSpec(
        name="gcn",
        kind="embedding",
        data_path=os.path.join(DATA, "gcn_results", "gcn_embedding_64.parquet"),
        dims=64,
        capabilities=["similar", "cluster", "feature_query", "transfer"],
        empirical_evidence=(
            "100% archetype_stability (vs Node2Vec 60%), 100% feature_query "
            "(vs Node2Vec 50%), 100% anti_similarity, 100% graph_smoothness. "
            "The only embedding combining graph + feature signals."
        ),
        description="Dual-graph GCN with masked category prediction; 64 dims.",
    ),

    "node2vec": ModelSpec(
        name="node2vec",
        kind="embedding",
        data_path=os.path.join(DATA, "baselines", "node2vec_64.parquet"),
        dims=64,
        capabilities=["similar", "cluster"],
        empirical_evidence=(
            "80% overall — best on graph-structural tasks: 98% pa_coherence, "
            "97% landmark, 65% robustness. Weak on feature_query (50%)."
        ),
        description="Random-walk graph embedding via skip-gram on influence graph; 64 dims.",
    ),

    "umap": ModelSpec(
        name="umap",
        kind="embedding",
        data_path=os.path.join(DATA, "baselines", "umap_64.parquet"),
        dims=64,
        capabilities=["similar", "cluster", "feature_query"],
        empirical_evidence=(
            "71% overall — best on functional-group cohesion (90%), strong on "
            "feature_query (100%). Weak on robustness (20%)."
        ),
        description="Nonlinear manifold of 391 raw features; 64 dims.",
    ),

    "transformer": ModelSpec(
        name="transformer",
        kind="embedding",
        data_path=os.path.join(DATA, "baselines", "transformer_64.parquet"),
        dims=64,
        capabilities=["similar", "feature_query"],
        empirical_evidence=(
            "59% overall — wins no category outright. Only competitive on "
            "feature_query (100%)."
        ),
        description="Masked-feature self-attention Transformer; 64 dims.",
    ),

    "xgboost": ModelSpec(
        name="xgboost",
        kind="predictor",
        data_path=os.path.join(DATA, "serving", "xgboost_models"),
        dims=24,
        capabilities=["predict", "gap"],
        empirical_evidence=(
            "R²=0.80 on 24-category count prediction — best prediction tool. "
            "Weak on similarity (43% overall pass)."
        ),
        description="24 XGBoost regressors, one per category; JSON format.",
    ),

    "xgboost_predictor": ModelSpec(  # alias used in use_cases registry
        name="xgboost_predictor",
        kind="predictor",
        data_path=os.path.join(DATA, "serving", "xgboost_models"),
        dims=24,
        capabilities=["predict", "gap"],
        empirical_evidence="Alias for 'xgboost'.",
        description="Alias: same 24 XGBoost regressors.",
    ),

    "raw_features": ModelSpec(
        name="raw_features",
        kind="feature_table",
        data_path=os.path.join(DATA, "hex_features_v10_normalized.parquet"),
        dims=391,
        capabilities=["supervised", "composite_score", "filter"],
        empirical_evidence=(
            "Used for composite metrics (15-min city), supervised downstream "
            "training, and rule-based filters. Full-dim source of truth."
        ),
        description="391 normalized features per hex; ground truth for training.",
    ),

    "bundle": ModelSpec(
        name="bundle",
        kind="feature_table",
        data_path=os.path.join(DATA, "hex_shareable_bundle.parquet"),
        dims=93,
        capabilities=["lookup", "compose"],
        empirical_evidence="Pre-computed 64-d GCN + 24-d XGBoost preds + identity.",
        description="Shareable bundle — 7,318 × 93 columns.",
    ),

    "graph": ModelSpec(
        name="graph",
        kind="graph",
        data_path=os.path.join(DATA, "hex_influence_graph.npz"),
        dims=0,
        capabilities=["neighbor_lookup", "propagation"],
        empirical_evidence="Dual-graph adjacency: 47K edges (spatial + transit).",
        description="Sparse adjacency matrix for influence graph.",
    ),
}


def get(name: str) -> ModelSpec | None:
    return MODELS.get(name)


def all_specs() -> list[ModelSpec]:
    return list(MODELS.values())


def validate_paths() -> dict:
    """Check that each model's backing file exists on disk. Returns report."""
    report = {}
    for name, spec in MODELS.items():
        exists = os.path.exists(spec.data_path)
        report[name] = {
            "path": spec.data_path,
            "exists": exists,
            "kind": spec.kind,
            "dims": spec.dims,
        }
    return report
