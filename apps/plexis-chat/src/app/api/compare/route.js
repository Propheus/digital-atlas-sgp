// Streams a side-by-side comparison: Alchemy (fine-tuned) vs raw Gemma.
// Proxies the SSE from the model server's /compare endpoint.
export const runtime = "nodejs";
export const dynamic = "force-dynamic";
const API = process.env.PLEXIS_API || "http://localhost:8080";

export async function POST(req) {
  let body;
  try { body = await req.json(); } catch { return new Response("bad request", { status: 400 }); }
  let upstream;
  try {
    upstream = await fetch(`${API}/compare`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ messages: body.messages, max_tokens: body.max_tokens ?? 400, temperature: body.temperature ?? 0.55 }),
    });
  } catch {
    return sseErr(`Couldn't reach the model server at ${API}.`);
  }
  if (!upstream.ok || !upstream.body) return sseErr(`Model server returned ${upstream.status}.`);
  return new Response(upstream.body, {
    headers: {
      "Content-Type": "text/event-stream; charset=utf-8",
      "Cache-Control": "no-cache, no-transform",
      Connection: "keep-alive",
      "X-Accel-Buffering": "no",
    },
  });
}

function sseErr(msg) {
  const enc = new TextEncoder();
  const s = new ReadableStream({
    start(c) {
      c.enqueue(enc.encode(`data: ${JSON.stringify({ model: "alchemy", token: "⚠️ " + msg })}\n\n`));
      c.enqueue(enc.encode("data: [DONE]\n\n"));
      c.close();
    },
  });
  return new Response(s, { headers: { "Content-Type": "text/event-stream; charset=utf-8", "Cache-Control": "no-cache" } });
}
