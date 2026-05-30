# MCP Chrome故障应急方案（2026-06-01）

## 问题
browser工具MCP（mcp_chrome_*）报错：
```
Error calling tool: Failed to connect to MCP server
Error calling tool: ClosedResourceError
```

## 根因
node mcp-chrome-stdio 进程退出，Chrome本身仍在运行。

## 应急方案

### 方案1：重启MCP进程
```bash
ps aux | grep mcp-chrome-stdio
kill <PID>
node /Users/aimac/.local/bin/mcp-chrome-stdio &
```

### 方案2：Playwright CDP绕过MCP（推荐）
Chrome调试端口9333仍然可用，直接用Playwright连接：

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp('http://localhost:9333')
    ctx = browser.contexts[0]
    page = ctx.pages[0]
    page.goto('https://example.com')
    page.click('button#submit')
    page.fill('textarea', 'text')
```

### 备用脚本
`~/.hermes/scripts/browser_cdp.py` — 支持nav/snapshot/click/type/press/screenshot

## 验证
Chrome PID：`ps aux | grep "user-data-dir.*chrome-debug"`
MCP端口：`curl -s http://localhost:12306`
