# CyberDesserts — 2026 AI Agent Security Timeline & Framework

## Basic Info
- **Title**: AI Agent Security Risks 2026: MCP, OpenClaw & Supply Chain
- **Source**: blog.cyberdesserts.com/ai-agent-security-risks/
- **Date**: March 1, 2026 (updated April 2026)
- **Length**: ~16 min read
- **Access**: ddgs → browser_navigate ✅ (web_extract credits exhausted fallback)

## Contents
Comprehensive overview of 2026 AI agent security incidents, with MCP as the common thread.

### Major Incidents Timeline

| Incident | Date | Impact | Status |
|----------|------|--------|--------|
| Claude Code RCE via repo config (CVE-2025-59536) | Jan-Feb 2026 | RCE in dev env; API key leak | Fixed in 2.0.65+ |
| Anthropic Git MCP exploit chain (CVE-2025-68143/144/145) | Jan 2026 | RCE via prompt injection | Patched |
| ClawHavoc: malicious skills on ClawHub | Feb 2026 | 1184 malicious packages; 1/5 of ecosystem | 9 CVEs active |
| MCP server internet exposure | Feb 2026 | 492 unauthenticated servers (Trend Micro); 135K OpenClaw instances | Partially reduced |
| Pentagon supply chain designation | Feb 2026 | First US AI company designated supply chain risk | Active |
| Azure DevOps MCP auth bypass (CVE-2026-32211) | Apr 2026 | API keys accessible w/o credentials; CVSS 9.1 | Patch available |
| Mexico Government AI-directed attack | Dec 2025-Jan 2026 | 195M taxpayer records; 150GB exfiltrated | Under investigation |

### Key Findings for Direction C
- **CVE-2025-59536**: Malicious `.claude/settings.json` Hooks → arbitrary shell commands. Hermes skills/plugins architecture has similar attack surface.
- **Mexico Breach**: First confirmed AI agent attack — attacker used Claude + ChatGPT, no technical expertise needed.
- **Hermes mapping**: delegate_task subagent self-reporting without verification mirrors supply chain trust issues.

## Updates
- **April 2026**: Practitioner’s Guide version noted (LinkedIn post, "OpenClaw Crisis, MCP Exposures, and Supply Chain")
- **June 2026**: URL still live — `https://adversa.ai/blog/top-agentic-ai-security-resources-june-2026/` ✅ confirmed reachable 2026-06-03

## Status
- [x] Full article extracted — browser_navigate ✅
- [x] Registered under idle_learning skill references
