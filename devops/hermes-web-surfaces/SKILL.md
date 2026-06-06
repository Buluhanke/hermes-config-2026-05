---
name: hermes-web-surfaces
description: Hermes Agent 提供的多个 web 表面（API server / Web dashboard / Web UI）— 端口、用途、URL、怎么识别用户在问哪个。覆盖"我打不开 chat UI / 哪个端口是 chat / 9120 跟 8642 跟 9119 区别"这类问题。
triggers:
  - 用户说"打不开 chat"
  - 用户报 9120/8642/9119 任何一个端口
  - 用户说"网页版卡了 / 没响应 / 404"
  - 用户说"web UI 在哪"
  - 用户问"hermes 的网页版用哪个端口"
  - 用户问"API server 跟 web dashboard 区别"
---

# Hermes Web Surfaces（端口速查 + 故障定位）

Hermes 在本机有 **3 个 web 表面 + 1 个 Chrome debug 端口**，用户经常把它们搞混。这一页是 1 分钟能答完"哪个端口是 chat"的速查表。

## 4 个端口

| 端口 | 是什么 | 启动方式 | 用户访问 |
|------|--------|----------|----------|
| **9119** | **Web Dashboard / Chat UI**（React SPA，built by Vite） | `hermes dashboard` 或 `hermes dashboard --port 9119` | `http://127.0.0.1:9119/` |
| **8642** | **API Server**（OpenAI 兼容 + Hermes 内部 REST API） | 配置 `API_SERVER_ENABLED=true` + `API_SERVER_PORT=8642`，gateway 启动时自动起 | `http://127.0.0.1:8642/v1/chat/completions` 等 API endpoint |
| **9120** | **不存在**（用户在浏览器记住的旧 URL 残留） | — | 打不开就是打不开 |
| **9333** | **Chrome debug port**（Hermes 复用的 Chrome） | `~/.hermes/chrome-debug/` 目录的 Chrome 实例 | 不能直接访问，是 CDP 内部端口 |

→ **用户要打开网页版 chat，正确 URL 是 `http://127.0.0.1:9119/`，命令是 `hermes dashboard`**。

## 3 个 web 表面的真实用途

### 9119 — Web Dashboard（用户要打开的）
- **React SPA**，Vite 构建产物在 `~/.hermes/hermes-agent/hermes_cli/web_dist/`
- 路由：`/` `/chat` `/sessions` `/skills` `/cron` `/config` ...
- 鉴权：session token 通过 `<script>` 注入到 `index.html`
- 默认 port 在 `hermes_cli/main.py:cmd_dashboard` 写死 `default=9119`
- 自定义：`hermes dashboard --port 9120 --host 0.0.0.0`

### 8642 — API Server
- **纯 API server**，无前端
- 兼容 OpenAI 协议：`/v1/chat/completions` `/v1/models` 等
- Hermes 内部 API：`/api/sessions` `/health` 等
- 鉴权：header `X-API-Key: $API_SERVER_KEY`
- 启动条件：`.env` 里 `API_SERVER_ENABLED=true`
- **用户在浏览器打 `8642/` → 404 Not Found**（这是正常的，没有 SPA）
- 验证：`curl http://127.0.0.1:8642/health` → `{"status":"ok"}` (0.6ms 响应)

### 用 8642 /health 做服务真活探测 (2026-06-05)

`launchctl list` 显示的 `Status` 列是**上次退出码** (e.g. `-9` = SIGKILL),
不是当前状态 — 单看 `Status` 列会把"刚被重启过但现在活得好好的"服务
误判为死。要真正确认 Gateway 健康, 用 8642 /health:

```bash
# 黄金标准: 3 道防线
GW_PID=$(launchctl list 2>/dev/null | grep -E "^[0-9-]+\s+[0-9-]+\s+ai\.hermes\.gateway$" | awk '{print $1}')
GW_HEALTH=$(curl -sS -o /dev/null -w "%{http_code}" --max-time 3 http://127.0.0.1:8642/health 2>/dev/null || echo "000")
# 真活: PID != "-" && PID > 0 && HEALTH == 200
```

如果 `/health` 200 = Gateway 真活, 不管 launchd 显示什么。
`/health` 0.6ms 响应, 可在 health-check cron 里放心用。
**反例**: 早期 daily_health_check.sh 只看 launchd 状态码 -9, 把
Gateway 误判为 ❌, 实际上 PID 79290 + /health 200 都正常。

### 9333 — Chrome debug
- Hermes 复用的 Chrome 实例在 `--remote-debugging-port=9333`
- **不是给用户访问的** — 是 CDP/WebSocket 端口
- 验证 CDP：`curl http://127.0.0.1:9333/json/version`

## 用户常见困惑（实测 2026-06-04）

### 困惑 1："http://127.0.0.1:9120/chat 正在更新"
**原因**：浏览器记住了旧 URL（某次更新前用过 9120）
**现状**：9120 根本没服务在监听
**解决**：
```
1. 清浏览器缓存（Cmd+Shift+R 硬刷）
2. 改用 http://127.0.0.1:9119/chat
3. 或重新跑 hermes dashboard
```

### 困惑 2："http://127.0.0.1:8642/=404"
**原因**：8642 是 API server，没有前端
**正常响应**：404 Not Found（正确）
**解决**：用 9119 而不是 8642

### 困惑 3："我用网页版升级 hermes 等了很久"
**原因**：`hermes update` 网页入口实际是 9119 的 dashboard
**诊断**：
```bash
lsof -i :9119  # 看 dashboard 在不在跑
lsof -i :8642  # 看 API server 在不在跑
lsof -i :9333  # 看 Chrome debug 在不在
```

## 1 分钟诊断脚本

```bash
# 4 个端口扫一遍
for p in 9119 8642 9120 9333; do
  printf "Port %s: " "$p"
  if lsof -i :$p >/dev/null 2>&1; then
    # 找进程
    proc=$(lsof -i :$p 2>/dev/null | tail -1 | awk '{print $1}')
    echo "UP ($proc)"
  else
    echo "DOWN"
  fi
done
```

输出示例（本机实际状态）：
```
Port 9119: DOWN        ← 用户要的 web dashboard 没跑
Port 8642: UP (python3.14)   ← API server 在跑
Port 9120: DOWN        ← 不存在
Port 9333: UP (Google) ← Chrome debug 在
```

## 启动/重启命令

```bash
# 启动 web dashboard（前台）
hermes dashboard

# 后台启动（nohup）
nohup hermes dashboard --port 9119 > ~/.hermes/logs/dashboard.log 2>&1 &

# 停止所有 dashboard
hermes dashboard --stop

# 看 dashboard 状态
hermes dashboard --status

# 启动/重启 API server（跟 gateway 一起）
hermes gateway restart   # gateway 自带 API server（如果 API_SERVER_ENABLED=true）
```

## 关联

- `hermes-agent` skill — `hermes dashboard` 命令总览（protected skill，不直接改）
- `proactive-execution` 规则1（不主动改）、规则16（不主动改 model 周围的东西）
- 改端口时同时改：`--port` 启动参数 + `~/.hermes/config.yaml` 的 `dashboard.port` + 浏览器收藏夹
- Dashboard 启动时若 `web_dist/index.html` 不存在 → 自动 `npm run build`（要装 node deps）
