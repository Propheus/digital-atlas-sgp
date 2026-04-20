"use client";
import { useState } from "react";
import { motion } from "framer-motion";
import { Code2, Info, MapPin, Grid3x3, Lightbulb, ChevronRight } from "lucide-react";

export default function ResultPanel({ data }) {
  const [view, setView] = useState("cards");

  if (!data) {
    return (
      <div className="glass rounded-xl p-5 h-full flex items-center justify-center text-fg-3 text-sm gap-2">
        <Info size={16} className="text-accent" />
        Ask a question to see real results from the Real World Engine…
      </div>
    );
  }

  const { result, chosen } = data;
  const stubbed = result?.status === "stub";
  const results = result?.results || [];
  const clusters = result?.clusters;
  const per_category = result?.per_category;

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="glass rounded-xl p-5 h-full overflow-y-auto"
    >
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Code2 size={16} className="text-accent" />
          <h3 className="text-xs uppercase tracking-wider text-fg-2 font-medium">
            {chosen?.use_case || "response"} · {result?.meta?.primary_model}
          </h3>
          {result?.k && (
            <span className="text-[10px] text-fg-3">k={result.k}</span>
          )}
        </div>
        <div className="flex items-center gap-1.5">
          {stubbed && (
            <span className="text-[10px] uppercase px-2 py-0.5 rounded bg-warn/15 text-warn">stub</span>
          )}
          {(results?.length > 0 || clusters) && (
            <div className="flex gap-1 rounded-md bg-bg-3/60 p-0.5">
              <button
                onClick={() => setView("cards")}
                className={`p-1 rounded ${view === "cards" ? "bg-accent-dim text-accent" : "text-fg-3"}`}
                title="Cards"
              >
                <Grid3x3 size={12} />
              </button>
              <button
                onClick={() => setView("json")}
                className={`p-1 rounded ${view === "json" ? "bg-accent-dim text-accent" : "text-fg-3"}`}
                title="Raw JSON"
              >
                <Code2 size={12} />
              </button>
            </div>
          )}
        </div>
      </div>

      {stubbed && (
        <div className="mb-3 rounded-lg border border-warn/30 bg-warn/10 px-3 py-2 text-xs text-warn/90">
          <strong>Layer 1 not wired for this case.</strong> Routing resolved correctly; inputs + metadata shown.
        </div>
      )}

      {result?.explanation && (
        <p className="text-[11px] text-fg-3 italic mb-3 leading-relaxed">
          {result.explanation}
        </p>
      )}

      {/* Cards view */}
      {view === "cards" && (
        <>
          {results.length > 0 && (
            <HexList
              results={results}
              perItem={result?.explain?.per_item || []}
            />
          )}
          {clusters && <ClusterList clusters={clusters} />}
          {per_category && <PerCategory data={per_category} info={result.info} />}
          {!results.length && !clusters && !per_category && (
            <RawJson data={result} />
          )}
        </>
      )}

      {/* JSON view */}
      {view === "json" && <RawJson data={result} />}

      {chosen && (
        <p className="mt-3 text-[10px] text-fg-3">
          {chosen.strategy === "llm" ? "🤖 Claude Sonnet" : "⚡ rule-based"} ·{" "}
          {(chosen.confidence * 100).toFixed(0)}% confidence
        </p>
      )}
    </motion.div>
  );
}

function HexList({ results, perItem = [] }) {
  const whyByHex = Object.fromEntries(perItem.map((p) => [p.hex_id, p.why]));
  return (
    <div className="space-y-1.5">
      {results.slice(0, 20).map((r, i) => {
        const why = whyByHex[r.hex_id];
        return (
          <HexRow key={r.hex_id + i} r={r} i={i} why={why} />
        );
      })}
    </div>
  );
}

function HexRow({ r, i, why }) {
  const [open, setOpen] = useState(false);
  return (
    <div
      className={`rounded-lg bg-bg-3/40 border ${open ? "border-brd" : "border-transparent"} hover:border-brd transition overflow-hidden`}
    >
      <div
        className="flex items-center gap-3 px-3 py-2 cursor-pointer hover:bg-accent-dim/30"
        onClick={() => why && setOpen((o) => !o)}
      >
        <span className="text-accent text-xs font-mono w-6 text-right">{i + 1}</span>
        <MapPin size={14} className="text-accent shrink-0" />
        <div className="flex-1 min-w-0">
          <div className="text-sm text-fg font-medium">
            {r.parent_subzone_name || r.parent_subzone || "—"}
          </div>
          <div className="text-[10px] text-fg-3 flex items-center gap-2 font-mono">
            <span>{r.parent_pa}</span>
            <span>·</span>
            <span>{r.hex_id}</span>
            {r.lat && <span>· {r.lat?.toFixed(4)}, {r.lng?.toFixed(4)}</span>}
          </div>
        </div>
        {r.score !== undefined && (
          <span className="font-mono text-xs text-accent">
            {typeof r.score === "number" ? r.score.toFixed(3) : r.score}
          </span>
        )}
        {r.predicted !== undefined && r.actual !== undefined && (
          <span className="font-mono text-[10px] text-fg-3">
            {r.predicted.toFixed(1)}p/{r.actual.toFixed(0)}a
          </span>
        )}
        {why && (
          <ChevronRight size={14} className={`text-fg-3 transition ${open ? "rotate-90" : ""}`} />
        )}
      </div>
      {open && why && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: "auto" }}
          className="px-3 pb-2.5 pt-1 ml-12 border-l-2 border-accent/40 flex items-start gap-2"
        >
          <Lightbulb size={13} className="text-accent mt-1 shrink-0" />
          <p className="text-[12px] text-fg-2 leading-relaxed">{why}</p>
        </motion.div>
      )}
    </div>
  );
}

function ClusterList({ clusters }) {
  return (
    <div className="space-y-1.5">
      {clusters.map((c) => (
        <div key={c.cluster_id} className="flex items-center gap-3 rounded-lg bg-bg-3/40 px-3 py-2">
          <span className="text-accent font-mono text-xs w-8">#{c.cluster_id}</span>
          <div className="flex-1 min-w-0">
            <div className="text-sm text-fg">
              <span className="text-accent mr-1.5">rep:</span>
              {c.parent_subzone_name || "—"}
            </div>
            <div className="text-[10px] text-fg-3 font-mono">
              {c.parent_pa} · {c.representative_hex}
            </div>
          </div>
          <span className="text-xs text-fg-2 font-mono">{c.size} hexes</span>
        </div>
      ))}
    </div>
  );
}

function PerCategory({ data, info }) {
  const rows = Object.entries(data || {}).sort((a, b) => b[1].predicted - a[1].predicted);
  return (
    <div>
      {info && (
        <div className="mb-3 text-[11px] text-fg-3 font-mono">
          {info.parent_subzone_name} · {info.parent_pa} · {info.hex_id}
        </div>
      )}
      <div className="grid grid-cols-1 gap-1 text-xs">
        <div className="grid grid-cols-12 gap-2 px-2 py-1 text-[10px] text-fg-3 uppercase tracking-wider">
          <span className="col-span-5">Category</span>
          <span className="col-span-2 text-right">Pred</span>
          <span className="col-span-2 text-right">Actual</span>
          <span className="col-span-3 text-right">Gap</span>
        </div>
        {rows.map(([cat, vals]) => {
          const gap = vals.gap ?? vals.predicted - vals.actual;
          const gapColor = gap > 2 ? "text-warn" : gap < -2 ? "text-ok" : "text-fg-2";
          return (
            <div key={cat} className="grid grid-cols-12 gap-2 px-2 py-1 rounded hover:bg-bg-3/50">
              <span className="col-span-5 text-fg-2">{cat}</span>
              <span className="col-span-2 text-right font-mono text-accent">
                {vals.predicted?.toFixed(1)}
              </span>
              <span className="col-span-2 text-right font-mono text-fg-2">
                {vals.actual?.toFixed(0)}
              </span>
              <span className={`col-span-3 text-right font-mono ${gapColor}`}>
                {gap >= 0 ? "+" : ""}{gap.toFixed(1)}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function RawJson({ data }) {
  return (
    <pre className="bg-bg font-mono text-[11px] leading-relaxed text-fg-2 p-4 rounded-lg overflow-x-auto border border-brd/40 max-h-[400px] overflow-y-auto">
      {JSON.stringify(data, null, 2)}
    </pre>
  );
}
