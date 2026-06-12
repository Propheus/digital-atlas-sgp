// record thumbs up/down feedback (proxy to the store service)
export const runtime = "nodejs";
export const dynamic = "force-dynamic";
const STORE = process.env.STORE_API || "http://localhost:8091";

export async function POST(req) {
  const body = await req.text();
  try {
    const r = await fetch(`${STORE}/feedback`, {
      method: "POST", headers: { "Content-Type": "application/json" }, body,
    });
    return new Response(await r.text(), { status: r.status, headers: { "Content-Type": "application/json" } });
  } catch { return Response.json({ ok: false }, { status: 502 }); }
}
