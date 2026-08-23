---
name: fluxdown
description: Install/wire FluxDown into agent MCP workflows.
---

# FluxDown

Free & open-source (AGPL-3.0) multi-protocol download manager — Rust engine + Flutter UI. IDM alternative: HTTP/HTTPS, FTP, BitTorrent, eD2K, HLS/DASH, with browser-extension takeover. Agent-facing feature: a built-in MCP server so agents (Hermes/Cursor/Claude) can manage downloads via `tools/call`.

Use when: the user wants to install FluxDown, add it as a download MCP server to Hermes, drive downloads from an agent, or asks about IDM alternatives / multi-protocol download managers.

## Install (macOS arm64)
```shell
TAG=$(curl -s https://api.github.com/repos/zerx-lab/FluxDown/releases/latest | python3 -c "import sys,json;print(json.load(sys.stdin)['tag_name'])")
curl -sL --retry 3 -C - -o ~/Downloads/FluxDown.dmg "https://github.com/zerx-lab/FluxDown/releases/download/$TAG/FluxDown-${TAG#v}-macos-arm64.dmg"
hdiutil attach -nobrowse -noautoopen ~/Downloads/FluxDown.dmg
cp -R "/Volumes/FluxDown */FluxDown.app" /Applications/
hdiutil detach "/Volumes/FluxDown *"
xattr -cr /Applications/FluxDown.app   # unsigned dev build — clear quarantine
open -a /Applications/FluxDown.app
```
- x64 users: replace `macos-arm64` with `macos-x64`. Other platforms (Windows `.exe`/`.zip`, Linux `.AppImage`/`.deb`, Android `.apk`, NAS Docker/`.spk`) from the same releases page.
- CLI alt: `cargo install --git https://github.com/zerx-lab/FluxDown fluxdown_cli`

## How it runs
- **Tray-only** Flutter app: `close_to_tray=true`. Window auto-hides to the menu bar on blur/close. `computer_use` / `cua-driver` CANNOT capture it (no on-screen window; AX query returns -25211 / "no on-screen window"). Drive it via the HTTP API or the config DB, never the GUI.
- Listens on `127.0.0.1:17800` (local-only by default).
- Confirm it's alive: `pgrep -f FluxDown.app/Contents/MacOS/FluxDown` and `lsof -iTCP:17800 -sTCP:LISTEN`.
- Config persists in SQLite: `~/Library/Application Support/fluxdown/flux_down.db`, table `config(key TEXT PRIMARY KEY, value TEXT)`.

## Verified API surface (v0.4.7)
| Endpoint | Status | Auth | Notes |
|---|---|---|---|
| `POST /jsonrpc` | LIVE | Bearer token (optional if unset) | aria2-compatible JSON-RPC (`aria2.getVersion`, etc.) |
| `POST /download` | LIVE | `X-FluxDown-Client` header + Bearer | script takeover; 403 without the header |
| `POST /mcp` | **NOT in desktop release** | Bearer token | README claims it; v0.4.7 desktop binary lacks it. The **headless `fluxdown_server` crate** (build from `main`) DOES serve it — see "Get the MCP server" below. |

Auth: Bearer token shared with the management API. Header `Authorization: Bearer <token>` or `X-FluxDown-Token`.

## Wiring to Hermes (MCP)
Recommended: run the **headless `fluxdown_server`** (built from `main`) on an isolated port (e.g. 17801) so it never disturbs the desktop app on 17800. Add to Hermes via `hermes config set` (do NOT hand-edit config.yaml — it's guard-blocked):

```shell
hermes config set mcp_servers.fluxdown '{"type":"streamable_http","url":"http://127.0.0.1:17801/mcp","headers":{"Authorization":"Bearer <FLUXDOWN_TOKEN>"},"enabled":true}'
```

Then restart the gateway so Hermes spawns the new server (see `hermes-config-tricks`). The server token comes from the `FLUXDOWN_TOKEN` env var (see "Get the MCP server" below) — set it before launch; it is adopted on first run.

## PITFALLS
1. **Release lags README.** As of v0.4.7 (tag 2026-08-16) the `/mcp` endpoint is NOT compiled in, even though the README and `main` branch source (`native/api/src/server.rs`, `mcp.rs`) implement the `local_server_mcp_enabled` flag and register `POST /mcp`. The MCP server landed in `main` AFTER the release was cut. Do not assume README features exist in the downloadable binary — probe the endpoint before believing it.
2. **DB edits do NOT persist (desktop app only).** Editing `local_server_token` / `local_server_mcp_enabled` directly in the desktop app's SQLite `config` table is silently dropped on launch (unknown keys discarded; token reset to empty). But the **headless `fluxdown_server` reads `FLUXDOWN_TOKEN` from the environment** and adopts it on first run — so prefer the env var over DB edits. For the desktop app, enable settings via the in-app UI, not by writing the DB.
3. **Tray-only window.** `computer_use` capture/focus_app on `FluxDown` / `com.fluxdown.app` returns "no on-screen window". Use the HTTP API or config DB. `osascript` AX queries fail too (-25211 without TCC).
4. **Token on /jsonrpc.** If a token is set, requests without it return `{"error":{"code":1,"message":"Unauthorized"}}`. If you set the token via DB edit it will NOT take effect (PITFALL 2) — set it in the UI.
5. **`.dmg` download truncates.** `curl` to GitHub releases can partial-transfer (exit 18). Always use `--retry 3 -C -` and re-verify with `shasum -a 256`.

## Get the MCP server (VERIFIED 2026-08-23)
The downloadable desktop release (v0.4.7) does NOT contain `/mcp`. Build the **headless `fluxdown_server`** crate from `main` — it's pure Rust, needs NO Flutter SDK, and seeds `local_server_mcp_enabled=true` by default.

Prereqs (macOS):
```shell
export HOMEBREW_NO_REQUIRE_TAP_TRUST=1
brew install --formula cmake pkg-config          # pkg-config installs as pkgconf; /opt/homebrew/bin/pkg-config symlink ok
# rinf_cli only needed if you later build the Flutter app; the server itself does NOT need it
cargo install rinf_cli
```
Build + run:
```shell
git clone -b main --depth 1 https://github.com/zerx-lab/FluxDown.git FluxDown-src
cd FluxDown-src
cargo build -p fluxdown_server --release         # ~3 min fresh; web/dist missing → harmless warning, API/MCP unaffected
BIN=$(pwd)/target/release/fluxdown-server
DATADIR=~/.hermes/fluxdown-mcp/data
mkdir -p "$DATADIR"
FLUXDOWN_BIND=127.0.0.1:17801 \
FLUXDOWN_DATA_DIR="$DATADIR" \
FLUXDOWN_TOKEN="fluxdown-mcp-<fixed-or-random>" \
FLUXDOWN_ANALYTICS=off \
"$BIN"
```
Verify BEFORE claiming success (both calls must return 200):
```shell
TOKEN="fluxdown-mcp-<same>"
curl -s -X POST http://127.0.0.1:17801/mcp -H 'Content-Type: application/json' \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"probe","version":"1.0"}}}'
# expect serverInfo.name == "FluxDown"
curl -s -X POST http://127.0.0.1:17801/mcp -H 'Content-Type: application/json' \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' | python3 -c "import sys,json;print(len(json.load(sys.stdin)['result']['tools']))"
# expect: 12
```
- 12 tools confirmed: download_add/list/get/pause/resume/pause_all/resume_all/remove, queue_list, rss_list/add/remove.
- No-token request → 401 `invalid or missing token` (auth enforced).
- The headless server's Web UI is NOT embedded (warning only) — that's fine, you only need `/mcp`.
- Keep it off 17800 (desktop app's port) to avoid conflict; 17801 used above.
- Once wired into Hermes, exercise one real `tools/call` (e.g. `download_add` with a small URL) before reporting the integration done.

## References
- `references/endpoints.md` — full endpoint/auth probe results, config keys, and the 12 MCP tool names from `mcp.rs`.
