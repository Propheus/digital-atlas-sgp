"use client";
import { useState } from "react";
import { Send, Sparkles } from "lucide-react";

const EXAMPLES = [
  "find sites to open Alfamart in singapore",
  "where should I open a new Starbucks",
  "where should FairPrice expand next",
  "find 10 hexes similar to Tiong Bahru for a specialty cafe",
  "where are hawker centres missing in the heartland",
  "cluster all neighborhoods into urban archetypes",
  "hexes comparable to Orchard for valuation",
  "predict expected cafes per hex in Marina Bay",
  "find food deserts in Singapore",
  "compute 15-minute city score for each hex",
];

export default function QueryBox({ onAsk, loading }) {
  const [q, setQ] = useState("");

  const submit = (text) => {
    const v = (text ?? q).trim();
    if (!v) return;
    onAsk(v);
  };

  return (
    <div className="glass rounded-xl p-5 shadow-glass">
      <div className="flex items-start gap-3">
        <Sparkles className="text-accent mt-1.5 shrink-0" size={20} />
        <textarea
          value={q}
          onChange={(e) => setQ(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              submit();
            }
          }}
          placeholder="Ask Merlion about Singapore's urban structure…"
          className="flex-1 bg-transparent resize-none outline-none text-fg placeholder:text-fg-3 text-[14px] leading-relaxed"
          rows={2}
          disabled={loading}
        />
        <button
          onClick={() => submit()}
          disabled={loading || !q.trim()}
          className="bg-accent text-bg font-medium px-4 py-2 rounded-lg text-sm disabled:opacity-40 hover:bg-accent-2 transition flex items-center gap-1.5 shrink-0"
        >
          <Send size={14} />
          {loading ? "Routing…" : "Ask"}
        </button>
      </div>
      <div className="mt-4 flex flex-wrap gap-1.5 pt-3 border-t border-brd/40">
        <span className="text-[10px] uppercase tracking-wide text-fg-3 mr-2 mt-1">try</span>
        {EXAMPLES.map((ex) => (
          <button
            key={ex}
            onClick={() => { setQ(ex); submit(ex); }}
            className="text-xs px-2.5 py-1 rounded-full bg-bg-3 text-fg-2 hover:bg-accent-dim hover:text-accent transition border border-brd/40"
            disabled={loading}
          >
            {ex}
          </button>
        ))}
      </div>
    </div>
  );
}
