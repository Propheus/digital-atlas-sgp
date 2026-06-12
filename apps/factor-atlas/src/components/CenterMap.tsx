import { AnimatePresence, motion } from "framer-motion";
import { GeoPanel } from "./GeoPanel";
import { LatentPanel } from "./LatentPanel";
import { useStore, ViewMode } from "../state/store";

const TABS: Array<{ id: ViewMode; label: string; sub: string }> = [
  { id: "geo", label: "Geographic", sub: "h3 hexagons · singapore" },
  { id: "latent", label: "Latent", sub: "umap projection · 8 modes" },
];

export function CenterMap() {
  const view = useStore((s) => s.view);
  const setView = useStore((s) => s.setView);

  return (
    <section className="px-10 py-7">
      <div className="rounded-[6px] border border-[#18342d] bg-[#0a1f1c] overflow-hidden">
        <div className="flex items-stretch border-b border-[#18342d]">
          {TABS.map((t) => {
            const active = view === t.id;
            return (
              <button
                key={t.id}
                onClick={() => setView(t.id)}
                className="relative flex-1 px-7 py-5 text-left group"
              >
                <div className="flex items-baseline gap-3">
                  <span
                    className={`font-serif text-[24px] leading-none transition-colors duration-300 ${active ? "text-[var(--color-ink)]" : "text-[var(--color-mute)] opacity-50 group-hover:opacity-90"}`}
                  >
                    {t.label}
                  </span>
                  <span
                    className={`label-mono transition-opacity duration-300 ${active ? "label-mono-accent opacity-100" : "opacity-40 group-hover:opacity-70"}`}
                    style={{ fontSize: 10 }}
                  >
                    {t.sub}
                  </span>
                </div>
                {active && (
                  <motion.div
                    layoutId="tab-underline"
                    className="absolute left-0 right-0 bottom-[-1px] h-[2px] bg-[var(--color-accent)]"
                    transition={{ type: "spring", stiffness: 380, damping: 32 }}
                  />
                )}
              </button>
            );
          })}
          <ViewLegend />
        </div>

        <div className="relative aspect-[16/10] w-full">
          <AnimatePresence mode="wait">
            <motion.div
              key={view}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.32, ease: [0.22, 1, 0.36, 1] }}
              className="absolute inset-0"
            >
              {view === "geo" ? <GeoPanel /> : <LatentPanel />}
            </motion.div>
          </AnimatePresence>
        </div>
      </div>
    </section>
  );
}

function ViewLegend() {
  const summary = useStore((s) => s.summary);
  if (!summary) return null;
  return (
    <div className="hidden md:flex items-center gap-7 px-7 border-l border-[#18342d]">
      <Stat label="modes" value={summary.n_clusters} />
      <Stat label="stability" value={summary.stability_ari?.toFixed(2) ?? "—"} />
      <Stat label="silhouette" value={summary.silhouette.toFixed(2)} />
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="text-right">
      <div className="font-serif text-[20px] leading-none text-[var(--color-accent)] font-light">
        {value}
      </div>
      <div className="label-mono mt-1.5" style={{ fontSize: 9 }}>
        {label}
      </div>
    </div>
  );
}
