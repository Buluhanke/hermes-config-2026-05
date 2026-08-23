---
name: chrome-cdp-browser-use
description: 用 browser-use + CDP 控制本机 Chrome 浏览器。两条实测可行路径：①干净profile + browser-use（browser-use启动或连接已有）；②真实Chrome窗口 + computer_use直控（需配置 grant_existing_profile）。触发：1688找品、已登录页面操作、逐商品抠规格。
triggers:
  - 控制 Chrome 浏览器
  - 1688 商品详情页
  - 操作已登录的浏览器
  - browser-use + CDP
  - Chrome 远程调试
  - computer_use existing_profile
---

## 两条实测可行工作流（2026-08-17）

### 工作流A：browser-use + 干净 profile（无登录态，适合公开页面）

**Step 1：启动 Chrome 调试实例（干净 profile）**
```bash
# 杀掉所有 Chrome
pkill -9 "Google Chrome"
sleep 1

# 用干净 profile 启动（--bwsi --disable-extensions 避免恢复对话框）
mkdir -p /tmp/chrome-debug
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --user-data-dir=/tmp/chrome-debug \
  --remote-debugging-port=9222 \
  --no-first-run \
  --bwsi \
  --disable-extensions \
  --no-sandbox \
  2>&1 &
```
用 `terminal(background=true)` 方式启动（终端不允许前台 &）。

**Step 2：获取 WebSocket URL 并连接**
```bash
WS=$(curl -s http://127.0.0.1:9222/json/version | python3 -c "import json,sys; print(json.load(sys.stdin)['webSocketDebuggerUrl'])")

BU_CDP_WS=$WS CDP_URL=http://127.0.0.1:9222 browser-use <<'PY'
import time as _t
new_tab('https://detail.1688.com/offer/77107896836.html')
_t.sleep(4)
print(page_info())
PY
```

**Step 3：常用操作**
```python
new_tab('https://...')           # 第一个标签用 new_tab（不是 goto_url）
wait_for_load()                  # 导航后必等
page_info()                      # {title, url, available_actions}
list_tabs()                      # 所有标签
js("document.querySelector(...).click()")  # JS点击
```

---

### 工作流B：computer_use 控制真实 Chrome 窗口（有登录态）

**前提：~/.hermes/config.yaml 已有 `grant_existing_profile: true`**

**Step 1：确保 Chrome 窗口可见且不是 DevTools 面板**
```bash
osascript -e 'activate application "Google Chrome"'
```

**Step 2：找到正确的 window_id（不是 DevTools）**
```
computer_use(action="list_windows")
→ 找 Google Chrome pid=XXX window_id=YYY，title 不是 "DevTools" 的那个
```

**Step 3：绑定 existing_profile**
```
computer_use(action="cua_browser_prepare", pid=XXX, window_id=YYY, profile_mode="existing_profile")
```

**Step 4：直控操作**
```
computer_use capture som        # 获取截图+AX树
computer_use click element=X    # 点击元素
computer_use type text="..."   # 输入文字
```

---

## 已知坑（2026-08-17 实测）

### 坑1：Chrome 带真实 profile 加 --remote-debugging-port 后 DevTools 端口不监听
**原因**：pkill -9 强制杀死 Chrome，重启时"要恢复页面吗"对话框阻塞主窗口初始化，DevTools 端口不打开。

**现象**：`curl http://127.0.0.1:9222/json/version` 返回空，Chrome 进程存在但端口不监听。

**解法**：
- 用干净的独立 profile（/tmp/chrome-debug）代替真实 profile
- 或清除 `~/Library/Application Support/Google/Chrome/Default/Preferences` 中的 `exit_state` 字段后再启动

### 坑2：browser-use 报错 "DevToolsActivePort not found"
**原因**：browser-use daemon 在默认路径找 DevToolsActivePort 文件，但 Chrome 用的是 `--user-data-dir` 指定路径。

**解法**：使用 `BU_CDP_WS` 环境变量直接指定 WebSocket URL，不走 daemon 自动发现：
```bash
WS=$(curl -s http://127.0.0.1:9222/json/version | python3 -c "import json,sys; print(json.load(sys.stdin)['webSocketDebuggerUrl'])")
BU_CDP_WS=$WS browser-use <<'PY'
print(page_info())
PY
```

### 坑3：computer_use existing_profile 报 "no exact New Tab button"
**原因**：绑定的 Chrome 窗口是 DevTools 面板，不是正常浏览器窗口。

**解法**：`list_windows` 中选 title 不是 "DevTools" 的 Chrome window_id。

### 坑4：Chrome 窗口未显示（list_apps 无 windows）
**原因**：Chrome 在后台运行但没有可见窗口。

**解法**：`osascript -e 'activate application "Google Chrome"'` 或 `open -a "Google Chrome"` 激活窗口。

---

## 快速启动命令（复制即用）

```bash
# 1. 一行启动干净 Chrome 调试实例
pkill -9 "Google Chrome"; sleep 1; mkdir -p /tmp/chrome-debug; /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --user-data-dir=/tmp/chrome-debug --remote-debugging-port=9222 --no-first-run --bwsi --disable-extensions --no-sandbox 2>&1 &

# 2. 等待4秒后验证
sleep 4 && curl -s http://127.0.0.1:9222/json/version

# 3. 获取WS URL并执行操作
WS=$(curl -s http://127.0.0.1:9222/json/version | python3 -c "import json,sys; print(json.load(sys.stdin)['webSocketDebuggerUrl'])")
BU_CDP_WS=$WS CDP_URL=http://127.0.0.1:9222 browser-use <<'PY'
import time as _t
new_tab('https://detail.1688.com/offer/77107896836.html')
_t.sleep(4)
print(page_info())
PY
```
