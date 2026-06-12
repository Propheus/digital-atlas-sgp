"""Anthropic API wrapper. Loads key from env or ~/notes/anthrophic-key.txt."""
import json, os
from pathlib import Path
from anthropic import Anthropic

# Default to Opus 4.5; override via env
MODEL = os.environ.get("EXTENDER_MODEL", "claude-opus-4-5")
KEY_FILE = Path.home() / "notes" / "anthrophic-key.txt"


def _load_key() -> str:
    if k := os.environ.get("ANTHROPIC_API_KEY"):
        return k
    if KEY_FILE.exists():
        for line in KEY_FILE.read_text().splitlines():
            if "ANTHROPIC_API_KEY" in line and "=" in line:
                v = line.split("=", 1)[1].strip().strip('"').strip("'")
                if v: return v
    raise SystemExit("No ANTHROPIC_API_KEY found (env or ~/notes/anthrophic-key.txt)")


_client = None
def client() -> Anthropic:
    global _client
    if _client is None:
        _client = Anthropic(api_key=_load_key())
    return _client


def call(system: str, user: str, max_tokens: int = 4096,
         temperature: float = 0.3, json_mode: bool = True,
         thinking_budget: int = 0):
    """Single Opus call. Set thinking_budget>0 to enable extended thinking (8000 typical)."""
    if json_mode:
        system = system.rstrip() + "\n\nRESPOND ONLY WITH VALID JSON. No prose, no markdown fences."

    kwargs = dict(
        model=MODEL,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    if thinking_budget > 0:
        # Extended thinking — Opus reasons internally before responding
        kwargs["thinking"] = {"type": "enabled", "budget_tokens": thinking_budget}
        kwargs["temperature"] = 1.0  # required when thinking is enabled
    else:
        kwargs["temperature"] = temperature

    msg = client().messages.create(**kwargs)
    # Extract the final text block (skip thinking blocks)
    txt = ""
    for block in msg.content:
        if getattr(block, "type", None) == "text":
            txt = block.text
            break
    txt = txt.strip()

    if json_mode:
        # Strip ```json ... ``` if model wraps anyway
        if txt.startswith("```"):
            txt = txt.split("```")[1]
            if txt.startswith("json"):
                txt = txt[4:]
            txt = txt.strip()
        try:
            return json.loads(txt)
        except json.JSONDecodeError as e:
            raise SystemExit(f"Invalid JSON from Opus:\n{txt[:500]}\n\nError: {e}")
    return txt
