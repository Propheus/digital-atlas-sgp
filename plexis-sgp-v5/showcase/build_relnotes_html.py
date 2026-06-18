import sys; from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from report_theme import page
import markdown
HERE = Path(__file__).parent; ROOT = Path.home()/"da-sgp"/"v5"
md = (HERE/"RELEASE_NOTES_v5.6.md").read_text()
body = markdown.markdown(md, extensions=["tables","fenced_code","sane_lists"])
out = ROOT/"showcase"/"RELEASE_NOTES_v5.6.html"
out.write_text(page("Plexis SGP Atlas — Release Notes v5.6", body))
print(f"wrote {out} ({len(out.read_text())/1024:.0f} KB)")
