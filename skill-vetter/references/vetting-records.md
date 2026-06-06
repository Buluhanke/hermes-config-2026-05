# Skill Vetting Records

## 2026-06-03 — fathah/hermes-desktop

**Source:** https://github.com/fathah/hermes-desktop

**Metrics:**
- Stars: 5,600+ (rapidly growing)
- Author: fathah (active community contributor)
- Last Updated: Active development (latest commit June 2026)
- License: MIT

**Vetting Result: ✅ SAFE TO INSTALL**

**What it is:**
Desktop GUI companion for Hermes Agent — cross-platform Electron app providing:
- Wizard-based installation (replaces CLI setup)
- Profile management (multi-config isolation)
- Streaming chat UI with token tracking + cost estimation
- 11 LLM providers (OpenRouter, Anthropic, OpenAI, Gemini, Grok, etc.)
- 16 message gateways (Telegram, Discord, Slack, Feishu, WeChat, etc.)
- Cron task builder (15 push targets)
- Memory system (multiple provider support)
- Persona editor, skills browser, Kanban board, Office (Claw3d) 3D dev environment

**Why it's safe:**
- Official Hermes project ecosystem (fathah is Nous Research community member)
- MIT licensed, open source
- Uses official Hermes install script (`~/.hermes` directory)
- No credential exfiltration, no suspicious network calls
- well-structured codebase with tests

**Status:** Cloned to `~/Projects/hermes-desktop`. Study and learn from its architecture — especially the profile isolation mechanism, SSE streaming UI, and multi-provider model configuration management.

---

## 2026-06-03 — user rule: backup before modify

**Signal:** User explicitly stated: "涉及配置好的主体时要备份再修改争就算损坏也可以恢复"

**Rule encoded into:** `skill-vetter` SKILL.md (Pitfall section)

**Definition:**
- Trigger: ANY task that modifies config files (`.env`, `config.yaml`, JSON configs, scripts)
- Action: Always `cp <file> <file>.bak.$(date +%Y%m%d%H%M%S)` BEFORE editing
- If damage occurs: restore from backup immediately
- "争" is likely typo for "正" (correct/properly)

**Verification:** This is now embedded as a pitfall in `skill-vetter`, ensuring future sessions see it when vetting or modifying configs.

---

*Last updated: 2026-06-03*