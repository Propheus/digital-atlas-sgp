// list + save conversations (proxy to the store service)
export const runtime = "nodejs";
export const dynamic = "force-dynamic";
const STORE = process.env.STORE_API || "http://localhost:8091";

export async function GET(req) {
  const client = new URL(req.url).searchParams.get("client") || "default";
  try {
    const r = await fetch(`${STORE}/conversations?client=${encodeURIComponent(client)}`, { cache: "no-store" });
    return new Response(await r.text(), { status: r.status, headers: { "Content-Type": "application/json" } });
  } catch { return Response.json([]); }
}

export async function POST(req) {
  const body = await req.text();
  try {
    const r = await fetch(`${STORE}/conversations`, {
      method: "POST", headers: { "Content-Type": "application/json" }, body,
    });
    return new Response(await r.text(), { status: r.status, headers: { "Content-Type": "application/json" } });
  } catch { return Response.json({ error: "store_unreachable" }, { status: 502 }); }
}
