# Plexis-Mind Chat

A simple, ChatGPT-style chat UI for **Plexis-Mind** — the fine-tuned Gemma-4-12B model
that reasons about Singapore's urban geography, grounded in the Plexis atlas.

Next.js 14 + Tailwind, reusing the Travel-Lens teal "geoagent" theme. Streaming replies,
sample questions, and a Help panel explaining what the model can answer.

## Architecture

```
browser  ──>  /api/chat (Next route, proxy)  ──>  PLEXIS_API /chat  (FastAPI on runpod:8080)
                                                     │
                                                     ├─ base google/gemma-4-12b-it (4-bit) + LoRA adapter
                                                     └─ auto context-injection from the atlas parquet
                                                        (resolve subzone/PA -> compact profile -> 88% mode)
```

The model is weak closed-book and over-abstains, so the server **auto-injects a `Context:`
block** for any named subzone / planning area it detects — running the model in its strong
"reason-in-context" production mode. The browser never sees the injection.

## Run

The inference server runs on `runpod-finetune:8080` (screen session `plexis`, with an
auto-restart supervisor). It only listens on localhost, so tunnel to it:

```bash
ssh -L 8080:localhost:8080 runpod-finetune     # keep this open
```

Then, in this folder:

```bash
npm install
npm run dev                # http://localhost:16090
```

`PLEXIS_API` (in `.env.local`) points the proxy at the model server — default
`http://localhost:8080`. Set it to a public URL if you expose the server directly.

## Model

`paperclip123/plexis-mind-v0-gemma4-12b-lora` on Hugging Face (LoRA adapter on
`google/gemma-4-12b-it`). ~88% on held-out subzones. See `docs/PLEXIS_MIND_MASTER.md`.

## Server ops (runpod)

```bash
# restart
ssh runpod-finetune 'pkill -f serve_plexis; screen -dmS plexis bash -c "bash /root/run_serve.sh > /root/serve.log 2>&1"'
# logs / health
ssh runpod-finetune 'tail -f /root/serve.log'
ssh runpod-finetune 'curl -s localhost:8080/health'
```

Server code: `llm-qa/serve_plexis.py` (+ `atlas_tools.py`, atlas parquets in `/root/atlas`).
