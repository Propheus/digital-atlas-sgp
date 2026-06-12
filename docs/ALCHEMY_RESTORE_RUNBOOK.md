# Alchemy / Plexis-Mind — shutdown & restore runbook

How to shut the GPU box down (stop billing) and bring the whole stack back later.

**Box:** `runpod-finetune` (RTX PRO 4500 Blackwell, 32 GB). **Services:** model `:8080`, store `:8091`,
chat `:7780`. **Public URL:** `https://e4245qvdon7vok-7780.proxy.runpod.net/`.

---

## What is backed up where (so nothing is lost)
| Artifact | Location |
|---|---|
| **Model (v1 adapter)** | HF `paperclip123/plexis-mind-v1-gemma4-12b-lora` |
| **Training data** | HF dataset `paperclip123/plexis-mind-sgp-reasoning-data` |
| **Methods (all scripts + docs)** | HF model repo `methods/` **and** local repo `llm-qa/` + `docs/` |
| **Store DB (15 convos + 7 feedback)** | local `backups/runpod-finetune/plexis_chat.db` (+ `plexis_memory.db`) |
| **Box run scripts** | local `backups/runpod-finetune/run_*.sh`, `redeploy_chat.sh` |
| **Chat app source** | local repo `apps/plexis-chat/` |
| **Atlas parquets** | re-copyable from `azold-test-server:/home/azureuser/da-sgp/v4/` |

→ **Everything box-only is now backed up.** Safe to **Stop** *or* **Terminate** the pod.

---

## Shut down
1. (optional) stop services cleanly:
   `ssh runpod-finetune 'for s in $(screen -ls|grep -oE "[0-9]+\.(plexis|store|chat)"); do screen -S "$s" -X quit; done; pkill -9 -f serve_plexis; pkill -9 -f store_server; pkill -9 -f next-server'`
2. **Stop the pod in the RunPod dashboard** (I can't from ssh). 
   - **Stop** = filesystem preserved (if on a persistent volume) → restore = Scenario A (fast).
   - **Terminate** = filesystem gone → restore = Scenario B (rebuild from HF + repo).

---

## Restore — Scenario A: pod was STOPPED (filesystem intact)
Just restart the three screens:
```bash
ssh runpod-finetune '
  cd /root
  screen -dmS store  bash -c "bash /root/run_store.sh  > /root/store.log  2>&1"
  screen -dmS plexis bash -c "bash /root/run_serve.sh  > /root/serve.log  2>&1"
  screen -dmS chat   bash -c "bash /root/run_chat.sh   > /root/chat.log   2>&1"
'
# wait for model: ssh runpod-finetune 'until curl -s localhost:8080/health>/dev/null; do sleep 3; done; echo UP'
```
Open the public URL (or tunnel `ssh -L 7780:localhost:7780 runpod-finetune`).
**ALWAYS kill old `plexis` screens before relaunch, verify GPU≈2 MiB** (zombie processes OOM the GPU → empty generations).

---

## Restore — Scenario B: fresh / terminated box (rebuild from HF + repo)
```bash
# 0. env (Blackwell sm_120 needs cu128 torch)
pip install --index-url https://download.pytorch.org/whl/cu128 torch
pip install transformers peft bitsandbytes accelerate fastapi "uvicorn[standard]" pandas pyarrow huggingface_hub
export HF_TOKEN=<token from ~/notes/hf-prop-token.txt>

# 1. atlas parquets (from azold) -> /root/atlas
ssh azold-test-server 'cd /home/azureuser/da-sgp/v4 && tar czf - hex/subzone_all_features.parquet hex/hex9_universe.parquet hex/hex8_universe.parquet data/lta_od/hex8_od_matrix.parquet' \
  | ssh runpod-finetune 'mkdir -p /root/atlas && tar xzf - -C /root/atlas'

# 2. model adapter + methods from HF
huggingface-cli download paperclip123/plexis-mind-v1-gemma4-12b-lora --local-dir /root/plexis-mind-v1-lora
#    methods/ contains serve_plexis.py, atlas_tools.py, run_*.sh logic, generators, train_continue.py, docs
#    (or just scp from the local repo: llm-qa/*.py)

# 3. store DB + run scripts (from local backup)
scp backups/runpod-finetune/plexis_chat.db runpod-finetune:/root/plexis_chat.db
scp backups/runpod-finetune/plexis_memory.db runpod-finetune:/root/plexis_memory.db
scp backups/runpod-finetune/run_*.sh backups/runpod-finetune/redeploy_chat.sh runpod-finetune:/root/
scp llm-qa/serve_plexis.py llm-qa/atlas_tools.py llm-qa/store_server.py llm-qa/kb_memory.py runpod-finetune:/root/

# 4. memory-observatory (for kb_memory; optional, memory is off by default)
cd ~/mem && tar czf - memory-observatory/memory memory-observatory/config | ssh runpod-finetune 'mkdir -p /root/memory-observatory && tar xzf - -C /root --strip-components=0'

# 5. node + chat app (from local repo)
ssh runpod-finetune 'cd /opt && curl -fsSL https://nodejs.org/dist/v20.18.0/node-v20.18.0-linux-x64.tar.xz | tar -xJ && ln -sf /opt/node-v20.18.0-linux-x64/bin/{node,npm,npx} /usr/local/bin/'
# ship apps/plexis-chat, then on box: npm install && npm run build

# 6. ensure run_serve.sh uses ADAPTER=/root/plexis-mind-v1-lora, then launch the 3 screens (as Scenario A)
```

---

## Service config reference
- **model** `run_serve.sh`: ADAPTER=/root/plexis-mind-v1-lora, ATLAS=/root/atlas, PORT=8080, supervisor loop, sdpa bf16 base+adapter (~24 GB).
- **store** `run_store.sh`: STORE_DB=/root/plexis_chat.db, PORT=8091, MEMORY_ENABLED=false.
- **chat** `run_chat.sh`: Next.js `next start -p 7780`, PLEXIS_API=localhost:8080, STORE_API=localhost:8091; frees port 7780 on start.
- Public 7780 is uncached (`Cache-Control: no-store` on `/`); other RunPod-exposed ports: 8080, 8888.

Master record: HF `methods/PLEXIS_MIND_MASTER.md` + `docs/` in the repo.
