# Dashboard Web UI — Troubleshooting Reference

## Embedded Chat (CHAT menu) won't show

**Symptom**: Navigation bar missing "CHAT" link. SessionsPage works but no chat tab.

**Root cause**: Dashboard is running without `--tui` flag, so `window.__HERMES_DASHBOARD_EMBEDDED_CHAT__=false` in the injected HTML.

**Fix**:
1. Kill existing Dashboard: `kill <PID>` (find PID via `lsof -i :9119` or `netstat -an | grep 9119`)
2. Restart with `--tui`: `hermes dashboard --port 9119 --no-open --tui`
3. Verify flag: `curl -s http://127.0.0.1:9119/ | grep EMBEDDED_CHAT` → should return `true`
4. Hard-refresh browser (Cmd+Shift+R / Ctrl+Shift+R)

**Permanent fix**: Set `HERMES_DASHBOARD_TUI=1` environment variable before starting Dashboard, or use launchd/launch-agent plist with the flag baked in.

---

## Menu pages return 500 / spinning

**Symptom**: All menu pages (ANALYTICS, MODELS, CONFIG) show "Error: 500" or spin forever.

**Check first**: Browser cache (try Cmd+Shift+R / Ctrl+Shift+R in incognito).

**Debug step**: Open DevTools → Network tab → click a menu → find the failing request URL. Common failure points:
- `/api/status` → 401 = session token not injected
- `/api/analytics/usage` → 500 = backend error (check Dashboard logs)
- `/api/config` → raw config fetch failure

**Session token flow**:
- Dashboard injects `window.__HERMES_SESSION_TOKEN__` and `window.__HERMES_DASHBOARD_EMBEDDED_CHAT__` into its own `index.html`
- Vite dev server's `hermesDevToken()` plugin fetches Dashboard's `index.html` on each page load and re-injects both values into the Vite-served HTML
- Frontend `api.ts` reads `window.__HERMES_SESSION_TOKEN__` and sends as `Authorization: Bearer <token>` header on all `/api/*` requests
- Backend validates that header → 401 if missing/wrong, 200 if correct

**If token injection seems broken**: Check Vite console for `[vite] connecting...` warnings. Could mean Dashboard is down or unreachable from Vite's perspective.

---

## xterm canvas 渲染但视觉上看不见

**Symptom**: browser_snapshot / browser_console 显示 xterm 元素存在、尺寸正确（600+px），但页面上几乎看不到内容。用户说"看不到聊天窗口"。

**Root cause**: xterm 背景是 `rgba(0, 0, 0, 0)`（完全透明），文字颜色是很淡的青色 (`color(srgb 0.607843 1 0.811765)`)，在白色浏览器背景下几乎不可见。

**诊断方法**（browser_console）：
```javascript
// 检查 xterm 是否渲染
document.querySelector('.xterm-helpers') ? 'xterm found' : 'xterm NOT found'

// 检查尺寸
const r = document.querySelector('.xterm').getBoundingClientRect()
// → {w: 661.25, h: 518} 表示正常渲染

// 检查背景色
window.getComputedStyle(document.querySelector('.xterm')).backgroundColor
// → rgba(0, 0, 0, 0) = 透明背景（正常，不是 bug）

// 检查文字内容长度
document.querySelector('.xterm-screen').textContent.length
// → > 0 表示终端有内容渲染（只是看不见）
```

**说明**: 透明背景是设计如此（Dashboard 深色主题背景），不是 bug。终端实际已正确渲染，只是浅色/白色浏览器背景下看不清浅色文字。**解决方法**：确保 Dashboard 使用深色主题（切换主题按钮），浏览器页面也是深色背景。

---

## Dashboard port 9119 not showing in lsof (macOS quirk)

**Symptom**: `lsof -i :9119` returns nothing, but `netstat -an | grep 9119` shows `LISTEN`.

**Cause**: `lsof` on macOS sometimes fails to list sockets for short-lived or specifically-structured processes. `netstat` always works.

**Always use**: `netstat -an | grep 9119` to confirm Dashboard is listening.

---

---

## Model quota exhausted → Dashboard chat silent (no error shown)

**Symptom**: Dashboard Web UI CHAT page sends messages but gets no response. No error message displayed. Other platforms (QQ, WeChat, Telegram) still respond normally through the gateway.

**Root cause**: The model selected in Dashboard's MODELS page has run out of quota (403 `insufficient_user_quota`). The Dashboard's TUI session (PTY) locks the model at the session level and does NOT use the config's `fallback_providers` chain. The gateway, by contrast, uses the global model config and falls through to fallback providers automatically.

**Diagnosis**:
1. Check errors.log for 403 quota errors:
   ```bash
   grep "insufficient_user_quota\|额度不足" ~/.hermes/logs/errors.log
   ```
2. Check which model the Dashboard session is using:
   ```bash
   grep -A2 "model\|provider" ~/.hermes/config.yaml | head -10
   ```
3. Verify the model API responds (replace with actual provider URL):
   ```bash
   curl -s -w "\n%{http_code}" https://v2.aicodee.com/v1/chat/completions \
     -H "Authorization: Bearer $API_KEY" \
     -H "Content-Type: application/json" \
     -d '{"model":"MiniMax-M2.7-highspeed","messages":[{"role":"user","content":"hi"}]}' | tail -5
   ```

**Fix options**:
- **Option A** (switch model in Dashboard): In MODELS page → CHANGE, pick a model with available quota (e.g. deepseek-v4-flash)
- **Option B** (switch global default model): `hermes config set model.default deepseek-v4-flash` and `hermes config set model.provider deepseek`, then restart Dashboard
- **Option C** (recharge provider): Top up the provider account (e.g. aicodee v2)

**Key distinction**: Dashboard session-scoped model selection overrides the global config and disables fallback. If you need fallback to work, use the global default model and avoid selecting a specific model in Dashboard's MODELS page.

**Example from real incident**:
```
Error: 403 - {'error': {'message': '用户额度不足, 剩余额度: ＄0.000000', 'code': 'insufficient_user_quota'}}
```
Provider: aicodee v2 (MiniMax-M2.7-highspeed) — balance fully depleted. Dashboard chat stopped responding around 12:09. QQ and WeChat continued working via deepseek-v4-flash fallback.

---

## Dashboard backend (9119) completely down — only Vite (5173) running

**Symptom**: Both embedded chat is missing AND all API calls return 500. Navigation bar shows only SESSIONS/ANALYTICS/... without CHAT. Every interaction with menu pages returns 500.

**Diagnosis**:
```bash
# Check what's actually listening
netstat -an | grep LISTEN | grep -E "5173|9119"

# Expected (both running):
# node ... 5173  (Vite dev server)
# Python ... 9119 (Dashboard backend)

# Actual (this bug):
# node ... 5173  (Vite only — no backend)
# (9119 column empty)
```

**Root cause**: User started only `npm run dev` (Vite frontend) but not `hermes dashboard` (backend). Vite proxies `/api/*` to `127.0.0.1:9119` — when backend is absent, every API call fails. The `hermesDevToken()` Vite plugin also can't fetch `window.__HERMES_DASHBOARD_EMBEDDED_CHAT__` from a non-existent backend, so the flag stays `false` and the CHAT menu is hidden.

**Fix — two processes required**:
```bash
# Terminal 1: Dashboard backend
~/.hermes/hermes-agent/venv/bin/hermes dashboard --port 9119 --host 127.0.0.1 --no-open --tui

# Terminal 2: Vite frontend (only needed for development with hot reload)
cd ~/.hermes/hermes-agent/web && npm run dev -- --host
# → http://localhost:5173
```

For production (recommended for auto-start): build once, then `hermes dashboard` self-serves everything — no separate Vite process needed:
```bash
cd ~/.hermes/hermes-agent/web && npm run build
~/.hermes/hermes-agent/venv/bin/hermes dashboard --port 9119 --host 127.0.0.1 --no-open --tui
```

**Why it looks like a "restart" problem**: If Dashboard was previously running and then stopped (crash, manual kill, machine reboot), the Vite dev server may still be alive at 5173. The browser tab still shows the old UI, but the backend is gone. User says "I just restarted and chat is broken" — the restart was incomplete.

---

## Architecture recap

```
Browser (5173)  ← Vite dev server (proxies /api/* to 9119, injects session token)
     ↓
localhost:9119  ← hermes dashboard (Python web server, serves index.html + API)
     ↓
Hermes Gateway (separate process, manages sessions/platforms)
```

- Vite (5173) does NOT serve the actual API — it proxies to Dashboard (9119)
- Changing Dashboard startup flags requires restart
- Changing Vite config (vite.config.ts) does NOT require restart (HMR)

---

## WebSocket for embedded chat (PTY)

The CHAT page connects via WebSocket at `/api/pty` (proxied by Vite to Dashboard). URL construction in ChatPage.tsx:
```javascript
const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
const url = `${proto}//${window.location.host}/api/pty?token=<session>&channel=<uuid>`;
```

- `token`: from `window.__HERMES_SESSION_TOKEN__`
- `channel`: randomly generated per tab mount (tab refresh = new channel/new PTY)
- Backend validates token and returns 4401 on auth failure
- PTY runs `hermes --tui` inside the Dashboard's Python server process
