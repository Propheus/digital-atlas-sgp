"use client";
import { useState } from "react";
import { motion } from "framer-motion";
import { MessageSquare, Lightbulb, BookOpen, ChevronDown } from "lucide-react";

export default function ExplainPanel({ explain }) {
  const [methodologyOpen, setMethodologyOpen] = useState(false);

  if (!explain || (!explain.summary && !explain.methodology)) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
      className="glass rounded-xl p-5 space-y-3"
    >
      {explain.summary && (
        <div className="flex items-start gap-3">
          <MessageSquare size={18} className="text-accent mt-0.5 shrink-0" />
          <div className="flex-1">
            <div className="text-[10px] uppercase tracking-wider text-fg-3 mb-1">
              Executive summary
            </div>
            <p className="text-sm text-fg leading-relaxed">{explain.summary}</p>
          </div>
        </div>
      )}

      {explain.methodology && (
        <div>
          <button
            onClick={() => setMethodologyOpen((o) => !o)}
            className="w-full flex items-center gap-2 text-[11px] text-fg-3 hover:text-accent pt-2 border-t border-brd/30"
          >
            <BookOpen size={12} />
            <span className="uppercase tracking-wider">How the engine reasoned</span>
            <ChevronDown
              size={12}
              className={`ml-auto transition ${methodologyOpen ? "rotate-180" : ""}`}
            />
          </button>
          {methodologyOpen && (
            <motion.p
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              className="mt-2 text-[12px] text-fg-2 leading-relaxed pl-5"
            >
              {explain.methodology}
            </motion.p>
          )}
        </div>
      )}
    </motion.div>
  );
}

export function WhyPerItem({ per_item, results }) {
  /** Map per-item explanations onto the visible hex list. */
  if (!per_item?.length) return null;
  const byHex = Object.fromEntries(per_item.map((p) => [p.hex_id, p]));
  return (
    <div className="space-y-1.5 mt-3">
      {per_item.slice(0, 5).map((p) => (
        <div
          key={p.hex_id + p.rank}
          className="flex items-start gap-2 rounded-md bg-accent-dim/30 px-3 py-2 border border-brd/30"
        >
          <Lightbulb size={13} className="text-accent mt-0.5 shrink-0" />
          <div className="text-[12px] leading-relaxed">
            <span className="text-accent font-semibold mr-1.5">#{p.rank}</span>
            <span className="text-fg-2">{p.why}</span>
          </div>
        </div>
      ))}
    </div>
  );
}
