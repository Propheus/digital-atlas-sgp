import { motion, AnimatePresence } from "framer-motion";
import { CLUSTER_PALETTE, useStore } from "../state/store";

export function HoverTip({ x, y, hexId }: { x: number; y: number; hexId: string | null }) {
  const data = useStore((s) => s.embedding);
  const labels = useStore((s) => s.labels);
  return (
    <AnimatePresence>
      {hexId && (() => {
        const p = data.find((d) => d.hex_id === hexId);
        if (!p) return null;
        const meta = labels[String(p.cluster)];
        const color = CLUSTER_PALETTE[p.cluster % CLUSTER_PALETTE.length];
        return (
          <motion.div
            key={hexId}
            initial={{ opacity: 0, y: 6, scale: 0.96 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 6, scale: 0.96 }}
            transition={{ type: "spring", stiffness: 380, damping: 28 }}
            className="tooltip"
            style={{
              left: x + 20,
              top: Math.max(12, y - 92),
              borderLeft: `3px solid ${color}`,
            }}
          >
            <div className="label-mono mb-1.5" style={{ color, fontSize: 11 }}>
              {meta?.code ?? `M${p.cluster}`}
            </div>
            <div className="text-[14px] font-medium mb-2" style={{ color: "#e6f6ee" }}>
              {meta?.name ?? `Cluster ${p.cluster}`}
            </div>
            <div className="text-[11.5px] opacity-75">{p.subzone}</div>
            <div className="text-[10.5px] opacity-50 mt-0.5">{p.region}</div>
            <div className="text-[10px] opacity-35 mt-2 tracking-wider font-mono">
              {p.hex_id}
            </div>
          </motion.div>
        );
      })()}
    </AnimatePresence>
  );
}
