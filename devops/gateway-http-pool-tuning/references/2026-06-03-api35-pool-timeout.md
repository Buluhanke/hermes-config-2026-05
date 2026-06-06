# 2026-06-03 API #35 Pool Timeout — full incident report

## Symptoms

Hermes gateway on Mac mini M4 24GB, running ~18.5 hours, suddenly stopped
responding to telegram. Log tail:

```
2026-06-03 15:14:xx WARNING  [Telegram] Network error on send (attempt 1/3), retrying in 1s: Pool timeout
2026-06-03 15:14:xx WARNING  [Telegram] Network error on send (attempt 2/3), retrying in 1s: Pool timeout
2026-06-03 15:14:xx ERROR    [Telegram] Pool timeout: All connections in the connection pool are occupied.
                              Request was *not* sent to Telegram. Consider adjusting the connection
                              pool size or the pool timeout.
```

5-station cross-test (Gemini/Doubao/ChatGLM/DeepSeek/ChatGPT/Grok) had
been running fan-out for ~2 hours before the stall. API call #35 was
the last successful one.

## Root cause (two layers, both present)

### Layer 1: per-call `async with httpx.AsyncClient(...)` thrash

`tools/send_message_tool.py` had 4 call sites and platform adapters had
more — all using the pattern:

```python
async with httpx.AsyncClient(timeout=30.0) as client:
    resp = await client.post(url, json=payload)
```

Every invocation built a brand-new `ConnectionPool`, opened fresh TLS to
the same Telegram/Feishu/QQBot host, then tore the pool down on
`__aexit__` — returning sockets to the kernel while the peer was still
draining CLOSE_WAIT (Cloudflare Warp + macOS).

Under 5-station fan-out, the bot would ramp ~35+ concurrent
`send_message` tool calls per turn. Each one re-handshakes Telegram's
TLS, and httpx's default unbounded-retry behaviour compounds the storm.

### Layer 2: oversized python-telegram-bot HTTPXRequest pool (the actual killer)

`gateway/platforms/telegram.py` had `connection_pool_size=512` as the
default in `request_kwargs`. python-telegram-bot's `HTTPXRequest` builds
its own internal httpx pool, and the gateway uses TWO of them — one for
normal `request`, one for `get_updates_request`:

```python
request = HTTPXRequest(**request_kwargs)             # 512
get_updates_request = HTTPXRequest(**request_kwargs) # 512
# Total: up to 1024 sockets
```

1024 is **4× the macOS 256 fd soft limit**. Even before the per-call
thrash from Layer 1, the bot's own pool had already walked past the
kernel ceiling. Once CLOSE_WAIT started accumulating (Cloudflare Warp),
the bot could not get a single new socket — every `do_request()` call
raised `PoolTimeout`.

## Fix

### File 1: `gateway/platforms/_shared_http_client.py` (new)

Module-level `httpx.AsyncClient` singleton with hard-pinned limits:

```python
limits = httpx.Limits(
    max_connections=50,
    max_keepalive_connections=10,
    keepalive_expiry=2.0,
)
timeout = httpx.Timeout(10.0, connect=5.0)
```

Thread-safe lazy build, `atexit` registration for clean shutdown,
`aclose_shared_client()` for explicit close, `reset_shared_client()` for
tests. Env-var overrides: `HERMES_GATEWAY_HTTPX_MAX_CONNECTIONS`,
`_MAX_KEEPALIVE`, `_TIMEOUT_READ`, `_TIMEOUT_CONNECT`,
`_POOL_TIMEOUT` (default 5.0s — guards against event-loop wedge when 51st+
request hits a full pool).

### File 2: `gateway/platforms/base.py`

Two functions migrated to shared client:

- `cache_image_from_bytes()` at line 636 — image download for media cache
- `cache_audio_from_bytes()` at line 745 — audio download for voice cache

Both needed `import httpx` retained (for exception type references in
`except (Exception, httpx.TimeoutException, httpx.HTTPStatusError)`) and
`_log.debug(...)` replaced with `logging.getLogger(__name__).debug(...)`.

### File 3: `gateway/platforms/telegram.py`

Line 4165 — photo URL fallback download: replaced per-call client with
`get_shared_client()`.

### File 4: `gateway/platforms/telegram_network.py`

Line 206 — DoH resolver: replaced `httpx.AsyncClient(timeout=httpx.Timeout(_DOH_TIMEOUT))`
with `get_shared_client()`.

### File 5: `tools/send_message_tool.py`

Three functions already migrated in session-1 of same date:
`_send_signal` (×2 call sites), `_send_dingtalk`, `_send_qqbot`.

### File 6: `gateway/platforms/telegram.py` (HTTPXRequest sizing)

Changed `request_kwargs` defaults:

```python
request_kwargs = {
    "connection_pool_size": 50,  # was 512
    "pool_timeout": 8.0,
    "connect_timeout": 10.0,
    "read_timeout": 35.0,         # was 20.0
    "write_timeout": 10.0,        # was 20.0
}
```

`read_timeout=35s` covers the 5-station LLM p99 (long streaming
replies can hold a single `Bot.send_message` for 30s+). All 5 fields
are env-overridable via `HERMES_TELEGRAM_HTTP_*`.

## Verification

```bash
# Syntax check after migration
cd ~/.hermes/hermes-agent && python3 -m py_compile \
  gateway/platforms/base.py \
  gateway/platforms/telegram.py \
  gateway/platforms/telegram_network.py \
  gateway/platforms/_shared_http_client.py \
  && echo "SYNTAX OK"

# Run the load probe
~/.hermes/hermes-agent/venv/bin/python ~/.hermes/skills/devops/gateway-http-pool-tuning/scripts/verify_pool.py
```

Healthy result:
- pool config: max_conn=50 max_keepalive=10
- timeout: read=10.0 connect=5.0 pool=5.0
- 5 stations × 10 turns = 50 concurrent cross-host requests
- 50/50 ok, 0 errors, avg 0.58s/turn, max 1.70s (first turn = TLS handshake)

Post-fix checks:
```bash
lsof -p $(pgrep -f 'hermes_cli.main gateway') | wc -l   # should be < 200
grep -c "Pool timeout" ~/.hermes/logs/gateway.log        # should be 0
```

## How to recognize this incident in the wild

```bash
# In gateway.log
grep -E "Pool timeout|TimedOut.*occupied" ~/.hermes/logs/gateway.log

# In fd table
lsof -p $(pgrep -f 'hermes_cli.main gateway') | wc -l
# > 200 = heading for trouble

# In httpx internals
from gateway.platforms._shared_http_client import get_shared_client
c = get_shared_client()
print(c._transport._pool._max_connections, c._transport._pool._max_keepalive_connections)
# expect: 50 10
```

## Common post-migration lint errors

After replacing `async with httpx.AsyncClient(...)` with `get_shared_client()`:

1. **`httpx` undefined** — shared client replaces the local `import httpx`
   but exception tuples still reference `httpx.TimeoutException`. Fix:
   retain `import httpx` but only for type references in the except clause.

2. **`_log` undefined** — functions that used `_log = logging.getLogger(__name__)`
   lose the variable when the httpx import block is removed. Fix: use
   `logging.getLogger(__name__).debug(...)` inline instead.

3. **`httpx.PoolTimeout` in exception tuple** — when the shared client
   raises (e.g. 51st request hits full pool), it's an `httpx.PoolTimeout`.
   But if any other exception type reaches the handler, accessing
   `.response` on a non-httpx exception raises AttributeError. Fix:
   `except (Exception, httpx.TimeoutException, httpx.HTTPStatusError)`.

## Related issues / context

- `_http_client_limits.py` already addressed the macOS fd pressure issue
  in #18451 (CLOSE_WAIT accumulation via Cloudflare Warp) — that
  helper existed but was **only used by 7 long-lived adapters**, not
  by `send_message_tool.py` or by the telegram bot pool. This fix
  extends the pattern to the missing call sites.
- python-telegram-bot's `HTTPXRequest` does NOT consult the
  `HERMES_GATEWAY_HTTPX_*` env vars — its pool is a separate
  configuration surface, controlled by `HERMES_TELEGRAM_HTTP_*`.
- The MiniMax-M3 model switch in the same session (from M2.7) is
  unrelated to this incident.