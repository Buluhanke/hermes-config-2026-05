#!/usr/bin/env python3
"""Verify the gateway HTTP pool fix under 5-station fan-out.

Usage:
    /Users/aimac/.hermes/hermes-agent/venv/bin/python scripts/verify_pool.py

Healthy result:
    pool config: max_conn=50 max_keepalive=10
    timeout: read=10.0 connect=5.0
    5 stations x 10 turns = 50 concurrent cross-host requests
    50/50 ok, 0 errors, avg 0.58s/turn, max 1.70s (first turn = TLS handshake)

If you see errors, timeouts > 5s, or fd growth above 200, the fix
is incomplete — check both:
  1. gateway/platforms/_shared_http_client.py exists and is importable
  2. gateway/platforms/telegram.py has connection_pool_size=50 (not 512)
"""
import asyncio
import sys
import time
from pathlib import Path

# Make the gateway package importable
HERMES_AGENT = Path("/Users/aimac/.hermes/hermes-agent")
sys.path.insert(0, str(HERMES_AGENT))


async def hit(client, host, i):
    t0 = time.monotonic()
    try:
        r = await client.get(f"{host}/", timeout=5.0)
        return host, i, time.monotonic() - t0, r.status_code
    except Exception as e:
        return host, i, time.monotonic() - t0, f"ERR:{type(e).__name__}"


async def main():
    from gateway.platforms._shared_http_client import get_shared_client

    c = get_shared_client()
    pool = c._transport._pool
    print(f"pool config: max_conn={pool._max_connections} "
          f"max_keepalive={pool._max_keepalive_connections} "
          f"keepalive_expiry={pool._keepalive_expiry}")
    print(f"timeout: read={c.timeout.read} connect={c.timeout.connect}")

    # 5 hosts — same shape as the 5-station cross-test that triggered
    # the original incident (Gemini/Doubao/ChatGLM/DeepSeek/ChatGPT).
    # We hit .com / .cn / .org domains for variety; the real test is
    # concurrent cross-host fan-out, not the specific endpoints.
    HOSTS = [
        "https://www.google.com",
        "https://www.apple.com",
        "https://www.microsoft.com",
        "https://github.com",
        "https://en.wikipedia.org",
    ]

    turn_times = []
    total_ok = 0
    total_err = 0
    for turn in range(10):
        t0 = time.monotonic()
        results = await asyncio.gather(
            *[hit(c, h, turn) for h in HOSTS], return_exceptions=True
        )
        ok = sum(1 for r in results if isinstance(r, tuple) and isinstance(r[3], int))
        err = sum(1 for r in results if isinstance(r, tuple) and isinstance(r[3], str))
        total_ok += ok
        total_err += err
        dt = time.monotonic() - t0
        turn_times.append(dt)
        print(f"  turn {turn+1:2d}: {dt:.2f}s | ok={ok} err={err}")

    avg = sum(turn_times) / len(turn_times)
    print(f"\nsummary: {total_ok}/{total_ok + total_err} ok, "
          f"avg turn {avg:.2f}s, max {max(turn_times):.2f}s, "
          f"total {sum(turn_times):.2f}s")

    # Verdict
    if total_err == 0 and avg < 1.0:
        print("\nPASS — pool is healthy under 5-station fan-out")
        return 0
    else:
        print(f"\nFAIL — {total_err} errors or avg {avg:.2f}s > 1s threshold")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
