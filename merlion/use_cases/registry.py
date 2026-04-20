"""
Use Case registry — maps canonical use case names to (description, handler, models).

Each handler is a callable(params_dict, atlas_ctx) -> result_dict.
Model choices are driven by our empirical 4-way test evidence:
  - Node2Vec wins structural similarity (PA coherence, landmarks)
  - GCN wins feature-aware clustering (archetype stability, feature query)
  - UMAP wins nonlinear manifold (functional PA cohesion)
  - XGBoost native for predictions (R²=0.80)

This v1 registers stubs for the 5 highest-value use cases. Each stub currently
returns a structured placeholder explaining what it WOULD do. The actual model
calls are marked TODO — to be wired in Layer 1 (models/).
"""
from dataclasses import dataclass, field
from typing import Any, Callable, Optional


@dataclass
class UseCase:
    name: str
    description: str
    primary_model: str
    augment_models: list[str] = field(default_factory=list)
    strategy: str = "single"
    handler: Optional[Callable] = None


# Real handlers wired in Layer 1 (merlion/use_cases/handlers.py).
# If a use case has no handler registered there, we fall back to a stub.
try:
    from .handlers import HANDLERS as _REAL_HANDLERS
except Exception as e:  # pragma: no cover
    print(f"[merlion] WARNING: could not load real handlers ({e}); using stubs.")
    _REAL_HANDLERS = {}


def _stub(use_case_name: str):
    def handler(params: dict, atlas_ctx: Any = None) -> dict:
        return {
            "use_case": use_case_name,
            "status": "stub",
            "message": f"Use case '{use_case_name}' resolved but no real handler wired.",
            "inputs": params,
        }
    return handler


def _get_handler(name: str):
    return _REAL_HANDLERS.get(name, _stub(name))


# ============================================================
# REGISTRY (canonical use cases + model choices)
# ============================================================
_DEFAULT_USE_CASES = [
    UseCase(
        name="site_selection",
        description="Find hexes similar to anchor stores for brand expansion.",
        primary_model="node2vec",       # winner at PA coherence 98%
        augment_models=["gcn"],          # feature filter
        strategy="rank_fusion_rrf",
        handler=_get_handler("site_selection"),
    ),
    UseCase(
        name="gap_analysis",
        description="Find hexes where predicted category count exceeds actual.",
        primary_model="xgboost",         # native for prediction R²=0.80
        augment_models=[],
        strategy="single",
        handler=_get_handler("gap_analysis"),
    ),
    UseCase(
        name="archetype_clustering",
        description="Segment SGP into 10–20 urban archetypes via k-means.",
        primary_model="gcn",             # 100% stability vs Node2Vec 60%
        augment_models=[],
        strategy="kmeans",
        handler=_get_handler("archetype_clustering"),
    ),
    UseCase(
        name="comparable_market",
        description="Find comparable hexes for property valuation.",
        primary_model="node2vec",        # PA coherence + landmark wins
        augment_models=["gcn"],          # GCN intersection for confidence
        strategy="intersection",
        handler=_get_handler("comparable_market"),
    ),
    UseCase(
        name="whitespace_analysis",
        description="Hexes where a brand fits but is absent.",
        primary_model="gcn",             # feature-aware centroid match
        augment_models=["node2vec"],
        strategy="filter_chain",
        handler=_get_handler("whitespace_analysis"),
    ),
    UseCase(
        name="category_prediction",
        description="Predicted count per category for a given hex.",
        primary_model="xgboost",
        augment_models=[],
        strategy="single",
        handler=_get_handler("category_prediction"),
    ),
    UseCase(
        name="feature_query",
        description="Retrieve hexes matching a feature profile.",
        primary_model="gcn",             # 100% on feature_query tests
        augment_models=["umap"],
        strategy="single",
        handler=_get_handler("feature_query"),
    ),
    UseCase(
        name="amenity_desert",
        description="Hexes where population is under-served in key categories.",
        primary_model="xgboost",
        augment_models=[],
        strategy="single",
        handler=_get_handler("amenity_desert"),
    ),
    UseCase(
        name="fifteen_minute_city",
        description="Walkability × category-access scorecard per hex.",
        primary_model="raw_features",
        augment_models=[],
        strategy="single",
        handler=_get_handler("fifteen_minute_city"),
    ),
]


class UseCaseRegistry:
    """Central lookup. Swap models by updating this class or subclassing."""

    def __init__(self, use_cases: Optional[list[UseCase]] = None):
        self._cases: dict[str, UseCase] = {}
        for uc in (use_cases or _DEFAULT_USE_CASES):
            self._cases[uc.name] = uc

    def get(self, name: str) -> Optional[UseCase]:
        return self._cases.get(name)

    def names(self) -> list[str]:
        return list(self._cases.keys())

    def describe(self) -> list[dict]:
        return [
            {
                "name": uc.name,
                "description": uc.description,
                "primary_model": uc.primary_model,
                "augment_models": uc.augment_models,
                "strategy": uc.strategy,
            }
            for uc in self._cases.values()
        ]

    def register(self, use_case: UseCase):
        self._cases[use_case.name] = use_case

    def run(self, name: str, params: dict, atlas_ctx: Any = None) -> dict:
        uc = self.get(name)
        if uc is None:
            return {"error": f"Unknown use case: {name}",
                    "available": self.names()}
        if uc.handler is None:
            return {"error": f"No handler registered for {name}"}
        result = uc.handler(params, atlas_ctx)
        # Attach metadata about which models would be used
        result.setdefault("meta", {})
        result["meta"].update({
            "primary_model": uc.primary_model,
            "augment_models": uc.augment_models,
            "strategy": uc.strategy,
        })
        return result
