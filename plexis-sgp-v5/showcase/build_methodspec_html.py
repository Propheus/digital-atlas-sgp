"""Render the portable Plexis-E hybrid method spec (Markdown) as a themed HTML page."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from report_theme import page
import markdown

HERE = Path(__file__).parent
ROOT = Path.home() / "da-sgp" / "v5"
md = (HERE / "PLEXIS_E_HYBRID_METHOD.md").read_text()
html_body = markdown.markdown(md, extensions=["tables", "fenced_code", "sane_lists", "md_in_html"])
out = ROOT / "showcase" / "PLEXIS_E_HYBRID_METHOD.html"
out.write_text(page("Plexis-E — the Hybrid Representation Method", html_body))
print(f"wrote {out} ({len(out.read_text())/1024:.0f} KB)")
