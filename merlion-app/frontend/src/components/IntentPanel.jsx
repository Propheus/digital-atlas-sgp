"use client";
import { motion, AnimatePresence } from "framer-motion";
import { Brain, Target, Workflow } from "lucide-react";

const CONF_COLOR = (c) =>
  c >= 0.85 ? "text-ok" : c >= 0.6 ? "text-warn" : "text-err";

const STRAT_BG = (s) =>
  s === "llm" ? "bg-accent-dim text-accent" :
  s === "rule_based" ? "bg-ok/15 text-ok" :
  s === "rule_based_fallback" ? "bg-warn/15 text-warn" :
  "bg-bg-3 text-fg-3";

export default function IntentPanel({ data }) {
  if (!data) {
    return (
      <div className="glass rounded-xl p-5 h-full">
        <div className="flex items-center gap-2 text-fg-3 text-sm">
          <Brain size={16} className="text-accent" />
          <span>Intent classification will appear here…</span>
        </div>
      </div>
    );
  }

  const { intents = [], chosen, result } = data;
  const ents = chosen?.entities || {};
  const meta = result?.meta || {};

  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={chosen?.use_case}
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -8 }}
        transition={{ duration: 0.25 }}
        className="glass rounded-xl p-5 space-y-5 h-full overflow-y-auto"
      >
        {/* Intent candidates */}
        <section>
          <div className="flex items-center gap-2 mb-2.5">
            <Brain size={16} className="text-accent" />
            <h3 className="text-xs uppercase tracking-wider text-fg-2 font-medium">
              Intent candidates
            </h3>
          </div>
          <div className="space-y-1.5">
            {intents.slice(0, 3).map((it, i) => (
              <div
                key={it.use_case + i}
                className={`flex items-center justify-between rounded-lg px-3 py-2 ${i === 0 ? "bg-accent-dim border border-brd" : "bg-bg-3/50"}`}
              >
                <div className="flex items-center gap-2">
                  {i === 0 && <span className="text-accent">→</span>}
                  <span className={`text-sm ${i === 0 ? "text-accent font-medium" : "text-fg-2"}`}>
                    {it.use_case}
                  </span>
                  <span className={`text-[9px] uppercase px-1.5 py-0.5 rounded ${STRAT_BG(it.strategy)}`}>
                    {it.strategy}
                  </span>
                </div>
                <span className={`font-mono text-xs ${CONF_COLOR(it.confidence)}`}>
                  {(it.confidence * 100).toFixed(0)}%
                </span>
              </div>
            ))}
          </div>
        </section>

        {/* Entities */}
        {chosen && Object.keys(ents).length > 0 && (
          <section>
            <div className="flex items-center gap-2 mb-2.5">
              <Target size={16} className="text-accent" />
              <h3 className="text-xs uppercase tracking-wider text-fg-2 font-medium">
                Extracted entities
              </h3>
            </div>
            <div className="space-y-1 text-xs font-mono">
              {Object.entries(ents).map(([k, v]) => (
                <div key={k} className="flex items-start gap-2">
                  <span className="text-fg-3 shrink-0 w-28">{k}</span>
                  <span className="text-fg-2 break-all">
                    {typeof v === "object" ? JSON.stringify(v) : String(v)}
                  </span>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Routing / models */}
        <section>
          <div className="flex items-center gap-2 mb-2.5">
            <Workflow size={16} className="text-accent" />
            <h3 className="text-xs uppercase tracking-wider text-fg-2 font-medium">
              Model choreography
            </h3>
          </div>
          <div className="space-y-1.5 text-xs">
            <Row label="Primary model" value={meta.primary_model} highlight />
            <Row
              label="Augment models"
              value={meta.augment_models?.length ? meta.augment_models.join(", ") : "—"}
            />
            <Row label="Strategy" value={meta.strategy} />
          </div>
        </section>
      </motion.div>
    </AnimatePresence>
  );
}

function Row({ label, value, highlight }) {
  return (
    <div className="flex items-center justify-between rounded-md px-3 py-1.5 bg-bg-3/50">
      <span className="text-fg-3">{label}</span>
      <span className={`font-mono ${highlight ? "text-accent" : "text-fg-2"}`}>
        {value || "—"}
      </span>
    </div>
  );
}
