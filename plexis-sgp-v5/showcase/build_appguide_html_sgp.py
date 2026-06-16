"""Render the Atlas V5 App Builder's Guide (Markdown) as a themed HTML page."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from report_theme import page

HERE = Path(__file__).parent
ROOT = Path.home() / "da-sgp" / "v5"
md = (HERE / "ATLAS_V5_APP_GUIDE.md").read_text()
try:
    import markdown
except ImportError:
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "-q",
                    "--break-system-packages", "markdown"], check=True)
    import markdown

html_body = markdown.markdown(
    md, extensions=["tables", "fenced_code", "sane_lists", "md_in_html"])
out = ROOT / "showcase" / "ATLAS_V5_APP_GUIDE.html"
out.parent.mkdir(exist_ok=True)
out.write_text(page("Digital Atlas Singapore V5 — App Builder's Guide", html_body))
print(f"wrote {out} ({len(out.read_text())/1024:.0f} KB)")
