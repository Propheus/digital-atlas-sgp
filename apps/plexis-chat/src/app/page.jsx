"use client";
import { useState, useRef, useEffect, useCallback } from "react";
import { ArrowUp, Square, PanelLeftOpen, HelpCircle, Sparkles } from "lucide-react";
import Message from "@/components/Message";
import HelpModal from "@/components/HelpModal";
import Sidebar from "@/components/Sidebar";
import Compare from "@/components/Compare";
import { SAMPLE_QUESTIONS, SHOWCASE_QUESTIONS } from "@/lib/content";
import { followUps } from "@/lib/followups";
import {
  listConversations, loadConversation, saveConversation, deleteConversation, sendFeedback,
} from "@/lib/store";

export default function Home() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [help, setHelp] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [view, setView] = useState("chat"); // "chat" | "compare"
  const [conversations, setConversations] = useState([]);
  const [convId, setConvId] = useState(null);
  const scrollRef = useRef(null);
  const taRef = useRef(null);
  const abortRef = useRef(null);
  const convIdRef = useRef(null);

  const hasChat = messages.length > 0;

  const refreshList = useCallback(async () => setConversations(await listConversations()), []);
  useEffect(() => { refreshList(); }, [refreshList]);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);
  useEffect(() => {
    const ta = taRef.current; if (!ta) return;
    ta.style.height = "auto"; ta.style.height = Math.min(ta.scrollHeight, 200) + "px";
  }, [input]);

  const persist = useCallback(async (msgs) => {
    if (!msgs.some((m) => m.role === "assistant" && m.content)) return;
    const res = await saveConversation({ id: convIdRef.current, messages: msgs });
    if (res?.id) {
      convIdRef.current = res.id; setConvId(res.id);
      refreshList();
    }
  }, [refreshList]);

  const send = useCallback(async (text) => {
    const content = (text ?? input).trim();
    if (!content || busy) return;
    setInput("");
    const history = [...messages, { role: "user", content }];
    const aiIndex = history.length;
    setMessages([...history, { role: "assistant", content: "", streaming: true }]);
    setBusy(true);

    const ctrl = new AbortController(); abortRef.current = ctrl;
    let acc = "", meta = null;
    try {
      const res = await fetch("/api/chat", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ messages: history.map(({ role, content }) => ({ role, content })) }),
        signal: ctrl.signal,
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
          let obj; try { obj = JSON.parse(p); } catch { continue; }
          if (obj.meta) meta = obj.meta;
          if (obj.token) acc += obj.token;
          setMessages((prev) => {
            const next = [...prev]; const m = { ...next[aiIndex] };
            if (obj.meta) { m.grounded = obj.meta.grounded; m.entity = obj.meta.entity; }
            if (obj.token) m.content += obj.token;
            next[aiIndex] = m; return next;
          });
        }
      }
    } catch (e) {
      if (e.name !== "AbortError") acc += "\n\n⚠️ Connection interrupted.";
    } finally {
      const finalMsgs = [...history, {
        role: "assistant", content: acc, streaming: false,
        entity: meta?.entity || null, grounded: !!meta?.grounded,
        q: content,
      }];
      setMessages(finalMsgs);
      setBusy(false); abortRef.current = null;
      persist(finalMsgs);
    }
  }, [input, busy, messages, persist]);

  const stop = () => abortRef.current?.abort();
  const newChat = () => { stop(); setMessages([]); setInput(""); convIdRef.current = null; setConvId(null); };

  const openConv = async (id) => {
    stop();
    const c = await loadConversation(id);
    if (!c) return;
    convIdRef.current = id; setConvId(id);
    setMessages(c.messages.map((m) => ({ ...m, streaming: false })));
  };
  const removeConv = async (id) => {
    await deleteConversation(id);
    if (id === convIdRef.current) newChat();
    refreshList();
  };

  const onFeedback = (index, vote) => {
    setMessages((prev) => {
      const next = [...prev];
      next[index] = { ...next[index], feedback: next[index].feedback === vote ? null : vote };
      return next;
    });
    const ans = messages[index];
    const q = messages[index - 1]?.content || ans?.q || "";
    sendFeedback({ conv_id: convIdRef.current, msg_idx: index, vote,
      question: q, answer: ans?.content?.slice(0, 2000), entity: ans?.entity || null });
  };

  const onKey = (e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); } };

  // follow-ups from the last completed assistant turn
  const last = messages[messages.length - 1];
  const suggestions = (!busy && last && last.role === "assistant" && last.entity)
    ? followUps(last.entity, messages[messages.length - 2]?.content || "")
    : [];

  return (
    <div className="h-screen flex">
      <Sidebar
        open={sidebarOpen} conversations={conversations} activeId={convId} view={view}
        onNew={() => { setView("chat"); newChat(); }}
        onOpen={(id) => { setView("chat"); openConv(id); }}
        onDelete={removeConv}
        onCompare={() => setView("compare")}
        onHelp={() => setHelp(true)} onCollapse={() => setSidebarOpen(false)}
      />
      <HelpModal open={help} onClose={() => setHelp(false)} />

      <div className="flex-1 flex flex-col min-w-0">
        {/* top bar */}
        <div className="flex items-center justify-between px-4 h-[54px] flex-shrink-0 glass"
          style={{ borderBottom: "1px solid var(--glass-border)" }}>
          <div className="flex items-center gap-3">
            {!sidebarOpen && (
              <button onClick={() => setSidebarOpen(true)} title="Show sidebar"
                className="w-8 h-8 rounded-md flex items-center justify-center" style={{ color: "var(--t2)" }}>
                <PanelLeftOpen size={17} />
              </button>
            )}
            <span style={{ color: "var(--t2)", fontSize: 13 }}>
              {view === "compare" ? "Compare · Alchemy vs raw Gemma"
                : convId ? (conversations.find((c) => c.id === convId)?.title || "Chat") : "New chat"}
            </span>
          </div>
          <button onClick={() => setHelp(true)}
            className="flex items-center gap-1.5 text-[13px] px-3 py-1.5 rounded-lg"
            style={{ color: "var(--teal)", border: "1px solid var(--glass-border)" }}>
            <HelpCircle size={15} /> Help
          </button>
        </div>

        {view === "compare" ? (
          <Compare />
        ) : (
          <>
            <main ref={scrollRef} className="flex-1 overflow-y-auto scroll-thin">
              {!hasChat ? (
                <EmptyState onPick={(q) => send(q)} onHelp={() => setHelp(true)} />
              ) : (
                <div className="py-4">
                  {messages.map((m, i) => <Message key={i} msg={m} index={i} onFeedback={onFeedback} />)}
                  <div className="h-2" />
                </div>
              )}
            </main>

            <Composer
              taRef={taRef} value={input} setValue={setInput} onKey={onKey}
              onSend={() => send()} onStop={stop} busy={busy}
              suggestions={suggestions} onSuggest={(q) => send(q)}
            />
          </>
        )}
      </div>
    </div>
  );
}

function EmptyState({ onPick, onHelp }) {
  return (
    <div className="max-w-3xl mx-auto px-4 pt-[7vh] pb-8">
      <div className="text-center mb-9">
        <img src="/propheus.svg" alt="Propheus" width={46} height={46} className="mx-auto mb-4" />
        <h1 className="text-3xl sm:text-4xl font-bold tracking-tight"
          style={{ color: "var(--teal-bright)", textShadow: "0 4px 24px rgba(23,199,186,0.28)" }}>
          Ask about Singapore
        </h1>
        <p className="mt-3 text-[15px]" style={{ color: "var(--t2)" }}>
          A reasoning model grounded in the Alchemy atlas — neighbourhoods, places, people, walkability and commuter flows.
        </p>
        <button onClick={onHelp} className="mt-2 text-[13px] underline-offset-2 hover:underline" style={{ color: "var(--teal)" }}>
          What can it answer?
        </button>
      </div>
      <div className="grid sm:grid-cols-2 gap-3">
        {SAMPLE_QUESTIONS.map((q, i) => (
          <button key={i} onClick={() => onPick(q.text)}
            className="glass text-left rounded-xl p-4 flex items-start gap-3 transition-all"
            style={{ borderColor: "var(--glass-border)" }}
            onMouseEnter={(e) => { e.currentTarget.style.borderColor = "rgba(32,178,170,0.5)"; e.currentTarget.style.transform = "translateY(-1px)"; }}
            onMouseLeave={(e) => { e.currentTarget.style.borderColor = "var(--glass-border)"; e.currentTarget.style.transform = "translateY(0)"; }}>
            <div className="w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0" style={{ background: `${q.color}22` }}>
              <q.icon size={18} style={{ color: q.color }} />
            </div>
            <span className="text-[14px] leading-snug pt-1" style={{ color: "var(--t1)" }}>{q.text}</span>
          </button>
        ))}
      </div>

      {/* model-only showcase pills */}
      <div className="mt-8">
        <div className="flex items-center gap-2 mb-3 justify-center">
          <Sparkles size={14} style={{ color: "var(--teal)" }} />
          <span className="text-[12.5px]" style={{ color: "var(--t2)" }}>
            Try what only Alchemy can do — judgment, data-sense &amp; honest limits, not just lookups
          </span>
        </div>
        <div className="flex flex-wrap gap-2 justify-center">
          {SHOWCASE_QUESTIONS.map((q, i) => (
            <button key={i} onClick={() => onPick(q)}
              className="text-[12.5px] px-3 py-1.5 rounded-full transition-all"
              style={{ background: "rgba(32,178,170,0.07)", color: "var(--teal-bright)", border: "1px solid var(--glass-border)" }}
              onMouseEnter={(e) => { e.currentTarget.style.background = "rgba(32,178,170,0.18)"; }}
              onMouseLeave={(e) => { e.currentTarget.style.background = "rgba(32,178,170,0.07)"; }}>
              {q}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

function Composer({ taRef, value, setValue, onKey, onSend, onStop, busy, suggestions, onSuggest }) {
  return (
    <div className="flex-shrink-0 px-4 pb-5 pt-2"
      style={{ background: "linear-gradient(to top, var(--bg) 55%, transparent)" }}>
      <div className="max-w-3xl mx-auto">
        {suggestions?.length > 0 && (
          <div className="flex flex-wrap gap-2 mb-2.5 animate-fadeUp">
            <span className="flex items-center gap-1 text-[12px] pr-1" style={{ color: "var(--t3)" }}>
              <Sparkles size={13} style={{ color: "var(--teal)" }} /> Continue:
            </span>
            {suggestions.map((s, i) => (
              <button key={i} onClick={() => onSuggest(s)}
                className="text-[12.5px] px-3 py-1.5 rounded-full transition-all"
                style={{ background: "rgba(32,178,170,0.08)", color: "var(--teal-bright)", border: "1px solid var(--glass-border)" }}
                onMouseEnter={(e) => (e.currentTarget.style.background = "rgba(32,178,170,0.18)")}
                onMouseLeave={(e) => (e.currentTarget.style.background = "rgba(32,178,170,0.08)")}>
                {s}
              </button>
            ))}
          </div>
        )}
        <div className="glass rounded-2xl flex items-end gap-2 p-2 pl-4" style={{ boxShadow: "0 8px 30px rgba(0,0,0,0.25)" }}>
          <textarea ref={taRef} rows={1} value={value}
            onChange={(e) => setValue(e.target.value)} onKeyDown={onKey}
            placeholder="Ask about a Singapore neighbourhood…"
            className="flex-1 bg-transparent resize-none outline-none py-2.5 text-[15px] scroll-thin"
            style={{ color: "var(--t1)", maxHeight: 200 }} />
          {busy ? (
            <button onClick={onStop} title="Stop" className="flex-shrink-0 w-9 h-9 rounded-xl flex items-center justify-center"
              style={{ background: "rgba(255,255,255,0.1)", color: "var(--t1)" }}>
              <Square size={15} fill="currentColor" />
            </button>
          ) : (
            <button onClick={onSend} disabled={!value.trim()} title="Send"
              className="flex-shrink-0 w-9 h-9 rounded-xl flex items-center justify-center transition-opacity"
              style={{ background: "linear-gradient(135deg,#20B2AA,#17c7ba)", color: "#06201e", opacity: value.trim() ? 1 : 0.4 }}>
              <ArrowUp size={18} strokeWidth={2.5} />
            </button>
          )}
        </div>
        <p className="text-center text-[11px] mt-2" style={{ color: "var(--t3)" }}>
          Alchemy grounds answers in the atlas and abstains when it doesn't know. Figures are model-stated — verify critical numbers.
        </p>
      </div>
    </div>
  );
}
