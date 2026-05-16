# browser-use — Local Browser Automation for AI Agents

## Overview
GitHub: https://github.com/browser-use/browser-use (91K Stars)
Category: AI agent web browsing / browser automation
License: Open source (MIT)

## What it does
Makes websites accessible for AI agents — AI controls a real Chrome browser to click links, fill forms, scrape pages, navigate. No cloud API needed for local use.

## Installation

### Prerequisites
- Python >= 3.11 (user has 3.14 ✓)
- `uv` package manager (faster than pip)
- Chromium browser (installed via `uvx browser-use install`)

### Install uv
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Install browser-use
```bash
uv init && uv add browser-use
```

### Install Chromium driver
```bash
uvx browser-use install
```

## Key Capabilities
- Local browser control (no API key required for local use)
- Supports Ollama (local models) — user has qwen2.5:latest on macmini (192.168.0.4)
- Integrates with OpenAI, Anthropic, Google GenAI, Groq, Ollama
- Python >= 3.11 required

## Hermes Integration
已作为 MCP server 注册，工具前缀 `mcp_browser_use_`：

| 工具 | 用途 |
|------|------|
| `browser_navigate` | 打开 URL |
| `browser_get_state` | 获取页面状态+元素列表 |
| `browser_screenshot` | 截图（返回 bytes，不写文件） |
| `browser_click` / `browser_type` | 交互 |
| `browser_scroll` | 滚动 |
| `browser_extract_content` | 提取内容（当前版本不稳定，常返回 No content extracted） |
| `browser_go_back` | 后退 |
| `browser_list_tabs` / `browser_switch_tab` | 多标签页 |

验证命令：
```bash
hermes mcp list                    # 确认 browser_use 状态
hermes tools list | grep browser   # 确认 tools 已启用
```

### 截图的正确获取方式
`browser_screenshot` 返回 JSON 含 `size_bytes` 和 `viewport` 信息，但**不写文件到磁盘**。

若需截图内容用于 `vision_analyze`：
- 调用 `browser_get_state(include_screenshot=true)` 获取 base64 编码截图
- 截图数据直接在返回结果中，不经过文件系统

### 与 Hermes 工具链配合
1. `browser_navigate` → 打开目标页面
2. `browser_get_state` → 查看元素和页面状态
3. `browser_click` / `browser_type` → 交互
4. `browser_get_state(include_screenshot=true)` → 获取截图供 vision 分析

## 1688 反扒警告
browser-use 的 Chrome CDP 自动化**仍被 1688 检测**，和 Playwright 一样返回虚假 HTML。需换 Selenium 或换平台（拼多多/淘宝）。

## Related
- **Browser Use Cloud** (cloud.browser-use.com) — paid SaaS version, free tier = 10 requests only
- **Playwright** (Microsoft) — lower-level browser control, more code needed
- **Puppeteer** (Google) — lower-level Chrome control
