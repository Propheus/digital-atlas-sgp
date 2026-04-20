# rwm-server — Running Services & Restart Guide

**Server:** rwm-server (Azure VM, `de-data-processor.internal.cloudapp.net`)
**Last audited:** 2026-03-29
**Total screen sessions:** 10
**Total listening ports:** 16

---

## Auto-Restart (survives reboot)

| Service | Port | Type | Notes |
|---|---|---|---|
| nginx | 9098 | systemd | NYC atlas reverse proxy at `/var/www/digital-atlas/` |
| event-discovery | 29080 | systemd (gunicorn) | Event Lake Explorer |
| CFA weather monitor | — | cron (hourly) | `cfa-platform/agents/weather_monitor` |
| CFA disruption monitor | — | cron (hourly) | `cfa-platform/agents/disruption_monitor` |
| CFA impact analyzer | — | cron (hourly) | `cfa-platform/agents/impact_analyzer` |
| Event daily collection | — | cron (6am daily) | `event-discovery/run_daily_collection.py` |

---

## Manual Restart Required (screen sessions)

### 1. SGP Digital Atlas
```bash
screen -dmS sgp-atlas bash -c 'cd /home/azureuser/digital-atlas-sgp/sgp-atlas-app/app/dist && python3 -m http.server 18067 --bind 0.0.0.0'
```
- **Port:** 18067
- **URL:** https://sgp-digital-atlas-v2.alchemy-propheus.ai/
- **Serves:** `/home/azureuser/digital-atlas-sgp/sgp-atlas-app/app/dist/`

### 2. NYC Digital Atlas V2
```bash
screen -dmS digital-atlas-v2 bash -c 'cd /home/azureuser/digital-atlas-v2 && python3 -m http.server 20990 --bind 0.0.0.0'
```
- **Port:** 20990
- **URL:** https://digital-atlas-v2.alchemy-propheus.ai/
- **Serves:** `/home/azureuser/digital-atlas-v2/`

### 3. Graph API (RWM Micrograph)
```bash
screen -dmS graphapi bash -c 'cd /home/azureuser/rwm-micrograph && .venv/bin/uvicorn src.api.server:app --host 0.0.0.0 --port 8000'
```
- **Port:** 8000

### 4. Atlas Search
```bash
screen -dmS atlas-search bash -c 'cd /home/azureuser && venv/bin/python3 atlas_search.py'
```
- **Port:** 15087

### 5. DA Insights V2
```bash
screen -dmS da-insights-v2 bash -c 'cd /home/azureuser/da-insights-v2 && python3 server.py'
```
- **Port:** 15034

### 6. Alchemy
```bash
screen -dmS alchemy bash -c 'cd /home/azureuser/propheus && python -m src.api.server'
```
- **Port:** 16060

### 7. RWM Micrograph Reasoning
```bash
screen -dmS reasoning bash -c 'cd /home/azureuser/rwm-micrograph && .venv/bin/python3 reasoning_engine.py'
```
- **Port:** 15035

### 8-10. Category Servers (food_bev, services, retail, health)
```bash
# Need to verify exact commands — check screen logs or process args
screen -dmS food_bev bash -c 'cd /home/azureuser/propheus && python -m src.api.category_server food_bev'
screen -dmS services bash -c 'cd /home/azureuser/propheus && python -m src.api.category_server services'
screen -dmS retail bash -c 'cd /home/azureuser/propheus && python -m src.api.category_server retail'
screen -dmS health bash -c 'cd /home/azureuser/propheus && python -m src.api.category_server health'
```

---

## Other Standalone Processes

| PID | Port | Process | Since | Restart |
|---|---|---|---|---|
| 70807 | 5001 | `venv/bin/python server.py` | Feb 12 | `cd /home/azureuser && venv/bin/python server.py` |
| 1257679 | 12035 | `python3 server.py` | Feb 27 | Unknown path — check `/proc/1257679/cwd` |
| 1233707 | 12302 | `python3 -m uvicorn` | Feb 27 | Unknown — check process |
| 2919405 | 16070 | `python3 app.py` | Mar 13 | Unknown path |

---

## Full Restart Script

Save as `/home/azureuser/restart_all.sh`:

```bash
#!/bin/bash
# Restart all screen sessions after reboot

echo "Starting SGP Digital Atlas..."
screen -dmS sgp-atlas bash -c 'cd /home/azureuser/digital-atlas-sgp/sgp-atlas-app/app/dist && python3 -m http.server 18067 --bind 0.0.0.0'

echo "Starting NYC Digital Atlas V2..."
screen -dmS digital-atlas-v2 bash -c 'cd /home/azureuser/digital-atlas-v2 && python3 -m http.server 20990 --bind 0.0.0.0'

echo "Starting Graph API..."
screen -dmS graphapi bash -c 'cd /home/azureuser/rwm-micrograph && .venv/bin/uvicorn src.api.server:app --host 0.0.0.0 --port 8000'

echo "Starting Atlas Search..."
screen -dmS atlas-search bash -c 'cd /home/azureuser && venv/bin/python3 atlas_search.py'

echo "Starting DA Insights V2..."
screen -dmS da-insights-v2 bash -c 'cd /home/azureuser/da-insights-v2 && python3 server.py'

echo "Starting Alchemy..."
screen -dmS alchemy bash -c 'cd /home/azureuser/propheus && python -m src.api.server'

echo "Starting RWM Reasoning..."
screen -dmS reasoning bash -c 'cd /home/azureuser/rwm-micrograph && .venv/bin/python3 reasoning_engine.py'

echo "Done. Check: screen -ls"
```

---

## Data Locations (DO NOT DELETE)

| Path | Size | What |
|---|---|---|
| `/home/azureuser/digital-atlas-sgp/` | 5.4 GB | SGP atlas project (places, micrographs, models, satellite) |
| `/home/azureuser/digital-atlas-v2/` | ~2 GB | NYC atlas (production) |
| `/home/azureuser/rwm-micrograph/` | — | Micrograph API + reasoning engine |
| `/home/azureuser/propheus/` | — | Alchemy platform |
| `/home/azureuser/da-insights-v2/` | — | DA insights server |
| `/home/azureuser/event-discovery/` | — | Event discovery (systemd) |
| `/home/azureuser/cfa-platform/` | — | CFA monitoring agents (cron) |
| `/var/www/digital-atlas/` | — | NYC atlas static files (nginx) |
