---
name: self-hosted-ai-service-install
description: Install and run self-hosted AI/web services (LibreChat, Open WebUI, n8n, Flowise, Langflow, ComfyUI, etc.) on resource-constrained macOS. Load when user asks to "装 LibreChat / Open WebUI / n8n", "deploy a chat frontend", "自托管 XX", or asks about installing any Node/Python-based multi-service app with optional DB + Redis + GPU. Covers pre-flight resource check, dependency discovery (DBs, ports, launchd services), clone-with-eval pattern, config routing to existing backends (e.g. LibreChat → Hermes gateway as Custom Endpoint), and clean uninstall.
---

# Self-Hosted AI Service Install (macOS, resource-constrained)

A workflow for installing and running multi-service self-hosted apps on a Mac mini (24GB) that already runs Hermes + browser + Claude/Cursor. Goal: get the user a working service **without blowing the memory budget** and **without clobbering existing infrastructure**.

## When to load

- User says "装 LibreChat / Open WebUI / Flowise / Langflow / ComfyUI / n8n / anything with docker-compose"
- User points at a GitHub repo and says "把这个跑起来"
- User wants to self-host any AI/web service with **its own database or backend**

## Pre-flight: 6 things to check BEFORE cloning

Stop and report if any of these block. Do not run `git clone` of a large repo until you know the answer to each:

1. **Database requirement** — open README, grep for `MongoDB` / `Postgres` / `SQLite` / `Redis` / `MySQL`. Self-hosted AI apps almost always need a DB. Note which one and whether it's bundled (Docker) or external (you have to `brew install` it).
2. **Provider / API key requirement** — grep for `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` / provider config. Many apps support "Custom Endpoint" / "OpenAI-compatible URL" — if you already run a local gateway (Hermes at `:8642`, LiteLLM, OpenRouter), you can route the new app through it instead of paying for separate keys.
3. **Port collision** — check `~/.hermes/config.yaml` and `lsof -iTCP -sTCP:LISTEN -P -n` for ports the new app wants (LibreChat 3080, Open WebUI 8080, n8n 5678, Flowise 3000). If a port is taken, stop and ask — don't silently pick another.
4. **Memory budget** — run `top -l 1 -n 0 -s 0 | grep PhysMem` and read free. Then estimate the new app's footprint:
   - Node backend only: ~300-500MB
   - Python backend (FastAPI): ~200-400MB
   - MongoDB: ~300MB-2GB depending on cache
   - Postgres: ~200-500MB
   - React frontend in dev mode: ~500MB-1GB
   - **Hard rule**: stop and ask user if remaining free < 2× estimated footprint. Mac mini 24GB has ~4-5GB free after Hermes+Chrome+Claude.
5. **Disk budget** — `df -h /`. LibreChat full clone + node_modules = ~2GB. Open WebUI = ~1.5GB. Add another 1GB for the DB if external. Stop if remaining free < 5GB.
6. **Launchd persistence** — if the app uses `brew services`, it auto-starts on boot and **eats RAM forever**. Always tell the user before running `brew services start`. Offer the alternative: run the service manually (`mongod --config ... &`) so it dies on logout.

**Present findings as方案 A/B/C, do not pick silently.** Example for LibreChat:
```
A: brew install mongodb-community + 复用 Hermes gateway as Custom Endpoint (recommended, ~500MB extra RAM)
B: brew install + 用 OpenAI API key (需要你提供 key)
C: 不装 MongoDB, 不行 (LibreChat 强依赖)
```

## Clone-with-eval pattern (replaces blind git clone)

For exploration / evaluation clones of repos >100MB, **always** use `--depth 1`:

```bash
cd ~/projects && git clone --depth 1 https://github.com/owner/repo.git
```

Full clones of large repos (LibreChat = 500MB+, easy-vibe = 200MB+) regularly exceed the 60-90s tool timeout and force you to start over with `--depth 1` anyway. Skip the wasted round trip.

After clone, **do not** `npm install` / `pip install` until you've shown the user the dependency footprint. Run `du -sh node_modules` only after install completes (it's 1.5-2GB for LibreChat — user needs to know that).

## Routing the new app to an existing local gateway

Most self-hosted AI apps support an OpenAI-compatible "Custom Endpoint" config. If you already run a local LLM gateway, **wire the new app to it** instead of paying for a separate API key. Patterns:

**LibreChat** — edit `librechat.yaml`:
```yaml
endpoints:
  custom:
    - name: "Hermes"
      apiKey: "fake-key"            # gateway may not validate, see below
      baseURL: "http://127.0.0.1:8642/v1"
      models:
        default: ["qwen/qwen3.5-397b-a17b"]
        fetch: true                  # auto-discover from /v1/models
```

**Open WebUI** — Admin Settings → Connections → OpenAI API → `http://127.0.0.1:8642/v1`

**Flowise / Langflow** — ChatOpenAI node → Base Path = `http://127.0.0.1:8642/v1`

**⚠️ Gateway auth pitfall**: some local gateways return `401 invalid api key` when a Custom Endpoint sends a fake/empty key. Two fixes, in order:
1. Set `apiKey` to the same key the gateway validates (check `ps eww -p <gateway-pid>` for env vars like `MAIN_API_KEY`, `OPENAI_API_KEY`, `HERMES_API_KEY`)
2. If gateway doesn't need a key at all but the client app requires one, set `apiKey: "sk-no-auth-needed"` and verify with a single curl from the new app's container

For Hermes specifically: the api_server at `:8642` validates against `MAIN_API_KEY` (or whatever env var the gateway checks). Always check `lsof -iTCP:8642 -sTCP:LISTEN -P -n` + `ps eww -p <pid> | tr ' ' '\n' | grep API_KEY` to find the right env var before guessing.

## Clean uninstall checklist (the user will eventually say "清除掉刚刚装的")

Self-hosted apps leave 4 kinds of residue:

1. **The cloned repo directory** — `rm -rf ~/projects/<app>` (user-may-have-edited-files → ask first if non-empty)
2. **npm/pip deps in `node_modules` / `venv`** — gone with the repo dir, but `pip uninstall <pkg>` if deps were installed system-wide
3. **Brew services (DBs etc.)** — `brew services stop <formula>` then `brew uninstall <formula>`. Also check `~/Library/LaunchAgents/` for any launchd plists the app installed.
4. **App data dir** — most apps store state in `~/.<app-name>` or `~/Library/Application Support/<app-name>`. **Always grep before declaring clean.**

For LibreChat specifically:
```bash
rm -rf ~/.hermes/LibreChat_install       # clone + node_modules (~2GB)
brew services stop mongodb-community
brew uninstall mongodb-community
rm -rf ~/Library/LaunchAgents/homebrew.mxcl.mongodb-community.plist
rm -rf ~/.mongodb                        # if app created it
# Note: ~/.hermes/scripts stays untouched — that's separate from the clone
```

## Verification before reporting "installed"

Per the verification-before-reporting skill:
- `npm run dev` / `docker compose up` actually starts without exiting in the first 30s
- `curl -s -o /dev/null -w "%{http_code}" http://localhost:3080/` returns `200`, not `502` or `000`
- DB connection works: `mongosh mongodb://localhost:27017/test --eval "db.runCommand({ping:1})"` returns `{ ok: 1 }`
- Provider route works: send one chat completion via the Custom Endpoint and verify it returns a non-error response

## Reference files

- `references/librechat-install-walkthrough.md` — concrete LibreChat 0.8.7 install on macOS, what worked / what didn't (MongoDB check, Hermes gateway routing, port 3080 collision check)
- `references/resource-budget-calculator.md` — table of common self-hosted AI apps and their memory/disk footprint at idle + under load

## Common pitfalls

- **MongoDB not pre-installed** — LibreChat will fail with cryptic errors at first request if mongod isn't running. Always `pgrep mongod` before `npm run dev`.
- **Node version mismatch** — LibreChat wants Node ≥20. Check `node --version` first.
- **`brew services start` runs forever** — it adds a launchd plist. Use `mongod --config /opt/homebrew/etc/mongod.conf --fork` for a one-off start instead.
- **Memory pressure after install** — if Mac mini starts swapping, the new app is the first suspect. Run `ps -axm -o pid,rss,comm | sort -nrk2 | head -10` to confirm.
- **Forgot to check the LICENSE** — some self-hosted AI apps are AGPL (commercial restrictions). Always grep before promising the user they can use it.
- **`npm run backend` before `npm run build` fails with `MODULE_NOT_FOUND @librechat/data-schemas`** (2026-06-30 实测). LibreChat 的后端依赖前端构建产物里的 `@librechat/data-schemas/dist/index.cjs`. 正确顺序: `npm ci` → `npm run build` → `npm run backend`. 先跑 backend 会报 MODULE_NOT_FOUND, 走错版本 (`api/server/index.js`) 而不是 `dist/index.cjs`. 修复: 跑一次 build 即可, build 完成后约 20s. **永远先 build 再 run backend**, 不要中间测试后端能不能起来.
- **`brew install mongodb-community` 后默认需要开机启动** — 如果只是临时评估, 用 `mongod --fork --config /opt/homebrew/etc/mongod.conf` 一次性启动, 避免 `brew services start` 注册 launchd plist 永久占内存. 评估完 `brew uninstall mongodb-community` 清理.
- **健康检查端点不是 `/api/health`** — LibreChat 0.8.7 没暴露 `/api/health`, 验证用 `curl -o /dev/null -w "%{http_code}" http://localhost:3080/` 应返回 200 + `curl http://localhost:3080/api/agents` 或浏览器打开看到登录页才算跑通.
- **后台进程必须验证 exit code** — LibreChat 第一次跑 backend 失败后看 exit code 0 也可能误报成功, 必查 `proc.list()` 看 `last_status` 或 `tail` 最近日志确认状态. **关联**: `verification-before-reporting` skill.