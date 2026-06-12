#!/bin/bash
# Move the Alchemy chat app to port 7780 (a RunPod-exposed port whose CF cache is
# clean/BYPASS, unlike 18080 which Cloudflare poisoned with a 1-year static-page cache).
# Runs detached so ssh drops can't interrupt it.
CHAT_PORT=7780
exec > /root/redeploy.log 2>&1
echo "=== redeploy chat -> :$CHAT_PORT  $(date) ==="

# free 7780 (kill the old training dashboard) and any old chat
pkill -9 -f dashboard_server.py 2>/dev/null
pkill -9 -f run_chat.sh 2>/dev/null
pkill -9 -f "next start" 2>/dev/null
pkill -9 -f next-server 2>/dev/null
for s in $(screen -ls 2>/dev/null | grep -oE "[0-9]+\.(chat|dash[a-z]*)"); do screen -S "$s" -X quit 2>/dev/null; done
fuser -k ${CHAT_PORT}/tcp 18080/tcp 2>/dev/null
sleep 4
echo "after nuke: next=$(pgrep -fc next-server) dash=$(pgrep -fc dashboard_server.py) port=$(ss -ltnp 2>/dev/null | grep -c :${CHAT_PORT})"

# supervisor on the clean port
cat > /root/run_chat.sh <<RC
#!/bin/bash
cd /root/plexis-chat
export PLEXIS_API=http://localhost:8080 STORE_API=http://localhost:8091 NODE_ENV=production
while true; do
  echo "[chat-sup] start \$(date)"
  ./node_modules/.bin/next start -H 0.0.0.0 -p ${CHAT_PORT}
  echo "[chat-sup] exit=\$? \$(date); restart 5s"; sleep 5
done
RC
chmod +x /root/run_chat.sh

cd /root/plexis-chat
setsid bash /root/run_chat.sh > /root/chat.log 2>&1 < /dev/null &
disown
echo "supervisor launched on :$CHAT_PORT"

for i in $(seq 1 45); do
  curl -s -m2 http://localhost:${CHAT_PORT}/ >/dev/null 2>&1 && { echo "UP after ~$((i*2))s"; break; }
  sleep 2
done
echo "listeners=$(ss -ltnp 2>/dev/null | grep -c :${CHAT_PORT})"
echo "--- branding on :$CHAT_PORT ---"
curl -s -m5 http://localhost:${CHAT_PORT}/ | grep -oiE "ALCHEMY|PLEXIS-MIND|Saved conversations" | sort | uniq -c
echo "=== done $(date) ==="
