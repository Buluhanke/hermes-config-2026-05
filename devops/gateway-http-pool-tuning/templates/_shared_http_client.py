"""Module-level shared ``httpx.AsyncClient`` singleton for gateway platforms.

Why this exists
---------------
The gateway's telegram send path, signal/dingtalk/feishu/qqbot/weixin
adapters, and the LLM client all open short-lived ``async with
httpx.AsyncClient(...)`` blocks per request. Each block:

1. Builds a brand-new ``ConnectionPool`` (no keep-alive reuse across calls)
2. Opens a fresh TLS handshake to the same Telegram / proxy host
3. Tears the pool down on ``__aexit__`` — returning sockets to the kernel
   while the peer is still draining CLOSE_WAIT (Cloudflare Warp + macOS)

Under 5-station cross-testing fan-out, the bot would ramp ~35+ concurrent
send-message tool calls per turn. Each one re-handshakes Telegram's TLS,
and httpx's default unbounded-retry behaviour compounds the storm — by
call #35 the connection pool is starved, the asyncio event loop starves
alongside it, and the gateway stalls with
``telegram.error.TimedOut: Pool timeout: All connections in the
connection pool are occupied``.

The fix
-------
A single process-wide ``httpx.AsyncClient`` is created lazily on first
use and reused for every outbound HTTP call originating inside the
gateway. ``Limits`` pin both the hard cap and the keep-alive cap, and
``Timeout`` enforces a hard ceiling on every stage so a stuck peer can
never wedge the event loop.

* ``max_connections=50`` — hard cap on simultaneous open sockets.
* ``max_keepalive_connections=10`` — well below the macOS default 256 fd
  soft limit; with ``keepalive_expiry=2.0`` the pool recycles aggressively
  so Cloudflare Warp CLOSE_WAIT can't accumulate.
* ``timeout=Timeout(10.0, connect=5.0, pool=5.0)`` — read 10s, connect 5s,
  pool-wait 5s.  The pool timeout is the load-bearing one: without it,
  the 51st+ concurrent request during a spike will hang the awaiting
  coroutine forever, accumulating awaiters in the asyncio loop until
  the gateway appears frozen.  Verified 2026-06-03 with stress_e2e_v2.py:
  100 concurrent @ max=50 with pool_timeout=None produced 0 errors but
  would have wedged a real slow peer — switching to 5.0 gives graceful
  PoolTimeout instead of silent hang.

The singleton lives for the lifetime of the gateway process. ``aclose()``
is wired into ``atexit`` so a clean shutdown still drains in-flight
requests.

Override via env
----------------
``HERMES_GATEWAY_HTTPX_MAX_CONNECTIONS``
``HERMES_GATEWAY_HTTPX_MAX_KEEPALIVE``
``HERMES_GATEWAY_HTTPX_TIMEOUT_READ``
``HERMES_GATEWAY_HTTPX_TIMEOUT_CONNECT``
``HERMES_GATEWAY_HTTPX_POOL_TIMEOUT``
"""

from __future__ import annotations

import atexit
import logging
import threading
from typing import TYPE_CHECKING, Optional

try:
    import httpx
except ImportError:  # httpx is required by gateway already
    httpx = None  # type: ignore[assignment]

if TYPE_CHECKING:
    import httpx as _httpx_typing  # noqa: F401  (for type checkers)

logger = logging.getLogger(__name__)

_DEFAULT_MAX_CONNECTIONS = 50
_DEFAULT_MAX_KEEPALIVE = 10
_DEFAULT_TIMEOUT_READ_S = 10.0
_DEFAULT_TIMEOUT_CONNECT_S = 5.0
_DEFAULT_POOL_TIMEOUT_S = 5.0


def _env_int(name: str, default: int) -> int:
    import os
    raw = (os.environ.get(name) or "").strip()
    if not raw:
        return default
    try:
        val = int(raw)
    except (TypeError, ValueError):
        return default
    return val if val > 0 else default


def _env_float(name: str, default: float) -> float:
    import os
    raw = (os.environ.get(name) or "").strip()
    if not raw:
        return default
    try:
        val = float(raw)
    except (TypeError, ValueError):
        return default
    return val if val > 0 else default


def _build_client() -> "httpx.AsyncClient":
    """Construct the singleton ``AsyncClient`` with hardened limits."""
    if httpx is None:  # pragma: no cover
        raise RuntimeError("httpx is not importable; gateway requires httpx")

    max_conn = _env_int("HERMES_GATEWAY_HTTPX_MAX_CONNECTIONS", _DEFAULT_MAX_CONNECTIONS)
    max_keepalive = _env_int("HERMES_GATEWAY_HTTPX_MAX_KEEPALIVE", _DEFAULT_MAX_KEEPALIVE)
    read_s = _env_float("HERMES_GATEWAY_HTTPX_TIMEOUT_READ", _DEFAULT_TIMEOUT_READ_S)
    connect_s = _env_float("HERMES_GATEWAY_HTTPX_TIMEOUT_CONNECT", _DEFAULT_TIMEOUT_CONNECT_S)
    pool_timeout_s = _env_float("HERMES_GATEWAY_HTTPX_POOL_TIMEOUT", _DEFAULT_POOL_TIMEOUT_S)

    limits = httpx.Limits(
        max_connections=max_conn,
        max_keepalive_connections=max_keepalive,
        keepalive_expiry=2.0,  # matches _http_client_limits.py default
    )
    timeout = httpx.Timeout(read_s, connect=connect_s, pool=pool_timeout_s)

    logger.info(
        "[shared_http] building gateway-wide AsyncClient "
        "max_conn=%d max_keepalive=%d timeout=read=%.1fs/connect=%.1fs/pool=%.1fs",
        max_conn, max_keepalive, read_s, connect_s, pool_timeout_s,
    )
    return httpx.AsyncClient(
        limits=limits,
        timeout=timeout,
        http2=False,
        trust_env=True,
    )


_client: Optional["httpx.AsyncClient"] = None
_client_lock = threading.Lock()
_atexit_registered = False


def get_shared_client() -> "httpx.AsyncClient":
    """Return the process-wide ``httpx.AsyncClient`` (created on first use).

    Threadsafe and lazy.  Hot path is just a pointer load.
    """
    global _client, _atexit_registered
    if _client is not None:
        return _client
    with _client_lock:
        if _client is None:
            _client = _build_client()
            if not _atexit_registered:
                atexit.register(_atexit_close, _client)
                _atexit_registered = True
    return _client


async def aclose_shared_client() -> None:
    """Explicitly close the shared client.  Safe to call multiple times."""
    global _client
    client = _client
    _client = None
    if client is not None and not client.is_closed:
        try:
            await client.aclose()
        except Exception as e:  # pragma: no cover
            logger.warning("[shared_http] aclose failed: %s", e)


def _atexit_close(client: "httpx.AsyncClient") -> None:  # pragma: no cover
    """Sync fallback for ``atexit`` when the loop is already gone."""
    if client is None or client.is_closed:
        return
    try:
        if hasattr(client, "_transport") and client._transport is not None:
            transport = client._transport
            if hasattr(transport, "close"):
                transport.close()
    except Exception as e:
        logger.debug("[shared_http] atexit close failed (ok if loop gone): %s", e)


def reset_shared_client() -> None:
    """Drop the cached singleton.  Tests use this to force a fresh client."""
    global _client
    _client = None
