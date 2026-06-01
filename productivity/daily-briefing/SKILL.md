---
name: daily-briefing
description: "AI-powered daily news/information briefing — multi-source aggregation, LLM curation, scheduled delivery. Supports any tool (Horizon, custom scripts) with configurable language, sources, and delivery channels."
version: 1.0.0
author: Hermes
platforms: [macos, linux]
metadata:
  hermes:
    tags: [daily-briefing, news-aggregation, AI-curation, RSS, automation, chinese]
    homepage: https://github.com/aimac/Horizon
---

# Daily Briefing

AI-powered multi-source news aggregation and daily briefing generation. Collects from HackerNews, RSS, Telegram, Reddit, GitHub, and more — then uses an LLM to score, filter, enrich with background knowledge, and produce a formatted daily summary.

## User Preferences

- **Language: Chinese first.** Always configure `languages: ["zh"]` on setup if the tool supports it. Content should default to Chinese (标题、摘要、背景、标签全部中文).
- **Active installation:** Horizon at `~/dev/Horizon/` is the current tool.

## Quick Start

### 1. Install Horizon

```bash
cd ~/dev
git clone https://github.com/aimac/Horizon.git
cd Horizon
uv sync
cp .env.example .env   # add API keys
```

Available API providers: DeepSeek (`DEEPSEEK_API_KEY`), OpenAI, Anthropic, Google Gemini.

### 2. Configure for Chinese

In `data/config.json`:

```json
{
  "ai": {
    "provider": "deepseek",
    "model": "deepseek-chat",
    "api_key_env": "DEEPSEEK_API_KEY",
    "languages": ["zh"],
    "temperature": 0.3,
    "max_tokens": 4096
  }
}
```

`languages: ["zh"]` is the key field. Without it, output defaults to English.

### 3. Run

```bash
uv run horizon
```

Output goes to `data/summaries/horizon-YYYY-MM-DD-zh.md` and `docs/_posts/YYYY-MM-DD-summary-zh.md` (for GitHub Pages).

### 4. Schedule

```bash
cronjob action=create schedule="0 9 * * *" prompt="Run the Horizon daily briefing at ~/dev/Horizon. First ensure the venv is active, then run 'uv run horizon'. Report any errors."
```

## Available Sources

| Source | Config Key | Status |
|--------|-----------|--------|
| HackerNews | `sources.hackernews` | ✅ Default on |
| RSS Feeds | `sources.rss` | ✅ Default on (Simon Willison) |
| Telegram | `sources.telegram` | ❌ Off by default |
| Reddit | `sources.reddit` | ❌ Off by default |
| Twitter/X | `sources.twitter` | ❌ Off by default |
| GitHub | `sources.github` | ❌ Off by default |
| OSS Insight | `sources.ossinsight` | ❌ Off by default |
| OpenBB Finance | `sources.openbb` | ❌ Off by default |

## Delivery Channels

- **Local file:** Always saved to `data/summaries/`
- **GitHub Pages:** Auto-copied to `docs/_posts/`
- **Webhook:** Enable `webhook.enabled = true` and set `webhook.url` for Feishu/DingTalk/Slack/Discord push
- **Hermes cron:** Schedule with cronjob for automated delivery to QQ/Telegram

## Monitoring

Check latest run token usage (printed at end of each run):
```
🧮 Token usage this run: 28418 tokens (input: 23049, output: 5369)
```

## Pitfalls

- **RSS feed failures:** Some feeds (e.g. Simon Willison) may fail with an empty error. This is non-fatal — other sources still work. If all RSS fails, check feed URLs and network access.
- **`languages` field position:** Must be under `ai` in config.json, not at the top level. Check Pydantic schema in `src/models.py`.
- **Entry point:** Use `uv run horizon`, not `python run.py`. The CLI entry point is defined in `pyproject.toml` under `[project.scripts]`.
- **Token budget:** Each run costs ~28K tokens (DeepSeek). With daily scheduling, monitor usage.
- **Chinese RSS feeds are not built-in:** If you want Chinese tech news, add RSS feeds from 36kr, 机器之心, 少数派, or similar manually.
