# FluxDown — Endpoint & Config Reference

Verified against **v0.4.7** (macOS arm64, 2026-08-16) and `main` branch source on 2026-08-23.

## Local API port
- Default: `127.0.0.1:17800` (local-only; LAN bind needs `local_server_lan_enabled`).
- Confirm listener: `lsof -iTCP:17800 -sTCP:LISTEN -P`

## Endpoints (probe results)
| Method | Path | Auth | Result in v0.4.7 |
|---|---|---|---|
| GET | `/` | none | `404 {"message":"unknown endpoint"}` |
| GET | `/api` `/docs` `/openapi.json` | none | `404` (management API off) |
| POST | `/jsonrpc` | Bearer (optional if token unset) | LIVE — aria2-compatible JSON-RPC. `aria2.getVersion` works. No token → `{"error":{"code":1,"message":"Unauthorized"}}` |
| POST | `/download` | `X-FluxDown-Client` header + Bearer | LIVE — script takeover. Missing header → `403 missing X-FluxDown-Client header` |
| POST | `/mcp` | Bearer | **404 in v0.4.7** — not compiled in. Registered in `main` (`server.rs` route `routes::MCP` gated by `config.mcp_enabled`). |

Auth header forms (from `native/api/src/auth.rs`, shared with management API):
`Authorization: Bearer <token>` OR `X-FluxDown-Token: <token>`.

## Config DB
- Path: `~/Library/Application Support/fluxdown/flux_down.db` (macOS)
- Table `config(key TEXT PRIMARY KEY, value TEXT)`.
- Server flags read by `ApiServerConfig::from_config_map` (native/api/src/server.rs):

| config key | default | controls |
|---|---|---|
| `local_server_enabled` | true | master switch (port binding) |
| `local_server_port` | 17800 | listen port |
| `local_server_token` | "" | Bearer token; empty = jsonrpc/takeover unauth, mgmt API rejects |
| `local_server_takeover_enabled` | true | `/download` script takeover |
| `local_server_jsonrpc_enabled` | true | `/jsonrpc` aria2 compat |
| `local_server_api_enabled` | false | `/api/v1/*` management REST |
| `local_server_mcp_enabled` | false | `/mcp` MCP server (**NOT honored by v0.4.7 binary**) |
| `local_server_lan_enabled` | false | bind `0.0.0.0` |
| `local_server_cors_allow_all` | false | permissive CORS |

⚠️ Direct `UPDATE config` writes are **discarded on next launch** (app rewrites/cleans config; unknown keys dropped, token reset). Enable via the in-app UI (Settings → API Service), not the DB.

## MCP tools (from `native/api/src/mcp.rs`, main branch — for when a release ships `/mcp`)
Transport: Streamable HTTP, stateless (no `Mcp-Session-Id`), JSON-RPC 2.0, `Accept: application/json, text/event-stream`. Protocol `2025-06-18`.

Methods: `initialize`, `ping`, `tools/list`, `tools/call`.

Tools (12):
1. `download_add` — `{url, fileName?, saveDir?, segments?, proxyUrl?, cookies?, referrer?, userAgent?, queueId?, checksum?}` → `{taskId}`
2. `download_list` — `{status?: all|pending|downloading|paused|completed|error|preparing}` → `{tasks, count}`
3. `download_get` — `{taskId}` → `{task}`
4. `download_pause` — `{taskId}` → `{paused}`
5. `download_resume` — `{taskId}` → `{resumed}`
6. `download_pause_all` → `{pausedAll:true}`
7. `download_resume_all` → `{resumedAll:true}`
8. `download_remove` — `{taskId, deleteFiles?:bool}` → `{removed, deletedFiles}`
9. `queue_list` → `{queues}`
10. `rss_list` → `{sources}`
11. `rss_add` — `{url, name?, queueId?, saveDir?, intervalMinutes?, autoDownload?}` → `{sourceId}`
12. `rss_remove` — `{sourceId}` → `{removed}`

Auth enforced before `handle_mcp` runs (`check_management_auth`). Unknown method → `-32601`; parse error → `-32700`.

## Hermes mcp_servers entry (once `/mcp` is live)
```yaml
mcp_servers:
  fluxdown: '{"type":"streamable_http","url":"http://127.0.0.1:17800/mcp","headers":{"Authorization":"Bearer <token>"}}'
```
Hub: `type: streamable_http` (Hermes catalog uses `streamable_http`; raw config JSON string also works as shown elsewhere in config.yaml).
