---
name: blogwatcher
description: "Monitor blogs and RSS/Atom feeds via blogwatcher-cli tool, with automated polling, content filtering, Telegram/Email notifications, and Hermes integration."
version: 3.0.0
author: JulienTant (fork of Hyaxia/blogwatcher) | Extended for Hermes
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [RSS, Blogs, Feed-Reader, Monitoring, Automation, Content-Alert]
    homepage: https://github.com/JulienTant/blogwatcher-cli
prerequisites:
  commands: [blogwatcher-cli]
---

# Blogwatcher Extended

Track blog and RSS/Atom feed updates with the `blogwatcher-cli` tool. This skill extends the base blogwatcher-cli with automated polling, smart content filtering, multi-channel notifications, and Hermes agent integration.

## Installation

Pick one method:

- **Go:** `go install github.com/JulienTant/blogwatcher-cli/cmd/blogwatcher-cli@latest`
- **Docker:** `docker run --rm -v blogwatcher-cli:/data ghcr.io/julientant/blogwatcher-cli`
- **Binary (macOS Apple Silicon):** `curl -sL https://github.com/JulienTant/blogwatcher-cli/releases/latest/download/blogwatcher-cli_darwin_arm64.tar.gz | tar xz -C /usr/local/bin blogwatcher-cli`
- **Binary (macOS Intel):** `curl -sL https://github.com/JulienTant/blogwatcher-cli/releases/latest/download/blogwatcher-cli_darwin_amd64.tar.gz | tar xz -C /usr/local/bin blogwatcher-cli`
- **Binary (Linux amd64):** `curl -sL https://github.com/JulienTant/blogwatcher-cli/releases/latest/download/blogwatcher-cli_linux_amd64.tar.gz | tar xz -C /usr/local/bin blogwatcher-cli`
- **Binary (Linux arm64):** `curl -sL https://github.com/JulienTant/blogwatcher-cli/releases/latest/download/blogwatcher-cli_linux_arm64.tar.gz | tar xz -C /usr/local/bin blogwatcher-cli`

All releases: https://github.com/JulienTant/blogwatcher-cli/releases

---

## Quick Start

```bash
# 1. Add a blog
blogwatcher-cli add "My Blog" https://example.com

# 2. Scan for new articles
blogwatcher-cli scan

# 3. List unread articles
blogwatcher-cli articles

# 4. Mark as read
blogwatcher-cli read 1
```

---

## Core Commands

### Managing blogs

- Add a blog: `blogwatcher-cli add "My Blog" https://example.com`
- Add with explicit feed: `blogwatcher-cli add "My Blog" https://example.com --feed-url https://example.com/feed.xml`
- Add with HTML scraping: `blogwatcher-cli add "My Blog" https://example.com --scrape-selector "article h2 a"`
- Add with category: `blogwatcher-cli add "Dev Blog" https://dev.example.com --category "Engineering"`
- List tracked blogs: `blogwatcher-cli blogs`
- Remove a blog: `blogwatcher-cli remove "My Blog" --yes`
- Import from OPML: `blogwatcher-cli import subscriptions.opml`

### Scanning and reading

- Scan all blogs: `blogwatcher-cli scan`
- Scan one blog: `blogwatcher-cli scan "My Blog"`
- Scan silently (CI/automation): `BLOGWATCHER_SILENT=1 blogwatcher-cli scan`
- List unread articles: `blogwatcher-cli articles`
- List all articles: `blogwatcher-cli articles --all`
- Filter by blog: `blogwatcher-cli articles --blog "My Blog"`
- Filter by category: `blogwatcher-cli articles --category "Engineering"`
- Mark article read: `blogwatcher-cli read 1`
- Mark article unread: `blogwatcher-cli unread 1`
- Mark all read: `blogwatcher-cli read-all`
- Mark all read for a blog: `blogwatcher-cli read-all --blog "My Blog" --yes`

### Environment Variables

| Variable | Description |
|---|---|
| `BLOGWATCHER_DB` | Path to SQLite database file |
| `BLOGWATCHER_WORKERS` | Number of concurrent scan workers (default: 8) |
| `BLOGWATCHER_SILENT` | Only output "scan done" when scanning |
| `BLOGWATCHER_YES` | Skip confirmation prompts |
| `BLOGWATCHER_CATEGORY` | Default filter for articles by category |

---

## Automated Content Monitoring

This section covers automated polling, smart filtering, notifications, and Hermes agent integration.

---

### Automated Polling (cron / launchd)

#### Option 1: cron (Linux/macOS)

```bash
# Run every hour, check all blogs
0 * * * * /usr/local/bin/blogwatcher-cli scan >> ~/.hermes/logs/blogwatcher.log 2>&1

# Run every 30 minutes
*/30 * * * * /usr/local/bin/blogwatcher-cli scan >> ~/.hermes/logs/blogwatcher.log 2>&1

# Run twice daily
0 8,20 * * * /usr/local/bin/blogwatcher-cli scan >> ~/.hermes/logs/blogwatcher.log 2>&1
```

#### Option 2: macOS launchd

Create `~/Library/LaunchAgents/com.hermes.blogwatcher.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.hermes.blogwatcher</string>
  <key>ProgramArguments</key>
  <array>
    <string>/usr/local/bin/blogwatcher-cli</string>
    <string>scan</string>
  </array>
  <key>StartInterval</key>
    <integer>3600</integer>  <!-- seconds (1 hour) -->
  <key>RunAtLoad</key>
    <true/>
  <key>StandardOutPath</key>
    <string>/Users/aimac/.hermes/logs/blogwatcher.log</string>
  <key>StandardErrorPath</key>
    <string>/Users/aimac/.hermes/logs/blogwatcher.log</string>
</dict>
</plist>
```

```bash
# Load the plist
launchctl load ~/Library/LaunchAgents/com.hermes.blogwatcher.plist

# Verify
launchctl list | grep blogwatcher

# Unload to stop
launchctl unload ~/Library/LaunchAgents/com.hermes.blogwatcher.plist
```

---

### Smart Content Filtering & Notification Script

The base `blogwatcher-cli scan` tells you how many new articles exist but does not send notifications. Use the companion script `SKILL_DIR/scripts/monitor_and_notify.py` to bridge this gap.

**Features:**
- Runs `blogwatcher-cli scan` and parses output
- Applies keyword filters (notify only if article title/body matches)
- Sends Telegram / Email / ntfy notifications
- Writes a checkpoint to avoid duplicate alerts
- Designed to run from cron or launchd

**Setup:**
```bash
pip install feedparser requests
```

**Usage:**
```bash
# Check all blogs, notify on any new article
python3 SKILL_DIR/scripts/monitor_and_notify.py --check

# Check with keyword filter (notify only if title contains these words)
python3 SKILL_DIR/scripts/monitor_and_notify.py --check --keywords "AI,LLM,Claude,OpenAI" --match-any

# Check with keyword filter (notify only if title contains ALL keywords)
python3 SKILL_DIR/scripts/monitor_and_notify.py --check --keywords "AI,benchmark" --match-all

# Dry run (show what would be notified without sending)
python3 SKILL_DIR/scripts/monitor_and_notify.py --check --dry-run

# Force re-check even if checkpoint is fresh (ignore cache)
python3 SKILL_DIR/scripts/monitor_and_notify.py --check --force
```

**Telegram Setup:**
```bash
export TELEGRAM_BOT_TOKEN="your-bot-token"
export TELEGRAM_CHAT_ID="your-chat-id"
python3 SKILL_DIR/scripts/monitor_and_notify.py --check --notify telegram
```

**Email Setup (via ssmtp/mail):**
```bash
export SMTP_HOST="smtp.gmail.com"
export SMTP_PORT="587"
export SMTP_USER="you@gmail.com"
export SMTP_PASS="app-password"
export EMAIL_TO="recipient@example.com"
python3 SKILL_DIR/scripts/monitor_and_notify.py --check --notify email
```

**ntfy Setup (self-hosted or ntfy.sh):**
```bash
export NTFY_TOPIC="your-topic-name"
python3 SKILL_DIR/scripts/monitor_and_notify.py --check --notify ntfy
```

**Cron + Notify Example:**
```bash
# Every hour, check blogs, notify via Telegram
0 * * * * /usr/bin/python3 SKILL_DIR/scripts/monitor_and_notify.py --check --notify telegram --keywords "AI,LLM,Claude" --match-any >> ~/.hermes/logs/blogwatcher.log 2>&1
```

---

### Hermes Agent Integration

Use the blogwatcher skill from within Hermes to manage feeds and get summaries of new articles.

#### Adding and Monitoring a Feed

```
User: 帮我监控 Paul Graham 的博客
Agent: blogwatcher-cli add "Paul Graham" http://www.aaronsw.com/face2face/gentlebot.pl?raw=1

User: 扫描一下有哪些新文章
Agent: blogwatcher-cli scan then blogwatcher-cli articles
```

#### Getting New Articles in Context

```
User: 有什么新的技术文章吗？
Agent: > blogwatcher-cli scan
     > blogwatcher-cli articles --category "Engineering"
     (then summarizes new articles for the user)
```

#### Auto-Read on Scan

A typical Hermes automation flow:

```bash
# 1. Scan all feeds
blogwatcher-cli scan

# 2. Show new unread articles with categories
blogwatcher-cli articles

# 3. Filter to a specific interest area
blogwatcher-cli articles --category "AI"

# 4. Open interesting article in browser for reading
# (then mark as read when done)
blogwatcher-cli read <article-id>
```

---

### Advanced: OPML Import & Categorization

Most feed readers (Feedly, Inoreader, NewsBlur) export OPML. Import in bulk:

```bash
# From Feedly/Inoreader export
blogwatcher-cli import ~/Downloads/feedly.opml

# After import, assign categories manually
blogwatcher-cli add "Some Blog" https://example.com --category "Tech"
```

The `--category` flag lets you filter articles later:
```bash
blogwatcher-cli articles --category "Tech"
blogwatcher-cli articles --category "Finance"
blogwatcher-cli articles --category "AI"
```

---

### Automated Polling with Keyword Escalation

Combine blogwatcher with Hermes's proactive capabilities. Place this in a daily cron:

```bash
#!/bin/bash
# ~/.hermes/scripts/daily-blog-check.sh
BLOGWATCHER_SILENT=1 blogwatcher-cli scan
NEW_COUNT=$(blogwatcher-cli articles --category "AI" | grep -c "new" || true)
if [ "$NEW_COUNT" -gt 0 ]; then
  echo "Found $NEW_COUNT new AI articles"
  blogwatcher-cli articles --category "AI"
fi
```

Run with:
```bash
# Every morning at 8am
0 8 * * * /Users/aimac/.hermes/scripts/daily-blog-check.sh >> ~/.hermes/logs/blogwatcher-daily.log 2>&1
```

---

## Notes

- Auto-discovers RSS/Atom feeds from blog homepages when no `--feed-url` is provided.
- Falls back to HTML scraping if RSS fails and `--scrape-selector` is configured.
- Categories from RSS/Atom feeds are stored and can be used to filter articles.
- Import blogs in bulk from OPML files exported by Feedly, Inoreader, NewsBlur, etc.
- Database stored at `~/.blogwatcher-cli/blogwatcher-cli.db` by default (override with `--db` or `BLOGWATCHER_DB`).
- Use `blogwatcher-cli <command> --help` to discover all flags and options.
- For Docker users: mount a persistent volume to preserve the database across container restarts.
