---
name: cua-browser-control
description: "cua_browser binding 工作流：isolated_new 与 existing_profile。"
version: "1.0"
platforms: [macos]
metadata:
  hermes:
    tags: [browser, computer-use, cua-driver, CDP]
---

# cua-browser-control

用 cua-driver 的 cua_browser_* 工具链操作 Chrome/Chromium。

## 架构

```
Layer 1 — computer_use (AX/原生)
  桌面 UI、系统设置、Native 应用窗口
  capture/click/type/scroll，背景执行

Layer 2 — cua_browser_* (CDP 精确绑定)
  浏览器页面内 DOM 操作
  browser_prepare → browser_state → browser_snapshot/navigate/click/type

Layer 3 — browser_* (Hermes browser 工具)
  通用网页读取，无登录态
```

## isolated_new 模式（不需要登录态）

```python
# 1. 启动独立浏览器
computer_use(action="cua_browser_prepare",
             profile_mode="isolated_new", allow_launch=True)

# 2. 枚举窗口找 window_id
computer_use(action="list_windows")

# 3. 精确绑定
computer_use(action="cua_browser_state", pid=<pid>, window_id=<wid>)
# → binding_quality="exact", mutation_allowed=true

# 4. 每次 mutation 前重新 state（tab_id 会变）
computer_use(action="cua_browser_state", pid=<pid>, window_id=<wid>)

# 5. 导航
computer_use(action="cua_browser_navigate",
            pid=<pid>, window_id=<wid>,
            target_id=<tid>, tab_id=<tab_id>,
            url="https://...")

# 6. 点击/输入
computer_use(action="cua_browser_click",
            pid=<pid>, window_id=<wid>,
            target_id=<tid>, tab_id=<tab_id>, ref=<ref>)

computer_use(action="cua_browser_type",
            pid=<pid>, window_id=<wid>,
            target_id=<tid>, tab_id=<tab_id>, ref=<ref>, text="...")
```

## existing_profile 模式（需要登录态）

```python
# 用户需在终端先运行：
# cua-driver browser-approve --existing-profile

computer_use(action="cua_browser_prepare",
             profile_mode="existing_profile",
             pid=<chrome_pid>, window_id=<chrome_wid>, allow_launch=True)
# 后续同 isolated_new
```

## 关键坑点

**tab_id 每次 state 都变**：mutation 前必须重新 cua_browser_state。
收到 `browser_verification_required` 时重新 state 即可。

**地址栏 Return 键**：background 模式失败，用 `delivery_mode="foreground"`。

**existing_profile 授权方式更新**：用户需在 `~/.hermes/config.yaml` 添加：
```yaml
computer_use:
  grant_existing_profile: true
```
然后另一个终端窗口运行 `hermes gateway restart`。

**坑：绑到 DevTools 窗口会报 "no exact New Tab button"**
`cua_browser_prepare` 要求目标窗口有 New Tab 按钮，但 Chrome DevTools 面板没有。`list_windows` 时要找 title **不是** "DevTools" 的那个 Chrome 窗口。如果当前只有 DevTools 窗口，先用 `osascript -e 'activate application "Google Chrome"'` 或在 Chrome 菜单 → 窗口 → 选择一个普通标签页。

**坑：真实 Chrome 带调试端口无法打通**（Mac M4 + Chrome 151）：Chrome 不允许同时运行两个相同 profile 实例，`open -n` 包装会触发「要恢复页面吗」对话框阻塞 DevTools 初始化。用独立干净 profile + 直接 Chrome 二进制启动是唯一可靠方案：
```bash
mkdir -p /tmp/chrome-debug
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --user-data-dir=/tmp/chrome-debug \
  --remote-debugging-port=9222 \
  --no-first-run --bwsi --disable-extensions --no-sandbox &
sleep 5 && curl -s http://127.0.0.1:9222/json/version
```

**坑：browser-use 的 "DevToolsActivePort not found"**
browser-use daemon 在默认路径找 DevToolsActivePort 文件，但 Chrome 用的是 `--user-data-dir` 指定路径。解法是用 `BU_CDP_WS` 环境变量直接指定 WebSocket URL：
```bash
WS=$(curl -s http://127.0.0.1:9222/json/version | python3 -c "import json,sys; print(json.load(sys.stdin)['webSocketDebuggerUrl'])")
BU_CDP_WS=$WS CDP_URL=http://127.0.0.1:9222 browser-use <<'PY'
print(page_info())
PY
```

**isolated_new 无登录态**：独立浏览器是新 profile，需要登录态时必须走 existing_profile。
