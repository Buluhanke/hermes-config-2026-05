# Telegram Pool Timeout Sequel — 2026-06-04 01:03-01:06 UTC

## Incident summary

Telegram bot experienced **repeated `Pool timeout: All connections in the connection pool are occupied`**
during a burst traffic period. Multiple send operations failed between 01:03 and 01:06 UTC.

## Root cause

`HERMES_TELEGRAM_HTTP_POOL_SIZE=80` was set after the 2026-06-03 fd-exhaustion incident (where 512 caused
macOS 256 fd limit to be exceeded). However, Telegram's `HTTPXRequest` creates **two** independent pools
(`request` + `get_updates`), so `80 × 2 = 160` max sockets was insufficient for the burst.

Simultaneously, `pool_timeout=12s` was too tight — at 01:03 UTC, network conditions caused responses
to slow, causing all 80 connections to be occupied waiting, triggering pool timeout on new requests.

## Key evidence from gateway.log

```
2026-06-04 01:03:35,348 WARNING gateway.platforms.base: [Telegram] Send failed (attempt 2/2, retrying in 4.8s)
2026-06-04 01:03:48,123 WARNING gateway.platforms.telegram: [Telegram] Network error on send (attempt 1/3), retrying in 1s
2026-06-04 01:04:07,134 ERROR gateway.platforms.telegram: [Telegram] Failed to send Telegram message
2026-06-04 01:04:15,140 WARNING gateway.platforms.telegram: [Telegram] Network error on send (attempt 1/3)
2026-06-04 01:04:24,145 WARNING gateway.platforms.telegram: [Telegram] Network error on send (attempt 2/3)
2026-06-04 01:04:34,150 ERROR gateway.platforms.telegram: [Telegram] Failed to send Telegram message
```

## Fix applied

| Parameter | Before | After | Reason |
|-----------|-------|------|--------|
| `HERMES_TELEGRAM_HTTP_POOL_SIZE` | 80 | 150 | 80×2=160 too small; 150×2=300 gives headroom |
| `HERMES_TELEGRAM_HTTP_POOL_TIMEOUT` | 12.0 | 15.0 | 12s too tight for burst conditions |

`read_timeout=40.0` and `write_timeout=15.0` remained unchanged.

## Other platforms status

- **Feishu**: Uses per-request `httpx.AsyncClient()` — no persistent pool, no pool exhaustion risk
- **Discord**: Uses temporary `aiohttp.ClientSession` for image download only — no persistent pool
- **WeChat/QQBot**: Use shared `_shared_http_client` singleton — already properly tuned

## Lessons learned

1. **Two-pool multiplier must be accounted for**: Telegram's `HTTPXRequest` creates two pools.
   Any pool_size target must be doubled to get the actual socket count.
2. **80 was a deliberate reduction from 512** to avoid fd exhaustion — but the reduction was
   too aggressive. The right answer is not 80 or 512, but a value that gives 3-4× headroom
   above typical load while staying below the macOS 256 fd soft limit per platform.
3. **pool_timeout must accommodate network variability**: 12s was enough for normal conditions
   but failed under burst. 15s gives a better margin.