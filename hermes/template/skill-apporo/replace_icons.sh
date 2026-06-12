#!/bin/sh
sleep 5

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
