# Rafter AI Agent Security Timeline 2025-2026

**URL**: https://rafter.so/blog/incidents/ai-agent-security-timeline-2025-2026
**Last updated**: 2026-04-05
**Scan date**: 2026-06-03
**Source type**: Chronological security incident database
**Reliability**: ✅ Verified via browser_navigate + browser_console JS extraction

---

## Unique CVE Coverage (not in other sources)

| CVE | Product | Severity | Vector | Status |
|-----|---------|----------|--------|--------|
| CVE-2026-21852 | Claude Code | High | ANTHROPIC_BASE_URL redirect steals plaintext API keys | Patched Dec 28, 2025 |
| CVE-2025-66414 | MCP TypeScript SDK (<1.24.0) | CVSS 7.6 | DNS rebinding bypasses SOP to reach localhost MCP | Patched (SDK v1.24.0) |
| CVE-2025-68143/44/45 | Anthropic Git MCP Server | High | Command injection / path traversal / info disclosure | Patched |
| CVE-2025-61260 | OpenAI Codex CLI (<0.23.0) | CVSS 9.8 | CODEX_HOME=.codex config redirect → arbitrary MCP tool RCE | Patched Aug 20, 2025 |
| CVE-2026-25253 | OpenClaw | CVSS 8.8 | WebSocket brute-force + auto-approval on localhost gateway | Patched Feb 26, 2026 |

---

## Three Dominant Attack Patterns

### Pattern 1: Config-as-Execution Supply Chain
**Incidents**: Claude Code (3 CVEs), Codex CLI (CVE-2025-61260)

Project configuration files that AI tools trust and execute automatically (`.claude/settings.json`, `.env`, `CODEX_HOME`). The new postinstall script — triggers on project open, not on explicit install.

**Hermes mapping**: skill loading (SKILL.md injection) — files Hermes trusts and executes on load.

### Pattern 2: Localhost Trust Assumption
**Incidents**: ClawJacked (CVE-2026-25253), MCP DNS Rebinding (CVE-2025-66414), MCP Git Server (3 CVEs)

Local services assume connections from 127.0.0.1 are trusted. Exploitable via browser (DNS rebinding, cross-origin WebSocket) or malicious MCP tool calls.

**Hermes mapping**: Gateway `ws://localhost:18789` has no authentication — same architectural flaw as OpenClaw.

### Pattern 3: AI Reading Untrusted Content with Privileged Context
**Incidents**: CamoLeak (CVSS 9.6), RoguePilot, Replit operational failure

AI tools read attacker-controlled input (PR descriptions, env vars, user prompts) while having access to private code, credentials, or destructive capabilities.

**Hermes mapping**: screen content as context (screen_trigger captures screenshots → VLM processes as input) — same pattern.

---

## Hermes Risk Matrix

| Attack Pattern | Hermes Component | Direct Risk | Mitigation |
|----------------|-----------------|------------|------------|
| Config-as-Execution | skill loading | MED — malicious SKILL.md could be injected via poisoned context | Do not load skills from untrusted sources |
| Localhost Trust | gateway ws://localhost:18789 | HIGH — no auth, same as OpenClaw | Already localhost-only; monitor for CVE announcements |
| AI Reading Untrusted | screen_trigger screen capture → VLM | MED — screenshots from untrusted sources | YOLO pre-classifier filters non-business scenes |
| Subagent self-report | delegate_task | MED — subagent executes then reports "recommended not to run" | Add execution verification step |
