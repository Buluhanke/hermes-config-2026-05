#!/usr/bin/env python3
"""
Dashboard / Web UI health checker.
Verifies both the Vite dev server (5173) AND the dashboard backend (9119).
Outputs one-line status — suitable for cron or health monitoring.

Usage:
    python3 check_dashboard.py

Exit codes:
    0  — both processes healthy
    1  — one or both are down (details printed to stdout)
"""
import subprocess, sys, time

VITE_PORT  = 5173
BACKEND_PORT = 9119
VITE_DIR  = "/Users/mac/.hermes/hermes-agent/web"
BACKEND   = "/Users/mac/.hermes/hermes-agent/venv/bin/hermes"

def curl(port, path="/"):
    r = subprocess.run(
        ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
         f"http://localhost:{port}{path}"],
        capture_output=True, text=True, timeout=5
    )
    return r.stdout.strip()

def is_vite_running():
    """Check if a Vite dev server process is alive (by checking its node_modules link exists + port responds)."""
    r = subprocess.run(["lsof", "-i", f":{VITE_PORT}"], capture_output=True, text=True)
    return bool(r.stdout.strip())

def is_backend_running():
    r = subprocess.run(["lsof", "-i", f":{BACKEND_PORT}"], capture_output=True, text=True)
    return bool(r.stdout.strip())

def main():
    vite_ok  = curl(VITE_PORT)     == "200"
    back_ok  = curl(BACKEND_PORT)  == "200"
    vite_proc = is_vite_running()
    back_proc = is_backend_running()

    print(f"Vite dev server (:{VITE_PORT}):  {'UP' if vite_ok  else 'DOWN'}")
    print(f"Dashboard backend (:{BACKEND_PORT}): {'UP' if back_ok else 'DOWN'}")

    if not vite_ok:
        print()
        print("FIX — start Vite dev server:")
        print(f"  cd {VITE_DIR} && npm run dev -- --host  &")
        print(f"  # then verify: curl http://localhost:{VITE_PORT}/sessions")

    if not back_ok:
        print()
        print("FIX — start dashboard backend:")
        print(f"  {BACKEND} dashboard --host 127.0.0.1 --port {BACKEND_PORT}")
        print(f"  # then verify: curl http://localhost:{BACKEND_PORT}/")

    if vite_ok and back_ok:
        print("OK — both processes healthy")
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
