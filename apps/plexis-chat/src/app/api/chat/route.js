// Proxies the chat request to the Plexis-Mind inference server (runpod:8080)
// and streams the SSE response straight back to the browser.
export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const API = process.env.PLEXIS_API || "http://localhost:8080";

export async function POST(req) {
  let body;
  try {
    body = await req.json();
  } catch {
    return new Response("bad request", { status: 400 });
  }

  let upstream;
  try {
    upstream = await fetch(`${API}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        messages: body.messages,
        max_tokens: body.max_tokens ?? 600,
        temperature: body.temperature ?? 0.55,
      }),
    });
  } catch (e) {
    return sseError(
      `Couldn't reach the model server at ${API}. ` +
        `If you're running locally, open the tunnel: ssh -L 8080:localhost:8080 runpod-finetune`
    );
  }

  if (!upstream.ok || !upstream.body) {
    return sseError(`Model server returned ${upstream.status}.`);
  }

  return new Response(upstream.body, {
    headers: {
      "Content-Type": "text/event-stream; charset=utf-8",
      "Cache-Control": "no-cache, no-transform",
      Connection: "keep-alive",
      "X-Accel-Buffering": "no",
    },
  });
}

function sseError(msg) {
  const enc = new TextEncoder();
  const stream = new ReadableStream({
    start(c) {
      c.enqueue(enc.encode(`data: ${JSON.stringify({ token: "⚠️ " + msg })}\n\n`));
      c.enqueue(enc.encode("data: [DONE]\n\n"));
      c.close();
    },
  });
  return new Response(stream, {
    headers: { "Content-Type": "text/event-stream; charset=utf-8", "Cache-Control": "no-cache" },
  });
}
