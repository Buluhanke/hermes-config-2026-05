# Remote Access Skills — Research Findings (2026-07-11)

## Cross-Platform Remote Control Options

| Skill/Project | Stars | Platform | Key Feature | Install |
|---|---|---|---|---|
| **agent-rdp** | 15 (npm 256 installs) | Windows only | RDP协议，Windows自带远程桌面，无需目标装任何软件 | `npm install -g agent-rdp` |
| **vnc-computer-use** (EYHN/vnc) | 6 | 任意有VNC的OS | VNC协议，跨平台（macOS/Linux/Windows） | `pip install vnc-computer-use` |
| **QuickDesk** | 260 | 多平台 | 内置MCP Server，专门AI远程桌面，MIT | 下载安装 |
| **HandsOn** | 2 | macOS/IP-KVM | 统一层，BIOS到桌面，Apache | pip |
| **computer-use skill** | 1.8K | Linux (headless) | Xvfb+XFCE，17种动作，VNC可视化 | npx skills add |
| **GhostDesk** | 134 | 任意 | Docker，AI完整桌面，无需API | Docker |

## Research Pattern Used

1. `find-skills` CLI: `npx skills find <query>` — searches skills.sh registry
2. `web_search_plus` (research mode) — broader internet search for agent ecosystem
3. Combined: CLI finds exact matches; web search finds emerging/newer projects

## Selection Guide

- **对方Windows** → `agent-rdp`（无需装软件，用RDP）
- **对方macOS/Linux/多平台** → `vnc-computer-use`（只需VNC server）
- **对方无头Linux** → `computer-use` skill（Xvfb虚拟桌面）
- **快速跨平台原型** → GhostDesk（Docker一键）
- **AI原生深度集成** → QuickDesk（MCP Server内置）

## Verification Commands

```bash
# agent-rdp
agent-rdp --version  # should print 0.6.5+

# vnc-computer-use
pip show vnc-computer-use  # or: python3 -m pip show vnc-computer-use
```
