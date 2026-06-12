import { useEffect, useMemo, useRef, useState } from "react";
import { cellToBoundary } from "h3-js";
import { CLUSTER_PALETTE, useStore } from "../state/store";
import { HoverTip } from "./HoverTip";

function pointInPoly(x: number, y: number, poly: [number, number][]): boolean {
  let inside = false;
  for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) {
    const [xi, yi] = poly[i];
    const [xj, yj] = poly[j];
    const intersect =
      yi > y !== yj > y && x < ((xj - xi) * (y - yi)) / (yj - yi + 1e-12) + xi;
    if (intersect) inside = !inside;
  }
  return inside;
}

/**
 * Geographic panel as actual H3 hexagons on canvas (no basemap).
 * Two canvases: base (cluster fills + annotations) + overlay (hover stroke).
 * Mount animation: hexes fade in over ~600 ms with a soft scale-up.
 */
export function GeoPanel() {
  const data = useStore((s) => s.embedding);
  const labels = useStore((s) => s.labels);
  const hoverHex = useStore((s) => s.hoverHex);
  const setHoverHex = useStore((s) => s.setHoverHex);
  const selectedCluster = useStore((s) => s.selectedCluster);
  const setSelectedCluster = useStore((s) => s.setSelectedCluster);

  const wrapRef = useRef<HTMLDivElement | null>(null);
  const baseRef = useRef<HTMLCanvasElement | null>(null);
  const overlayRef = useRef<HTMLCanvasElement | null>(null);
  const [size, setSize] = useState({ w: 900, h: 720 });
  const [tip, setTip] = useState<{ x: number; y: number; id: string } | null>(null);
  const [mounted, setMounted] = useState(false);

  const hexBoundaries = useMemo(() => {
    const out = new Map<string, [number, number][]>();
    for (const p of data) {
      try { out.set(p.hex_id, cellToBoundary(p.hex_id)); } catch { /* */ }
    }
    return out;
  }, [data]);

  const bounds = useMemo(() => {
    if (!data.length) return null;
    let xMin = Infinity, xMax = -Infinity, yMin = Infinity, yMax = -Infinity;
    for (const p of data) {
      if (p.lng < xMin) xMin = p.lng; if (p.lng > xMax) xMax = p.lng;
      if (p.lat < yMin) yMin = p.lat; if (p.lat > yMax) yMax = p.lat;
    }
    return { xMin, xMax, yMin, yMax };
  }, [data]);

  useEffect(() => {
    if (!wrapRef.current) return;
    // sync first read so we paint at correct size on first frame
    const r0 = wrapRef.current.getBoundingClientRect();
    if (r0.width && r0.height) setSize({ w: r0.width, h: r0.height });
    const ro = new ResizeObserver(() => {
      const r = wrapRef.current!.getBoundingClientRect();
      if (r.width && r.height) setSize({ w: r.width, h: r.height });
    });
    ro.observe(wrapRef.current);
    return () => ro.disconnect();
  }, []);

  const project = useMemo(() => {
    if (!bounds) return (x: number, y: number) => [0, 0] as [number, number];
    const pad = 64;
    const w = size.w, h = size.h;
    const dx = bounds.xMax - bounds.xMin, dy = bounds.yMax - bounds.yMin;
    const s = Math.min((w - 2 * pad) / dx, (h - 2 * pad) / dy);
    const cx = (bounds.xMin + bounds.xMax) / 2;
    const cy = (bounds.yMin + bounds.yMax) / 2;
    return (lng: number, lat: number) =>
      [w / 2 + (lng - cx) * s, h / 2 - (lat - cy) * s] as [number, number];
  }, [bounds, size]);

  const hexPx = useMemo(() => {
    return data.map((p) => {
      const boundary = hexBoundaries.get(p.hex_id);
      if (!boundary) return null;
      const pts: [number, number][] = boundary.map(([lat, lng]) => project(lng, lat));
      let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
      let cx = 0, cy = 0;
      for (const [x, y] of pts) {
        if (x < minX) minX = x; if (x > maxX) maxX = x;
        if (y < minY) minY = y; if (y > maxY) maxY = y;
        cx += x; cy += y;
      }
      cx /= pts.length; cy /= pts.length;
      return {
        hex_id: p.hex_id,
        cluster: p.cluster,
        pts,
        cx, cy,
        bbox: [minX, minY, maxX, maxY] as [number, number, number, number],
      };
    }).filter((h): h is NonNullable<typeof h> => h != null);
  }, [data, hexBoundaries, project]);

  const centroids = useMemo(() => {
    const acc: Record<number, { lng: number; lat: number; n: number }> = {};
    for (const p of data) {
      const a = acc[p.cluster] || (acc[p.cluster] = { lng: 0, lat: 0, n: 0 });
      a.lng += p.lng; a.lat += p.lat; a.n += 1;
    }
    return Object.entries(acc).map(([cid, v]) => ({
      cluster: Number(cid), lng: v.lng / v.n, lat: v.lat / v.n,
    }));
  }, [data]);

  // CSS-driven fade-in: paint at full intro, then flip mounted to trigger opacity transition.
  useEffect(() => {
    if (!data.length) return;
    setMounted(false);
    const id = requestAnimationFrame(() => setMounted(true));
    return () => cancelAnimationFrame(id);
  }, [data.length]);

  // BASE
  useEffect(() => {
    const canvas = baseRef.current;
    if (!canvas || !bounds) return;
    const dpr = window.devicePixelRatio || 1;
    canvas.width = size.w * dpr; canvas.height = size.h * dpr;
    canvas.style.width = `${size.w}px`; canvas.style.height = `${size.h}px`;
    const ctx = canvas.getContext("2d")!;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.fillStyle = "#0a1f1c";
    ctx.fillRect(0, 0, size.w, size.h);

    // faint grid
    ctx.strokeStyle = "#13312b";
    ctx.lineWidth = 0.5;
    for (let i = 1; i < 8; i++) {
      ctx.beginPath(); ctx.moveTo(0, (size.h * i) / 8); ctx.lineTo(size.w, (size.h * i) / 8); ctx.stroke();
    }
    for (let i = 1; i < 12; i++) {
      ctx.beginPath(); ctx.moveTo((size.w * i) / 12, 0); ctx.lineTo((size.w * i) / 12, size.h); ctx.stroke();
    }

    for (const h of hexPx) {
      const color = CLUSTER_PALETTE[h.cluster % CLUSTER_PALETTE.length];
      const dim = selectedCluster != null && h.cluster !== selectedCluster;
      ctx.fillStyle = color;
      ctx.globalAlpha = dim ? 0.08 : 0.82;
      ctx.beginPath();
      h.pts.forEach(([x, y], i) => { if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y); });
      ctx.closePath();
      ctx.fill();
    }
    ctx.globalAlpha = 1;

    // annotations
    {
      const annotAlpha = 1;
      ctx.font = "500 12px 'JetBrains Mono', monospace";
      const cx0 = size.w / 2, cy0 = size.h / 2;
      const rim = Math.min(size.w, size.h) * 0.5;
      const angled = [...centroids].sort((a, b) => {
        const [ax, ay] = project(a.lng, a.lat);
        const [bx, by] = project(b.lng, b.lat);
        return Math.atan2(ay - cy0, ax - cx0) - Math.atan2(by - cy0, bx - cx0);
      });
      angled.forEach((c, i) => {
        const [px, py] = project(c.lng, c.lat);
        const ang = -Math.PI + (2 * Math.PI * (i + 0.5)) / angled.length;
        let lx = cx0 + rim * Math.cos(ang);
        let ly = cy0 + rim * Math.sin(ang);
        lx = Math.max(160, Math.min(size.w - 160, lx));
        ly = Math.max(48, Math.min(size.h - 36, ly));
        const meta = labels[String(c.cluster)] || { code: `M${c.cluster}`, name: `Cluster ${c.cluster}`, blurb: "" };
        const color = CLUSTER_PALETTE[c.cluster % CLUSTER_PALETTE.length];
        ctx.strokeStyle = color;
        ctx.globalAlpha = 0.7 * annotAlpha;
        ctx.lineWidth = 1;
        ctx.beginPath(); ctx.moveTo(px, py); ctx.lineTo(lx, ly); ctx.stroke();
        ctx.globalAlpha = annotAlpha;
        ctx.fillStyle = color;
        ctx.beginPath(); ctx.arc(px, py, 4, 0, Math.PI * 2); ctx.fill();
        ctx.textAlign = lx > cx0 ? "start" : "end";
        const nx = lx + (lx > cx0 ? 7 : -7);
        ctx.font = "600 10.5px 'JetBrains Mono', monospace";
        ctx.fillStyle = color;
        ctx.fillText(meta.code.toUpperCase(), nx, ly - 8);
        ctx.font = "500 11.5px 'JetBrains Mono', monospace";
        ctx.fillStyle = "#e6f6ee";
        ctx.fillText(meta.name.toUpperCase(), nx, ly + 6);
      });
      ctx.globalAlpha = 1;
    }
  }, [hexPx, project, size, selectedCluster, labels, centroids, bounds]);

  // OVERLAY
  useEffect(() => {
    const canvas = overlayRef.current;
    if (!canvas) return;
    const dpr = window.devicePixelRatio || 1;
    canvas.width = size.w * dpr; canvas.height = size.h * dpr;
    canvas.style.width = `${size.w}px`; canvas.style.height = `${size.h}px`;
    const ctx = canvas.getContext("2d")!;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, size.w, size.h);
    if (!hoverHex) return;
    const h = hexPx.find((x) => x.hex_id === hoverHex);
    if (!h) return;
    const color = CLUSTER_PALETTE[h.cluster % CLUSTER_PALETTE.length];
    // glow halo
    ctx.shadowColor = color;
    ctx.shadowBlur = 18;
    ctx.fillStyle = color;
    ctx.globalAlpha = 1;
    ctx.beginPath();
    h.pts.forEach(([x, y], i) => { if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y); });
    ctx.closePath();
    ctx.fill();
    ctx.shadowBlur = 0;
    ctx.strokeStyle = "#e6f6ee";
    ctx.lineWidth = 1.6;
    ctx.stroke();
  }, [hoverHex, hexPx, size]);

  function onMouseMove(e: React.MouseEvent) {
    const rect = overlayRef.current!.getBoundingClientRect();
    const mx = e.clientX - rect.left;
    const my = e.clientY - rect.top;
    let found: string | null = null;
    for (const h of hexPx) {
      const [minX, minY, maxX, maxY] = h.bbox;
      if (mx < minX || mx > maxX || my < minY || my > maxY) continue;
      if (pointInPoly(mx, my, h.pts)) { found = h.hex_id; break; }
    }
    if (found) {
      setHoverHex(found);
      setTip({ x: mx, y: my, id: found });
    } else {
      setHoverHex(null);
      setTip(null);
    }
  }
  function onClick() {
    if (!hoverHex) return;
    const point = data.find((p) => p.hex_id === hoverHex);
    if (point) setSelectedCluster(point.cluster);
  }

  return (
    <div className="relative h-full w-full" ref={wrapRef}>
      <canvas
        ref={baseRef}
        className="absolute inset-0 w-full h-full pointer-events-none transition-opacity duration-700 ease-out"
        style={{ opacity: mounted ? 1 : 0, transform: mounted ? "scale(1)" : "scale(0.98)", transition: "opacity 700ms ease-out, transform 700ms cubic-bezier(0.22,1,0.36,1)" }}
      />
      <canvas
        ref={overlayRef}
        onMouseMove={onMouseMove}
        onMouseLeave={() => { setHoverHex(null); setTip(null); }}
        onClick={onClick}
        className="absolute inset-0 w-full h-full cursor-crosshair"
      />
      <HoverTip x={tip?.x ?? 0} y={tip?.y ?? 0} hexId={tip ? tip.id : null} />
    </div>
  );
}
