"use client";
import { useMemo } from "react";
import { MapPin, ThumbsUp, ThumbsDown } from "lucide-react";
import { renderMd } from "@/lib/md";

function Avatar({ who }) {
  const isUser = who === "user";
  return (
    <div
      className="flex-shrink-0 w-8 h-8 rounded-lg flex items-center justify-center text-[13px] font-semibold"
      style={{
        background: isUser ? "rgba(255,255,255,0.08)" : "linear-gradient(135deg,#20B2AA,#17c7ba)",
        color: isUser ? "var(--t2)" : "#06201e",
        border: isUser ? "1px solid var(--glass-border)" : "none",
      }}
    >
      {isUser ? "You" : "A"}
    </div>
  );
}

export default function Message({ msg, index, onFeedback }) {
  const isUser = msg.role === "user";
  const html = useMemo(() => {
    if (isUser) return null;
    return renderMd(msg.content);
  }, [msg.content, isUser]);

  return (
    <div className="w-full animate-fadeUp">
      <div className="max-w-3xl mx-auto px-4 py-5 flex gap-4">
        <Avatar who={msg.role} />
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2 mb-1.5">
            <span className="text-[13px] font-semibold" style={{ color: isUser ? "var(--t1)" : "var(--teal-bright)" }}>
              {isUser ? "You" : "Alchemy"}
            </span>
            {msg.grounded && msg.entity && (
              <span
                className="inline-flex items-center gap-1 text-[11px] px-2 py-0.5 rounded-full"
                style={{ background: "rgba(32,178,170,0.12)", color: "var(--teal-bright)", border: "1px solid var(--glass-border)" }}
                title="Answer grounded in the Alchemy atlas for this area"
              >
                <MapPin size={11} /> {msg.entity}
              </span>
            )}
          </div>
          {isUser ? (
            <div className="text-[15px] leading-relaxed whitespace-pre-wrap" style={{ color: "var(--t1)" }}>
              {msg.content}
            </div>
          ) : (
            <div
              className={`md ${msg.streaming && !msg.content ? "" : ""} ${msg.streaming ? "cursor-blink" : ""}`}
              dangerouslySetInnerHTML={{ __html: html }}
            />
          )}
          {!isUser && msg.streaming && !msg.content && (
            <span className="text-[14px]" style={{ color: "var(--t3)" }}>Thinking…</span>
          )}
          {!isUser && !msg.streaming && msg.content && (
            <div className="flex items-center gap-1 mt-2.5">
              {["up", "down"].map((v) => {
                const Icon = v === "up" ? ThumbsUp : ThumbsDown;
                const active = msg.feedback === v;
                return (
                  <button key={v} title={v === "up" ? "Helpful" : "Not helpful"}
                    onClick={() => onFeedback?.(index, v)}
                    className="w-7 h-7 rounded-md flex items-center justify-center transition-colors"
                    style={{ color: active ? (v === "up" ? "var(--teal-bright)" : "#f87171") : "var(--t3)" }}
                    onMouseEnter={(e) => (e.currentTarget.style.background = "rgba(255,255,255,0.06)")}
                    onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}>
                    <Icon size={14} fill={active ? "currentColor" : "none"} />
                  </button>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
