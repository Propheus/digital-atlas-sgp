import { motion } from "framer-motion";
import { CLUSTER_PALETTE, useStore } from "../state/store";

export function Footer() {
  const summary = useStore((s) => s.summary);
  const labels = useStore((s) => s.labels);
  const selectedCluster = useStore((s) => s.selectedCluster);
  const setSelectedCluster = useStore((s) => s.setSelectedCluster);

  if (!summary) return null;

  const highlights: Array<{ num: string; lbl: string; sub: string }> = [
    {
      num: summary.n_hexes.toLocaleString(),
      lbl: "H3 hexagons",
      sub: "level 9 · ~0.105 km² each",
    },
    {
      num: String(summary.n_features),
      lbl: "engineered features",
      sub: "buildings · transit · land use · places",
    },
    {
      num: String(summary.n_clusters),
      lbl: "emergent modes",
      sub: `stability ${summary.stability_ari?.toFixed(2) ?? "—"} · 0 labels used`,
    },
  ];

  return (
    <footer className="px-10 pt-12 pb-20 border-t border-[#18342d] mt-2">
      <div className="grid grid-cols-3 gap-12 pb-12 border-b border-[#18342d]">
        {highlights.map((h, i) => (
          <motion.div
            key={h.lbl}
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, amount: 0.4 }}
            transition={{ duration: 0.55, delay: i * 0.08, ease: [0.22, 1, 0.36, 1] }}
          >
            <div className="font-serif font-light text-[92px] leading-[0.95] tracking-[-0.02em]">
              {h.num}
            </div>
            <div className="label-mono mt-4" style={{ fontSize: 11.5 }}>
              {h.lbl}
            </div>
            <div
              className="mt-2 text-[var(--color-mute)] tracking-[0.04em]"
              style={{ fontSize: 12 }}
            >
              {h.sub}
            </div>
          </motion.div>
        ))}
      </div>

      <p className="font-serif font-light text-[28px] leading-[1.3] mt-12 max-w-[1020px]">
        One island. One{" "}
        <em className="not-italic text-[var(--color-accent)]">
          {summary.n_clusters}-mode decomposition
        </em>
        . Every hex placed in latent space without a single human label —
        then projected back onto the map.
      </p>

      <h3 className="headline-serif text-[24px] mt-14 mb-5">Emergent modes</h3>
      <div className="border-t border-[#122723]">
        {summary.clusters.map((c, i) => {
          const color = CLUSTER_PALETTE[c.cluster % CLUSTER_PALETTE.length];
          const meta = labels[String(c.cluster)] || { code: `M${c.cluster}`, name: `Cluster ${c.cluster}`, blurb: "" };
          const active = selectedCluster === c.cluster;
          return (
            <motion.button
              key={c.cluster}
              onClick={() => setSelectedCluster(c.cluster)}
              initial={{ opacity: 0, x: -8 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true, amount: 0.6 }}
              transition={{ duration: 0.35, delay: i * 0.04 }}
              className={`w-full grid grid-cols-[18px_70px_300px_70px_1fr] gap-5 items-center py-3 border-b border-[#122723] text-left transition-opacity ${active ? "opacity-100" : selectedCluster != null ? "opacity-25 hover:opacity-70" : "opacity-90 hover:opacity-100"}`}
            >
              <span
                className="w-3.5 h-3.5 rounded-full transition-transform"
                style={{
                  background: color,
                  transform: active ? "scale(1.4)" : "scale(1)",
                  boxShadow: active ? `0 0 14px ${color}` : "none",
                }}
              />
              <span
                className="label-mono"
                style={{ color, letterSpacing: "0.22em", fontSize: 11 }}
              >
                {meta.code}
              </span>
              <span
                className="label-mono"
                style={{ color: "#e6f6ee", letterSpacing: "0.18em", fontSize: 11.5 }}
              >
                {meta.name}
              </span>
              <span className="label-mono" style={{ fontSize: 11 }}>
                {Math.round(c.share * 100)}%
              </span>
              <span className="font-serif italic text-[15px] leading-snug text-[var(--color-mute)]">
                {meta.blurb}
              </span>
            </motion.button>
          );
        })}
      </div>

      <div className="label-mono mt-12 pt-6 border-t border-[#18342d]" style={{ fontSize: 10.5 }}>
        propheus · digital atlas sgp · factor decomposition · build {summary.feature_set} · k={summary.n_clusters}
      </div>
    </footer>
  );
}
