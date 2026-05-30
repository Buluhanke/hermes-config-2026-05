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

## 已知坑

### target_id 输出截断 vs /json端点获取
有两种不同的 target_id 截断问题：

**问题A（已修复）**：`dom_tabs()` 输出截断  
`Target.getTargets` CDP 返回的 `targetId` 实际是完整32字符，但 `dom_tabs()` 用 `tid[:12]` 切片输出，导致 `dom_snapshot`/`dom_click` 接收到的ID不完整而报错 "No target with given id found"。

**解法**：修 `dom_tools.py` line 380 附近，将 `[{tid[:12]}...]` 改为 `[{tid}]`。

**问题B**（已在用解法）：`/json` HTTP 端点获取完整 ID  
某些场景下通过 HTTP `http://127.0.0.1:9333/json` 获取 targets 列表，可以同时拿到完整 `id`（32字符）和 `webSocketDebuggerUrl`。

### websockets 版本必须用 15.x
browser_supervisor.py（browser_dialog_tool）依赖 `websockets.asyncio`，需要 **websockets==15.0.1**。
hermes-agent 的 `.venv` (Python 3.13) 需手动安装：
```bash
uv pip install websockets==15.0.1 -p ~/.hermes/hermes-agent/.venv/bin/python
```
dom_tools 用自己的 WS 连接，兼容 12-16 任意版本，不受此影响。

### dispatch() 空参数测试说明
registry.dispatch() 在独立进程中调用工具，环境变量（如 BROWSER_CDP_URL）不传递。因此 `dom_snapshot()` 空跑会报"No CDP endpoint"，但实际 Agent 对话调用时参数会注入，正常工作。这是进程隔离机制，不是故障。

### MCP Chrome 工具 vs dom_tools
MCP chrome (`mcp_chrome_*`) 提供了27个工具，但需要 Chrome 扩展启动端口 12306 的 HTTP 服务器。扩展必须装在 chrome-debug profile 并手动点击 Connect 按钮。

**当前状态**: MCP chrome 工具注册成功但 tool call 失败（端口 12306 无响应）。dom_tools 已覆盖其核心功能，建议优先使用。详细排障过程见 `references/mcp-chrome-debugging.md`。

---

## 文件位置

- **生产工具**: `~/.hermes/hermes-agent/tools/dom_tools.py`
- **验证脚本**: `~/.hermes/hermes-dom-extractor/cdp_ws_client.py`
- **排障参考**: `references/mcp-chrome-debugging.md`