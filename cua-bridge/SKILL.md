---
name: cua-bridge
---
name: cua-bridge
description: cua-bridge — 把 cua-driver 包装成可复用 helper 接入 Hermes 工作流。cua-driver 是 TryCua 的 macOS/Windows/Linux 跨平台 GUI 自动化 driver（已在跑 MCP），本 skill 提供 Python 包装层（cua_gui_ops.py 做 GUI 操作 + playwright_extract.py 抓 JS 渲染页面）。触发：GUI 自动化、定时点按钮、JS 渲染页抓取、后台不抢焦点操作 macOS。
version: 2.0.0
created: 2026-06-07
author: hermes
tags:
  - cua
  - computer-use
  - gui-automation
  - mcp
  - browser
  - core
  - bridge
  - playwright
trigger_keywords:
  - 抓 SPA / JS 渲染页 / playwright
  - 操作浏览器 / GUI 自动化 / cua
  - 真实浏览器测试 / headless 抓页
  - 定时 GUI 任务 / 后台点按钮
  - 不抢焦点 / 后台操作 macOS
  - 跨平台桌面操作
---
# cua-bridge — cua-driver + Playwright 接入 Hermes 的桥

## 一句话

把 cua-driver 的 MCP 能力**包成 Python helper**（cua_gui_ops.py 做 GUI 操作），并把 JS 渲染页抓取交给 Playwright（playwright_extract.py）— 避开 cua-driver 走 Chrome AppleScript JS 的天坑。

## v2 重构（2026-06-07）：cua-driver 回到 GUI，Playwright 接抓页

**v1 的失败教训**：
- v1 (cua_extract.py) 想用 cua-driver 抓 JS 渲染页
- 撞了 Chrome "Apple Events 关闭 JavaScript" 的 TCC 坑
- 每次 Chrome 重启/升级都可能回退，要用户改设置 + 重启 Chrome

**v2 的修法**：
- cua-driver 只做**真 GUI 操作**（launch_app/click/hotkey/type_text）— 它做这个很稳
- JS 渲染页抓取走 **Playwright** — 自带 headless chromium，不依赖 AppleScript
- fetch_url.py 加 `--js` 选项自动升级到 Playwright

## cua-driver 现状（2026-06-07 实测）

| 项 | 状态 |
|----|------|
| 二进制 | `~/.local/bin/cua-driver` v0.5.1 |
| GUI App | `/Applications/CuaDriver.app/` |
| 权限 | Accessibility + Screen Recording **全 Granted** |
| MCP server | **正在跑**（Hermes 已接入 `mcp__cua_driver__*` 工具集）|
| 官方 skill pack | ❌ 不识别 hermes_agent（已记入 v1 changelog）|

## 决策表：什么场景用什么（v2 更新）

| 场景 | 用什么 | 为什么 |
|------|--------|--------|
| 普通网页（HTML 静态）| **fetch_url.py** (Trafilatura) | 轻量，5s 出结果 |
| **JS 渲染页面 / SPA** | **playwright_extract.py** (本 skill) | 绕开 Chrome AppleScript JS 坑 |
| **JS 渲染 + 已知结构** | fetch_url.py `--js` | Trafilatura 不够时自动升级到 Playwright |
| 服务端 API（JSON/REST）| curl | 最快 |
| **后台 GUI 操作**（不抢焦点）| **cua_gui_ops.py** (本 skill) | 唯一不抢光标的方案 |
| **GUI 元素点击/输入** | cua_gui_ops.py `click @element` | 用 element_index 不用盲坐标 |
| 前台快速测试 | browser_navigate / Playwright | 抢焦点但快 |
| 跨平台（macOS+Windows+Linux）| cua-driver | 唯一跨 3 平台的 GUI 自动化 |

## 降级链（v2 更新）

```
抓 URL 内容
 ├─ fetch_url.py (Trafilatura)        ← 静态页面主路（5s）
 ├─ fetch_url.py --js                 ← Trafilatura 不够时自动升 Playwright
 ├─ playwright_extract.py             ← JS 渲染场景（独立调）
 └─ curl + html2text                  ← 终极兜底（v1 留下）

GUI 操作
 ├─ cua-driver (mcp__cua_driver__*)   ← 后台不抢焦点（首选）
 ├─ cua_gui_ops.py                    ← CLI 包装（脚本/cron 用）
 └─ Playwright/computer_use           ← 前台调试用
```

## 标准调用

### 1. 抓 JS 渲染页面（Playwright）

```bash
~/.hermes/hermes-agent/venv/bin/python ~/.hermes/skills/cua-bridge/scripts/playwright_extract.py "https://app.example.com/dashboard"
```

返回 markdown 正文（article/main 区域）。

### 2. fetch_url 自动升级到 JS 渲染

```bash
# 静态页 Trafilatura；不够时自动用 Playwright
~/.hermes/scripts/fetch_url.py "https://example.com" --js
```

### 3. 后台启动 app + 打开 URL

```bash
# CLI 包装（脚本/cron 用）
~/.hermes/hermes-agent/venv/bin/python ~/.hermes/skills/cua-bridge/scripts/cua_gui_ops.py open-url --url "https://hermes-agent.nousresearch.com"
# → Chrome 后台启动，self_activation_suppressed=true（不抢焦点）
```

### 4. GUI 元素操作（脚本里）

```python
import sys
sys.path.insert(0, "/Users/aimac/.hermes/skills/cua-bridge/scripts")
from cua_gui_ops import launch_app, get_window_state, click, type_text

# 后台开 Chrome
result = launch_app(bundle_id="com.google.Chrome", urls=["https://..."])
pid = result["data"]["pid"]
window_id = result["data"]["windows"][0]["window_id"]

# 拿 AX 树看可点元素
state = get_window_state(pid, window_id)

# 点 element_index
click(pid, window_id, element_index=42)
```

### 5. 接入 search.py（v3.2 已支持自动降级）

```bash
~/.hermes/scripts/search.py "RTX 5090 价格" --js-extract
# 自动：搜 → 拿 top 3 URL → playwright_extract 抓全文
# (--cua-extract 保留为 v3.1 别名，向后兼容)
```

## 已知限制

- **Playwright 需要 chromium**：`~/.hermes/hermes-agent/venv/bin/python -m playwright install chromium`（首次装）
- **cua-driver 调 `page.execute_javascript` 在默认 Chrome 上失败**（AppleScript JS 关闭）—— v2 已弃用此路径，抓页全走 Playwright
- **窗口/焦点**：cua-driver 后台驱动不抢光标；Playwright headless 完全后台

## 维护记录

- **v2.0.0 (2026-06-07)** — 重构：cua-driver 回到 GUI，Playwright 接抓页
  - 新增 `scripts/cua_gui_ops.py`：launch_app/click/hotkey/type_text CLI 包装
  - 新增 `scripts/playwright_extract.py`：headless chromium 抓 JS 渲染页
  - fetch_url.py 加 `--js` 选项：Trafilatura 不够时自动升级到 Playwright
  - search.py v3.1 → v3.2：新增 `--js-extract`，`--cua-extract` 保留为别名
  - 删除 `scripts/cua_extract.py`（撞 Chrome AppleScript JS 天坑）

- **v1.0.0 (2026-06-07 09:08)** — 首版：把 cua-driver MCP 包成 cua_extract.py
  - 已知 broken: Chrome 默认关闭 AppleScript JS，cua-driver 调 page.execute_javascript 失败
  - 未被搜索工作流真正跑通



```python
import sys
sys.path.insert(0, "/Users/aimac/.hermes/skills/cua-bridge/scripts")
from cua_extract import cua_call

# 列应用
r = cua_call("list_apps")
# 抓窗口状态
r = cua_call("get_window_state", pid=53785, window_id=12345)
# 在浏览器里跑 JS
r = cua_call("page", action="execute_javascript", pid=53785,
             javascript="document.title")
```

## 触发词速查

| 你说 | 动作 |
|------|------|
| "抓这个 SPA / 抓 JS 渲染的页面" | `cua_extract.py URL` |
| "用浏览器填这个表单" | cua-driver `page.click_element` + `type_text` |
| "后台帮我点 X 按钮（不抢焦点）" | cua-driver `mcp__cua_driver_click` |
| "截屏 / 看看屏幕上是什么" | cua-driver `mcp__cua_driver_get_window_state` |
| "定时帮我点这个" | cron + cua-bridge script |
| "跨平台 GUI 测试" | cua-driver（MCP）|

## ⚠️ cua_extract.py 已知不工作（2026-06-07 端到端验证翻车）

**症状**：跑 `cua_extract.py "https://example.com"` → 报 `❌ empty_content` 或 600+ 字符的 osascript 错误。

**两个真 bug，叠加触发**：

### Bug 1：CLI 包装层调 `page.execute_javascript` 缺 `window_id`

`scripts/cua_extract.py` 里 `cua_call("page", action="execute_javascript", pid=pid, javascript=js)` 通过 `cua-driver call` CLI 子进程调用时，daemon 报 `Missing required parameter: window_id` ——尽管官方 `describe page` 的 JSON schema 标 `window_id` 不是 required。

**根因**：CLI 包装的 stdin JSON 没有 window_id，daemon 实际验证逻辑比 schema 严。

**临时绕过**：直接用 `mcp__cua_driver_page` MCP 工具（不经过 CLI 包装层）——不用 `--call` 子进程。

### Bug 2：Chrome 默认关闭了 AppleScript JS 执行

绕开 Bug 1 用 MCP 工具后报：
```
"osascript error: ... 'Google Chrome'遇到一个错误: 通过 AppleScript 执行 JavaScript 的功能已关闭。
要开启此功能，请在菜单栏中依次转到'查看'>'开发者'>'允许 Apple 事件中的 JavaScript'。"
```

**这是 Chrome 自身的开关**（不是 cua-driver 的问题），OFF by default，每次 Chrome 升级/重装可能回退。

**绕过方案**（按推荐度）：
1. **优先用 fetch_url (Trafilatura)** ——95% 抓页场景够用，零配置
2. **必须 JS 渲染时**：用 `browser_navigate` 工具直接控制真 Chrome（CDP 路径，不走 AppleScript）
3. **最后才用 cua-driver 抓页**：要求用户先去 Chrome 菜单手动开 AppleScript JS 开关

**降级链（修正后）**：

```
抓 URL 内容（Hermes 默认走这个）
 ├─ fetch_url.py (Trafilatura)         ← 95% 场景首选，零配置
 ├─ browser_navigate + DOM 提取        ← JS 渲染 + 已有 CDP 路径
 └─ cua_extract.py (cua-driver)        ← 最后才用，需 AppleScript JS 开关
```

**search.py `--cua-extract` 选项现状**：脚本里写了但**默认不用**。当前实操：`search.py "X"` 走 fetch_url 路径，质量已够用。

## 反模式

- ❌ 用 `osascript` 或 `open` 调 app ——抢焦点、违反 cua 原则
- ❌ 用 Playwright headless 抓 SPA 内的 macOS 上下文 ——headless 拿不到
- ❌ 不等 `document.readyState === 'complete'` 就抓 ——抓不到 JS 渲染
- ❌ 写坐标点击 ——窗口一动就坏，永远用 `element_index`（AX 树）

## 文件清单

| 路径 | 角色 |
|------|------|
| `~/.hermes/skills/cua-bridge/SKILL.md` | 本文件 |
| `~/.hermes/skills/cua-bridge/scripts/cua_extract.py` | 主 helper：JS 页面抓取 |
| `~/.hermes/skills/cua-bridge/references/scenarios.md` | 实战场景速查 |
| `~/.hermes/skills/cua-bridge/references/cua-extract-known-broken-2026-06-07.md` | **cua_extract.py 翻车实录 + 2 个 bug + 3 条修复路线** |
| `~/.cua-driver/skills/cua-driver/SKILL.md` | 官方 skill pack（28KB，跨平台核心） |
| `~/.cua-driver/skills/cua-driver/MACOS.md` | 官方 macOS 专门章节 |
| `~/.cua-driver/skills/cua-driver/WEB_APPS.md` | 官方 web app 章节（SPA/浏览器） |

## 安装验证清单

跑下面 3 条，全 OK 才能用：

```bash
# 1. cua-driver 装好
~/.local/bin/cua-driver --version
# → cua-driver 0.5.1

# 2. 权限齐
~/.local/bin/cua-driver permissions status
# → Accessibility: ✅ / Screen Recording: ✅

# 3. 官方 skill pack 装好
~/.local/bin/cua-driver skills status
# → Local skill pack: ✅ installed
# → Hermes 没列在里面是正常的（cua-driver 不识别）
```

## 维护记录

- **v1.1.0 (2026-06-07)** — 端到端验证翻车 + 修正决策表
  - 跑 `cua_extract.py "https://hermes-agent.nousresearch.com/"` 实测 → empty_content
  - **真 bug #1**：`cua-driver call page` CLI 包装层缺 window_id，daemon 验证逻辑比 schema 严
  - **真 bug #2**：Chrome 默认关闭 AppleScript JS 执行（View > Developer > Allow JavaScript from Apple Events）
  - 修正决策表：JS 渲染从 `cua_extract.py` 改成 `browser_navigate` (CDP 路径)
  - 降级链重排：fetch_url 提到第一（零配置），cua_extract 放最后
- **v1.0.0 (2026-06-07)** — 初版
  - 装官方 skill pack（之前是死链）
  - 写 cua_extract.py（用 cua-driver 抓 JS 页面）
  - 写决策表（什么用 cua、什么用 fetch_url、什么用 Playwright）
  - 接入 search.py v3.1（`--cua-extract` 选项预留）
