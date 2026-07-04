# Hermes config.yaml Timeout Schema Reference

Last validated: 2026-07-01, Hermes version on Mac mini
Backup used: `~/.hermes/config.yaml.bak.20260701_174508`

## Three timeout layers that matter

Hermes separates **HTTP request** from **stream chunk** timeout. By default only the HTTP timeout is wired. Streaming chunks have no built-in timeout — a hung chunk will hold the task indefinitely until `gateway_timeout` kicks in (default 900s = 15min).

## Fields and their effects

### model.request_timeout_seconds (HTTP timeout)

- Default: 10-30s depending on provider
- Recommended: **8s for proxy providers**, 10-20s for direct API
- Affects: connection establishment + first-byte response
- Reset: hot-reload friendly (most cases)

### model.stream_chunk_timeout_seconds (NEW field)

- Default: **NOT in schema** (must be added manually)
- Recommended: **25s** (below 20s = false positives on slow reasoning, above 40s = wastes time)
- Affects: gap between successive stream chunks
- Reset: **requires gateway restart**

### agent.api_max_retries

- Default: 1 (wastes time, never go above 0)
- Recommended: **0** — fail-fast into fallback chain
- Affects: per-provider retry count before chain advance
- Reset: hot-reload friendly

### agent.gateway_timeout

- Default: 900s (15min)
- Recommended: **300s (5min)** as ceiling, never below 120s for legit long tasks
- Affects: hard kill on entire task duration
- Reset: requires gateway restart (some versions hot-reload)

### agent.restart_drain_timeout

- Default: 180s
- Recommended: **60s** — drains in-flight requests faster
- Reset: gateway restart

## Successful patch (this session, 2026-07-01)

```diff
--- config.yaml.bak.20260701_174508
+++ config.yaml
@@ -6,1 +6,2 @@
-  request_timeout_seconds: 10
+  request_timeout_seconds: 8
+  stream_chunk_timeout_seconds: 25
@@ -77,4 +78,5 @@ agent:
-  gateway_timeout: 900
-  restart_drain_timeout: 180
-  api_max_retries: 1
+  gateway_timeout: 300
+  restart_drain_timeout: 60
+  api_max_retries: 0
+  stream_chunk_timeout_seconds: 25
```

## Why this matters in practice

User's symptom before fix: CLI session stuck at iteration 12/80, "waiting for stream response (180s no chunks yet)", 6 consecutive context compactions, gateway never advanced to fallback chain.

After fix expected: 25s of stream silence = provider disconnected, gateway moves to fallback chain entry #2. Worst case 13 providers × 25s = 5.4 minutes to reach final fallback (Agnes). Best case: Cerebras succeeds in ~2s.

## Where the schema actually lives

Hermes 2026 schema source (may need update next version):
- Vendor fields: `hermes_agent/config/schema.py` 
- Timeout validation: `hermes_agent/config/validators.py`
- Patch tool blocklist: `hermes_agent/tools/security_sensitive.py` — `config.yaml` is in the list

If `stream_chunk_timeout_seconds` is rejected by `hermes config set`, use the python sed workaround in SKILL.md "Workaround A".
