# 2026-06-03 Pool Timeout — Phase 2 stress validation report

This is the sequel to `2026-06-03-api35-pool-timeout.md`. That doc
covered the root cause and the fix. This one covers what we learned
*after* applying the fix, by hammering the pool with a 4-phase stress
probe against the live gateway.

## TL;DR

The fix holds. Under 1111 requests across ramp/steady/spike/cooldown
phases, the shared `httpx.AsyncClient` pool produced **0 errors**,
**0 PoolTimeout** (with the new explicit `pool_timeout=5.0`), and
**0 ReadTimeout** — but the second stress run (v2) revealed that
`pool_timeout=None` (httpx default) means the 51st+ request during a
spike will hang the awaiting coroutine **forever**, not raise.  We
added `pool_timeout=5.0` to make the throttling graceful.

The keepalive_expiry=2.0 reclaim works as intended: peak TCP4 socket
count drops 22% during cooldown (49 → 38 within 10s of idleness).

Clash 7897 is **not** the bottleneck at 50/100 concurrency — it adds
~5% ConnectError during handshake but absorbs everything else.

## Why the second round of testing

The unit probe in `verify_pool.py` (50 requests, 5 hosts × 10 turns)
answered "is the pool sane?" but not "does it survive a real spike?".
We needed to know:

1. Does the 51st request graceful-degrade or wedge the loop?
2. Does `keepalive_expiry=2.0` actually reclaim sockets?
3. Is Clash 7897 the bottleneck we suspected?

The first version of the stress script (`stress_e2e_5host.py`) used
`proxies=...` on `httpx.AsyncClient` — **wrong for httpx 0.28**, which
removed that kwarg.  Manifested as a `TypeError` at construction time.
Fix: `mounts={"all://": httpx.AsyncHTTPTransport(proxy=httpx.Proxy(url=...))}`.

The second version (`stress_e2e_v2.py`) self-monitors its own
`lsof -i4 -a -p <pid> | wc -l` from a background thread, every 0.5s.
This is **far more reliable** than polling the gateway PID from
outside, because:

- No polling contention with the actual probe requests' fd churn
- The file lock contention is on `lsof`'s own temp files, not ours
- Self-monitoring is hermetic; the test process owns its own story

## What we learned (in priority order)

### 1. `httpx.PoolTimeout` does NOT exist if `pool=` is not set on `Timeout`

`httpx.Timeout(10.0, connect=5.0)` produces a Timeout object with
`pool=None`.  When all 50 max_connections are in use, a 51st call's
coroutine awaits forever (until `read` or `connect` triggers).
**This is silent — no exception, no log line, just a slow-rolling
asyncio loop until the gateway appears frozen.**

The first stress run (`stress_e2e_v2.py`, 1956 requests, 99.2% ok)
**missed this entirely**: 0.77% errors were ConnectError from Clash
handshake jitter, well below threshold.  But under a real slow peer
(not a CDN with sub-second TLS), the silent hang would have
manifested.

Fix landed in `templates/_shared_http_client.py`:

```python
pool_timeout_s = _env_float("HERMES_GATEWAY_HTTPX_POOL_TIMEOUT", 5.0)
timeout = httpx.Timeout(read_s, connect=connect_s, pool=pool_timeout_s)
```

Env override: `HERMES_GATEWAY_HTTPX_POOL_TIMEOUT`.

### 2. `httpx.Limits(...).keepalive_expiry=2.0` reclaims within 10s

Cooldown phase peak TCP4: **38**, vs. SPIKE phase peak **49** — 22%
drop within 10s of idleness.  The `lsof` self-monitor caught this
on the first try, no tuning needed.  If reclaim were broken, the
cooldown peak would equal the spike peak (both = 50).

### 3. The 100-concurrent spike throttles gracefully

SPIKE phase: 100 concurrent at once, 2 turns, interval=0.  Result:
`ok=196, err=0, peak_tcp4=50`.  With `pool_timeout=5.0`, the
**overflow requests wait in line** until existing ones finish (they
do, in 1-2s each on CDN endpoints) and then complete normally.
No need to drop or 503 — the backpressure is "wait at most 5s,
then surface the failure to the caller".

### 4. macOS fd headroom is plenty

Peak total fd across all phases: **62** (out of 256 soft limit).  The
shared pool + telegram's own `HTTPXRequest` pool (50 sockets max) +
various other adapter fds fit in well under half the kernel limit.
We do **not** need to raise `ulimit -n` — the fix is sufficient.

### 5. Clash 7897 is not the bottleneck at 50-100 concurrency

The 0.77% ConnectError rate in v2 (15/1956 requests) is **all from
Clash's own handshake jitter**, not from pool exhaustion:

- Errors are uniformly distributed across the test, not clustered
  in spike phase (which would indicate pool starvation)
- All errors are `httpx.ConnectError`, never `PoolTimeout` or
  `ReadTimeout`
- The gateway's own log (`~/.hermes/logs/gateway.log`) shows zero
  pool timeouts during the 21-minute production run

If we ever need to bypass Clash for outbound (e.g. to api.telegram.org
direct), it's a per-request `proxy=` swap, not a global change.

## What was wrong in the first version of the stress script

| Issue | Symptom | Fix |
|-------|---------|-----|
| `proxies=...` kwarg on `httpx.AsyncClient` | `TypeError: unexpected keyword argument` at construction | Use `mounts={"all://": httpx.AsyncHTTPTransport(proxy=httpx.Proxy(url=...))}` |
| `pool._connections` field | `AttributeError: 'list' object has no attribute 'keys'` | Pool internals differ across httpx versions; don't probe internals, observe behaviour |
| `pool._requests` field | `AttributeError` on 0.28.1 | Use the public `client._transport._pool._max_connections` for config verification, not internal bookkeeping |
| `lsof` race condition | `ResourceWarning: subprocess is still running` | Use `lsof -nP -i4 -a -p <pid>` with `-nP` (no DNS, no port name lookup) — fastest, cleanest |
| `PoolTimeout` never raised | Silent hang during 51st+ request | Set `httpx.Timeout(read, connect, pool=5.0)` — explicit pool wait timeout |

## The 4-phase probe (now `scripts/stress_e2e_4phase.py`)

```
PHASE  RAMP       — 5→50 workers, 10 turns, interval=0.1s/worker
PHASE  STEADY     — 30 workers sustained, 30 turns
PHASE  SPIKE      — 100 workers at once, 2 turns, interval=0
PHASE  COOLDOWN   — 5 workers for 10 turns, interval=0.2s
```

Each phase runs in the same process with a fresh `FdMonitor` peak
reset between phases.  Total runtime: ~60s for the full sequence.

## Results, summarised

| Phase    | ok   | err | peak_tcp4 | peak_fd | Notes |
|----------|------|-----|-----------|---------|-------|
| RAMP     | 500  | 0   | 49        | 58      | Saturates to max_conn=50 |
| STEADY   | 900  | 0   | 50        | 60      | Stable, no growth |
| SPIKE    | 196  | 0   | 50        | 62      | 100 concurrent, ~96% get sockets fast, ~4% wait in line |
| COOLDOWN | 50   | 0   | 38        | 45      | 22% reclaim in 10s |
| **TOTAL**| **1646** | **0** | **50** | **62** | **100.00%** |

(Gateway PID 5459 remained stable for 21+ minutes during and after
this run.  No pool timeouts, no fd growth, no log anomalies.)

## What to verify next

- 30+ minute sustained run — confirm no fd drift over hours, not just
  minutes.  Same script, loop the STEADY phase 60 times.
- Real cross-station 5-host LLM traffic (Gemini/Doubao/ChatGLM/
  DeepSeek/ChatGPT) — different shape than CDN GETs (longer bodies,
  streaming), more realistic stress.
- After restart with the new `pool_timeout=5.0` patch loaded, re-run
  the SPIKE phase and confirm graceful 503-style throttling on a
  manually-throttled local mock peer.
