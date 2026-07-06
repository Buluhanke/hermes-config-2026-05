# browser-harness BU_CDP_WS Bypass（2026-07-07 实测）

## 症状
```
RuntimeError: fatal: CDP WS handshake failed: server rejected WebSocket connection: HTTP 404
```
daemon 连接 `/devtools/browser/` 但 Chrome mirror profile 只有 page targets，导致 WS 握手 404。

## 根因
browser-harness daemon 默认路由到 `browser` target，但 Hermes Chrome mirror (`--user-data-dir=~/.hermes/chrome-profile-mirror`) 没有 browser target，只有 page targets。

## 绕过方案（已验证成功）

### 步骤 1：获取当前 page WS URL
```bash
PAGE_WS=$(curl -s http://127.0.0.1:9222/json/list | python3 -c "
import sys,json
pages=[p for p in json.load(sys.stdin) if p['type']=='page']
print(pages[0]['webSocketDebuggerUrl'] if pages else '')
")
```

### 步骤 2：显式传入 WS URL
```bash
BU_CDP_WS="$PAGE_WS" browser-harness << 'PY'
print(page_info())
PY
```

## 关键发现
- Chrome CDP HTTP (`curl http://127.0.0.1:9222/json/list`) 正常 → page targets 存在
- WS 握手失败是因为 daemon 路由到 browser target 而非 page target
- `BU_CDP_WS` 环境变量强制直连特定 page WS URL，绕过 daemon 路由

## 关联
- Chrome mirror profile PID ~59667，user-data-dir `~/.hermes/chrome-profile-mirror`
- browser-use skill → homebrew 版因 Python 3.14 asyncio 问题损坏，用 browser-harness 替代
