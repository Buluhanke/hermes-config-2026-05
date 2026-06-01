# coasty-ai/open-computer-use — 82% OSWorld Open-Source Platform

**Source**: GitHub coasty-ai/open-computer-use (725+ stars, Apache 2.0)
**Website**: coasty.ai
**Last commit**: 5 days ago (418 commits total, actively maintained)

## Claims
- "State of the Art 82% OSWorld Computer Using Agent"
- "Production-ready. Remote and Local!"

## Architecture
- **Electron desktop app** + Next.js web console
- **Multi-agent orchestration**:
  - Browser agent (search-first navigation, form filling, multi-tab)
  - Terminal agent (command execution, file ops)
  - Desktop agent (mouse/keyboard control, screenshots, CV-based UI detection)
  - Planner agent (task decomposition → sub-agent dispatch)
- **MCP server integration**: compatible with Claude Desktop, Cursor, Windsurf
- Docker-based AI desktop environment

## Limitations
- **Requires coasty.ai API key** — not fully local/offline
- Cloud backend dependency for core intelligence
- SaaS-tiered: free sandbox keys available but limited

## Hermes Relevance
- **Multi-agent planner** architecture mirrors Hermes's delegate_task pattern
- **MCP bridge** approach: if Hermes adds MCP support, could dual-run native delegate_task + MCP
- Computer Vision-based UI detection (not DOM/AX only) — aligns with Hermes vision agent approach
- **Reference architecture** for future multi-agent orchestration patterns
