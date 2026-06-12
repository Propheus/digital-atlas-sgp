"use client";
import { Plus, HelpCircle } from "lucide-react";

export default function Header({ onNew, onHelp, hasChat }) {
  return (
    <header
      className="glass flex items-center justify-between px-5 flex-shrink-0"
      style={{ height: 54, borderBottom: "1px solid var(--glass-border)" }}
    >
      <div className="flex items-center gap-2.5">
        <div
          className="w-7 h-7 rounded-lg flex items-center justify-center font-bold text-[15px]"
          style={{ background: "linear-gradient(135deg,#20B2AA,#17c7ba)", color: "#06201e" }}
        >
          P
        </div>
        <div className="leading-tight">
          <div style={{ color: "var(--teal)", fontWeight: 600, fontSize: 16, letterSpacing: "0.3px" }}>
            ALCHEMY
          </div>
          <div style={{ color: "var(--t3)", fontSize: 11 }}>Singapore spatial intelligence</div>
        </div>
      </div>

      <div className="flex items-center gap-2">
        {hasChat && (
          <button
            onClick={onNew}
            className="flex items-center gap-1.5 text-[13px] px-3 py-1.5 rounded-lg transition-colors"
            style={{ color: "var(--t2)", border: "1px solid var(--glass-border)", background: "transparent" }}
            onMouseEnter={(e) => (e.currentTarget.style.background = "rgba(32,178,170,0.08)")}
            onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
          >
            <Plus size={15} /> New chat
          </button>
        )}
        <button
          onClick={onHelp}
          className="flex items-center gap-1.5 text-[13px] px-3 py-1.5 rounded-lg transition-colors"
          style={{ color: "var(--teal)", border: "1px solid var(--glass-border)", background: "transparent" }}
          onMouseEnter={(e) => (e.currentTarget.style.background = "rgba(32,178,170,0.12)")}
          onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
        >
          <HelpCircle size={15} /> Help
        </button>
      </div>
    </header>
  );
}
