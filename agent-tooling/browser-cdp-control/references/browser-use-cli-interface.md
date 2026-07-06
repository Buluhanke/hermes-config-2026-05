# browser-use / browser-harness CLI Interface（2026-07-07 实测）

## 关键发现：接口是 Python heredoc，不是 CLI

**文档描述**：`browser-use open <url>` / `browser-use state` / `browser-use click 5`
**实际接口**：Python heredoc — 所有命令通过 `browser-use << 'PY'\n...PY` 执行 Python 代码

```bash
# ❌ 文档写法（不存在）
browser-use open https://example.com
browser-use state

# ✅ 实际写法
browser-use << 'PY'
print(page_info())
PY
```

## browser-use 与 browser-harness 是同一包

```
browser-use (pypi: browser-use)
browser-harness (pypi: browser-use)
↓ 同一个包，两个入口点
~/.local/bin/browser-use  ← uv tool install --python 3.11 browser-use
~/.local/bin/browser-harness
```

- `browser-use doctor` = `browser-harness doctor`（内部调用同一函数）
- `browser-use << 'PY'` = `browser-harness << 'PY'`
- **homebrew 版本**（`/opt/homebrew/bin/browser-use`）= Python 3.14，asyncio 损坏
- **uv 版本**（`~/.local/bin/browser-use`）= Python 3.11，正常

## 修复 homebrew 版本

```bash
# 卸载 homebrew 损坏版本
# (homebrew uninstall browser-use 报错 "No available formula"，说明不是通过 homebrew 安装的)
# 直接用 uv 重装即可

uv tool uninstall browser-use
uv tool install --python 3.11 browser-use

# 验证
browser-use doctor
# 期望输出：全绿，daemon alive，active browser connections — 1
```

## browser-use Python API 全局函数（已验证）

```python
# 基础
page_info()          # {'url': ..., 'title': ..., 'w': 1920, 'h': 874, ...}
capture_screenshot()  # 返回截图文件路径，如 /Users/aimac/.config/browser-harness/tmp/shot.png
new_tab(url)         # 打开新标签页
goto_url(url)       # 导航
wait_for_load()     # 等待加载
ensure_real_tab()   # 确保在真实标签页

# 交互
click_at_xy(x, y)   # 坐标点击
type_text(text)      # 输入文本
scroll(direction)    # scroll up/down
fill_input(selector, text)  # 填入 input
upload_file(selector, path) # 上传文件
press_key(key)       # 按键
wait_for_element(selector)  # 等待元素

# 信息
list_tabs()          # 列出所有标签页
current_tab()        # 当前标签页
js(expression)       # 执行 JS
cdp(method, params)  # 原始 CDP 调用

# 远程
start_remote_daemon(name)  # 启动云浏览器 daemon
stop_remote_daemon(name)   # 停止云浏览器
```

## BU_CDP_WS 绕过（daemon 404 问题）

当 daemon 报 `fatal: CDP WS handshake failed: server rejected WebSocket connection: HTTP 404` 时：

```bash
PAGE_WS=$(curl -s http://127.0.0.1:9222/json/list | python3 -c "
import sys,json
pages=[p for p in json.load(sys.stdin) if p['type']=='page']
print(pages[0]['webSocketDebuggerUrl'] if pages else '')
")
BU_CDP_WS="$PAGE_WS" browser-use << 'PY'
print(page_info())
PY
```

## 与 browser-cdp-control 的关系

- `browser-cdp-control`：直接 CDP WebSocket 调用（底层，最灵活）
- `browser-use`：对 CDP 的 Python 包装（通过 browser-harness daemon）
- `browser-use doctor` 是入口诊断命令
- daemon 活跃时，所有 page 操作通过 `browser-use << 'PY'` 进行
