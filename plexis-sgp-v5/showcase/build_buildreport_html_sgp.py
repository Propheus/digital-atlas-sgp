"""Render the Singapore Markdown build report as a themed HTML page."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from report_theme import page

HERE = Path(__file__).parent
ROOT = Path.home() / "da-sgp" / "v5"
md = (HERE / "SGP_ATLAS_BUILD_REPORT.md").read_text()
try:
    import markdown
except ImportError:
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "-q",
                    "--break-system-packages", "markdown"], check=True)
    import markdown

html_body = markdown.markdown(md, extensions=["tables", "fenced_code", "sane_lists"])
out = ROOT / "showcase" / "SGP_ATLAS_BUILD_REPORT.html"
out.parent.mkdir(exist_ok=True)
out.write_text(page("Building a Digital Atlas for Singapore", html_body))
print(f"wrote {out} ({len(out.read_text())/1024:.0f} KB)")
