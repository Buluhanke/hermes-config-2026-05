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
- **Chrome CDP不支持JSON-RPC 2.0** — 发送CDP命令时禁止包含`jsonrpc`字段
  - ❌ `{"jsonrpc": "2.0", "id": 1, "method": "..."}` 会导致`-32600`错误
  - ✅ `{"id": 1, "method": "..."}`
- iframe内元素需分别连接对应frame的target

## Chrome双实例架构（重要更新 2026-06-03）

**两种完全独立的Chrome运行方式：**

| 实例 | 用途 | 启动方式 | 端口 |
|------|------|---------|-----|
| agent-browser Chromium | browser_navigate/click等工具 | hermes-agent自动管理 | 无调试端口 |
| chrome-debug profile | Playwright CDP / 原生CDP | 需手动启动launcher | 9333 |
| 用户真实Chrome (已登录) | computer_use / CDP直连 | 用户日常使用 | 9222 |

**browser工具Chrome ≠ 用户日常Chrome。** browser_navigate用agent-browser起独立headless Chromium，与用户Chrome完全独立。

**关键端口区分：**
- **端口 9222**：用户真实Chrome调试端口（`--remote-debugging-port=9222`），可访问已登录的AI网站会话
- **端口 9333**：独立的chrome-debug profile，无登录态，仅用于dom_tools

**用户真实Chrome (9222) 已验证可用！**（2026-06-01 确认）
```python
# 成功验证：CDP WebSocket 直连用户Chrome (2026-06-01)
ws_url = "ws://127.0.0.1:9222/devtools/page/<tab_id>"
# DOM.getDocument 返回根节点，包含2个子节点
# Page.getLayoutMetrics 返回 clientWidth=1200, clientHeight=864
```

**Hermes Browser (CDP engine) 直连 9222，不走 MCP bridge**
- MCP chrome bridge 报错 `Failed to connect to MCP server` — 不影响
- `browser_navigate("https://www.1688.com")` → 307元素 Accessibility Tree，@eN ref_id可用
- 结论：CDP engine 已是最优方案，不需要等 MCP bridge 修

**读取用户已登录AI网站的正确方式：**
```bash
# 1. 先确认端口
curl http://127.0.0.1:9222/json/version
# 返回: Chrome/148.0.7778.179

# 2. 列出标签页（找到已登录的AI网站标签）
curl http://127.0.0.1:9222/json/list

# 3. 用原生Python WebSocket连接（不依赖Playwright）
python3 << 'EOF'
import websocket, json
tab_id = "<目标标签页ID>"
ws = websocket.create_connection(f"ws://127.0.0.1:9222/devtools/page/{tab_id}", timeout=10)
cmd = {"id": 1, "method": "DOM.getDocument", "params": {"depth": 3}}
ws.send(json.dumps(cmd))
result = json.loads(ws.recv())
print(result)
ws.close()
EOF
```

**computer_use vs CDP直连的选择：**
- `computer_use`：读取用户可见窗口的AX Tree，适合需要用户参与的场景
- CDP WebSocket直连(9222)：纯后台读取，适合自动化场景
- `browser_navigate`：开独立实例，无用户登录态

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

### 问题C（2026-06-01 新增）：Playwright 临时实例不暴露 9333 端口

**现象**：`lsof -i :9333` 无输出，但 `browser_navigate` 能正常控制 Chrome。

**根因**：Hermes agent 的 browser 工具使用 **Playwright 临时 Chrome 实例**（路径 `/var/folders/.../agent-browser-chrome-XXX/`），每次启动是全新临时 profile，不复用，也**不开放外部 CDP 端口**。端口 9333 只有在用户手动启动 `chrome-debug Chrome`（带 `--remote-debugging-port=9333` 参数）时才存在。

**确认方法**：
```bash
# 检查 9333 端口
lsof -i :9333

# 检查 browser 工具实际用的 Chrome 实例
ps aux | grep -i chrome | grep -v grep
# 如果看到 /var/folders/.../agent-browser-chrome-XXX 就是临时实例
```

**解法**：
1. 需要持久化 CDP 访问时，手动启动 chrome-debug Chrome：
   ```bash
   /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
     --user-data-dir="$HOME/.hermes/chrome-debug" \
     --remote-debugging-port=9333 \
     --no-first-run
   ```
2. 然后用 `dom-js-inject` 的 `cdp_ws_client.py` 连接

### 问题G（2026-06-01 新增）：启动用户Chrome调试端口的正确方式

**教训**：不要 kill 用户的 Chrome 进程！重启会丢失所有标签页和登录态。

**错误做法**：
```bash
pkill -f "Google Chrome"  # ❌ 会杀掉用户所有标签页
open -a "Google Chrome" --args --remote-debugging-port=9222  # ❌ open 不接受 --args
```

**正确做法**：
- 如果用户Chrome已在运行 → **直接用它**，不需要重启，配置 `cdp_url: 'http://127.0.0.1:9222'` 即可
- 如果必须新开调试Chrome（用户明确说"可以重启"时）：
```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 \
  --user-data-dir="/Users/aimac/Library/Application Support/Google/Chrome/Default" \
  --no-first-run --no-default-browser-check --remote-allow-origins=*
```

**关键标志**：
- `--remote-allow-origins=*` — 允许 WebSocket 从任何 origin 连接
- `--user-data-dir` 指定用户的 Default profile，保留已登录状态

**读取AI网站对话内容（如ChatGPT、豆包、智谱清言）：用 CDP Runtime.evaluate，不截图**
**读取AI网站对话内容（如ChatGPT、豆包、智谱清言）：用 CDP Runtime.evaluate，不截图**

> ⚠️ **重要发现（2026-06-02）**：大多数现代AI聊天网站（DeepSeek、豆包、ChatGPT等）将对话内容渲染在 Shadow DOM 自定义组件的私有 `shadowRoot` 里。递归遍历 shadowRoot 仍返回空——这些组件使用了更深的 DOM 隔离（custom elements + closed shadowRoot + 虚拟化列表）。

**实战结果（2026-06-02）**：
- DeepSeek：输入文字✅、发送✅、但AI回复 0 节点（Shadow DOM 隔离）
- 豆包：同上的 shadow DOM 隔离
- Grok：同上

**正确解法：不要通过浏览器读取 AI 对话内容，直接调 AI 厂商 API**

```python
# ✅ 正确方案：绕开浏览器，直接调 DeepSeek API
import openai
client = openai.OpenAI(
    api_key="你的DeepSeek API Key",
    base_url="https://api.deepseek.com"
)
response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[{"role": "user", "content": "请用3句话说清楚你是谁"}],
    max_tokens=200
)
print(response.choices[0].message.content)
```

**什么时候用这个 vs. 截图：**
| 场景 | 正确方式 |
|------|---------|
| AI 网站对话（DeepSeek/豆包/Grok等） | **直接调厂商 API**（绕开浏览器） |
| 动态渲染页面（React/Vue SPA） | CDP Runtime.evaluate |
| 页面有验证码/CAPTCHA | browser_vision 截图 |
| 表单/列表/普通网站 | dom_tag_and_extract |

**教训（2026-06-02）**：Shadow DOM + closed shadowRoot 是比预期更深的隔离——**正确战略是不走浏览器这条路**。

### 问题H（2026-06-01 新增）：accessibility Tree 为空的正确解读

**现象**：`Accessibility.getFullAXTree` 返回 0 节点，但 `DOM.getDocument` 正常。

**根因**：React/Vue 单页应用（SPA）渲染时机问题。ChatGPT 等 AI 网站使用客户端渲染，页面加载早期 DOM 几乎为空，accessibility 树也为空。

**验证 CDP 连接是否正常（不依赖 accessibility）**：
```python
import websocket, json, urllib.request

with urllib.request.urlopen('http://127.0.0.1:9222/json/list') as f:
    tabs = json.loads(f.read())
chatgpt_tab = [t for t in tabs if 'chatgpt' in t.get('url','') and t.get('type')=='page'][0]
tab_id = chatgpt_tab['id']

ws = websocket.create_connection(f"ws://127.0.0.1:9222/devtools/page/{tab_id}", timeout=15)
ws.send(json.dumps({"id":99,"method":"Runtime.enable"})); ws.recv()

# 测试1：页面标题
ws.send(json.dumps({"id":2,"method":"Runtime.evaluate","params":{"expression":"document.title","returnByValue":True}}))
print(json.loads(ws.recv()))

# 测试2：DOM根节点
ws.send(json.dumps({"id":3,"method":"DOM.getDocument","params":{"depth":2}}))
result = json.loads(ws.recv())
print(f"根节点: {result['result']['root']['nodeName']}")

ws.close()
```

**结论**：accessibility tree 空白 ≠ CDP 连接失败。CDP HTTP 和 WebSocket 都通才是真通。

### 问题D（2026-06-01 新增）：macOS Chrome Keychain 加密导致 browsercookie 失效

**现象**：`browsercookie` 库调用后超时（60s），无法读取任何 cookie。

**根因**：macOS Chrome 的 cookies 使用 **Apple Safe Storage**（Keychain）加密，密钥绑定用户登录密码。`browsercookie` 底层调用 Chrome 的 JSON 类型文件读取 cookie，但解密时需要访问 Keychain——若 Keychain 处于锁定状态（用户未解锁或使用了独立的 Keychain），解密会一直等待直到超时。

**解法**：
1. **用户手动解锁 Keychain**（一次性）：
   - 打开 `钥匙串访问` → 右键 `登录` Keychain → `锁定"登录"钥匙串` 再 `解锁`
   - 解锁后立即运行 cookie 提取脚本
2. **浏览器扩展导出 Cookie**（推荐）：
   - 安装 `EditThisCookie` 或 `Cookie-Editor` 扩展
   - 登录目标网站后导出 JSON
   - 手动导入到 hermes 可用的位置
3. **在 browser 工具的 Chrome 里重新登录**（最简单）：
   - `browser_navigate` 打开目标网站
   - `browser_click` 登录
   - 用户扫码/输入
   - cookies 会保存在临时 profile 下，当前 session 可用

### 问题E（2026-06-01 新增）：browser_vision API key 无效

**现象**：`browser_vision` 调用返回 "API key not valid"。

**根因**：辅助视觉模型使用的 Gemini API key 配置无效或过期。

**状态**：不影响 DOM 提取（`dom-js-inject` 不依赖 `browser_vision`），但影响屏幕内容理解。

**解法**：见 `hermes-ocr` skill 的降级路径。

### 问题F（2026-06-01 新增）：AI 网站登录墙汇总

| 网站 | 登录要求 | 未登录行为 | 访客可用性 |
|------|---------|-----------|-----------|
| 豆包 (doubao) | 手机号/抖音账号 | 显示"登录"按钮，无法对话 | ❌ 完全阻止 |
| ChatGLM | 手机号注册 | 访客可输入但无回复 | ❌ 需注册 |
| DeepSeek | 手机号注册 | 显示登录页 | ❌ 需注册 |
| Gemini | Google 账号 | 显示登录按钮 | ❌ 需 Google 账号 |
| ChatGPT | OpenAI 账号 | 显示登录按钮 | ❌ 需账号 |
| Grok | X/Twitter 账号 | 显示登录按钮 | ❌ 需账号 |

**结论**：browser 工具的临时 Chrome 实例没有任何 AI 网站的登录态。在 browser 工具里完成一次登录后，当前 session 可用，但重启后失效。

**替代方案**：用 `computer_use` 控制用户真实 Chrome（已打开标签页），可以读取已登录内容，但需要用户可见窗口。详见 `macos-computer-use` skill。
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
- **Shadow DOM 隔离与 AI 对话**: `references/shadow-dom-ai-chat-isolation.md`