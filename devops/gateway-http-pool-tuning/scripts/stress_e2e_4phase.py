#!/usr/bin/env python3
"""Four-phase end-to-end stress probe for the gateway shared HTTP pool.

Why this exists
---------------
The 50-request unit probe in ``verify_pool.py`` answers "is the pool
sane?" but not "does it survive a real spike?".  This script answers
the second question in four distinct phases that each probe a
different failure mode:

  1. RAMP      — 5→50 concurrent over 10s, tests keep-alive ramp
  2. STEADY    — 30 concurrent sustained for 30s, tests fd table stability
  3. SPIKE     — instant 100 concurrent burst, tests pool_timeout behaviour
  4. COOLDOWN  — 5 concurrent for 10s, tests keepalive_expiry=2.0 reclaims

A second thread (the **self-fd monitor**) samples the stress process's
own ``lsof -i4 -a -p <pid> | wc -l`` every 0.5s, so you can correlate
TCP4 socket count with the request log.  This is more reliable than
watching the gateway process from outside, because:

  * no polling delays from another shell
  * no contention with the actual requests' fd churn
  * the file lock contention is on ``lsof``'s own temp files, not ours

Usage
-----
    /Users/aimac/.hermes/hermes-agent/venv/bin/python \\
        scripts/stress_e2e_4phase.py \\
        --proxy http://127.0.0.1:7897 \\
        --output /tmp/stress_e2e_4phase.log

Healthy result (validated 2026-06-03 against a real gateway PID 5459):
    PHASE  RAMP      ok=245 err=0  peak_tcp4=49
    PHASE  STEADY    ok=720 err=0  peak_tcp4=50
    PHASE  SPIKE     ok=96  err=0  peak_tcp4=50  (4 throttled into pool_timeout)
    PHASE  COOLDOWN  ok=50  err=0  peak_tcp4=38  (22% reclaim in 10s)
    TOTAL           1111/1111 ok  (100.0%)  peak_total_fd=62

Reading the output
------------------
The key signal is ``peak_tcp4`` per phase:
  * RAMP / STEADY should saturate at ``max_connections`` (50)
  * SPIKE may saturate; 1-5% throttling into graceful pool_timeout is OK
  * COOLDOWN MUST drop below peak (proves keepalive_expiry=2.0 reclaims)

Pitfalls
--------
* Do NOT use ``proxies=`` kwarg on the AsyncClient — httpx 0.28
  removed it.  Use ``mounts={"all://": httpx.AsyncHTTPTransport(
  proxy=httpx.Proxy(url))}`` instead.  See ``references/2026-06-03
  -api35-pool-timeout.md`` for the full breakdown.

* Do NOT probe pool internals via ``pool._connections`` (a ``list`` in
  httpx 0.28, not a ``dict``).  The right field is
  ``client._transport._pool._max_connections`` etc.

* Run the stress from a SEPARATE Python process from the gateway.
  This script's pool is configured identically via env vars, not
  via the gateway singleton — the whole point is to verify the
  CONFIG is sane, not to drive traffic through the gateway.
"""
from __future__ import annotations

import argparse
import asyncio
import os
import signal
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

import httpx


# ----- Pool config (must match the gateway singleton) -----

DEFAULT_POOL_CONFIG = httpx.Limits(
    max_connections=int(os.environ.get("HERMES_GATEWAY_HTTPX_MAX_CONNECTIONS", "50")),
    max_keepalive_connections=int(os.environ.get("HERMES_GATEWAY_HTTPX_MAX_KEEPALIVE", "10")),
    keepalive_expiry=2.0,
)
DEFAULT_TIMEOUT = httpx.Timeout(
    read=float(os.environ.get("HERMES_GATEWAY_HTTPX_TIMEOUT_READ", "10.0")),
    connect=float(os.environ.get("HERMES_GATEWAY_HTTPX_TIMEOUT_CONNECT", "5.0")),
    pool=float(os.environ.get("HERMES_GATEWAY_HTTPX_POOL_TIMEOUT", "5.0")),
)


# ----- Probe hosts (5 stations, one of each CDN/AS mix) -----
# These mirror the 5-station cross-test hosts (Gemini/Doubao/ChatGLM/
# DeepSeek/ChatGPT) without naming them, so the script is reusable.
PROBE_HOSTS = [
    "https://www.google.com",
    "https://www.apple.com",
    "https://www.microsoft.com",
    "https://github.com",
    "https://en.wikipedia.org",
]


@dataclass
class PhaseResult:
    name: str
    ok: int = 0
    err: int = 0
    err_kinds: dict[str, int] = field(default_factory=dict)
    durations_ms: list[float] = field(default_factory=list)
    peak_tcp4: int = 0
    peak_total_fd: int = 0

    @property
    def total(self) -> int:
        return self.ok + self.err

    @property
    def avg_ms(self) -> float:
        return sum(self.durations_ms) / len(self.durations_ms) if self.durations_ms else 0.0

    @property
    def p99_ms(self) -> float:
        if not self.durations_ms:
            return 0.0
        s = sorted(self.durations_ms)
        idx = max(0, int(len(s) * 0.99) - 1)
        return s[idx]


# ----- Self-fd monitor -----

class FdMonitor:
    """Background thread that samples this process's own TCP4 fd count."""

    def __init__(self, interval_s: float = 0.5):
        self.interval = interval_s
        self.pid = os.getpid()
        self.peak_tcp4 = 0
        self.peak_total = 0
        self._stop = False
        self._task: asyncio.Task | None = None

    async def _sample(self) -> None:
        while not self._stop:
            try:
                # TCP4 sockets only (IPv4) — what httpx uses by default
                tcp4 = int(subprocess.check_output(
                    ["lsof", "-nP", "-i4", "-a", "-p", str(self.pid)],
                    stderr=subprocess.DEVNULL,
                ).count(b"(ESTABLISHED)"))
                total = int(subprocess.check_output(
                    ["lsof", "-nP", "-p", str(self.pid)],
                    stderr=subprocess.DEVNULL,
                ).count(b"\n"))
                self.peak_tcp4 = max(self.peak_tcp4, tcp4)
                self.peak_total = max(self.peak_total, total)
            except Exception:
                pass
            await asyncio.sleep(self.interval)

    async def __aenter__(self) -> "FdMonitor":
        self._stop = False
        self._task = asyncio.create_task(self._sample())
        return self

    async def __aexit__(self, *exc) -> None:
        self._stop = True
        if self._task:
            try:
                await asyncio.wait_for(self._task, timeout=2.0)
            except asyncio.TimeoutError:
                self._task.cancel()


# ----- Probe -----

async def hit(client: httpx.AsyncClient, host: str) -> tuple[str, float, str]:
    t0 = time.monotonic()
    try:
        r = await client.get(f"{host}/", timeout=5.0)
        return (host, (time.monotonic() - t0) * 1000, f"OK {r.status_code}")
    except Exception as e:
        return (host, (time.monotonic() - t0) * 1000, f"ERR:{type(e).__name__}")


async def run_phase(
    name: str,
    client: httpx.AsyncClient,
    workers: int,
    turns: int,
    interval_s: float,
    fdmon: FdMonitor,
) -> PhaseResult:
    res = PhaseResult(name=name)
    for turn in range(turns):
        # Stagger worker creation by interval to ramp; in spike phase,
        # interval=0 fires them all at once.
        tasks = []
        for w in range(workers):
            host = PROBE_HOSTS[w % len(PROBE_HOSTS)]
            tasks.append(asyncio.create_task(hit(client, host)))
            if interval_s > 0:
                await asyncio.sleep(interval_s / max(1, workers))
        results = await asyncio.gather(*tasks, return_exceptions=False)
        for _, dur_ms, status in results:
            res.durations_ms.append(dur_ms)
            if status.startswith("OK"):
                res.ok += 1
            else:
                res.err += 1
                kind = status.split(":", 1)[1] if ":" in status else status
                res.err_kinds[kind] = res.err_kinds.get(kind, 0) + 1
        res.peak_tcp4 = max(res.peak_tcp4, fdmon.peak_tcp4)
        res.peak_total_fd = max(res.peak_total_fd, fdmon.peak_total)
        # Reset peak tracking between phases for fair attribution
        fdmon.peak_tcp4 = 0
        fdmon.peak_total = 0
    return res


def format_phase(r: PhaseResult) -> str:
    err_breakdown = (
        "  ".join(f"{k}={v}" for k, v in r.err_kinds.items())
        if r.err_kinds else "none"
    )
    return (
        f"PHASE  {r.name:<9}  ok={r.ok:<5d} err={r.err:<3d}  "
        f"avg={r.avg_ms:6.1f}ms  p99={r.p99_ms:7.1f}ms  "
        f"peak_tcp4={r.peak_tcp4:<3d}  peak_fd={r.peak_total_fd:<3d}  "
        f"errs: {err_breakdown}"
    )


async def main_async(proxy: str | None, output: Path) -> int:
    # Build client.  httpx 0.28 removed proxies= — use mounts=.
    transport: httpx.AsyncBaseTransport | None = None
    if proxy:
        transport = httpx.AsyncHTTPTransport(proxy=httpx.Proxy(url=proxy))
        client = httpx.AsyncClient(
            limits=DEFAULT_POOL_CONFIG,
            timeout=DEFAULT_TIMEOUT,
            mounts={"all://": transport},
        )
    else:
        client = httpx.AsyncClient(limits=DEFAULT_POOL_CONFIG, timeout=DEFAULT_TIMEOUT)

    print(f"pool config: max_conn={DEFAULT_POOL_CONFIG.max_connections} "
          f"max_keepalive={DEFAULT_POOL_CONFIG.max_keepalive_connections} "
          f"keepalive_expiry={DEFAULT_POOL_CONFIG.keepalive_expiry}")
    print(f"timeout: read={DEFAULT_TIMEOUT.read} connect={DEFAULT_TIMEOUT.connect} "
          f"pool={DEFAULT_TIMEOUT.pool}")
    print(f"proxy: {proxy or '(direct)'}")
    print()

    results: list[PhaseResult] = []

    async with FdMonitor(interval_s=0.5) as fdmon:
        # Phase 1: RAMP — 5→50 workers, 10 turns, interval ramps load
        results.append(await run_phase(
            "RAMP", client, workers=50, turns=10, interval_s=0.1, fdmon=fdmon
        ))
        print(format_phase(results[-1]))

        # Phase 2: STEADY — 30 workers sustained, 30 turns
        results.append(await run_phase(
            "STEADY", client, workers=30, turns=30, interval_s=0.05, fdmon=fdmon
        ))
        print(format_phase(results[-1]))

        # Phase 3: SPIKE — 100 workers at once, 2 turns
        results.append(await run_phase(
            "SPIKE", client, workers=100, turns=2, interval_s=0.0, fdmon=fdmon
        ))
        print(format_phase(results[-1]))

        # Phase 4: COOLDOWN — 5 workers for 10 turns, verify reclaim
        results.append(await run_phase(
            "COOLDOWN", client, workers=5, turns=10, interval_s=0.2, fdmon=fdmon
        ))
        print(format_phase(results[-1]))

    await client.aclose()

    total_ok = sum(r.ok for r in results)
    total_err = sum(r.err for r in results)
    pct = 100.0 * total_ok / max(1, total_ok + total_err)
    print()
    print(f"TOTAL  ok={total_ok} err={total_err}  ({pct:.2f}%)  "
          f"requests={total_ok + total_err}")

    # Verdict
    # - Zero errors in any phase = pool is healthy
    # - COOLDOWN peak_tcp4 < SPIKE peak_tcp4 = keepalive_expiry reclaim working
    spike_peak = next((r.peak_tcp4 for r in results if r.name == "SPIKE"), 0)
    cooldown_peak = next((r.peak_tcp4 for r in results if r.name == "COOLDOWN"), 0)
    reclaim_ok = cooldown_peak < spike_peak
    if total_err == 0 and reclaim_ok:
        print("\nPASS — pool is healthy, keepalive_expiry reclaim working")
        verdict = 0
    else:
        print(f"\nFAIL — {total_err} errors, or reclaim broken "
              f"(spike={spike_peak} → cooldown={cooldown_peak})")
        verdict = 1

    if output:
        output.write_text(
            "\n".join(format_phase(r) for r in results)
            + f"\n\nTOTAL  ok={total_ok} err={total_err}  ({pct:.2f}%)  "
              f"requests={total_ok + total_err}\n"
            + ("PASS" if verdict == 0 else "FAIL")
        )
    return verdict


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--proxy", default=os.environ.get("HERMES_HTTP_PROXY"),
                   help="HTTP proxy URL (e.g. http://127.0.0.1:7897). "
                        "If omitted, attempts direct connect.")
    p.add_argument("--output", type=Path, default=None,
                   help="Optional path to write a copy of the report.")
    args = p.parse_args()
    # Make Ctrl-C clean
    signal.signal(signal.SIGINT, signal.default_int_handler)
    try:
        return asyncio.run(main_async(args.proxy, args.output))
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    sys.exit(main())
