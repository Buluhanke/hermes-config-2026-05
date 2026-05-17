---
name: autonomous-ai-agents
description: Skills for autonomous AI agents — browser automation, CLI delegation, multi-agent orchestration, and framework integrations
triggers:
  - browser automation for AI agents
  - delegate to claude code / codex / opencode
  - multi-agent workflows
  - uv package manager for AI tools
  - browser-use local setup
  - install from github
  - python 3.13 compatibility issue
  - free claude code proxy
  - NVIDIA NIM free models
version: 1.0.0
---

# Autonomous AI Agents

Skills for building, deploying, and orchestrating autonomous AI agents — frameworks, tool integrations, browser/cloud automation, and multi-agent coordination patterns.

## Tools & Integrations

### Browser Automation
- **browser-use** — Local browser automation for AI agents (91K Stars). No API key needed for local use. Install via `uv add browser-use`, browser driver via `uvx browser-use install`. Works with Ollama (local qwen2.5). → 独立 skill `browser-use`
- **CDP direct control** — When `mcp-chrome-stdio` bridge is down, control local Chrome directly via raw Python WebSocket + CDP. Bypasses the MCP bridge entirely. Includes tab discovery, masked frame encoding, scroll/click/screenshot patterns. → `references/cdp-raw-websocket.md`

### CLI Delegation
- **claude-code**: Delegate to Claude Code CLI
- **codex**: Delegate to OpenAI Codex CLI
- **opencode**: Delegate to OpenCode CLI
- **free-claude-code**: Anthropic-compatible proxy for Claude Code routing to free/cheap backends (NVIDIA NIM, Ollama, LM Studio). Deploys a local proxy at `:8082` with Admin UI for config management. Auth token: `freecc`. → `references/free-claude-code.md`

### Perception Kernel (Hermes 本地感知内核)
- **perception-kernel.md** — 浏览器快照 → 标准化 → 世界状态 → 查询 → 动作 → 验证 → 策略学习完整架构，含真实方法签名和 SiteExplorer 用法
- **references/vlm-screen-understanding.md** — 本地VLM屏幕理解：Ollama + smolvlm2-agentic-gui 输出点击坐标的完整工作流，包含API格式、坐标转换、分辨率获取、集成到perception bridge的路径

### Desktop CUA (Computer Use Agent)
- **TuriX-CUA**: macOS desktop automation via screen capture + vision LLM + pyautogui. 4-slot LLM pipeline (brain/actor/planner/memory). Supports OpenAI-compatible providers. Needs Screen Recording + Accessibility permissions. → `references/turix-cua.md`

### Frameworks
- **dspy**: Declarative LM programs, auto-optimize prompts, RAG
- **huashu-nuwa**: Person creation from name/theme/需求

## Umbrella Scope
This skill governs: agent frameworks, tool integrations that extend agent capabilities (browser, code execution, APIs), multi-agent orchestration patterns, and delegation to external agent processes.

## References
- `references/browser-use.md` — Local browser automation for AI agents (91K Stars, uv install, Ollama compatible)
- `references/agent-browser-runtime.md` — Anti-bot browser runtime: fingerprint consistency, Bezier mouse curves, platform cooldowns, Canvas/Audio noise injection (analyzed 2026-05-17)
- `references/web-access.md` — eze-is web-access Skill 分析存档：CDP Proxy 架构、浏览哲学（目标驱动）、find-url 思路、URL POST body 传输方式、站点经验积累机制。与 Hermes 内置实现的架构对比。
- `references/cdp-raw-websocket.md` — Raw Python WebSocket + CDP control of local Chrome (fallback when MCP bridge is down, tab discovery, scroll/click/screenshot, frame encoding, pitfall: SOCKS proxy + websockets library)

---

## Pitfalls

### MCP Chrome Bridge Is Not The Only Path
**Do not** assume browser control requires the MCP bridge. When the bridge is broken or the session is fresh:
1. Chrome is already running on port 9333 with `--remote-debugging-port`
2. Use raw Python WebSocket + CDP directly (see `references/cdp-raw-websocket.md`)
3. Do NOT try to open a new Chrome window/instance — the existing Chrome profile is already logged in

### AppleScript JavaScript Execution in Chrome
Chrome disables AppleScript-triggered JavaScript by default. To enable: Chrome menu → View → Developer → Allow JavaScript from Apple Events. Without this, `tell application "Google Chrome" to execute javascript` silently fails.
- `references/turix-cua.md` — TuriX-CUA: macOS desktop CUA agent (screen capture → vision LLM → pyautogui). Install, config (OpenAI-compatible providers), permission setup, and pitfalls.
- `references/python-env-issues.md` — Python 3.13兼容性问题（pillow/camal-oasis）、uv sync VIRTUAL_ENV警告、Homebrew超时处理、npm workspaces安装顺序
- `references/install-from-github.md` — GitHub项目快速安装标准流程（克隆→识安装方式→按技术栈安装→后台启动模式）
- `references/free-claude-code.md` — free-claude-code 部署：安装、配置、NVIDIA NIM模型路由、Admin UI、API调试方法
