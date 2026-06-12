"use client";
import { motion, AnimatePresence } from "framer-motion";
import { X, HelpCircle, Sparkles, Lightbulb, AlertCircle } from "lucide-react";
import { CAPABILITIES, TIPS, LIMITS } from "@/lib/content";

export default function HelpModal({ open, onClose }) {
  return (
    <AnimatePresence>
      {open && (
        <>
          <motion.div
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 z-50"
            style={{ background: "rgba(0,0,0,0.6)", backdropFilter: "blur(4px)" }}
          />
          <motion.div
            initial={{ opacity: 0, scale: 0.96, y: 16 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.96, y: 16 }}
            transition={{ duration: 0.2 }}
            className="fixed z-50 top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[92vw] max-w-2xl max-h-[85vh] overflow-hidden rounded-2xl scroll-thin"
            style={{ background: "linear-gradient(135deg,#0D1F21,#132C30)", border: "1px solid var(--glass-border)", boxShadow: "0 25px 60px -12px rgba(0,0,0,0.6)" }}
          >
            {/* header */}
            <div className="flex items-center justify-between p-5" style={{ borderBottom: "1px solid var(--glass-border)" }}>
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl flex items-center justify-center"
                  style={{ background: "rgba(32,178,170,0.15)", border: "1px solid var(--glass-border)" }}>
                  <HelpCircle className="w-5 h-5" style={{ color: "var(--teal)" }} />
                </div>
                <div>
                  <h2 className="text-lg font-semibold" style={{ color: "var(--t1)" }}>What Alchemy can answer</h2>
                  <p className="text-xs" style={{ color: "var(--t3)" }}>A reasoning model grounded in the Alchemy atlas of Singapore</p>
                </div>
              </div>
              <button onClick={onClose} className="w-8 h-8 rounded-lg flex items-center justify-center transition-colors"
                style={{ color: "var(--t3)" }}
                onMouseEnter={(e) => (e.currentTarget.style.background = "rgba(255,255,255,0.08)")}
                onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}>
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* body */}
            <div className="p-5 overflow-y-auto scroll-thin" style={{ maxHeight: "calc(85vh - 80px)" }}>
              <SectionTitle icon={Sparkles} label="Ask about" />
              <div className="grid sm:grid-cols-2 gap-2.5 mb-6">
                {CAPABILITIES.map((c, i) => (
                  <motion.div key={i} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.04 }}
                    className="flex gap-3 p-3 rounded-xl" style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.05)" }}>
                    <div className="w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0" style={{ background: "rgba(32,178,170,0.14)" }}>
                      <c.icon className="w-4 h-4" style={{ color: "var(--teal)" }} />
                    </div>
                    <div>
                      <h4 className="text-sm font-medium mb-0.5" style={{ color: "var(--t1)" }}>{c.title}</h4>
                      <p className="text-xs leading-relaxed" style={{ color: "var(--t3)" }}>{c.desc}</p>
                    </div>
                  </motion.div>
                ))}
              </div>

              <SectionTitle icon={Lightbulb} label="Tips for the best answers" />
              <div className="space-y-2 mb-6">
                {TIPS.map((t, i) => (
                  <div key={i} className="flex gap-3 p-3 rounded-xl" style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.05)" }}>
                    <t.icon className="w-4 h-4 mt-0.5 flex-shrink-0" style={{ color: "var(--teal-bright)" }} />
                    <div>
                      <h4 className="text-sm font-medium mb-0.5" style={{ color: "var(--t1)" }}>{t.title}</h4>
                      <p className="text-xs leading-relaxed" style={{ color: "var(--t3)" }}>{t.desc}</p>
                    </div>
                  </div>
                ))}
              </div>

              <SectionTitle icon={AlertCircle} label="Good to know" />
              <ul className="space-y-1.5">
                {LIMITS.map((l, i) => (
                  <li key={i} className="flex gap-2 text-xs leading-relaxed" style={{ color: "var(--t3)" }}>
                    <span style={{ color: "var(--teal)" }}>•</span> {l}
                  </li>
                ))}
              </ul>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}

function SectionTitle({ icon: Icon, label }) {
  return (
    <div className="flex items-center gap-2 mb-3">
      <Icon className="w-4 h-4" style={{ color: "var(--teal)" }} />
      <span className="text-[13px] font-semibold uppercase tracking-wide" style={{ color: "var(--t2)" }}>{label}</span>
    </div>
  );
}
