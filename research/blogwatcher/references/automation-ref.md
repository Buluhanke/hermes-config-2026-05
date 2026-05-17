# Blogwatcher Automation Reference

## Quick Reference

| Command | Purpose |
|---------|---------|
| `blogwatcher-cli add "Name" https://example.com` | Add a blog/feed |
| `blogwatcher-cli scan` | Scan all blogs for new articles |
| `blogwatcher-cli articles` | List unread articles |
| `blogwatcher-cli import file.opml` | Bulk import from OPML |
| `python3 SKILL_DIR/scripts/monitor_and_notify.py --check --notify telegram` | Automated scan + notification |

## Cron Examples

```bash
# Every hour, log to file
0 * * * * /usr/local/bin/blogwatcher-cli scan >> ~/.hermes/logs/blogwatcher.log 2>&1

# Every hour with notification
0 * * * * /usr/bin/python3 SKILL_DIR/scripts/monitor_and_notify.py --check --notify telegram --keywords "AI,LLM,Claude" --match-any >> ~/.hermes/logs/blogwatcher.log 2>&1

# Daily digest at 8am
0 8 * * * /usr/bin/python3 SKILL_DIR/scripts/monitor_and_notify.py --check --notify email >> ~/.hermes/logs/blogwatcher-daily.log 2>&1
```

## Environment Variables

| Variable | Used By | Description |
|----------|---------|-------------|
| `BLOGWATCHER_DB` | blogwatcher-cli | Path to SQLite database |
| `BLOGWATCHER_WORKERS` | blogwatcher-cli | Concurrent scan workers |
| `BLOGWATCHER_SILENT` | blogwatcher-cli | Suppress progress output |
| `TELEGRAM_BOT_TOKEN` | monitor_and_notify.py | Telegram bot token |
| `TELEGRAM_CHAT_ID` | monitor_and_notify.py | Telegram chat ID |
| `SMTP_HOST` | monitor_and_notify.py | SMTP server hostname |
| `SMTP_PORT` | monitor_and_notify.py | SMTP port (default 587) |
| `SMTP_USER` | monitor_and_notify.py | SMTP username |
| `SMTP_PASS` | monitor_and_notify.py | SMTP password / app password |
| `EMAIL_FROM` | monitor_and_notify.py | From address (default: SMTP_USER) |
| `EMAIL_TO` | monitor_and_notify.py | To address (default: SMTP_USER) |
| `NTFY_TOPIC` | monitor_and_notify.py | ntfy.sh topic name |
| `NTFY_SERVER` | monitor_and_notify.py | ntfy server URL |

## OPML Import

Export from: Feedly, Inoreader, NewsBlur, Tiny Tiny RSS, etc.

```bash
# After exporting from your reader
blogwatcher-cli import ~/Downloads/feedly.opml
```

## Keyword Filtering

```
# Notify only if title contains AI OR LLM OR Claude
monitor_and_notify.py --check --keywords "AI,LLM,Claude" --match-any

# Notify only if title contains BOTH "AI" AND "benchmark"
monitor_and_notify.py --check --keywords "AI,benchmark" --match-all

# Dry run (show what would be notified without sending)
monitor_and_notify.py --check --keywords "AI,LLM" --notify telegram --dry-run
```

## Adding Categories

```bash
blogwatcher-cli add "Paul Graham" http://www.aaronsw.com/face2face/gentlebot.pl?raw=1 --category "Essays"
blogwatcher-cli add "Hacker News" https://news.ycombinator.com/rss --category "Tech"
```

## Related Skills

- `youtube-content` — Monitor YouTube channels (RSS-based, separate system)
- `deep-research` — Deep analysis of content once read
- `llm-wiki` — Save interesting articles to personal knowledge base
