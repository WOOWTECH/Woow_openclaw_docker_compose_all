#!/bin/sh
# Wait for hermeswebui_init.bash rsync to populate /app/static/index.html
# The init script rsyncs /apptoo/ -> /app/ which overwrites index.html.
# We must wait for that to finish before applying branding.
for i in $(seq 1 30); do
  [ -f /app/static/index.html ] && break
  sleep 2
done
sleep 2  # extra buffer after index.html appears

# 1. Copy icon files from PVC to app static
if [ -f /home/hermeswebui/.hermes/icons/favicon-32.png ]; then
  cp /home/hermeswebui/.hermes/icons/favicon-32.png /app/static/favicon-32.png
  cp /home/hermeswebui/.hermes/icons/favicon-192.png /app/static/favicon-192.png
  cp /home/hermeswebui/.hermes/icons/favicon-512.png /app/static/favicon-512.png
  cp /home/hermeswebui/.hermes/icons/apple-touch-icon.png /app/static/apple-touch-icon.png
  cp /home/hermeswebui/.hermes/icons/favicon.ico /app/static/favicon.ico
  cp /home/hermeswebui/.hermes/icons/favicon.svg /app/static/favicon.svg
  cp /home/hermeswebui/.hermes/icons/favicon-512.svg /app/static/favicon-512.svg
fi

# 2. Replace inline SVGs + login page + hide tabs via Python
python3 /home/hermeswebui/.hermes/apply_branding.py 2>/dev/null

# 3. Fix cron permissions
chmod 666 /opt/data/cron/jobs.json 2>/dev/null
chmod 666 /home/hermeswebui/.hermes/cron/jobs.json 2>/dev/null
