# Remote Computer Control — Skills Research Findings

> Research date: 2026-07-11  
> Method: `web_search_plus` (research mode) + `skills.sh` CLI (`npx skills find`) + GitHub direct search  
> Verified: vnc-computer-use PyPI package confirmed accessible; pip install timeout on slow network (120s limit)

---

## Top Recommendation: `vnc-computer-use` (simplest, cross-platform)

**Install:** `pip install vnc-computer-use` (or `npx skills add EYHN/vnc --skill vnc`)

**What it does:** CLI that lets an AI agent control any computer via an existing VNC server.  
- Screenshot → AI interprets → sends mouse/keyboard commands back over VNC
- No target-side install beyond a running VNC server
- Works on macOS, Linux, Windows (any OS with VNC)

**Workflow:**
```bash
pip install vnc-computer-use
vnc-computer-use --host <target-ip> --port 5900 --password <vnc-pass>
# then agent loop: screenshot → action → screenshot → action
```

**Source:** github.com/EYHN/vnc · 6 stars · MIT · PyPI: vnc-computer-use

---

## Skills.sh Installable Skills

| Skill | Installs | Platform | Install command |
|-------|----------|----------|---------------|
| `thisnick/agent-rdp@agent-rdp` | 256 | Windows RDP | `npx skills add https://github.com/thisnick/agent-rdp --skill agent-rdp` |
| `EYHN/vnc` (Claude Code) | — | VNC cross-platform | `npx skills add EYHN/vnc --skill vnc` |
| `athola/claude-night-market@computer-control` | 101 | General | skills.sh |
| `a-green-hand-jack/remote-project-control` | 43 | SSH remote project | `npx skills add ... --skill remote-project-control` |

### agent-rdp detail
```
agent-rdp connect --host <ip> -u <user> -p <pass> --enable-win-automation
agent-rdp automate snapshot -i   # get @e refs
agent-rdp automate click "@e5"
agent-rdp automate fill "@e7" "text"
agent-rdp disconnect
```
Windows only. 15 GitHub stars.

---

## GitHub Standalone Projects (no skills.sh skill)

| Project | Stars | Notes |
|---------|-------|-------|
| **barry-ran/QuickDesk** | 260 | First AI-native remote desktop; built-in MCP Server; multi-platform; active development |
| **mayflower/vnc-use** | 8 | LangGraph agent via VNC; supports Gemini 2.5 / Claude Haiku 4.5 |
| **auxten/handson** | 2 | Unified layer: macOS (Peekaboo) + IP-KVM hardware |
| **dev-core-busy/jarvis** | 9 | Linux AI desktop agent; VNC + WhatsApp; Docker-based |

---

## Selection Guide

| Goal | Solution |
|------|---------|
| Simplest, any OS with VNC already running | `pip install vnc-computer-use` |
| Windows target, full GUI automation | `agent-rdp` (npx install) |
| macOS ↔ macOS, built for AI | QuickDesk (MCP native) |
| Operate code on remote servers (no screen) | `remote-project-control` (SSH) |
| Dedicated hardware (PiKVM, NanoKVM) | QuickDesk or HandsOn |

---

## Prerequisites per Approach

| Approach | Target must have |
|----------|-----------------|
| vnc-computer-use | VNC server running + network access to VNC port |
| agent-rdp | Windows Remote Desktop enabled + credentials |
| QuickDesk | QuickDesk app installed + running |
| QuickDesk MCP | QuickDesk running as MCP server |

---

## Key Pitfalls

- **pip install timeout**: vnc-computer-use install can timeout on slow network → use `--timeout 120` or try npm alternative
- **VNC server required**: vnc-computer-use cannot start VNC on target, target must already have it running
- **Windows only for RDP**: agent-rdp uses RDP protocol, won't work with macOS/Linux
- **QuickDesk active development**: releases may lag; check GitHub for latest build
- **web_extract GitHub blocked**: GitHub requires `browser_navigate` or `curl` directly; web_extract returns Unauthorized
