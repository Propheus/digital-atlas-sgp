// load + delete a single conversation (proxy to the store service)
export const runtime = "nodejs";
export const dynamic = "force-dynamic";
const STORE = process.env.STORE_API || "http://localhost:8091";

export async function GET(_req, { params }) {
  try {
    const r = await fetch(`${STORE}/conversations/${params.id}`, { cache: "no-store" });
    return new Response(await r.text(), { status: r.status, headers: { "Content-Type": "application/json" } });
  } catch { return Response.json({ error: "store_unreachable" }, { status: 502 }); }
}

export async function DELETE(_req, { params }) {
  try {
    const r = await fetch(`${STORE}/conversations/${params.id}`, { method: "DELETE" });
    return new Response(await r.text(), { status: r.status, headers: { "Content-Type": "application/json" } });
  } catch { return Response.json({ error: "store_unreachable" }, { status: 502 }); }
}
