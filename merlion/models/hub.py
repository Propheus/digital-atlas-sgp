"""
ModelHub — singleton that lazy-loads and caches all models.

Usage:
  from merlion.models.hub import hub
  hub.gcn.similar(hex_id, k=10)
  hub.xgboost.predict(hex_id)
  hub.features.identity(hex_id)
"""
from .base import EmbeddingModel, XGBoostPredictor, FeatureTable
from .registry import MODELS


class ModelHub:
    def __init__(self):
        self._cache: dict = {}

    def _embed(self, name: str, col_prefix: str) -> EmbeddingModel:
        if name in self._cache:
            return self._cache[name]
        spec = MODELS.get(name)
        if spec is None:
            raise ValueError(f"No spec for model {name}")
        m = EmbeddingModel(name=name, parquet_path=spec.data_path,
                           col_prefix=col_prefix, dims=spec.dims)
        self._cache[name] = m
        return m

    @property
    def gcn(self) -> EmbeddingModel:
        return self._embed("gcn", col_prefix="g")

    @property
    def node2vec(self) -> EmbeddingModel:
        return self._embed("node2vec", col_prefix="n")

    @property
    def umap(self) -> EmbeddingModel:
        return self._embed("umap", col_prefix="u")

    @property
    def transformer(self) -> EmbeddingModel:
        return self._embed("transformer", col_prefix="t")

    @property
    def xgboost(self) -> XGBoostPredictor:
        if "xgboost" not in self._cache:
            xgb_spec = MODELS["xgboost"]
            feat_spec = MODELS["raw_features"]
            bundle_spec = MODELS["bundle"]
            self._cache["xgboost"] = XGBoostPredictor(
                models_dir=xgb_spec.data_path,
                features_path=feat_spec.data_path,
                bundle_path=bundle_spec.data_path,
            )
        return self._cache["xgboost"]

    @property
    def features(self) -> FeatureTable:
        if "features" not in self._cache:
            feat_spec = MODELS["raw_features"]
            # raw_features in registry points to normalized; we also need the raw
            # hex_features_v10.parquet for identity / raw values.
            import os
            raw_path = feat_spec.data_path.replace("_normalized.parquet", ".parquet")
            if not os.path.exists(raw_path):
                raw_path = feat_spec.data_path  # fallback
            self._cache["features"] = FeatureTable(
                raw_path=raw_path,
                norm_path=feat_spec.data_path,
            )
        return self._cache["features"]

    def get_embedding_model(self, name: str) -> EmbeddingModel:
        """Fetch any embedding model by its registry name."""
        if name == "gcn": return self.gcn
        if name == "node2vec": return self.node2vec
        if name == "umap": return self.umap
        if name == "transformer": return self.transformer
        raise ValueError(f"Unknown embedding model: {name}")


# Singleton
hub = ModelHub()
