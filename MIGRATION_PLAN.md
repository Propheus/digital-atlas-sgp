# Digital Atlas SGP — Migration Plan: rwm-server → atlas-1

## Executive summary

Move all Singapore-specific Digital Atlas assets (~6 GB of data + code + 6 running services) from `rwm-server` to a fresh `atlas-1` VM (Ubuntu 24.04, 16 CPU / 62 GB RAM / 240 GB disk), using **propheusdatalake2** (ADLS Gen2) as the durable transfer medium. NYC atlas (`digital-atlas-v2`) stays on rwm-server and must not be touched.

Expected downtime per service: **~5 minutes cutover** (parallel-run eliminates extended outages).
Total wall-clock timeline: **~4 hours** (bulk data transfer is the long pole; everything else is parallelizable).

---

## What we're moving (footprint summary)

| Source (rwm-server) | Size | Destination (atlas-1) |
|---|---|---|
| `/home/azureuser/digital-atlas-sgp/` | **5.9 GB** | `/home/azureuser/digital-atlas-sgp/` |
| `/home/azureuser/hex-adequacy-app/` | **31 MB** | `/home/azureuser/hex-adequacy-app/` |
| `/var/www/digital-atlas/` | (check) | `/var/www/digital-atlas/` |
| `/etc/nginx/sites-enabled/digital-atlas` | config | `/etc/nginx/sites-enabled/digital-atlas` |

### Breakdown of `digital-atlas-sgp/` (5.9 GB)

| Subfolder | Size | Note |
|---|---|---|
| `data/places_consolidated/` | 441 MB | v2 LLM-classified places (source of truth) |
| `data/new_datasets/` | 395 MB | |
| `data/hex_v10/` | 296 MB | Feature tables + embeddings + models |
| `data/personas/` | 263 MB | |
| `data/results/` | 247 MB | |
| `data/osm/` | 232 MB | |
| `data/business/` | 222 MB | |
| `data/roads/` | 220 MB | |
| `data/land_use/` | 167 MB | |
| `data/buildings/` | 82 MB | |
| `data/housing/` | 77 MB | |
| `data/demographics/` | 72 MB | |
| `data/property/` | 65 MB | |
| `data/buildings_overture/` | 60 MB | |
| `data/transit/` | 40 MB | |
| (other data/*) | ~140 MB | |
| `micrograph_output/` | 650 MB | 12 category micrograph JSONLs |
| `cache/` | 277 MB | Regeneratable but safer to copy |
| `sgp-atlas-app/` | 38 MB | Built frontend |
| `model/` | 29 MB | |
| `scenario_sim/` + `scripts/` + `docs/` + misc | ~5 MB | |
| `merlion/` + `merlion-app/` (NEW) | ~80 MB | incl `node_modules/` |

### Running services to migrate

| Screen | Port | Service | Exposed via |
|---|---|---|---|
| `hex-adequacy` | 16789 | Hex Adequacy Explorer | `sgp-sim.alchemy-propheus.ai` |
| `sgp-atlas` | 18067 | SGP Atlas (static HTTP server) | — |
| `scenario-sim` | 18070 | Scenario Sim API | — |
| `gcn64-engine` | — | Continuous GCN-64 training | — |
| `merlion-api` (new) | 18700 | Real World Engine FastAPI | to be set up |
| `merlion-ui` (new) | 18701 | Real World Engine Next.js | to be set up |
| `da-blr-atlas` | ? | Possibly stale | verify / archive |
| `atlas-search` | ? | Possibly stale | verify / archive |

### Stays on rwm-server (do NOT touch)
- `digital-atlas-v2` (NYC) on port 20990, screen `digital-atlas-v2`, URL `digital-atlas-v2.alchemy-propheus.ai`

---

## Transfer strategy: via propheusdatalake2 (ADLS Gen2)

Using the data lake as transfer medium has 3 benefits:
1. **Durable backup** — the migrated data becomes a 30-day retained snapshot
2. **Fast** — azcopy parallelizes; no SSH bandwidth bottleneck between VMs
3. **Both VMs authorized** — managed-identity-based auth works from both

### Container layout (proposed)

```
propheusdatalake2/
└── migrations/
    └── sgp-atlas-2026-04-14/
        ├── digital-atlas-sgp/       # tarball OR directory sync
        ├── hex-adequacy-app/
        ├── nginx-config/
        └── MANIFEST.md              # what's included + checksums
```

---

## Phased plan

### Phase 0 — Pre-flight (30 min)

- [ ] Confirm `atlas-1` SSH access ✓ (done)
- [ ] Confirm `azcopy login --identity` works on both servers
- [ ] Decide on container/path within `propheusdatalake2` (e.g. `migrations/sgp-atlas-2026-04-14/`)
- [ ] Take inventory of secrets + env vars that need to come along:
  - [ ] `ANTHROPIC_API_KEY` (merlion/.env, Claude Sonnet)
  - [ ] `OPENROUTER_API_KEY` (~/.env or similar, used by micrograph pipeline)
  - [ ] `data.gov.sg API key`
  - [ ] Mapbox public token (for Atlas app)
- [ ] Pick a maintenance window — ideally off-hours in SGP

### Phase 1 — atlas-1 provisioning (30 min)

Run on `atlas-1`:

```bash
# System packages
sudo apt update
sudo apt install -y python3-pip python3-venv nginx screen rsync \
                     build-essential git curl nodejs npm \
                     libspatialindex-dev  # for h3/rtree

# azcopy (if not already present)
which azcopy || {
    curl -sSL https://aka.ms/downloadazcopy-v10-linux | tar -xz
    sudo mv azcopy_linux_amd64_*/azcopy /usr/local/bin/
}

# Python deps (global, same pattern as rwm-server)
sudo pip install --break-system-packages \
    pandas numpy scipy scikit-learn xgboost torch torchvision \
    fastapi 'uvicorn[standard]' pydantic anthropic \
    h3 pyarrow gensim umap-learn networkx \
    matplotlib seaborn geopandas shapely

# Directory prep
mkdir -p /home/azureuser/digital-atlas-sgp
mkdir -p /home/azureuser/hex-adequacy-app
```

### Phase 2 — Upload from rwm-server → ADLS (45–60 min)

Run on `rwm-server`:

```bash
# Authenticate
azcopy login --identity

# Stop rwm-server writers for a clean snapshot (but NOT NYC)
screen -S gcn64-engine -X quit       # continuous training — pause during snapshot
# hex-adequacy / sgp-atlas / scenario-sim can keep running (they're read-mostly)

# Sync digital-atlas-sgp (exclude node_modules + .git to save bandwidth)
azcopy sync /home/azureuser/digital-atlas-sgp/ \
  "https://propheusdatalake2.dfs.core.windows.net/migrations/sgp-atlas-2026-04-14/digital-atlas-sgp/" \
  --recursive \
  --exclude-path="merlion-app/frontend/node_modules;merlion-app/frontend/.next" \
  --exclude-pattern="*.pyc;__pycache__"

# Sync hex-adequacy-app
azcopy sync /home/azureuser/hex-adequacy-app/ \
  "https://propheusdatalake2.dfs.core.windows.net/migrations/sgp-atlas-2026-04-14/hex-adequacy-app/" \
  --recursive

# Back up nginx config
sudo tar czf /tmp/nginx-sgp.tar.gz \
  /etc/nginx/sites-enabled/digital-atlas \
  /etc/nginx/sites-available/digital-atlas 2>/dev/null
azcopy copy /tmp/nginx-sgp.tar.gz \
  "https://propheusdatalake2.dfs.core.windows.net/migrations/sgp-atlas-2026-04-14/nginx-sgp.tar.gz"

# Create MANIFEST with checksums
(
  cd /home/azureuser
  find digital-atlas-sgp hex-adequacy-app -type f ! -path "*/node_modules/*" \
    ! -path "*/__pycache__/*" -exec sha256sum {} \; > /tmp/MANIFEST.sha256
)
azcopy copy /tmp/MANIFEST.sha256 \
  "https://propheusdatalake2.dfs.core.windows.net/migrations/sgp-atlas-2026-04-14/MANIFEST.sha256"
```

Bandwidth estimate: 6 GB @ ~100 MB/s = ~60s upload, but managed-identity throughput varies. Budget 45 min.

### Phase 3 — Download ADLS → atlas-1 (30–45 min)

Run on `atlas-1`:

```bash
azcopy login --identity

azcopy sync \
  "https://propheusdatalake2.dfs.core.windows.net/migrations/sgp-atlas-2026-04-14/digital-atlas-sgp/" \
  /home/azureuser/digital-atlas-sgp/ \
  --recursive

azcopy sync \
  "https://propheusdatalake2.dfs.core.windows.net/migrations/sgp-atlas-2026-04-14/hex-adequacy-app/" \
  /home/azureuser/hex-adequacy-app/ \
  --recursive

azcopy copy \
  "https://propheusdatalake2.dfs.core.windows.net/migrations/sgp-atlas-2026-04-14/nginx-sgp.tar.gz" \
  /tmp/

# Verify checksums
azcopy copy \
  "https://propheusdatalake2.dfs.core.windows.net/migrations/sgp-atlas-2026-04-14/MANIFEST.sha256" \
  /tmp/
cd /home/azureuser && sha256sum -c /tmp/MANIFEST.sha256 | grep -v ": OK$" | head
```

### Phase 4 — Restore services on atlas-1 (45 min)

```bash
# 4a — nginx config
sudo tar xzf /tmp/nginx-sgp.tar.gz -C /
sudo ln -s /etc/nginx/sites-available/digital-atlas /etc/nginx/sites-enabled/digital-atlas
sudo nginx -t && sudo systemctl restart nginx

# 4b — Restore secrets (hand-copy, do NOT commit)
cat > /home/azureuser/digital-atlas-sgp/merlion/.env <<EOF
ANTHROPIC_API_KEY=sk-ant-...
EOF

# 4c — Install frontend npm deps (wasn't synced)
cd /home/azureuser/digital-atlas-sgp/merlion-app/frontend
npm install

# 4d — Start each screen session
cd /home/azureuser

screen -dmS hex-adequacy bash -c "cd hex-adequacy-app && python3 server.py"

screen -dmS sgp-atlas bash -c \
  "cd digital-atlas-sgp/sgp-atlas-app/app/dist && python3 -m http.server 18067 --bind 0.0.0.0"

screen -dmS scenario-sim bash -c \
  "cd digital-atlas-sgp/scenario_sim && python3 -u -m server.app > /tmp/scenario_sim.log 2>&1"

screen -dmS merlion-api bash -c \
  "cd digital-atlas-sgp/merlion-app/backend && uvicorn server:app --host 0.0.0.0 --port 18700"

screen -dmS merlion-ui bash -c \
  "cd digital-atlas-sgp/merlion-app/frontend && npm run build && npm start"

# 4e — Continuous GCN engine (optional — resume if desired)
screen -dmS gcn64-engine bash -c \
  "cd digital-atlas-sgp && python3 gcn64_continuous_engine.py --sleep 30 > /tmp/gcn64_engine.log 2>&1"

# Verify ports
ss -tlnp | grep -E ":(16789|18067|18070|18700|18701|9098)"
```

### Phase 5 — Smoke tests on atlas-1 (15 min)

```bash
# Self-checks (run from atlas-1)
curl -s localhost:16789/ | head -5                         # hex-adequacy
curl -s localhost:18067/ | head -5                         # sgp-atlas static
curl -s localhost:18070/api/health 2>/dev/null || true     # scenario-sim
curl -s localhost:18700/ | python3 -m json.tool            # RWE backend
curl -s localhost:18701/ | head -5                         # RWE UI

# Full RWE pipeline test
curl -s -X POST localhost:18700/api/ask \
  -H "Content-Type: application/json" \
  -d '{"query":"find sites to open Alfamart in singapore"}' \
  | python3 -c "import sys, json; d=json.load(sys.stdin); print(d['chosen']['use_case'], '→', len(d['result']['results']), 'sites')"
```

### Phase 6 — DNS cutover (5 min per subdomain)

Currently points to rwm-server:
- `sgp-sim.alchemy-propheus.ai` → rwm-server:16789

Planned on atlas-1:
- `sgp-sim.alchemy-propheus.ai` → atlas-1:16789 (preserve existing URL)
- `sgp-atlas.alchemy-propheus.ai` → atlas-1:18067 (new, optional)
- `rwe.alchemy-propheus.ai` → atlas-1:18701 (new — Real World Engine UI)
- `rwe-api.alchemy-propheus.ai` → atlas-1:18700 (new — RWE backend)

**Action:** update Azure DNS / Cloudflare records. TTL 300s for fast rollback.

### Phase 7 — Validation (24 h monitoring)

- [ ] Keep both servers running in parallel for 24–48 h
- [ ] Monitor atlas-1 screen logs daily
- [ ] Compare API outputs (sanity: same hex IDs returned)
- [ ] Check nginx access logs for 5xx spikes
- [ ] Update local `CLAUDE.md` to point at atlas-1

### Phase 8 — Decommission (after 48 h)

```bash
# On rwm-server — stop ONLY SGP screens (keep digital-atlas-v2 / NYC)
ssh rwm-server '
  screen -S hex-adequacy -X quit
  screen -S sgp-atlas -X quit
  screen -S scenario-sim -X quit
  screen -S gcn64-engine -X quit
  # DO NOT touch digital-atlas-v2
  screen -ls
'

# Archive digital-atlas-sgp directory (don't delete immediately)
ssh rwm-server 'mv ~/digital-atlas-sgp ~/digital-atlas-sgp.archived.$(date +%Y%m%d)'

# Remove nginx site
ssh rwm-server 'sudo rm /etc/nginx/sites-enabled/digital-atlas && sudo systemctl reload nginx'
```

Keep the ADLS backup for **30 days** minimum before purging.

---

## Risk matrix

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Data corruption during transfer | Low | High | SHA256 MANIFEST verification; azcopy has built-in MD5 |
| Missing Python dep on atlas-1 | Med | Med | Install list above; smoke test each service |
| DNS propagation delay | Med | Low | 300s TTL; run parallel 24h |
| Node.js version mismatch (Next.js build) | Med | Med | Install Node 20 LTS explicitly |
| Mapbox token / API key not migrated | High | Low | Audit all `.env` files upfront (Phase 0) |
| Accidentally touching NYC atlas on rwm-server | Low | High | **Never SSH with wildcard commands**; always grep for `digital-atlas-v2` and skip |
| Continuous GCN engine state loss | Med | Low | It restarts from scratch anyway; archive `gcn64_engine/history.jsonl` |
| User-invisible bugs in new env | Med | Med | 24-48h parallel run; smoke-test all 9 RWE use cases + adequacy UI |

---

## Rollback plan

If atlas-1 validation fails during Phase 7:

1. Revert DNS → rwm-server IPs (TTL 300s → 5 min propagation)
2. rwm-server services are still running in parallel (Phase 2 didn't stop them)
3. No data loss — atlas-1 wasn't authoritative yet
4. Investigate + retry

---

## Post-migration updates

After cutover confirmed stable:

- [ ] Update `CLAUDE.md`: change "rwm-server" references to "atlas-1" throughout
- [ ] Update `CONTEXT.md` deployment section
- [ ] Update `merlion-app/README.md` deploy instructions
- [ ] Commit migration log to repo

---

## Time budget (total ≈ 4 hours, mostly parallel-friendly)

| Phase | Duration | Can run in parallel? |
|---|---|---|
| 0 pre-flight | 30 min | — |
| 1 atlas-1 provision | 30 min | with phase 2 |
| 2 upload to ADLS | 45 min | — |
| 3 download to atlas-1 | 30 min | — |
| 4 restore services | 45 min | — |
| 5 smoke tests | 15 min | — |
| 6 DNS cutover | 5 min per subdomain | — |
| 7 parallel validation | 24–48 h | passive |
| 8 decommission | 15 min | after phase 7 |

---

## Open questions (please confirm before executing)

1. **atlas-1 has `azcopy login --identity` pre-authorized for `propheusdatalake2`?** (I assume yes since you mentioned both servers have access.)
2. **Which container within propheusdatalake2** should migrations land in? Default proposal: create `migrations/` container.
3. **Do we migrate the two stale-looking screens** (`da-blr-atlas`, `atlas-search`) or leave them on rwm-server to die?
4. **Should I also move the continuous `gcn64-engine` training history**, or reset it on atlas-1?
5. **Subdomain scheme for RWE UI**: `rwe.alchemy-propheus.ai` ok? Or prefer different naming?
6. **Any scheduled maintenance window?** Cutover takes ~5 min per service — can we do it now?
