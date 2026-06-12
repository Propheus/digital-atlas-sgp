"use client";
import { useState, useRef, useEffect, useCallback } from "react";
import { ArrowUp, Sparkles, GitCompare, MapPin } from "lucide-react";
import { renderMd } from "@/lib/md";

const SUGGESTIONS = [
  "What is Tampines East most under-served for?",
  "How family-friendly is Bedok North, and what drives it?",
  "Where's the F&B opportunity in Jurong East?",
  "What's the crime rate in Tampines?",
];

export default function Compare() {
  const [rounds, setRounds] = useState([]); // {q, entity, grounded, alchemy, raw}
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const scrollRef = useRef(null);
  const taRef = useRef(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [rounds]);
  useEffect(() => {
    const ta = taRef.current; if (!ta) return;
    ta.style.height = "auto"; ta.style.height = Math.min(ta.scrollHeight, 160) + "px";
  }, [input]);

  const send = useCallback(async (text) => {
    const q = (text ?? input).trim();
    if (!q || busy) return;
    setInput(""); setBusy(true);
    const idx = rounds.length;
    setRounds((r) => [...r, { q, entity: null, grounded: false, alchemy: "", raw: "" }]);

    const upd = (patch) => setRounds((r) => {
      const n = [...r]; n[idx] = { ...n[idx], ...(typeof patch === "function" ? patch(n[idx]) : patch) }; return n;
    });

    try {
      const res = await fetch("/api/compare", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ messages: [{ role: "user", content: q }] }),
      });
      const reader = res.body.getReader();
      const dec = new TextDecoder(); let buf = "";
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buf += dec.decode(value, { stream: true });
        const lines = buf.split("\n"); buf = lines.pop();
        for (const line of lines) {
          const s = line.trim();
          if (!s.startsWith("data:")) continue;
          const p = s.slice(5).trim();
          if (p === "[DONE]") continue;
          let o; try { o = JSON.parse(p); } catch { continue; }
          if (o.meta) upd({ entity: o.meta.entity, grounded: o.meta.grounded });
          if (o.token && o.model === "alchemy") upd((cur) => ({ alchemy: cur.alchemy + o.token }));
          if (o.token && o.model === "raw") upd((cur) => ({ raw: cur.raw + o.token }));
        }
      }
    } catch {
      upd((cur) => ({ alchemy: cur.alchemy + "\n\n⚠️ Connection interrupted." }));
    } finally { setBusy(false); }
  }, [input, busy, rounds]);

  const onKey = (e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); } };

  return (
    <div className="flex-1 flex flex-col min-h-0">
      <div className="px-4 py-2.5 flex items-center justify-center gap-2 flex-shrink-0"
        style={{ borderBottom: "1px solid var(--glass-border)", background: "rgba(32,178,170,0.04)" }}>
        <GitCompare size={14} style={{ color: "var(--teal)" }} />
        <span className="text-[12.5px]" style={{ color: "var(--t2)" }}>
          Same question, same atlas context sent to both — only the model weights differ.
        </span>
      </div>

      <div ref={scrollRef} className="flex-1 overflow-y-auto scroll-thin">
        {rounds.length === 0 ? (
          <div className="max-w-2xl mx-auto px-4 pt-[8vh] text-center">
            <GitCompare size={40} className="mx-auto mb-4" style={{ color: "var(--teal-bright)" }} />
            <h1 className="text-2xl font-bold" style={{ color: "var(--teal-bright)" }}>Compare models</h1>
            <p className="mt-2 text-[14px]" style={{ color: "var(--t2)" }}>
              Alchemy (fine-tuned) vs raw Gemma 12B — same prompt, side by side. Try the abstention and
              calibration questions to see the difference.
            </p>
            <div className="flex flex-wrap gap-2 justify-center mt-6">
              {SUGGESTIONS.map((s, i) => (
                <button key={i} onClick={() => send(s)}
                  className="text-[12.5px] px-3 py-1.5 rounded-full"
                  style={{ background: "rgba(32,178,170,0.08)", color: "var(--teal-bright)", border: "1px solid var(--glass-border)" }}>
                  {s}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="max-w-5xl mx-auto px-4 py-5 space-y-7">
            {rounds.map((r, i) => (
              <div key={i} className="animate-fadeUp">
                <div className="flex items-center gap-2 mb-3">
                  <span className="text-[13px] font-semibold px-3 py-1.5 rounded-lg"
                    style={{ background: "rgba(255,255,255,0.06)", color: "var(--t1)" }}>{r.q}</span>
                  {r.grounded && r.entity && (
                    <span className="inline-flex items-center gap-1 text-[11px] px-2 py-0.5 rounded-full"
                      style={{ background: "rgba(32,178,170,0.12)", color: "var(--teal-bright)", border: "1px solid var(--glass-border)" }}>
                      <MapPin size={11} /> {r.entity}
                    </span>
                  )}
                </div>
                <div className="grid md:grid-cols-2 gap-3">
                  <Col title="Alchemy" tag="fine-tuned" accent="var(--teal-bright)"
                    glow="rgba(32,178,170,0.35)" content={r.alchemy} busy={busy && !r.alchemy} />
                  <Col title="Gemma 12B" tag="base · no fine-tuning" accent="#94a3b8"
                    glow="rgba(148,163,184,0.25)" content={r.raw}
                    busy={busy && !!r.alchemy && !r.raw} waiting={busy && !r.raw && !r.alchemy} />
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* composer */}
      <div className="flex-shrink-0 px-4 pb-5 pt-2" style={{ background: "linear-gradient(to top, var(--bg) 55%, transparent)" }}>
        <div className="max-w-3xl mx-auto">
          <div className="glass rounded-2xl flex items-end gap-2 p-2 pl-4" style={{ boxShadow: "0 8px 30px rgba(0,0,0,0.25)" }}>
            <textarea ref={taRef} rows={1} value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={onKey}
              placeholder={busy ? "Generating both answers…" : "Ask the same question to both models…"}
              disabled={busy}
              className="flex-1 bg-transparent resize-none outline-none py-2.5 text-[15px] scroll-thin"
              style={{ color: "var(--t1)", maxHeight: 160 }} />
            <button onClick={() => send()} disabled={!input.trim() || busy} title="Compare"
              className="flex-shrink-0 w-9 h-9 rounded-xl flex items-center justify-center"
              style={{ background: "linear-gradient(135deg,#20B2AA,#17c7ba)", color: "#06201e", opacity: (input.trim() && !busy) ? 1 : 0.4 }}>
              <ArrowUp size={18} strokeWidth={2.5} />
            </button>
          </div>
          <p className="text-center text-[11px] mt-2" style={{ color: "var(--t3)" }}>
            Both run on the same Gemma-12B weights; Alchemy adds the fine-tuned LoRA adapter. Answers stream left then right.
          </p>
        </div>
      </div>
    </div>
  );
}

function Col({ title, tag, accent, glow, content, busy, waiting }) {
  return (
    <div className="rounded-xl p-4 glass" style={{ borderColor: "var(--glass-border)" }}>
      <div className="flex items-center gap-2 mb-2.5 pb-2.5" style={{ borderBottom: "1px solid var(--glass-border)" }}>
        <span className="w-2 h-2 rounded-full" style={{ background: accent, boxShadow: `0 0 8px ${glow}` }} />
        <span className="text-[13px] font-semibold" style={{ color: accent }}>{title}</span>
        <span className="text-[11px] px-2 py-0.5 rounded-full" style={{ background: "rgba(255,255,255,0.05)", color: "var(--t3)" }}>{tag}</span>
      </div>
      {content
        ? <div className="md" dangerouslySetInnerHTML={{ __html: renderMd(content) }} />
        : <div className="text-[13px]" style={{ color: "var(--t3)" }}>{waiting ? "Queued…" : busy ? "Thinking…" : "—"}</div>}
    </div>
  );
}
