import { useEffect, useMemo, useRef, useState } from "react";
import { CLUSTER_PALETTE, useStore } from "../state/store";
import { HoverTip } from "./HoverTip";

/**
 * Latent UMAP scatter on canvas. Two layers: base (dots + annotations) and
 * overlay (hover highlight).
 *
 * Mount: dots animate from cluster centroid outward to their UMAP position
 * over ~900 ms — an "expansion" reveal that visually narrates the decomposition.
 */
export function LatentPanel() {
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
  const [intro, setIntro] = useState(1); // dots expand-from-centroid (1 = at final pos)
  const introRaf = useRef<number | null>(null);

  const bounds = useMemo(() => {
    if (!data.length) return null;
    let xMin = Infinity, xMax = -Infinity, yMin = Infinity, yMax = -Infinity;
    for (const p of data) {
      if (p.x < xMin) xMin = p.x; if (p.x > xMax) xMax = p.x;
      if (p.y < yMin) yMin = p.y; if (p.y > yMax) yMax = p.y;
    }
    return { xMin, xMax, yMin, yMax };
  }, [data]);

  useEffect(() => {
    if (!wrapRef.current) return;
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
    const pad = 90;
    const w = size.w, h = size.h;
    const dx = bounds.xMax - bounds.xMin, dy = bounds.yMax - bounds.yMin;
    const s = Math.min((w - 2 * pad) / dx, (h - 2 * pad) / dy);
    const cx = (bounds.xMin + bounds.xMax) / 2;
    const cy = (bounds.yMin + bounds.yMax) / 2;
    return (x: number, y: number) =>
      [w / 2 + (x - cx) * s, h / 2 - (y - cy) * s] as [number, number];
  }, [bounds, size]);

  // per-point pixel coords + per-cluster centroid (also in pixels)
  const points = useMemo(() => {
    const centroidsByCluster: Record<number, { x: number; y: number; n: number }> = {};
    const out = data.map((p) => {
      const [x, y] = project(p.x, p.y);
      const c = centroidsByCluster[p.cluster] || (centroidsByCluster[p.cluster] = { x: 0, y: 0, n: 0 });
      c.x += x; c.y += y; c.n += 1;
      return { hex_id: p.hex_id, cluster: p.cluster, x, y };
    });
    const centroids: Record<number, { x: number; y: number }> = {};
    for (const k of Object.keys(centroidsByCluster)) {
      const v = centroidsByCluster[Number(k)];
      centroids[Number(k)] = { x: v.x / v.n, y: v.y / v.n };
    }
    return { out, centroids };
  }, [data, project]);

  // Two-phase intro:
  // 1) start at intro=0 (dots collapsed to centroids), opacity=0
  // 2) next frame: opacity → 1 (CSS) and intro → 1 (RAF) so dots expand outward
  useEffect(() => {
    if (!data.length) return;
    setMounted(false);
    setIntro(0);
    const idMount = requestAnimationFrame(() => setMounted(true));
    const t0 = performance.now();
    const dur = 900;
    const step = () => {
      const t = Math.min(1, (performance.now() - t0) / dur);
      setIntro(1 - Math.pow(1 - t, 3));
      if (t < 1) introRaf.current = requestAnimationFrame(step);
    };
    introRaf.current = requestAnimationFrame(step);
    // safety: snap to final after duration in case RAF is throttled (headless)
    const failsafe = setTimeout(() => setIntro(1), dur + 300);
    return () => {
      cancelAnimationFrame(idMount);
      if (introRaf.current) cancelAnimationFrame(introRaf.current);
      clearTimeout(failsafe);
    };
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

    ctx.strokeStyle = "#13312b";
    ctx.lineWidth = 0.5;
    for (let i = 1; i < 8; i++) {
      ctx.beginPath(); ctx.moveTo(0, (size.h * i) / 8); ctx.lineTo(size.w, (size.h * i) / 8); ctx.stroke();
    }
    for (let i = 1; i < 12; i++) {
      ctx.beginPath(); ctx.moveTo((size.w * i) / 12, 0); ctx.lineTo((size.w * i) / 12, size.h); ctx.stroke();
    }

    // dots — expand from centroid
    for (const p of points.out) {
      const c = points.centroids[p.cluster];
      const ix = c.x + (p.x - c.x) * intro;
      const iy = c.y + (p.y - c.y) * intro;
      const dim = selectedCluster != null && p.cluster !== selectedCluster;
      const color = CLUSTER_PALETTE[p.cluster % CLUSTER_PALETTE.length];
      ctx.fillStyle = color;
      ctx.globalAlpha = (dim ? 0.1 : 0.78) * Math.min(1, intro * 1.6);
      ctx.beginPath();
      ctx.arc(ix, iy, 2.0, 0, Math.PI * 2);
      ctx.fill();
    }
    ctx.globalAlpha = 1;

    // annotations (always at full opacity once dots are placed)
    {
      const annotAlpha = Math.min(1, Math.max(0, (intro - 0.4) / 0.3));
      const cx0 = size.w / 2, cy0 = size.h / 2;
      const rim = Math.min(size.w, size.h) * 0.46;
      const clusterIds = Object.keys(points.centroids).map(Number);
      const angled = clusterIds.sort((a, b) => {
        const ca = points.centroids[a], cb = points.centroids[b];
        return Math.atan2(ca.y - cy0, ca.x - cx0) - Math.atan2(cb.y - cy0, cb.x - cx0);
      });
      angled.forEach((cid, i) => {
        const { x: px, y: py } = points.centroids[cid];
        const ang = -Math.PI + (2 * Math.PI * (i + 0.5)) / angled.length;
        let lx = cx0 + rim * Math.cos(ang);
        let ly = cy0 + rim * Math.sin(ang);
        lx = Math.max(160, Math.min(size.w - 160, lx));
        ly = Math.max(48, Math.min(size.h - 36, ly));
        const meta = labels[String(cid)] || { code: `M${cid}`, name: `Cluster ${cid}`, blurb: "" };
        const color = CLUSTER_PALETTE[cid % CLUSTER_PALETTE.length];
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
  }, [points, size, selectedCluster, labels, intro, bounds]);

  // OVERLAY (hover)
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
    const p = points.out.find((p) => p.hex_id === hoverHex);
    if (!p) return;
    const color = CLUSTER_PALETTE[p.cluster % CLUSTER_PALETTE.length];
    ctx.shadowColor = color;
    ctx.shadowBlur = 16;
    ctx.fillStyle = color;
    ctx.beginPath(); ctx.arc(p.x, p.y, 5.2, 0, Math.PI * 2); ctx.fill();
    ctx.shadowBlur = 0;
    ctx.strokeStyle = "#e6f6ee";
    ctx.lineWidth = 1.4;
    ctx.beginPath(); ctx.arc(p.x, p.y, 7, 0, Math.PI * 2); ctx.stroke();
  }, [hoverHex, points, size]);

  function onMouseMove(e: React.MouseEvent) {
    const rect = overlayRef.current!.getBoundingClientRect();
    const mx = e.clientX - rect.left;
    const my = e.clientY - rect.top;
    let best: { hex: string; d2: number } | null = null;
    for (const p of points.out) {
      const dx = p.x - mx, dy = p.y - my;
      const d2 = dx * dx + dy * dy;
      if (d2 < 36 && (!best || d2 < best.d2)) best = { hex: p.hex_id, d2 };
    }
    if (best) { setHoverHex(best.hex); setTip({ x: mx, y: my, id: best.hex }); }
    else { setHoverHex(null); setTip(null); }
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
        className="absolute inset-0 w-full h-full pointer-events-none"
        style={{
          opacity: mounted ? 1 : 0,
          transition: "opacity 700ms ease-out",
        }}
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
