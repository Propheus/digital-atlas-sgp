"""Synthesizer agent — UCS + catalog → list of feature proposals (with code)."""
import json
from ..api import call

SYSTEM = """You are a feature engineer extending the Plexis SGP atlas.

Given a Use Case Spec and a summary of existing features, propose 5-10 NEW
features that would help the use case but are NOT yet in the atlas.

Each proposal must be one of three types:
  - "derive":   computable from existing columns via a single Python expression
                operating on a pandas DataFrame named `df`. Must produce a new
                column directly assigned: df['new_name'] = ...
                Use only NumPy (np) / pandas operations. No imports needed
                (np and pd are available). No multi-line code, no loops.
  - "external": needs a new external data source not in the atlas. Name it.
  - "learned":  needs a model to train (skip for now — mark and explain).

Be SPECIFIC about which existing columns the derive code uses. The execution
sandbox has only the master parquet's columns plus np / pd. If you reference
a column that doesn't exist, the build fails.

GOOD example:
{
  "name": "knowledge_worker_intensity",
  "description": "Density of business-office places weighted by walkability",
  "scale": "hex9",
  "dtype": "float32",
  "derivation_type": "derive",
  "code": "df['knowledge_worker_intensity'] = (df['pc_cat_business_office'].fillna(0) * df['walkability_score'].fillna(0)).astype('float32')",
  "dependencies": ["pc_cat_business_office", "walkability_score"],
  "rationale": "Cafés depend on knowledge workers who cluster around offices in walkable zones."
}

BAD example (don't do this):
- code with `import` (not allowed)
- code referencing a column that's not in dependencies
- code with for-loops or multi-line statements
- proposing a feature that already exists with a different name

Return JSON with EXACTLY this schema:
{
  "proposed_features": [
    {
      "name": "<snake_case>",
      "description": "<one sentence>",
      "scale": "hex9" | "hex8" | "subzone" | "place",
      "dtype": "float32" | "float64" | "int32" | "int64" | "bool",
      "derivation_type": "derive" | "external" | "learned",
      "code": "<python expression assigning to df['<name>']; only for derive>",
      "dependencies": ["col1", "col2"],
      "external_source": "<source name; only for external>",
      "rationale": "<why this helps the use case>"
    }
  ]
}"""


def synthesize(ucs: dict, catalog_summary: str, sample_columns: list) -> dict:
    user = (
        f"USE CASE SPEC:\n{json.dumps(ucs, indent=2)}\n\n"
        f"EXISTING FEATURES (by scale and family):\n{catalog_summary}\n\n"
        f"SAMPLE OF AVAILABLE COLUMNS at the target scale (these are real column "
        f"names you can use in derive code):\n{', '.join(sample_columns[:200])}"
    )
    return call(SYSTEM, user, max_tokens=8000, json_mode=True)
