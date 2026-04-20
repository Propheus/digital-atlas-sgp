"""
Merlion — Singapore urban intelligence orchestrator.

3-layer architecture over the SGP hex embedding bundle:
  Intent layer    → natural language / structured queries → use case + params
  Use case layer  → named operations (site_selection, gap_analysis, ...)
  Model layer     → atomic ops over GCN / Node2Vec / UMAP / XGBoost / Raw

Usage:
  from merlion import Merlion
  m = Merlion()
  result = m.ask("find sites similar to tanjong pagar for a cafe brand")
  # or direct:
  result = m.run("site_selection", anchor_hexes=[...], brand="Cafe X")
"""
from .atlas import Merlion
from .intent.parser import IntentParser, Intent
from .use_cases.registry import UseCaseRegistry

__version__ = "0.1.0"
__all__ = ["Merlion", "IntentParser", "Intent", "UseCaseRegistry"]
