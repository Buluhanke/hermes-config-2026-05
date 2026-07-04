# hermes-agent release history — key facts for "real-humanization" agents

Quick-reference card for the agent's own framework. NOT a mirror of upstream release
notes — only the items that change how we operate day-to-day.

## v0.17.0 "Reach Release" (v2026.6.19) — 2026-06-19

**Tag**: `v2026.6.19` · **Stats**: ~1,475 commits / ~800 merged PRs / 245 contributors / 300+ issues closed since v0.16.0.

### What actually matters for an agent in production

- **`memory` tool atomic batch operations** — `operations` array applies add/replace/remove edits **atomically against the final character budget**. Collapses fragile multi-turn dance into one reliable operation. **Pitfall**: schema fields are `old_text` (not `old_string`); see `verification-before-reporting` Failure 48.
- **iMessage via Photon Spectrum** — `hermes photon login` + device code auth. Replaces BlueBubbles. No Mac relay required. Free to start.
- **Raft agent network integration** — wake-channel bridge; payloads carry only metadata (event IDs, timestamps), never message bodies. Privacy-by-contract.
- **Background/async subagents** — `delegate_task(background=True)` (or default in some builds) returns a handle immediately; result re-enters as a new message when finished. We already use this.
- **WhatsApp Business Cloud API adapter** — Meta first-party hosted, no QR bridge process. Alternative to BlueBubbles/Telegram for high-reliability messaging.
- **Telegram rich text via Bot API 10.1** — better formatting, native markup. On by default with opt-out. Our existing Telegram skill can now use richer formatting.
- **Curator cost optimization** — `curator.consolidate: true` or `hermes curator run --consolidate` opts in. **Zero tokens** for routine background curation (default). Don't waste cycles worrying about curator costs.
- **Full profile builder in dashboard** — browser-based model + skills + MCP server config. Useful for hot-swap experiments.
- **Secure dashboard login** — every token-required endpoint returns 401 behind OAuth gate; websocket auth uses served dashboard token. Stops accidental unauth access.
- **Skills Hub browser rehaul** — Connected hubs, Featured section, full skill previews, security scan on each skill. Use this before installing third-party skills.

### Cross-cuts with our existing SOPs

- **v3.1 跨渠道铁律** (`cross-channel-sop-sync`) gains new enforcement surface: iMessage + WhatsApp Business join Telegram / Discord / Slack / Matrix / Mattermost. The "唯一权威 skill + 自动索引机制" must index these new channels.
- **`proactive-execution`** cron scripts can now safely fire Telegram rich messages without manual formatting.
- **Vision pipeline** (see `hermes-mac-os-agent` Skill 1.6): no changes — Vision兜底 still needed for canvas / WebGL / video; Gemini provider still down per Failure 39/40.

## v0.16.0 "Surface Release" (v2026.6.5) — 2026-06-05

**Tag**: `v2026.6.5` · **Stats**: 874 commits / 542 PRs / 170 contributors / 399 issues closed (2 P0, 62 P1, 16 security).

### Operational impact

- **Hermes Desktop — native Electron app** (macOS/Linux/Windows) — Cmd+K palette, in-app self-update, drag-drop, clipboard image paste. NOT relevant for our headless Mac mini deployment (we run gateway + cron, not desktop). Don't recommend this to users whose Hermes host is the only Mac.
- **Remote Hermes gateway with OAuth / username-password** — connect desktop to remote gateway over WebSocket. No `--insecure` flags. Useful for splitting the laptop (desktop UI) from Mac mini (gateway + agent execution).
- **Full web admin panel** — Channels, MCP catalog with enable/disable, credential management, webhooks, memory config, gateway controls. Single source of truth for channel/MCP config.
- **Simplified Chinese (简体中文) translation** — complete UI across chat / sidebar / settings / command center / cron / messaging / profiles / skills / agents. Built on typed i18n layer.
- **Leaner default skill set** — removed spotify, linear, kanban-codex-lane, debugging-hermes-tui-commands. Optional skills moved out: Baoyu creative set, dspy, subagent-driven-development, minecraft-modpack-server, pokemon-player, hermes-s6-container-supervision. **Implication**: if a skill we depend on is removed in a future release, plan the swap before upgrade.

## Detection / monitoring

Use `scripts/hermes_release_monitor.py` (under `proactive-execution` umbrella) to auto-alert on new releases:

```bash
python3 ~/.hermes/skills/meta/proactive-execution/scripts/hermes_release_monitor.py
# [NEW] NousResearch/hermes-agent → v2026.6.19
#       name: Hermes Agent v0.17.0 (v2026.6.19)
#       published: 2026-06-19T19:39:06Z
# ---
# # Hermes Agent v0.17.0 (v2026.6.19)
# ...
```

State file: `~/.hermes/hermes_release_state.json`. Schedule via cron for daily check.

## Sources

- GitHub API: `https://api.github.com/repos/NousResearch/hermes-agent/releases/latest`
- Full notes: `https://github.com/NousResearch/hermes-agent/releases/tag/v2026.6.19`
- This card last updated: 2026-06-27 (saw v0.17.0 4 days late due to no auto-alert).