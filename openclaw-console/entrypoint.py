#!/usr/bin/env python3
"""
Entrypoint: runs Flask (management UI) + ttyd (terminal) side by side.
"""
import os
import signal
import subprocess
import sys

TUI_PASSWORD = os.environ.get("TUI_PASSWORD", "changeme")
NAMESPACE = os.environ.get("NAMESPACE", "openclaw-tenant-1")


def main():
    # ttyd: web terminal that kubectl-execs into the gateway container
    ttyd_proc = subprocess.Popen([
        "ttyd", "-p", "7681",
        "-c", f"admin:{TUI_PASSWORD}",
        "-W", "/app/connect.sh",
    ])

    # Flask: management web UI (must run from /app so templates/ is found)
    flask_proc = subprocess.Popen(
        [sys.executable, "/app/app.py"],
        cwd="/app",
    )

    def shutdown(sig, frame):
        ttyd_proc.terminate()
        flask_proc.terminate()
        sys.exit(0)

    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)

    # Wait for either process to exit, then stop both
    pid, status = os.waitpid(-1, 0)
    ttyd_proc.terminate()
    flask_proc.terminate()
    sys.exit(1)


if __name__ == "__main__":
    main()
