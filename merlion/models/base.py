"""
Base classes for Layer 1 model execution.

  EmbeddingModel   — 64-d cosine-similarity backend (GCN/Node2Vec/UMAP/Transformer)
  Predictor        — XGBoost-style per-category count predictor
  FeatureTable     — raw feature lookup / composite scoring

All are lazy-loaded and cached via ModelHub.
"""
import os
import time
from typing import Optional

import numpy as np
import pandas as pd


def _log(msg: str):
    print(f"[merlion] {msg}", flush=True)


# ============================================================
# EmbeddingModel
# ============================================================
class EmbeddingModel:
    """64-d cosine-similarity wrapper over a parquet embedding."""

    def __init__(self, name: str, parquet_path: str, col_prefix: str, dims: int = 64):
        self.name = name
        self.path = parquet_path
        self.col_prefix = col_prefix
        self.dims = dims
        self._Z = None           # [N, d] z-standardized + L2-normalized
        self._hex_ids: list[str] = []
        self._hex_to_idx: dict[str, int] = {}

    def load(self):
        if self._Z is not None:
            return
        t0 = time.perf_counter()
        df = pd.read_parquet(self.path)
        if "hex_id" not in df.columns:
            raise ValueError(f"{self.path} missing hex_id column")
        self._hex_ids = df["hex_id"].astype(str).tolist()
        self._hex_to_idx = {h: i for i, h in enumerate(self._hex_ids)}
        cols = [c for c in df.columns if c.startswith(self.col_prefix)][: self.dims]
        Z = df[cols].to_numpy(np.float32)
        # z-standardize per dim
        Z = (Z - Z.mean(axis=0, keepdims=True)) / (Z.std(axis=0, keepdims=True) + 1e-9)
        # L2-normalize rows for cosine
        Z = Z / (np.linalg.norm(Z, axis=1, keepdims=True) + 1e-9)
        self._Z = Z
        _log(f"{self.name}: loaded {Z.shape} in {(time.perf_counter()-t0)*1000:.0f}ms")

    def has(self, hex_id: str) -> bool:
        self.load()
        return hex_id in self._hex_to_idx

    def embedding(self, hex_id: str) -> Optional[np.ndarray]:
        self.load()
        i = self._hex_to_idx.get(hex_id)
        return None if i is None else self._Z[i].copy()

    def similar(self, hex_id: str, k: int = 10) -> list[dict]:
        """Return top-k most similar hexes (excluding self)."""
        self.load()
        i = self._hex_to_idx.get(hex_id)
        if i is None:
            return []
        sims = self._Z @ self._Z[i]
        sims[i] = -np.inf
        top = np.argpartition(-sims, k)[:k]
        top = top[np.argsort(-sims[top])]
        return [{"hex_id": self._hex_ids[j], "score": float(sims[j])} for j in top]

    def similar_to_vector(self, vec: np.ndarray, k: int = 10,
                          exclude: Optional[set] = None) -> list[dict]:
        """Similar to an arbitrary vector (e.g. centroid of multiple hexes)."""
        self.load()
        v = vec / (np.linalg.norm(vec) + 1e-9)
        sims = self._Z @ v
        if exclude:
            for h in exclude:
                if h in self._hex_to_idx:
                    sims[self._hex_to_idx[h]] = -np.inf
        top = np.argpartition(-sims, k)[:k]
        top = top[np.argsort(-sims[top])]
        return [{"hex_id": self._hex_ids[j], "score": float(sims[j])} for j in top]

    def centroid(self, hex_ids: list[str]) -> Optional[np.ndarray]:
        self.load()
        ixs = [self._hex_to_idx[h] for h in hex_ids if h in self._hex_to_idx]
        if not ixs:
            return None
        return self._Z[ixs].mean(axis=0)


# ============================================================
# XGBoost Predictor (24 category models)
# ============================================================
class XGBoostPredictor:
    def __init__(self, models_dir: str,
                 features_path: str,
                 bundle_path: Optional[str] = None):
        self.models_dir = models_dir
        self.features_path = features_path
        self.bundle_path = bundle_path
        self._models: dict = {}
        self._features = None      # DataFrame with hex_id + 391 normalized features
        self._feat_cols: list = []
        self._bundle = None        # Optional pre-computed predictions bundle
        self._loaded = False

    def load(self):
        if self._loaded:
            return
        t0 = time.perf_counter()
        # Pre-computed predictions from the shareable bundle (fast path)
        if self.bundle_path and os.path.exists(self.bundle_path):
            self._bundle = pd.read_parquet(self.bundle_path).set_index("hex_id")
            _log(f"xgboost: loaded pre-computed predictions from bundle")
        # Also make raw features available for on-demand predictions
        if os.path.exists(self.features_path):
            self._features = pd.read_parquet(self.features_path)
            ID = {"hex_id","lat","lng","area_km2","parent_subzone","parent_subzone_name",
                  "parent_pa","parent_region"}
            BK = {"subzone_pop_total","subzone_res_floor_area","residential_floor_weight"}
            self._feat_cols = [c for c in self._features.columns
                               if c not in ID and c not in BK and not c.startswith("pc_")]
        # Lazy model loading happens per-category on demand
        self._loaded = True
        _log(f"xgboost: ready in {(time.perf_counter()-t0)*1000:.0f}ms")

    def _get_model(self, category: str):
        """Lazy-load a single category's XGBoost JSON."""
        if category in self._models:
            return self._models[category]
        try:
            import xgboost as xgb
        except ImportError:
            return None
        path = os.path.join(self.models_dir, f"pc_cat_{category}.json")
        if not os.path.exists(path):
            return None
        booster = xgb.Booster()
        booster.load_model(path)
        self._models[category] = booster
        return booster

    def list_categories(self) -> list[str]:
        self.load()
        if self._bundle is not None:
            return [c.replace("pred_", "") for c in self._bundle.columns
                    if c.startswith("pred_")]
        if not os.path.isdir(self.models_dir):
            return []
        return [f.replace("pc_cat_", "").replace(".json", "")
                for f in os.listdir(self.models_dir) if f.endswith(".json")]

    def predict(self, hex_id: str, categories: Optional[list[str]] = None) -> dict:
        """Return {category: predicted_count} for this hex. Uses bundle if available."""
        self.load()
        cats = categories or self.list_categories()
        out = {}
        # Fast path: pre-computed bundle
        if self._bundle is not None and hex_id in self._bundle.index:
            for c in cats:
                key = f"pred_{c}"
                if key in self._bundle.columns:
                    # bundle stores log-space, convert to count
                    val = float(self._bundle.loc[hex_id, key])
                    out[c] = float(max(0.0, np.expm1(val)))
            if out:
                return out
        return out

    def actual(self, hex_id: str, categories: Optional[list[str]] = None) -> dict:
        """Return {category: actual_count} from the raw feature table (pc_cat_*)."""
        self.load()
        if self._features is None:
            return {}
        row = self._features[self._features["hex_id"] == hex_id]
        if row.empty:
            return {}
        cats = categories or self.list_categories()
        return {c: float(row[f"pc_cat_{c}"].values[0])
                for c in cats if f"pc_cat_{c}" in row.columns}

    def gap(self, hex_id: str, categories: Optional[list[str]] = None) -> dict:
        """Return {category: pred - actual} gap per category."""
        preds = self.predict(hex_id, categories)
        actuals = self.actual(hex_id, categories)
        return {c: preds.get(c, 0.0) - actuals.get(c, 0.0)
                for c in (categories or list(preds.keys()))}

    def predict_all_hexes(self, category: str) -> pd.Series:
        """Return pred for this category for ALL hexes (for rollups)."""
        self.load()
        key = f"pred_{category}"
        if self._bundle is not None and key in self._bundle.columns:
            return np.expm1(self._bundle[key].clip(lower=0))
        return pd.Series(dtype=float)

    def actual_all_hexes(self, category: str) -> pd.Series:
        self.load()
        key = f"pc_cat_{category}"
        if self._features is None or key not in self._features.columns:
            return pd.Series(dtype=float)
        return pd.Series(self._features[key].values,
                         index=self._features["hex_id"].values)


# ============================================================
# FeatureTable — raw features + identity lookup
# ============================================================
class FeatureTable:
    def __init__(self, raw_path: str, norm_path: str):
        self.raw_path = raw_path
        self.norm_path = norm_path
        self._raw = None          # with lat/lng/parent_subzone/parent_pa
        self._norm = None

    def load(self):
        if self._raw is not None:
            return
        t0 = time.perf_counter()
        self._raw = pd.read_parquet(self.raw_path)
        self._norm = pd.read_parquet(self.norm_path)
        _log(f"features: loaded raw {self._raw.shape} + norm {self._norm.shape} "
             f"in {(time.perf_counter()-t0)*1000:.0f}ms")

    def identity(self, hex_id: str) -> dict:
        """Lat/lng, subzone, PA for a hex."""
        self.load()
        row = self._raw[self._raw["hex_id"] == hex_id]
        if row.empty:
            return {"hex_id": hex_id, "found": False}
        r = row.iloc[0]
        return {
            "hex_id": hex_id,
            "lat": float(r.get("lat", 0)),
            "lng": float(r.get("lng", 0)),
            "parent_subzone": str(r.get("parent_subzone", "")),
            "parent_subzone_name": str(r.get("parent_subzone_name", "")),
            "parent_pa": str(r.get("parent_pa", "")),
            "parent_region": str(r.get("parent_region", "")),
            "found": True,
        }

    def get(self, hex_id: str, col: str) -> Optional[float]:
        self.load()
        row = self._raw[self._raw["hex_id"] == hex_id]
        if row.empty or col not in row.columns:
            return None
        return float(row[col].values[0])

    def hexes_in_pa(self, pa: str) -> list[str]:
        self.load()
        return self._raw.loc[self._raw["parent_pa"] == pa, "hex_id"].astype(str).tolist()

    def all_hex_ids(self) -> list[str]:
        self.load()
        return self._raw["hex_id"].astype(str).tolist()

    def raw_df(self) -> pd.DataFrame:
        self.load()
        return self._raw

    def norm_df(self) -> pd.DataFrame:
        self.load()
        return self._norm
