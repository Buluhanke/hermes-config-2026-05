# Camoufox + Peekaboo Anti-Detection Setup (2026-05-12, updated 2026-05-13)

## Environment
- **Machine:** Mac mini M4 (24GB), macOS 26.4.1
- **Project:** camofox-browser (github.com/jo-inc/camofox-browser)
- **Peekaboo:** v3.1.2 via npm global install
- **Camoufox-js:** v0.8.5 (via npm in camofox-browser project)

## Camofox Browser Setup Steps

```bash
# Clone
git clone https://github.com/jo-inc/camofox-browser.git ~/dev/camofox-browser
cd ~/dev/camofox-browser

# Install (postinstall script runs npx camoufox-js fetch)
npm install

# Start server (port 9377)
node server.js

# Verify server
curl http://localhost:9377
# Expected: {"ok":true,"enabled":true,"running":false,"engine":"camoufox",...}
```

## Binary Locations

| Location | Type | Status |
|----------|------|--------|
| `~/Library/Caches/camoufox/Camoufox.app` | camoufox-js cache dir | Incomplete (empty shell after failed fetch) |
| `~/.camoufox/Camoufox.app` | Old install | Complete binary (Mar 2025, v135.0.1-beta.24) |

To restore cache from old binary:
```bash
rm -rf ~/Library/Caches/camoufox/Camoufox.app
cp -R ~/.camoufox/Camoufox.app ~/Library/Caches/camoufox/Camoufox.app
```

## Known Failure: Binary Compatibility (macOS 26.4.1)

**Symptom:** `camoufox --version` hangs indefinitely (process starts but never returns).
Server log: `browserType.launch: Timeout 180000ms exceeded`

**Root cause:** Camoufox binary v135.0.1-beta.24 (compiled Mar 2025) incompatible with macOS 26.4.1.
Binary launches as a process but never connects to Playwright's juggler pipe.

**Attempted workarounds (all failed):**
- Direct command: `/path/to/camoufox --version` → hangs
- Via `camoufox-js` + server → 180s timeouts
- Re-download via `npx camoufox-js fetch` → GitHub timeout (connect to github.com:443 blocked)

**Resolution:** No fix available for current environment. Requires:
1. Network access to GitHub (to download updated binary)
2. Or a Camoufox binary compiled for macOS 26.x

## Peekaboo Setup (⚠️ 安装成功，但授权未执行 — 2026-05-13确认)

**Correct install method:** `npm install -g @steipete/peekaboo`

**Homebrew fails** (repeated 180s+ timeouts):
```bash
brew install steipete/tap/peekaboo  # ← DO NOT USE
```

**⚠️ 授权步骤从未执行（2026-05-13对话确认）：**
Peekaboo 安装成功，但 `peekaboo permissions grant` 从未运行，实际使用会失败。
**必须手动执行：**
```bash
peekaboo permissions grant
```

**Verification:**
```bash
peekaboo permissions status
# Expected: Screen Recording Granted, Accessibility Granted, Event Synthesizing Granted
peekaboo --version
# v3.1.2
```

## Camoufox-js Cache Structure

Expected contents of `~/Library/Caches/camoufox/`:
- `version.json` — version info (e.g. `{"version":"135.0.1","release":"beta.24"}`)
- `GeoLite2-City.mmdb` — GeoIP data (~65.6MB, download is slow)
- `Camoufox.app/Contents/MacOS/camoufox` — main binary (arm64)
- `Camoufox.app/Contents/Resources/properties.json` — fingerprint config (required)
- `Camoufox.app/Contents/Resources/fontconfig/` — font configuration
- `Camoufox.app/Contents/Resources/addons/UBO/` — uBlock Origin

**Fetch command:** `npx camoufox-js fetch` downloads:
1. Camoufox binary (GitHub releases)
2. GeoLite2-City.mmdb (MaxMind, ~65.6MB, very slow on limited connections)
3. UBO addon (addons.mozilla.org, may fail if blocked)

## Server API (Camofox Browser, port 9377)

```bash
# Health check
GET / → {"ok":true,"enabled":true,"running":false,"engine":"camoufox","browserConnected":false}

# Create tab (requires userId and sessionKey)
POST /tabs {"url":"https://example.com","userId":"test","sessionKey":"..."}
# Fails with 500 if browser not running

# Browser launch workflow (automatic):
# Server starts → background warm process → camoufox launch
```
