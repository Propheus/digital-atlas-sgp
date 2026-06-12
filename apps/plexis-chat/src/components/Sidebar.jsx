"use client";
import { Plus, MessageSquare, Trash2, HelpCircle, PanelLeftClose, GitCompare } from "lucide-react";

export default function Sidebar({ open, conversations, activeId, view, onNew, onOpen, onDelete, onHelp, onCollapse, onCompare }) {
  return (
    <aside
      className="flex-shrink-0 flex flex-col h-full transition-all duration-300 overflow-hidden"
      style={{
        width: open ? 276 : 0,
        background: "rgba(9,22,24,0.6)",
        borderRight: open ? "1px solid var(--glass-border)" : "none",
        backdropFilter: "blur(8px)",
      }}
    >
      <div style={{ width: 276 }} className="flex flex-col h-full">
        {/* brand */}
        <div className="flex items-center justify-between px-4 h-[54px] flex-shrink-0"
          style={{ borderBottom: "1px solid var(--glass-border)" }}>
          <div className="flex items-center gap-2.5">
            <img src="/propheus.svg" alt="Propheus" width={26} height={26} style={{ display: "block" }} />
            <div className="leading-tight">
              <div style={{ color: "var(--teal)", fontWeight: 700, fontSize: 15, letterSpacing: "0.3px" }}>ALCHEMY</div>
              <div style={{ color: "var(--t3)", fontSize: 10 }}>by Propheus</div>
            </div>
          </div>
          <button onClick={onCollapse} title="Hide sidebar"
            className="w-7 h-7 rounded-md flex items-center justify-center" style={{ color: "var(--t3)" }}
            onMouseEnter={(e) => (e.currentTarget.style.background = "rgba(255,255,255,0.06)")}
            onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}>
            <PanelLeftClose size={16} />
          </button>
        </div>

        {/* new chat + compare */}
        <div className="p-3 space-y-2">
          <button onClick={onNew}
            className="w-full flex items-center gap-2 px-3 py-2.5 rounded-lg text-[14px] font-medium transition-all"
            style={{ background: "linear-gradient(135deg,#20B2AA,#17c7ba)", color: "#06201e" }}>
            <Plus size={16} /> New chat
          </button>
          <button onClick={onCompare}
            className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-[13px] font-medium transition-all"
            style={{
              background: view === "compare" ? "rgba(32,178,170,0.16)" : "transparent",
              color: view === "compare" ? "var(--teal-bright)" : "var(--t2)",
              border: "1px solid var(--glass-border)",
            }}>
            <GitCompare size={15} /> Compare models
          </button>
        </div>

        {/* conversation list */}
        <div className="flex-1 overflow-y-auto scroll-thin px-2">
          <div className="px-2 py-1 text-[11px] uppercase tracking-wide" style={{ color: "var(--t3)" }}>
            Saved conversations
          </div>
          {conversations.length === 0 && (
            <div className="px-2 py-3 text-[12px]" style={{ color: "var(--t3)" }}>
              Your chats will appear here.
            </div>
          )}
          {conversations.map((c) => (
            <div key={c.id}
              className="group flex items-center gap-2 px-2.5 py-2 rounded-lg cursor-pointer mb-0.5 transition-colors"
              style={{ background: c.id === activeId ? "rgba(32,178,170,0.14)" : "transparent" }}
              onClick={() => onOpen(c.id)}
              onMouseEnter={(e) => { if (c.id !== activeId) e.currentTarget.style.background = "rgba(255,255,255,0.05)"; }}
              onMouseLeave={(e) => { if (c.id !== activeId) e.currentTarget.style.background = "transparent"; }}>
              <MessageSquare size={14} style={{ color: c.id === activeId ? "var(--teal-bright)" : "var(--t3)", flexShrink: 0 }} />
              <span className="flex-1 truncate text-[13px]" style={{ color: c.id === activeId ? "var(--t1)" : "var(--t2)" }}>
                {c.title || "New chat"}
              </span>
              <button title="Delete"
                onClick={(e) => { e.stopPropagation(); onDelete(c.id); }}
                className="opacity-0 group-hover:opacity-100 w-6 h-6 rounded-md flex items-center justify-center flex-shrink-0"
                style={{ color: "var(--t3)" }}
                onMouseEnter={(e) => (e.currentTarget.style.color = "#f87171")}
                onMouseLeave={(e) => (e.currentTarget.style.color = "var(--t3)")}>
                <Trash2 size={13} />
              </button>
            </div>
          ))}
        </div>

        {/* footer */}
        <div className="p-3" style={{ borderTop: "1px solid var(--glass-border)" }}>
          <button onClick={onHelp}
            className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-[13px] transition-colors"
            style={{ color: "var(--t2)" }}
            onMouseEnter={(e) => (e.currentTarget.style.background = "rgba(32,178,170,0.1)")}
            onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}>
            <HelpCircle size={15} /> What can it answer?
          </button>
        </div>
      </div>
    </aside>
  );
}
