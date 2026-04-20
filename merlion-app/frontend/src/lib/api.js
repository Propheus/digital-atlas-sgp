const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "";

async function jsonFetch(path, opts = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    ...opts,
    headers: { "Content-Type": "application/json", ...(opts.headers || {}) },
  });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json();
}

export const api = {
  health: () => jsonFetch("/"),
  useCases: () => jsonFetch("/api/use_cases"),
  audit: () => jsonFetch("/api/audit"),
  ask: (query, top_n = 3) =>
    jsonFetch("/api/ask", { method: "POST", body: JSON.stringify({ query, top_n }) }),
  run: (use_case, params = {}) =>
    jsonFetch("/api/run", { method: "POST", body: JSON.stringify({ use_case, params }) }),
};
