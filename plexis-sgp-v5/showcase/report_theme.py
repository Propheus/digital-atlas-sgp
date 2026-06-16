"""Shared report theme — travel-lens / geoagent dark glassmorphism + teal accent,
San Francisco system fonts. Used by all plexis-jkt-v1 HTML reports."""

FONT = ('-apple-system,BlinkMacSystemFont,"SF Pro Text","SF Pro Display",'
        '"Helvetica Neue",Helvetica,Arial,sans-serif')

THEME_CSS = """
:root{--accent:#20b2aa;--accent2:#2dd4bf;--ok:#39d98a;--warn:#f0c14b;
 --glass:rgba(17,40,42,.55);--glass2:rgba(12,27,29,.72);
 --border:rgba(32,178,170,.18);--border2:rgba(32,178,170,.32);
 --text:#e9eef0;--muted:#8fa3a6;--mono:#7fe3da}
*{box-sizing:border-box}
body{font-family:__FONT__;color:var(--text);
 background:radial-gradient(1100px 560px at 72% -12%,#173f41 0%,transparent 58%),
   linear-gradient(162deg,#0a1a1c,#0d2123 55%,#102628);
 background-attachment:fixed;min-height:100vh;max-width:1060px;margin:0 auto;
 padding:46px 26px;font-size:14px;line-height:1.55;-webkit-font-smoothing:antialiased}
h1{font-size:30px;font-weight:700;letter-spacing:-.022em;margin:0 0 4px}
.accent{color:var(--accent)}
h2{font-size:16px;font-weight:600;margin:34px 0 12px;color:#d4ecea;
 border-bottom:1px solid var(--border);padding-bottom:7px;letter-spacing:-.01em}
h2 .n{color:var(--muted);font-weight:400;font-size:13px}
.sub{color:var(--muted);margin:0 0 22px;font-size:14px}
a{color:var(--accent);text-decoration:none} a:hover{text-decoration:underline}
.cards{display:grid;grid-template-columns:repeat(6,1fr);gap:11px;margin:20px 0 8px}
.card{background:var(--glass);border:1px solid var(--border);border-radius:13px;
 padding:16px 12px;text-align:center;backdrop-filter:blur(13px);-webkit-backdrop-filter:blur(13px)}
.cv{font-size:23px;font-weight:700;color:#fff;letter-spacing:-.02em}
.cl{font-size:10.5px;color:var(--muted);margin-top:4px;text-transform:uppercase;letter-spacing:.045em}
table{width:100%;border-collapse:separate;border-spacing:0;background:var(--glass2);
 border:1px solid var(--border);border-radius:13px;overflow:hidden;margin-bottom:8px;
 backdrop-filter:blur(11px);-webkit-backdrop-filter:blur(11px)}
th,td{text-align:left;padding:9px 13px;border-bottom:1px solid rgba(32,178,170,.10);font-size:13px;vertical-align:top}
th{background:rgba(32,178,170,.09);color:var(--accent);font-size:10.5px;text-transform:uppercase;letter-spacing:.05em;font-weight:600}
tr:last-child td{border-bottom:none}
tbody tr:hover td{background:rgba(32,178,170,.05)}
td.f{font-family:ui-monospace,"SF Mono",Menlo,monospace;font-size:12px;color:var(--mono);white-space:nowrap}
td.t{color:var(--muted);font-size:11.5px}
td.s{color:#b9c9cb;font-size:12px;white-space:nowrap}
.banner{background:linear-gradient(90deg,rgba(57,217,138,.16),rgba(32,178,170,.04));
 border:1px solid var(--border2);color:#8fe9c4;border-radius:13px;padding:13px 17px;font-weight:600;margin:8px 0 4px}
.note{color:var(--muted);font-size:12.5px;margin-top:9px}
.pill{display:inline-block;background:rgba(32,178,170,.14);border:1px solid var(--border);
 color:#9fe9e1;border-radius:20px;padding:3px 11px;margin:3px 2px;font-size:12.5px}
code{background:rgba(32,178,170,.1);padding:1px 6px;border-radius:5px;font-size:12px;color:#9fe9e1;
 font-family:ui-monospace,"SF Mono",Menlo,monospace}
.tag{display:inline-block;font-size:9.5px;background:rgba(32,178,170,.2);color:#9fe9e1;
 border-radius:6px;padding:1px 7px;margin-left:7px;vertical-align:middle;text-transform:uppercase;letter-spacing:.04em;font-weight:600}
/* prose (markdown) */
p{margin:10px 0}
ul,ol{margin:8px 0 12px;padding-left:22px} li{margin:4px 0;color:#cdd9da}
strong,b{color:#fff;font-weight:600}
em{color:#bcd}
hr{border:none;border-top:1px solid var(--border);margin:30px 0}
blockquote{border-left:3px solid var(--accent);background:rgba(32,178,170,.06);
 margin:14px 0;padding:10px 16px;border-radius:0 8px 8px 0;color:#bcd0d2}
blockquote p{margin:4px 0}
pre{background:rgba(8,18,20,.85);border:1px solid var(--border);border-radius:10px;
 padding:13px 15px;overflow-x:auto;margin:12px 0;font-size:12.5px;line-height:1.5}
pre code{background:none;padding:0;color:#cfeae6;font-family:ui-monospace,"SF Mono",Menlo,monospace}
h1+p em,h1+p{color:var(--muted)}
@media(max-width:680px){.cards{grid-template-columns:repeat(3,1fr)}}
""".replace("__FONT__", FONT)


def page(title, body):
    return (f'<!doctype html><html><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{title}</title><style>{THEME_CSS}</style></head><body>{body}</body></html>')
