"use client";
// Thin client over the store proxy routes. Anonymous per-browser client id.

export function clientId() {
  if (typeof window === "undefined") return "default";
  let id = localStorage.getItem("plexis_client");
  if (!id) { id = "c_" + Math.random().toString(36).slice(2, 12); localStorage.setItem("plexis_client", id); }
  return id;
}

export async function listConversations() {
  try {
    const r = await fetch(`/api/conversations?client=${clientId()}`, { cache: "no-store" });
    return r.ok ? await r.json() : [];
  } catch { return []; }
}

export async function loadConversation(id) {
  try {
    const r = await fetch(`/api/conversations/${id}`, { cache: "no-store" });
    return r.ok ? await r.json() : null;
  } catch { return null; }
}

export async function saveConversation({ id, title, messages }) {
  // strip transient flags; keep what the store expects
  const clean = messages
    .filter((m) => m.content && !m.streaming)
    .map((m) => ({ role: m.role, content: m.content, entity: m.entity || null, grounded: !!m.grounded }));
  try {
    const r = await fetch(`/api/conversations`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id, client: clientId(), title, messages: clean }),
    });
    return r.ok ? await r.json() : null;
  } catch { return null; }
}

export async function deleteConversation(id) {
  try { await fetch(`/api/conversations/${id}`, { method: "DELETE" }); } catch {}
}

export async function sendFeedback(fb) {
  try {
    await fetch(`/api/feedback`, {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(fb),
    });
  } catch {}
}
