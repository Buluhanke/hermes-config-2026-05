# agent-reach quickstart (macOS, in Hermes venv)

agent-reach is a CLI that routes across 15+ Chinese/vertical platforms (Twitter, 小红书, B站, Reddit, GitHub, V2EX, YouTube, RSS, Jina Reader, …). It installs into the Hermes venv and auto-registers a skill at `~/.agents/skills/agent-reach/`, so Hermes can invoke it via shell.

## Install

```bash
# The #egg= segment is required — repo has no setup.py egg hint.
pip install -e "git+https://github.com/Panniantong/Agent-Reach#egg=agent-reach"
which agent-reach     # /Users/kk/.hermes/hermes-agent/venv/bin/agent-reach
```

## Doctor (declared channels)

```bash
agent-reach doctor          # text, what works / needs config / not installed
agent-reach doctor --json   # machine-readable
```

`doctor` only reports whether the binary is present and configured. It does **not** probe whether the channel actually works at this network egress. Run the real-probe section below before claiming a channel is "available."

## Configure a per-channel probe (always do this after install)

```bash
# V2EX (public API, almost always works)
curl -s -m 5 "https://www.v2ex.com/api/topics/hot.json" | python3 -c "import sys,json;d=json.loads(sys.stdin.read());print(f'V2EX OK: {len(d)} topics')"

# RSS / Atom (Python feedparser)
python3 -c "import feedparser;d=feedparser.parse('https://hnrss.org/frontpage');print(f'RSS OK: {len(d.entries)} entries')"

# YouTube metadata + subtitles (yt-dlp)
yt-dlp --skip-download --list-subs "https://www.youtube.com/watch?v=jNQXAC9IVRw"

# B站 search API (often blocked at egress IP)
curl -s -G "https://api.bilibili.com/x/web-interface/search/type/v2/search" \
  --data-urlencode "keyword=test" --data-urlencode "search_type=video" \
  -w "B站 HTTP: %{http_code}\n" -o /tmp/bili.json

# Jina Reader (often blocked at Cloudflare-customer egress)
curl -s -m 5 -o /dev/null -w "Jina HTTP: %{http_code}\n" "https://r.jina.ai/https://example.com"
```

A channel reporting ✅ in `doctor` but returning 401/403 in the probe is **egress-IP blocked, not a config issue.** Don't try to fix it; record as blocked.

## Network egress gotcha

Many Chinese / academic services fingerprint datacenter and proxy ASNs (AS20473 = Choopa/Cloudflare customer range, etc.) and return 401/403 to those ranges. Symptoms:

- `agent-reach doctor` says ✅
- `curl` returns 401/403 immediately
- No retry will help

If you see this pattern across multiple channels, the egress IP is the cause, not the agent-reach config.

## Optional channels (require login cookie, install on demand)

The agent-reach install leaves these disabled. Each one needs the user to log into the platform in their real browser, then provide the cookie:

- Twitter / X
- Reddit
- Facebook
- Instagram
- 小红书 (xiaohongshu)
- 雪球 (xueqiu)
- 小宇宙 (xiaoyuzhou podcast)
- LinkedIn

Tell the agent "install X" and it will walk the user through cookie extraction.

## Exa / mcporter (semantic search)

To get a real semantic search backend (not DuckDuckGo), install `mcporter` and add the Exa MCP:

```bash
npm install -g mcporter
mcporter config add exa https://mcp.exa.ai/mcp
```

This requires a working `npm`/`node` (already in `~/.hermes/node/bin/`) and an Exa account. Skip on machines without npm or where the user doesn't need it.

## Tools

- `agent-reach format xhs` — format raw 小红书 note JSON to readable markdown
- `agent-reach transcribe` — local audio transcription (uses ffmpeg + Whisper)
- `agent-reach watch` — poll feeds/sources and surface changes (cron-friendly)

## Files it owns

- `~/.agents/skills/agent-reach/SKILL.md` — auto-generated skill that Hermes loads
- `~/.hermes/hermes-agent/venv/bin/agent-reach` — the binary

Removing agent-reach: `pip uninstall agent-reach -y` (removes binary; the skill folder at `~/.agents/skills/` stays as a stale pointer — delete manually if you want a clean uninstall).