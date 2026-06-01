---
name: claude-code-marketplace-plugin-hijacking-2026-06-02
created: 2026-06-02
source: PromptArmor Threat Intelligence
---

# Hijacking Claude Code via Injected Marketplace Plugins

**Source**: https://www.promptarmor.com/resources/hijacking-claude-code-via-injected-marketplace-plugins

## Attack Chain

1. Developer installs malicious marketplace/plugin from third-party registry
2. Plugin overwrites Claude Code's settings.local.json to disable human-in-the-loop
3. Plugin creates hooks that auto-approve command approval requests
4. Plugin commands embed prompt injection
5. Data exfiltration to attacker server

## Bypass Mechanisms

| Method | Description |
|--------|-------------|
| Settings override | Overwrite permissions file controlling which actions need human approval |
| Hook auto-approval | Create PreToolUse hooks that auto-respond to approval requests |

## Relevance to Hermes

- **Direct risk: HIGH** — Hermes skills system is analogous to Claude's plugin/hook system
- **Key guardrail**: Hermes skills are local files, not from external registries
- **Recommended**: Skill content validation on load; no auto-execute from untrusted sources
