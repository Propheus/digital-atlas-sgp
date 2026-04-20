"use client";
import { useEffect, useState } from "react";
import Header from "@/components/Header";
import QueryBox from "@/components/QueryBox";
import IntentPanel from "@/components/IntentPanel";
import ResultPanel from "@/components/ResultPanel";
import ProfilePanel from "@/components/ProfilePanel";
import ExplainPanel from "@/components/ExplainPanel";
import { api } from "@/lib/api";

export default function Home() {
  const [apiStatus, setApiStatus] = useState("unknown");
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState(null);
  const [error, setError] = useState(null);
  const [history, setHistory] = useState([]);

  useEffect(() => {
    api.health().then(() => setApiStatus("ok")).catch(() => setApiStatus("error"));
  }, []);

  const onAsk = async (query) => {
    setLoading(true);
    setError(null);
    try {
      const start = performance.now();
      const res = await api.ask(query);
      const dur = Math.round(performance.now() - start);
      setResponse(res);
      setHistory((h) => [{ query, ts: Date.now(), dur, uc: res.chosen?.use_case }, ...h].slice(0, 8));
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen flex flex-col">
      <Header apiStatus={apiStatus} />

      <div className="flex-1 max-w-[1400px] mx-auto w-full px-6 py-6 space-y-6">
        <QueryBox onAsk={onAsk} loading={loading} />

        {error && (
          <div className="rounded-lg border border-err/30 bg-err/10 px-4 py-2 text-sm text-err">
            Error: {error}
          </div>
        )}

        {/* Plain-English explanation — business-user summary */}
        {response?.result?.explain && (
          <ExplainPanel explain={response.result.explain} />
        )}

        {/* Concept profile banner — only when the handler produced one */}
        {response?.result?.profile && (
          <ProfilePanel profile={response.result.profile} />
        )}

        <div className="grid grid-cols-1 lg:grid-cols-5 gap-6 min-h-[420px]">
          <div className="lg:col-span-2">
            <IntentPanel data={response} />
          </div>
          <div className="lg:col-span-3">
            <ResultPanel data={response} />
          </div>
        </div>

        {history.length > 0 && (
          <section className="glass rounded-xl p-4">
            <h3 className="text-xs uppercase tracking-wider text-fg-2 font-medium mb-2">
              Recent queries
            </h3>
            <div className="space-y-1.5">
              {history.map((h, i) => (
                <div key={i} className="flex items-center gap-3 text-xs">
                  <span className="font-mono text-fg-3 w-16">{h.dur}ms</span>
                  <span className="text-accent font-mono min-w-[160px]">{h.uc || "—"}</span>
                  <span className="text-fg-2 truncate">{h.query}</span>
                </div>
              ))}
            </div>
          </section>
        )}
      </div>

      <footer className="text-center text-xs text-fg-3 py-4 border-t border-brd/30">
        Propheus · Real World Engine v0.1 · powered by Merlion · 9 use cases · 4 embedding models · 260-test validated
      </footer>
    </main>
  );
}
