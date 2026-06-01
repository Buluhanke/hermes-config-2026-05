---
name: dom-js-inject
description: Chrome CDP JS注入打标签 — 极速DOM提取 + 精准元素定位。通过CDP WebSocket(9333)连接Chrome，在页面内执行JS给所有可见交互元素打data-hermes-id标签，提取极简元素列表(<500 Token)供LLM决策，然后用精确坐标执行click/fill操作。比browser_snapshot更轻量、比VLM截图更快。依赖chrome-debug实例运行于9333端口。
triggers:
  - 需要提取网页可交互元素列表
  - 需要精准点击/输入而不依赖XPath/CSS selector
  - 发现browser_snapshot返回太慢或token消耗太大
  - 想让LLM直接看到带坐标的精简元素描述
---

## 快速使用

```bash
cd ~/.hermes/hermes-dom-extractor
python3 cdp_ws_client.py              # 列出当前Chrome标签页
python3 cdp_ws_client.py <url>         # 提取指定URL的页面元素
```

## Python API

```python
import asyncio
from hermes_dom_extractor.cdp_ws_client import (
    CDPConnection, list_chrome_tabs, dom_tag_and_extract,
    build_hermes_prompt, dom_click_by_id, dom_fill_by_id
)

async def example():
    tabs = list_chrome_tabs()
    tab = next((t for t in tabs if t['url'].startswith('http')), None)

    cdp = CDPConnection(tab['ws_url'], tab['id'])
    await cdp.connect()

    elements, title, url = await dom_tag_and_extract(cdp)
    prompt = build_hermes_prompt(elements, title, url)
    # prompt 示例:
    # 页面标题: 订单表单
    # 页面URL: https://httpbin.org/forms/post
    # 可交互元素 (共 13 个):
    #   [ID:1] input type=text 文本='custname' @(212,29) 153x21
    #   [ID:13] button type=submit 文本='Submit order' @(54,636) 92x21

    # 执行操作
    await dom_fill_by_id(cdp, hermes_id=1, value='张三', elements=elements)
    await dom_click_by_id(cdp, hermes_id=13, elements=elements)

    await cdp.close()

asyncio.run(example())
```

## 核心优势

| 对比项 | DOM提取(本技能) | browser_snapshot |
|--------|----------------|-----------------|
| Token/页 | ~300-500 | ~2000-5000 |
| 推理速度 | <1秒 | 3-8秒 |
| 定位方式 | data-hermes-id+坐标 | @eN ref |
| 适用场景 | 表单/列表/普通网站 | 复杂动态UI/验证码 |

## 工作流程

1. **Observe**: `dom_tag_and_extract()` → JS注入打标签 + 提取精简元素列表
2. **Think**: LLM阅读prompt，决定要操作哪个元素
3. **Act**: `dom_click_by_id()` / `dom_fill_by_id()` 用精确坐标执行
4. **Loop**: 等待页面渲染 → 重复步骤1

## JS标签注入脚本核心逻辑

```javascript
// 给所有可见交互元素打 data-hermes-id
var els = document.querySelectorAll('a[href], button, input, textarea, select...');
els.forEach(el => {
    if (rect.width > 0 && rect.height > 0 && style.display !== 'none') {
        var uid = counter++;
        el.setAttribute('data-hermes-id', uid);
        // 提取描述: tag, type, text, 坐标
    }
});
```

## 已知限制

- 依赖 Chrome CDP 9333(chrome-debug实例)运行
- Chrome内部页面(chrome://)无法通过CDP访问
- 反爬站点(百度等)可能注入隐藏UI → JS已用getBoundingClientRect过滤零尺寸元素
- iframe内元素需分别连接对应frame的target

## Chrome双实例架构（重要更新 2026-06-03）

**两种完全独立的Chrome运行方式：**

| 实例 | 用途 | 启动方式 | 端口 |
|------|------|---------|------|
| agent-browser Chromium | browser_navigate/click等工具 | hermes-agent自动管理 | 无调试端口 |
| chrome-debug profile | Playwright CDP | 需手动启动launcher | 9333 |

**browser工具Chrome ≠ 用户日常Chrome。** browser_navigate用agent-browser起独立headless Chromium，与用户Chrome完全独立。

**启动chrome-debug Chrome的正确方式：**
```bash
python3 ~/.hermes/scripts/chrome-debug-launcher.py &
# 阻塞运行，保持9333端口
```

## JS标签注入脚本

`~/.hermes/scripts/dom_label.py` — Playwright CDP直连9333：

```bash
python3 ~/.hermes/scripts/dom_label.py inject    # 注入标签+打印元素
python3 ~/.hermes/scripts/dom_label.py click h5  # 点击指定hermes-id
python3 ~/.hermes/scripts/dom_label.py navigate https://www.baidu.com
```

## Playwright CDP接入方式

```python
from playwright.sync_api import sync_playwright
p = sync_playwright().start()
browser = p.chromium.connect_over_cdp('http://localhost:9333')
# CDP endpoint是HTTP URL，不是WebSocket
ctx = browser.contexts[0]
page = ctx.pages[0]  # 默认about:blank，需主动goto
```

## 已知限制

- chrome-debug Chrome是headless，用户看不到页面
- 需在chrome-debug里打开目标页，dom_label才能注入
- MCP chrome bridge不可用，不影响本方案
- agent-browser和Playwright CDP两个通道互不干扰

## 两种使用方式

### 方式1：原生 Agent 工具（生产级，推荐）

`dom_tools.py` 已注册为 Hermes Agent 内置工具，可在 Agent 对话中直接调用：

```
dom_tabs()           → 列出所有Chrome标签页 (target_id, url, title)
dom_snapshot()       → 提取当前活动页面可交互元素，<500 Token
dom_click(hermes_id=N) → 精准点击指定ID元素
dom_fill(hermes_id=N, value="xxx") → 精准填充输入框
```

**环境变量**（必需）：
```bash
export BROWSER_CDP_URL=ws://127.0.0.1:9333
```
写入 `~/.zshrc` 后新session生效。**注意**：`config.yaml` 受保护，不能通过 `browser.cdp_url` 配置。

### 方式2：独立脚本（测试/原型）

```bash
cd ~/.hermes/hermes-dom-extractor
python3 cdp_ws_client.py              # 列出标签页
python3 cdp_ws_client.py <url>         # 提取指定URL元素
```

---

## Chrome debug实例启动脚本

`~/.hermes/scripts/chrome-hermes.sh` — 启动chrome-debug Chrome的正确方式（4个flag缺一不可）：

```bash
#!/bin/bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --user-data-dir="$HOME/.hermes/chrome-debug" \
  --remote-debugging-port=9333 \
  --load-extension="$HOME/.hermes/mcp-chrome-extension" \
  --no-first-run \
  --no-default-browser-check
```

**关键flag说明：**
- `--user-data-dir` — 指定独立的Chrome profile，避免与用户日常Chrome冲突
- `--remote-debugging-port=9333` — 开放CDP调试端口，Playwright/MCP bridge都依赖这个端口
- `--load-extension` — 加载MCP Chrome扩展（即使MCP bridge当前不通，扩展已注册到Chrome）
- `--no-first-run` + `--no-default-browser-check` — 避免Chrome首次运行检查阻塞

**启动后验证：**
```bash
# 端口确认
lsof -i :9333 | grep Chrome

# 页面确认（应为about:blank）
curl -s http://127.0.0.1:9333/json | head -50
```

**注意：** 进程需要在后台保持运行。Chrome退出后9333端口随之关闭。

### MCP Chrome Bridge架构（已废弃，仅供参考）

MCP chrome bridge是4层串接链：
```
Chrome扩展(Native Messaging) → stdio → mcp-chrome-stdio → WebSocket → 9333端口
```

**断点在哪：** Native Messaging层（Chrome扩展未装进chrome-debug），导致整条链失效。

**不修原因：** 修复需要解决Chrome扩展安装+Native Messaging host配置+stdio通信三层问题，收益有限。Playwright CDP直连9333已覆盖所有核心功能。

**相关工具状态：**
- `mcp_chrome_get_windows_and_tabs` → ❌ 失败（bridge断）
- `browser_navigate` → ✅ 正常（走agent-browser独立Chromium）
- `Playwright CDP` → ✅ 正常（直连9333）

## 阿里云盘登录：browser工具 + Playwright CDP 混合用法

**原则：browser_* 工具负责操作，Playwright CDP 负责读token。**

### 正确流程

1. `browser_navigate("https://www.alipan.com/")`
2. `browser_click("登录")` → 弹窗出现（二维码在iframe里）
3. 用户扫码
4. 用 Playwright CDP 读 `localStorage.token` 验证

### 登出并重新登录的正确姿势

token过期时间**不会**因"重新打开登录页"而刷新！用户在已登录状态下再次点击"登录"，Chrome会直接复用旧token，`expire_time`保持不变。

正确操作序列：
1. Playwright 执行 `localStorage.removeItem('token')` + `context.clear_cookies()`
2. `browser_navigate("https://www.alipan.com/")` → 自动跳转登录页
3. 用户扫码
4. 立刻用 Playwright 读token，验证 `expire_time` 是否为**未来时间**

如果expire_time和之前完全一样 = 登录没有刷新token，需重来。

### 阿里云盘iframe弹窗

登录弹窗在iframe里，`browser_snapshot`只能看到iframe外壳，二维码在内部。无需强制进入iframe，等用户扫码即可。

## 已知坑

### 问题A（已修复）：`dom_tabs()` 输出截断
`Target.getTargets` CDP 返回的 `targetId` 实际是完整32字符，但旧版 `dom_tabs()` 用 `tid[:12]` 切片导致ID不完整。

**解法**：修 `dom_tools.py` line 380 附近，将 `[{tid[:12]}...]` 改为 `[{tid}]`。

### 问题B：/json HTTP端点获取完整ID
通过 HTTP `http://127.0.0.1:9333/json` 获取 targets 列表，可同时拿到完整 `id`（32字符）和 `webSocketDebuggerUrl`。

### websockets 版本必须用 15.x
browser_supervisor.py（browser_dialog_tool）依赖 `websockets.asyncio`，需要 **websockets==15.0.1**。
hermes-agent 的 `.venv` (Python 3.13) 需手动安装：
```bash
uv pip install websockets==15.0.1 -p ~/.hermes/hermes-agent/.venv/bin/python
```

### MCP Chrome 工具已废弃
MCP chrome bridge (`mcp-chrome-stdio`) 因Chrome扩展通信架构问题不可用。Playwright CDP接chrome-debug端口已覆盖所有核心功能，无需修复MCP bridge。

---

## 相关文件

- **生产工具**: `~/.hermes/hermes-agent/tools/dom_tools.py`
- **启动脚本**: `scripts/chrome-debug-launcher.py` — 启动chrome-debug Chrome并开放9333端口
- **注入脚本**: `scripts/dom_label.py` — inject/click/navigate三种命令
- **排障参考**: `references/mcp-chrome-debugging.md`
- **阿里云盘token提取**: `references/aliyundrive-token-extraction.md`