# Community Tips for Hermes Agent

*Sources: r/hermesagent, Hermes Atlas, TechJacks Solutions, awesome-hermes-skills, Hermes official docs*

## Key System Behaviors

### Skill Description Truncation to 60 Chars (r/hermesagent, verified Apr 2026)
- Hermes trims ALL skill descriptions to **60 chars** in the system prompt injection
- Optimization: front-load the most essential keywords in first 60 chars of every skill/rule description
- "Hermes trims all skill descriptions to 60 chars in the system prompt — so best practice is to make that description exceptionally terse"
- Applies equally to AGENTS.md rule descriptions

### Curator System (Hermes v0.12.0+, 2026-04-30)
- Automated 7-day evaluation cycle: usage frequency, success rate, execution time, user satisfaction
- Actions: Promote (raise priority), Consolidate (merge duplicates), Archive (move to .archive/)
- Protect critical skills: `hermes skills pin <name>` prevents Curator archive
- Community skills auto-shielded from Curator modification (security boundary)

### MEMORY.md Capacity Truth (2026-07-01 verified)
- Official docs say 2200 chars but 8-12KB is viable
- Real bottleneck: signal-to-noise ratio, not byte count
- Past 12KB triggers compression (merge adjacent sections, remove redundant cron blocks)

## Top 10 Community Skills (2026, ranked by TechJacks Solutions)

| Rank | Name | Type | Category | Key Feature |
|------|------|------|----------|-------------|
| 1 | Anthropic-Cybersecurity-Skills | Community | Security | 750+ MITRE ATT&CK-mapped skills |
| 2 | mission-control | Self-Gen | DevOps | Multi-instance dashboard monitoring |
| 3 | kanban-orchestrator | Self-Gen | Productivity | Persistent kanban boards w/ auto-categorization |
| 4 | memory-hygiene | Self-Gen | Productivity | Automated memory file cleanup on schedule |
| 5 | hermes-skill-factory | Community | Development | Meta-skill: templates + quality scoring |
| 6 | git-workflow | Self-Gen | DevOps | Context-aware commits + auto PR creation |
| 7 | research-synthesizer | Self-Gen | Research | Multi-source research with citation chains |
| 8 | docker-orchestrator | Self-Gen | DevOps | Container lifecycle + resource limits |
| 9 | scheduled-reports | Self-Gen | Productivity | Daily/weekly/monthly activity summaries |
| 10 | platform-bridge | Community | Communication | Cross-platform message routing |

## awesome-hermes-skills Editor's Picks (ZeroPointRepo, 73★)

Top 5 from the curated list (updated Jul 2026):

1. **youtube-full** (🥇 Skill of the Week) — YouTube transcripts, search, channel browsing, playlists. Uses TranscriptAPI.com (15M+/month). Install: `hermes skills install skills-sh/ZeroPointRepo/youtube-skills/skills/youtube-full`

2. **mattpocock/skills** — 15 battle-tested skills from Total TypeScript creator (Matt Pocock, 60k+ newsletter). Key skills: `grill-me` / `grill-with-docs` (interviews agent before writing code), `tdd` (red-green-refactor), `caveman` (cuts 75% token usage). Install: `npx skills@latest add mattpocock/skills`

3. **SkillClaw** (705★) — Auto-evolves, deduplicates, and improves skill library from real session data. Safety: `skillclaw doctor hermes` / `skillclaw restore hermes`

4. **resemble-ai/detect-skill** — Deepfake detection for agents ingesting user-submitted media

5. **hermes-workspace** (500★) — Web-based GUI with chat, terminal, memory browser, skills manager, inspector

## Hermes Atlas Top Skills by GitHub Stars

| Stars | Project | Description |
|-------|---------|-------------|
| 73.9K | nexu-io/open-design | Open-source Claude Design alternative |
| 23.9K | mukul975/Anthropic-Cybersecurity-Skills | 817 structured cybersecurity skills |
| 5.0K | Agents365-ai/drawio-skill | Generate draw.io diagrams from NL |
| 2.1K | conorbronsdon/avoid-ai-writing | Remove AI writing patterns |
| 2.0K | AMAP-ML/SkillClaw | Collective skill evolution |
| 1.5K | wondelai/skills | Cross-platform agent skills |
| 416 | Romanescu11/hermes-skill-factory | Meta-skill: auto-create skills from workflows |
| 310 | ZeroPointRepo/youtube-skills | YouTube transcript API |
| 277 | Cranot/super-hermes | Self-analytical prompting |
| 232 | AkoliteZA/hermes-agent-idea-workflow | Idea-to-spec workflow |

## Recommended Desktop Clients
- **Hermes-One**: New desktop app with some bugs but highly recommended for daily use.
- **hermes-ui**: Second favorite, offers kanban board, todo list, and better readability than the default interface.

## Model & Plugin Strategy
- Use cheaper models (e.g., local Llama, Mistral) with strong harness/plugins to match the quality of Claude Code or Codex.
- Reserve expensive models (GPT-4, Claude 3 Opus) for specific tasks that require top-tier reasoning.
- Hermes has a strong cache hit rate, making it cost-effective when paired with good plugins are well-tuned.

## Skill Building Best Practices
- Before creating a new skill, always check existing plugins and skills (both official and community) to avoid duplication.
- Leverage the Hermes skill ecosystem: many common workflows already have skills on agentskills.io or in the official bundle.
- When building a skill, prefer to extend an existing one rather than starting from scratch.

## Troubleshooting Notes
- If Hermes feels "dumb" in long conversations, consider rotating models or clearing context more frequently.
- OpenClaw may be more token-efficient for certain tasks, but Hermes excels at skill creation and agent orchestration.
- For persistent Ollama issues, look into the `hermes-runtime-fortress` skill which provides auto-restart and health monitoring.