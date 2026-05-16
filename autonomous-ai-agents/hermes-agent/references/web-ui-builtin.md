# Hermes Agent 内置 Web UI

## 路径
`~/.hermes/hermes-agent/web/`（React + Vite + Tailwind + xterm）

## 架构：两个进程必须同时运行

| 进程 | 命令 | 端口 | 作用 |
|------|------|------|------|
| Python Dashboard 后端 | `~/.hermes/hermes-agent/venv/bin/hermes dashboard --host 127.0.0.1 --port 9119` | 9119 | 提供 `/api/*` REST 接口 + session token |
| Vite 前端 | `cd web && npm run dev -- --host` | 5173 | React Web UI，代理 `/api/*` 到后端 |

**所有操作返回 500 的原因：** 只启动了 Vite 前端，没启动 Python 后端。Vite 的 `vite.config.ts` 将 `/api` 代理到 `127.0.0.1:9119`，后端不运行则 500。

## 启动步骤

```bash
# 1. 启动后端（后台运行）
~/.hermes/hermes-agent/venv/bin/hermes dashboard --host 127.0.0.1 --port 9119 &
sleep 5
# 验证后端就绪
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:9119

# 2. 启动前端（后台运行）
cd ~/.hermes/hermes-agent/web && npm run dev -- --host
# 浏览器打开 http://localhost:5173
```

## 首次启动
```bash
cd ~/.hermes/hermes-agent/web
npm install          # 必需，否则 predev 的 sync-assets 失败（copy node_modules/@nous-research/ui/dist/fonts）
npm run dev -- --host
```

## 坑

- **`predev` 脚本自动运行 `sync-assets`**：如果没跑过 `npm install`，`node_modules` 为空，`sync-assets` 报错：`cp: node_modules/@nous-research/ui/dist/fonts: No such file or directory`。解决：先 `npm install` 再启动。
- **后端没启动就开前端**：症状"操作失败: 500"，curl 到 `127.0.0.1:9119` 返回 000（连接不上）。
- **hermes 二进制路径**：直接用 `hermes` 可能走错 venv，要用完整路径 `~/.hermes/hermes-agent/venv/bin/hermes`。
- **session token**：开发模式下 Vite plugin 自动从 `127.0.0.1:9119` 的 HTML 里抓 `window.__HERMES_SESSION_TOKEN__` 注入到前端，无此 token 则所有 `/api` 调用 401。

## session token 陈旧导致 500/转圈

**症状**：Dashboard 之前正常，某次操作后所有菜单点开都是 Error: 500 或一直转圈。

**根因**：Dashboard 重启后 session token 会变化，但 Vite dev server 内存里缓存的是旧的 token。Vite plugin 只在启动时从 Dashboard HTML 里抓一次 token，后续 Dashboard 重启不会自动更新。

**诊断**：
```bash
# Dashboard 在跑但 token 已过期 → 返回 401
curl -s -o /dev/null -w "%{http_code}" http://localhost:5173/api/config
# 401 = token 陈旧（Dashboard 重启过但 Vite 没重启）

# Dashboard 根本没跑 → 连接不上
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:9119
# 000 或 ECONNREFUSED = Dashboard 未运行
```

**修复**：杀掉并重启 Vite dev server（5173），让它重新获取新 token：
```bash
kill $(lsof -ti :5173 -c node)
cd ~/.hermes/hermes-agent/web && npm run dev -- --host
```

**预防**：如果 Dashboard 会频繁重启，用 production build 代替 dev server（production build 由 Dashboard 自带 static files，无需 separate Vite process，不会出现 token 陈旧问题）：
```bash
cd ~/.hermes/hermes-agent/web && npm run build
# 之后只需启动 Dashboard：~/.hermes/hermes-agent/venv/bin/hermes dashboard --port 9119
```
