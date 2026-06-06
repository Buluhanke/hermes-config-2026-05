# CDP 浏览器自动化 — 环境配置参考

## browser.cdp_url 配置（核心发现，2026-06-04）

### 问题现象
Chrome debug 实例已在 9333 端口运行，`/json/version` 返回正常，但 Hermes 浏览器工具始终连接不到该 Chrome，而是每次都启动后端 headless Chromium。

### 根因
`browser.cdp_url` 配置为空 → Hermes 默认走 `agent-browser`（内置 headless Chromium），完全忽略本地 Chrome debug 实例。

### 修复
在 `config.yaml` 的 `browser:` 小节下添加 `cdp_url`:

```yaml
browser:
  cdp_url: ws://127.0.0.1:9333
```

### 配置生效方式
- 修改 `config.yaml` 后需要重启 gateway（`/restart`）或启动新 session
- 工具链判断顺序（`browser_tool.py` 的 `_get_cdp_override()`）:
  1. `BROWSER_CDP_URL` 环境变量
  2. `browser.cdp_url` in `config.yaml` ← 置空则跳过
  3. 未设置 → 走内置 headless Chromium

### 验证方法
```python
# 方法1: 检查 config.yaml
grep -A2 "^browser:" ~/.hermes/config.yaml

# 方法2: 检查 CDP 连接
curl -s http://127.0.0.1:9333/json/version | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('webSocketDebuggerUrl',''))"

# 方法3: 用 browser_navigate 测试
# cdp_url 正确配置后，browser_navigate 会直接控制本地 Chrome，而非开后端浏览器
```

### Chrome Debug 实例启动（供参考）
```bash
# 用户本地 Chrome 已配置 debug port=9333
# 如果需要重新配置：
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --remote-debugging-port=9333 \
  --user-data-dir=~/.hermes/chrome-debug &

# 确认运行中
curl -s http://127.0.0.1:9333/json/version | grep Browser
```

## CDP 协议端点速查

| 端点 | 路径 | 用途 |
|------|------|------|
| Browser WS URL | `/json/version` → `webSocketDebuggerUrl` | 主连接（格式: `ws://127.0.0.1:9333/devtools/browser/UUID`） |
| Tab 列表 | `/json/pages` 或 `Target.getTargets` | 枚举所有标签页 |
| 页面详情 | `/json/pages` → `id` |Attach 到特定 tab |

**注意:** `/json/windows` 在某些 Chrome 版本返回 404，改用 `/json/pages` 枚举 tab。

## cdp-browser-automation 技能调用前提

1. 确认 `browser.cdp_url: ws://127.0.0.1:9333` 在 config.yaml 中
2. 确认 Chrome debug 实例运行中
3. 6 个 AI 网站已登录（cookies 保留）

满足条件后，`browser_navigate` 等工具直接控制前台 Chrome；不满足则走 headless Chromium（无登录态）。