"""
Render the SGP Factor Decomposition poster (josefchen-style).

Reads:
  data/factor_atlas/{embedding.json, cluster_summary.json, labels.json}

Writes:
  factor_atlas_poster.html        single-file HTML poster (SVG inside)

The poster mirrors the reference image:
  - dark teal canvas (#0a1f1c)
  - monospace tracked-out caps annotations
  - leader lines from labels to cluster centroids
  - hero numbers row + metadata strip
  - faded background scatter, accented cluster dots
"""
from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "factor_atlas"
OUT = ROOT / "factor_atlas_poster.html"

# josefchen-aligned palette
BG = "#081915"
PANEL = "#0a1f1c"
GRID = "#13312b"
INK = "#e6f6ee"
MUTE = "#9fc8b8"
ACCENT = "#7af5c5"
CLUSTER_PALETTE = [
    "#7af5c5",  # mint
    "#f4cf9d",  # cream
    "#9bd1ff",  # sky
    "#c4f560",  # lime
    "#ff8fa3",  # rose
    "#b794f4",  # lavender
    "#fce38a",  # sand
    "#5eead4",  # teal
    "#fda4af",  # coral
    "#a78bfa",  # iris
]


def fit_transform(points, *, target_w, target_h, pad):
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    x0, x1 = min(xs), max(xs)
    y0, y1 = min(ys), max(ys)
    dx, dy = x1 - x0, y1 - y0
    s = min((target_w - 2 * pad) / dx, (target_h - 2 * pad) / dy)
    cx = (x0 + x1) / 2
    cy = (y0 + y1) / 2
    out = []
    for x, y in points:
        # flip Y so up is up
        out.append((
            target_w / 2 + (x - cx) * s,
            target_h / 2 - (y - cy) * s,
        ))
    return out, s, (cx, cy)


def geo_panel_hex_svg(*, width, height, embedding, palette, labels_meta,
                       title, subtitle):
    """Render geographic panel as actual H3 hexagons (not dots)."""
    import h3
    # collect (lng, lat) per hex polygon vertex, fit-transform together with centroids
    centroids = [(p["lng"], p["lat"]) for p in embedding]
    _, s, (cx_geo, cy_geo) = fit_transform(centroids, target_w=width, target_h=height, pad=46)

    def to_screen(lng, lat):
        return (
            width / 2 + (lng - cx_geo) * s,
            height / 2 - (lat - cy_geo) * s,
        )

    parts = [
        f'<svg viewBox="0 0 {width} {height}" '
        f'xmlns="http://www.w3.org/2000/svg" class="panel" '
        f'preserveAspectRatio="xMidYMid meet">',
        f'<rect width="{width}" height="{height}" fill="{PANEL}"/>',
    ]
    # faint grid
    parts.append(f'<g stroke="{GRID}" stroke-width="0.5" opacity="0.35">')
    for i in range(1, 8):
        parts.append(f'<line x1="0" y1="{height*i/8:.1f}" x2="{width}" y2="{height*i/8:.1f}"/>')
    for i in range(1, 12):
        parts.append(f'<line x1="{width*i/12:.1f}" y1="0" x2="{width*i/12:.1f}" y2="{height}"/>')
    parts.append('</g>')

    # group hexes by cluster, render as filled polygons
    by_cluster: dict[int, list[str]] = {}
    centroids_screen: dict[int, list[tuple[float, float]]] = {}
    for p in embedding:
        try:
            boundary = h3.cell_to_boundary(p["hex_id"])
        except Exception:
            continue
        # h3 v4 returns [(lat, lng), ...]
        pts = [to_screen(lng, lat) for (lat, lng) in boundary]
        poly = " ".join(f"{x:.1f},{y:.1f}" for (x, y) in pts)
        by_cluster.setdefault(p["cluster"], []).append(poly)
        cx, cy = to_screen(p["lng"], p["lat"])
        centroids_screen.setdefault(p["cluster"], []).append((cx, cy))

    for cid, polys in sorted(by_cluster.items()):
        color = palette[cid % len(palette)]
        parts.append(f'<g fill="{color}" fill-opacity="0.78" stroke="{color}" '
                     f'stroke-opacity="0.35" stroke-width="0.35">')
        for poly in polys:
            parts.append(f'<polygon points="{poly}"/>')
        parts.append('</g>')

    # cluster annotations on geo
    cluster_centroids = {
        cid: (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))
        for cid, pts in centroids_screen.items()
    }
    parts.extend(_render_annotations(cluster_centroids, labels_meta, palette,
                                     width, height))

    parts.append(_title_block(title, subtitle, width, height))
    parts.append("</svg>")
    return "\n".join(parts)


def _render_annotations(cluster_centroids, labels_meta, palette, width, height):
    parts = []
    cx0, cy0 = width / 2, height / 2
    angled = sorted(
        cluster_centroids.items(),
        key=lambda kv: math.atan2(kv[1][1] - cy0, kv[1][0] - cx0),
    )
    n = len(angled)
    rim_r = min(width, height) * 0.5
    for i, (cid, (px, py)) in enumerate(angled):
        ang = -math.pi + (2 * math.pi * (i + 0.5) / n)
        lx = cx0 + rim_r * math.cos(ang)
        ly = cy0 + rim_r * math.sin(ang)
        lx = max(140, min(width - 140, lx))
        ly = max(50, min(height - 36, ly))
        meta = labels_meta.get(cid, {})
        code = meta.get("code", f"M{cid}")
        name = meta.get("name", f"Cluster {cid}").upper()
        color = palette[cid % len(palette)]
        # leader
        parts.append(f'<line x1="{px:.1f}" y1="{py:.1f}" x2="{lx:.1f}" y2="{ly:.1f}" '
                     f'stroke="{color}" stroke-width="0.9" opacity="0.7"/>')
        parts.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="3.6" fill="{color}" '
                     f'stroke="{PANEL}" stroke-width="1.4"/>')
        anchor = "start" if lx > cx0 else "end"
        nx = lx + (6 if lx > cx0 else -6)
        parts.append(
            f'<g font-family="\'JetBrains Mono\', \'IBM Plex Mono\', ui-monospace, monospace" '
            f'font-size="11" letter-spacing="0.22em" text-anchor="{anchor}">'
            f'<text x="{nx:.1f}" y="{ly-8:.1f}" fill="{color}">{code}</text>'
            f'<text x="{nx:.1f}" y="{ly+6:.1f}" fill="{INK}">{name}</text>'
            f'</g>'
        )
    return parts


def _title_block(title, subtitle, width, height):
    pad = 28
    title_svg = (
        f'<text x="{pad}" y="32" font-family="\'JetBrains Mono\', monospace" '
        f'font-size="11" letter-spacing="0.3em" fill="{ACCENT}">{title.upper()}</text>'
    )
    sub = ""
    if subtitle:
        sub = (
            f'<text x="{pad}" y="{height-22}" font-family="\'JetBrains Mono\', monospace" '
            f'font-size="9" letter-spacing="0.2em" fill="{MUTE}">{subtitle.upper()}</text>'
        )
    return title_svg + sub


def panel_svg(*, width, height, points, clusters, labels_meta, palette, title,
              subtitle):
    """Latent space scatter panel (UMAP projection)."""
    pad = 60
    coords, _, _ = fit_transform(points, target_w=width, target_h=height, pad=pad)
    by_cluster: dict[int, list[tuple[float, float]]] = {}
    for (x, y), c in zip(coords, clusters):
        by_cluster.setdefault(c, []).append((x, y))

    parts = [
        f'<svg viewBox="0 0 {width} {height}" '
        f'xmlns="http://www.w3.org/2000/svg" class="panel" '
        f'preserveAspectRatio="xMidYMid meet">',
        f'<rect width="{width}" height="{height}" fill="{PANEL}"/>',
    ]
    parts.append(f'<g stroke="{GRID}" stroke-width="0.5" opacity="0.35">')
    for i in range(1, 8):
        parts.append(f'<line x1="0" y1="{height*i/8:.1f}" x2="{width}" y2="{height*i/8:.1f}"/>')
    for i in range(1, 12):
        parts.append(f'<line x1="{width*i/12:.1f}" y1="0" x2="{width*i/12:.1f}" y2="{height}"/>')
    parts.append('</g>')

    # cluster dots, sized by proximity to centroid (centroid = brightest)
    for cid, pts in sorted(by_cluster.items()):
        color = palette[cid % len(palette)]
        cx = sum(p[0] for p in pts) / len(pts)
        cy = sum(p[1] for p in pts) / len(pts)
        # sort by distance from centroid
        dists = [(p, math.hypot(p[0] - cx, p[1] - cy)) for p in pts]
        max_d = max(d for _, d in dists) or 1
        parts.append(f'<g fill="{color}">')
        for (x, y), d in dists:
            t = d / max_d
            r = max(1.2, 3.2 - 2.0 * t)
            op = max(0.4, 0.95 - 0.55 * t)
            parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" opacity="{op:.2f}"/>')
        parts.append('</g>')

    # annotations
    cluster_centroids = {
        cid: (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))
        for cid, pts in by_cluster.items()
    }
    parts.extend(_render_annotations(cluster_centroids, labels_meta, palette,
                                     width, height))
    parts.append(_title_block(title, subtitle, width, height))
    parts.append("</svg>")
    return "\n".join(parts)


def main():
    embedding = json.loads((DATA / "embedding.json").read_text())
    summary = json.loads((DATA / "cluster_summary.json").read_text())
    labels_path = DATA / "labels.json"
    if labels_path.exists():
        labels = json.loads(labels_path.read_text())
    else:
        labels = {}
    # build {cluster_id: {code,name,blurb}} dict
    labels_meta: dict[int, dict] = {}
    for c in summary["clusters"]:
        cid = c["cluster"]
        entry = labels.get(str(cid), {})
        labels_meta[cid] = {
            "code": entry.get("code", f"M{cid}"),
            "name": entry.get("name", f"Mode {cid}"),
            "blurb": entry.get("blurb", ""),
        }

    points_latent = [(p["x"], p["y"]) for p in embedding]
    points_geo = [(p["lng"], p["lat"]) for p in embedding]
    clusters = [p["cluster"] for p in embedding]
    palette = CLUSTER_PALETTE

    latent_svg = panel_svg(
        width=900, height=720, points=points_latent, clusters=clusters,
        labels_meta=labels_meta, palette=palette,
        title="latent space  ·  umap projection",
        subtitle=f"pca {summary['pca_dim']}  ·  umap n={summary['umap_n_neighbors']}  "
                 f"d={summary['umap_min_dist']}  ·  variance retained {int(summary['pca_variance_retained']*100)}%",
    )
    geo_svg = geo_panel_hex_svg(
        width=900, height=720, embedding=embedding,
        labels_meta=labels_meta, palette=palette,
        title="geographic projection  ·  singapore",
        subtitle=f"{summary['n_hexes']:,} h3-level-9 hexes  ·  filled by emergent mode",
    )

    # bottom rail: hero numbers
    stab = summary.get("stability_ari")
    stab_s = f"{stab:.2f}" if stab is not None else "—"
    sil_s = f"{summary['silhouette']:.2f}"
    n_modes = summary["n_clusters"]

    # cluster legend rows
    legend_rows = []
    for c in summary["clusters"]:
        cid = c["cluster"]
        meta = labels_meta[cid]
        color = palette[cid % len(palette)]
        share = int(round(c["share"] * 100))
        legend_rows.append(
            f'<div class="row">'
            f'  <span class="swatch" style="background:{color}"></span>'
            f'  <span class="code" style="color:{color}">{meta["code"]}</span>'
            f'  <span class="name">{meta["name"].upper()}</span>'
            f'  <span class="share">{share}%</span>'
            f'  <span class="blurb">{meta["blurb"]}</span>'
            f'</div>'
        )

    html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<title>SGP · Factor Decomposition · F_{n_modes:02d}</title>
<meta name="viewport" content="width=1600"/>
<link rel="preconnect" href="https://fonts.googleapis.com"/>
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin/>
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;700&family=Fraunces:wght@300;500;700&display=swap" rel="stylesheet"/>
<style>
  :root {{
    --bg: {BG};
    --panel: {PANEL};
    --ink: {INK};
    --mute: {MUTE};
    --accent: {ACCENT};
  }}
  * {{ box-sizing: border-box; }}
  html, body {{ margin: 0; padding: 0; background: var(--bg); color: var(--ink);
    font-family: 'JetBrains Mono', ui-monospace, monospace; }}
  .poster {{ max-width: 1760px; margin: 0 auto; padding: 56px 56px 80px; }}
  .header {{ display: flex; justify-content: space-between; align-items: flex-end;
    padding-bottom: 22px; border-bottom: 1px solid #18342d; }}
  .header .left h1 {{ margin: 0; font-family: 'Fraunces', serif; font-weight: 300;
    font-size: 38px; letter-spacing: -0.01em; color: var(--ink); }}
  .header .left .tagline {{ font-size: 11px; letter-spacing: 0.28em; color: var(--accent);
    margin-top: 6px; text-transform: uppercase; }}
  .header .right {{ text-align: right; font-size: 10.5px; letter-spacing: 0.22em;
    color: var(--mute); text-transform: uppercase; line-height: 1.7; }}
  .metabar {{ display: flex; gap: 36px; padding: 22px 0 26px;
    border-bottom: 1px solid #18342d; }}
  .metabar .item {{ font-size: 10px; letter-spacing: 0.24em; color: var(--mute);
    text-transform: uppercase; }}
  .metabar .item b {{ color: var(--accent); font-weight: 500; letter-spacing: 0.1em; }}
  .panels {{ display: grid; grid-template-columns: 1fr 1fr; gap: 22px; padding: 26px 0; }}
  .panel-wrap {{ background: {PANEL}; border: 1px solid #18342d; border-radius: 4px;
    overflow: hidden; }}
  svg.panel {{ display: block; width: 100%; height: auto; }}
  .footer {{ padding-top: 26px; border-top: 1px solid #18342d; }}
  .hero {{ display: grid; grid-template-columns: repeat(4, 1fr);
    gap: 28px; padding: 14px 0 30px; border-bottom: 1px solid #18342d; }}
  .hero .num {{ font-family: 'Fraunces', serif; font-weight: 300; font-size: 56px;
    line-height: 1; color: var(--ink); }}
  .hero .lbl {{ font-size: 10px; letter-spacing: 0.3em; color: var(--mute);
    text-transform: uppercase; margin-top: 8px; }}
  .legend {{ padding: 26px 0 0; }}
  .legend h3 {{ font-family: 'Fraunces', serif; font-weight: 300; color: var(--ink);
    font-size: 20px; margin: 0 0 16px; letter-spacing: -0.01em; }}
  .legend .row {{ display: grid;
    grid-template-columns: 14px 56px 280px 60px 1fr;
    gap: 16px; align-items: center; padding: 7px 0;
    border-bottom: 1px solid #122723; font-size: 11px; }}
  .legend .swatch {{ width: 12px; height: 12px; border-radius: 50%; }}
  .legend .code {{ letter-spacing: 0.22em; font-size: 10.5px; }}
  .legend .name {{ color: var(--ink); letter-spacing: 0.18em; font-size: 10.5px; }}
  .legend .share {{ color: var(--mute); letter-spacing: 0.18em; font-size: 10.5px; }}
  .legend .blurb {{ color: var(--mute); font-family: 'Fraunces', serif; font-style: italic;
    font-size: 13px; line-height: 1.5; letter-spacing: 0; }}
  .claim {{ font-family: 'Fraunces', serif; font-weight: 300; font-size: 28px;
    color: var(--ink); margin: 36px 0 8px; max-width: 980px; line-height: 1.25; }}
  .claim em {{ color: var(--accent); font-style: normal; }}
  .stamp {{ font-size: 10px; letter-spacing: 0.3em; color: var(--mute);
    text-transform: uppercase; padding-top: 24px; border-top: 1px solid #18342d; }}
</style>
</head>
<body>
<main class="poster">
  <section class="header">
    <div class="left">
      <div class="tagline">SGP atlas — factor decomposition · F_{n_modes:02d}</div>
      <h1>All of Singapore, compressed into {n_modes} urban modes.</h1>
    </div>
    <div class="right">
      released 2026 · digital atlas sgp<br/>
      hex_v10 · normalized<br/>
      seed {summary['seed']}
    </div>
  </section>

  <section class="metabar">
    <div class="item">stability <b>{stab_s}</b></div>
    <div class="item">silhouette <b>{sil_s}</b></div>
    <div class="item">modes <b>{n_modes}</b></div>
    <div class="item">labels used <b>0</b></div>
    <div class="item">variance retained <b>{int(summary['pca_variance_retained']*100)}%</b></div>
    <div class="item">resolver <b>kmeans · pca → umap</b></div>
  </section>

  <section class="panels">
    <div class="panel-wrap">{latent_svg}</div>
    <div class="panel-wrap">{geo_svg}</div>
  </section>

  <section class="footer">
    <div class="hero">
      <div><div class="num">{summary['n_hexes']:,}</div><div class="lbl">hexes</div></div>
      <div><div class="num">{summary['n_features']}</div><div class="lbl">features</div></div>
      <div><div class="num">{n_modes}</div><div class="lbl">emergent modes</div></div>
      <div><div class="num">332</div><div class="lbl">subzones covered</div></div>
    </div>

    <div class="claim">
      One island. One <em>{n_modes}-mode decomposition</em>. Every hex placed in latent space without a single human label —
      then projected back onto the map.
    </div>

    <div class="legend">
      <h3>Emergent modes</h3>
      {"".join(legend_rows)}
    </div>

    <div class="stamp">
      digital atlas sgp · factor decomposition · {Path(__file__).name}
    </div>
  </section>
</main>
</body>
</html>
"""
    OUT.write_text(html)
    print(f"wrote {OUT} ({len(html)//1024} KB)")


if __name__ == "__main__":
    main()
