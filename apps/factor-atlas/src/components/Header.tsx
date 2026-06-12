import { motion } from "framer-motion";
import { useStore } from "../state/store";

export function Header() {
  const summary = useStore((s) => s.summary);
  const n = summary?.n_clusters ?? 8;
  return (
    <motion.header
      initial={{ opacity: 0, y: -8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
      className="border-b border-[#18342d] px-10 pt-9 pb-7 flex items-end justify-between gap-10"
    >
      <div className="flex items-end gap-5">
        <img
          src="/propheus.svg"
          alt="Propheus"
          className="h-10 w-10 mb-1 opacity-95"
        />
        <div>
          <div className="label-mono label-mono-accent" style={{ fontSize: 11 }}>
            propheus · digital atlas singapore · F_{String(n).padStart(2, "0")}
          </div>
          <h1 className="headline-serif text-[44px] leading-[1.05] mt-2 max-w-[860px]">
            All of Singapore, compressed into {n} urban modes.
          </h1>
          <p className="text-[14px] text-[var(--color-mute)] mt-3 max-w-[640px] leading-relaxed">
            A latent-space decomposition of {summary?.n_hexes.toLocaleString() ?? "—"} hexagons
            and {summary?.n_features ?? "—"} features. Switch between the geographic and latent
            views to see the same structure two ways.
          </p>
        </div>
      </div>
      <div className="text-right label-mono leading-[1.85]" style={{ fontSize: 10.5 }}>
        released 2026
        <br />
        digital atlas sgp
        <br />
        hex_v10 · {summary?.feature_set ?? "—"}
      </div>
    </motion.header>
  );
}
