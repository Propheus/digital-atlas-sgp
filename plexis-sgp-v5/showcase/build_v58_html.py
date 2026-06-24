import sys; from pathlib import Path
HERE=Path("/home/azureuser/da-sgp/v5/showcase"); sys.path.insert(0,str(HERE))
from report_theme import page
import markdown
for src,title,out in [
  ("RELEASE_NOTES_v5.8.md","Plexis SGP Atlas — Release Notes v5.8","RELEASE_NOTES_v5.8.html"),
  ("PLACES_FIX_RESPONSE_V4.md","Atlas Team — nous V4 Response","PLACES_FIX_RESPONSE_V4.html")]:
    body=markdown.markdown((HERE/src).read_text(),extensions=["tables","fenced_code","sane_lists"])
    (HERE/out).write_text(page(title,body))
    print("wrote",out,f"({(HERE/out).stat().st_size/1024:.0f} KB)")
