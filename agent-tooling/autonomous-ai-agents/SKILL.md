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
---

# Autonomous AI Agents

Skills for building, deploying, and orchestrating autonomous AI agents — frameworks, tool integrations, browser/cloud automation, and multi-agent coordination patterns.

## Tools & Integrations

### Browser Automation
- **browser-use** — Local browser automation for AI agents (91K Stars). No API key needed for local use. Install via `uv add browser-use`, browser driver via `uvx browser-use install`. Works with Ollama (local qwen2.5). → `references/browser-use.md`

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
- `references/turix-cua.md` — TuriX-CUA: macOS desktop CUA agent (screen capture → vision LLM → pyautogui). Install, config (OpenAI-compatible providers), permission setup, and pitfalls.
- `references/python-env-issues.md` — Python 3.13兼容性问题（pillow/camal-oasis）、uv sync VIRTUAL_ENV警告、Homebrew超时处理、npm workspaces安装顺序
- `references/install-from-github.md` — GitHub项目快速安装标准流程（克隆→识安装方式→按技术栈安装→后台启动模式）
- `references/free-claude-code.md` — free-claude-code 部署：安装、配置、NVIDIA NIM模型路由、Admin UI、API调试方法
