"""
Merlion — central entry point.

Wires together: Intent → Use Case → Model layers.
Currently stubs Layer 1 (models) — returns structured routing info for v0.1.

Usage:
  from merlion import Merlion

  m = Merlion()                              # rule-based intent only
  m = Merlion(use_llm=True)                  # also tries Claude Sonnet
  m = Merlion(use_llm=True, api_key="...")   # pass key explicitly

  result = m.ask("find 20 sites similar to tanjong pagar for a cafe")
  # → classified intent, routed to site_selection, returns stub for now

  result = m.run("archetype_clustering", k=15)   # direct call, skip intent layer
"""
import os
from typing import Optional

from .intent.parser import IntentParser, Intent
from .use_cases.registry import UseCaseRegistry


class Merlion:
    """Orchestrator sitting over intent + use case + model layers."""

    def __init__(
        self,
        use_llm: bool = False,
        api_key: Optional[str] = None,
        llm_model: str = "claude-sonnet-4-6",
        registry: Optional[UseCaseRegistry] = None,
    ):
        self.registry = registry or UseCaseRegistry()
        self.llm_backend = None
        if use_llm:
            try:
                from .intent.llm_backend import ClaudeIntentBackend
                self.llm_backend = ClaudeIntentBackend(api_key=api_key, model=llm_model)
            except Exception as e:
                # Soft-fail: rule-based still works
                print(f"[merlion] Warning: LLM backend disabled ({e})")
        self.parser = IntentParser(llm_backend=self.llm_backend)

    # ============================================================
    # High-level entry points
    # ============================================================
    def ask(self, query: str, top_n: int = 3) -> dict:
        """
        Natural-language entry. Returns dict with:
          intents  — list of top-N candidate Intents
          chosen   — the selected Intent (highest confidence)
          result   — result from running the chosen use case
        """
        intents = self.parser.parse(query, top_n=top_n)

        # Case 1: rule-based confidence low → full LLM classification
        if self.llm_backend and (not intents or intents[0].confidence < 0.7):
            llm_data = self.llm_backend(query)
            if llm_data and llm_data.get("use_case") != "unknown":
                intents = [Intent(
                    use_case=llm_data["use_case"],
                    entities=llm_data.get("entities", {}),
                    confidence=llm_data.get("confidence", 0.7),
                    raw_query=query,
                    strategy="llm",
                )] + intents

        # Case 2: rule-based is confident BUT entities look incomplete for this
        # use case → use LLM as entity extractor (don't override use_case).
        # This handles novel brands / places the rule vocab doesn't know.
        elif self.llm_backend and intents:
            top = intents[0]
            uc = top.use_case
            ents = top.entities or {}
            needs_brand = uc in ("site_selection", "whitespace_analysis") and not (
                ents.get("brands") or ents.get("brand")
            )
            needs_cat = uc in ("gap_analysis", "category_prediction") and not (
                ents.get("categories") or ents.get("category")
            )
            needs_loc_or_hex = uc in ("comparable_market", "site_selection") and not (
                ents.get("locations") or ents.get("location") or
                ents.get("hex_ids") or ents.get("target_hex") or ents.get("coords")
            )
            if needs_brand or needs_cat or needs_loc_or_hex:
                llm_data = self.llm_backend(query)
                if llm_data:
                    # Merge: LLM entities win where rule-based found nothing
                    merged = {**(llm_data.get("entities") or {}), **ents}
                    top.entities = merged
                    top.strategy = "rule_based+llm_entities"

        if not intents:
            return {
                "intents": [],
                "chosen": None,
                "result": {"error": "Could not classify intent",
                           "available_use_cases": self.registry.names()},
            }
        chosen = intents[0]
        result = self.registry.run(chosen.use_case, chosen.entities, atlas_ctx=self)
        # Attach plain-English explanation
        from .explain import explain_result
        result["explain"] = explain_result(chosen.use_case, result, query=query)
        return {
            "intents": [i.to_dict() for i in intents],
            "chosen": chosen.to_dict(),
            "result": result,
        }

    def run(self, use_case: str, **params) -> dict:
        """Direct API: skip intent layer, call a use case by name."""
        result = self.registry.run(use_case, params, atlas_ctx=self)
        from .explain import explain_result
        result["explain"] = explain_result(use_case, result, query=str(params))
        return result

    def use_cases(self) -> list[dict]:
        """List all registered use cases with descriptions."""
        return self.registry.describe()
