---
name: hermes-agent
description: "Configure, extend, and troubleshoot Hermes Agent: browser tools, API keys, messaging platforms, and gateway management."
version: 1.0.0
tags: [hermes, browser, setup, troubleshooting]
---

# Hermes Agent — Browser Tool Setup

See: `autonomous-ai-agents/hermes-agent/SKILL.md` (bundled skill) + `references/browser-tool-setup-failures.md`

## Quick Reference

**Browser tools enabled but not working?**

1. Check backend: `grep -E "BROWSERBASE|CAMOFOX" ~/.hermes/.env`
2. Is browserbase key set? → Get one at https://browserbase.com
3. Is camofox running? → `curl http://localhost:9377/health`
4. Is tool enabled? → `hermes tools list | grep browser`

**Decision: Browserbase (API key, cloud) vs Camofox (local, ~300MB download)**

See `references/browser-tool-setup-failures.md` for full failure matrix.
