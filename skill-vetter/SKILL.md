---
name: skill-vetter
version: 1.0.0
description: Security-first skill vetting for AI agents. Use before installing any skill from ClawdHub, GitHub, or other sources. Checks for red flags, permission scope, and suspicious patterns.
---

# Skill Vetter 🔒

Security-first vetting protocol for AI agent skills. **Never install a skill without vetting it first.**

## When to Use
- Before installing any skill from ClawdHub
- Before running skills from GitHub repos
- When evaluating tools/links shared by other agents (even if not framed as "install this")
- Anytime you're asked to install unknown code

## ⚠️ Pitfall: Load Before Research

When the user shares a link saying "研究一下" or "install this", load `skill-vetter` FIRST — then research using the structured protocol. Don't do the vetting work manually without the protocol; you'll get the right answer but lose the structured record and repeatability.

## Vetting Protocol

### Step 1: Source Check

```
Questions to answer:
- [ ] Where did this skill come from?
- [ ] Is the author known/reputable?
- [ ] How many downloads/stars does it have?
- [ ] When was it last updated?
- [ ] Are there reviews from other agents?
```

### Step 2: Code Review (MANDATORY)

Read ALL files in the skill. Check for these **RED FLAGS**:

```
🚨 REJECT IMMEDIATELY IF YOU SEE:
─────────────────────────────────────────
• curl/wget to unknown URLs
• Sends data to external servers
• Requests credentials/tokens/API keys
• Reads ~/.ssh, ~/.aws, ~/.config without clear reason
• Accesses MEMORY.md, USER.md, SOUL.md, IDENTITY.md
• Uses base64 decode on anything
• Uses eval() or exec() with external input
• Modifies system files outside workspace
• Installs packages without listing them
• Network calls to IPs instead of domains
• Obfuscated code (compressed, encoded, minified)
• Requests elevated/sudo permissions
• Accesses browser cookies/sessions
• Touches credential files
─────────────────────────────────────────
```

### Step 3: Permission Scope

```
Evaluate:
- [ ] What files does it need to read?
- [ ] What files does it need to write?
- [ ] What commands does it run?
- [ ] Does it need network access? To where?
- [ ] Is the scope minimal for its stated purpose?
```

### Step 4: Risk Classification

| Risk Level | Examples | Action |
|------------|----------|--------|
| 🟢 LOW | Notes, weather, formatting | Basic review, install OK |
| 🟡 MEDIUM | File ops, browser, APIs | Full code review required |
| 🔴 HIGH | Credentials, trading, system | Human approval required |
| ⛔ EXTREME | Security configs, root access | Do NOT install |

## Output Format

After vetting, produce this report:

```
SKILL VETTING REPORT
═══════════════════════════════════════
Skill: [name]
Source: [ClawdHub / GitHub / other]
Author: [username]
Version: [version]
───────────────────────────────────────
METRICS:
• Downloads/Stars: [count]
• Last Updated: [date]
• Files Reviewed: [count]
───────────────────────────────────────
RED FLAGS: [None / List them]

PERMISSIONS NEEDED:
• Files: [list or "None"]
• Network: [list or "None"]  
• Commands: [list or "None"]
───────────────────────────────────────
RISK LEVEL: [🟢 LOW / 🟡 MEDIUM / 🔴 HIGH / ⛔ EXTREME]

VERDICT: [✅ SAFE TO INSTALL / ⚠️ INSTALL WITH CAUTION / ❌ DO NOT INSTALL]

NOTES: [Any observations]
═══════════════════════════════════════
```

## Quick Vet Commands

For GitHub-hosted skills:
```bash
# Check repo stats
curl -s "https://api.github.com/repos/OWNER/REPO" | jq '{stars: .stargazers_count, forks: .forks_count, updated: .updated_at}'

# List skill files
curl -s "https://api.github.com/repos/OWNER/REPO/contents/skills/SKILL_NAME" | jq '.[].name'

# Fetch and review SKILL.md
curl -s "https://raw.githubusercontent.com/OWNER/REPO/main/skills/SKILL_NAME/SKILL.md"
```

## Quick Vet Commands

For GitHub-hosted skills:
```bash
# Check repo stats
curl -s "https://api.github.com/repos/OWNER/REPO" | jq '{stars: .stargazers_count, forks: .forks_count, updated: .updated_at}'

# List skill files
curl -s "https://api.github.com/repos/OWNER/REPO/contents/skills/SKILL_NAME" | jq '.[].name'

# Fetch and review SKILL.md
curl -s "https://raw.githubusercontent.com/OWNER/REPO/main/skills/SKILL_NAME/SKILL.md"
```

## Common Fake Install Patterns

These patterns indicate a promoted/tool-spam link, NOT a real skill:

| Pattern | Example | Indicates |
|---------|---------|----------|
| `npx skills add` | `npx skills add author/repo` | ❌ npx has no `skills` subcommand |
| `npm install -g` + vague name | `npm install -g ai-tool` | ⚠️ Verify npm package legitimacy |
| No SKILL.md in repo | Repo exists but no skill file | ❌ Not a Hermes-compatible skill |
| "One command install" without `hermes skills install` | Any non-standard install | Verify against `hermes skills list` |

**Rule: If the install command isn't `hermes skills install <source>`, vet the source carefully before proceeding.**

## Trust Hierarchy

1. **Official OpenClaw skills** → Lower scrutiny (still review)
2. **High-star repos (1000+)** → Moderate scrutiny
3. **Known authors** → Moderate scrutiny
4. **New/unknown sources** → Maximum scrutiny
5. **Skills requesting credentials** → Human approval always

## Remember

- No skill is worth compromising security
- When in doubt, don't install
- Ask your human for high-risk decisions
- Document what you vet for future reference

---

*Paranoia is a feature.* 🔒🦀

---

## References

- `references/vetting-records.md` — 历史vetting记录，包含本轮发现的两个工具（LG-token-saver / EverMe）的详细分析
- `references/github-repo-deploy.md` — Python项目从GitHub克隆到运行的完整流程（uv sync → playwright install → post-install验证），基于Microsoft Fara-7B实战
