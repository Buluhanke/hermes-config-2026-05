#!/usr/bin/env python3
"""
monitor_and_notify.py — Blogwatcher automated scan + notification script.

Runs blogwatcher-cli scan, parses output, applies keyword filters,
sends notifications via Telegram / Email / ntfy, and maintains a checkpoint
file to avoid duplicate alerts.

Usage:
    python3 monitor_and_notify.py --check
    python3 monitor_and_notify.py --check --keywords "AI,LLM,Claude" --match-any
    python3 monitor_and_notify.py --check --notify telegram --dry-run
    python3 monitor_and_notify.py --check --notify email --keywords "AI" --match-any

Environment variables (optional, for notifications):
    TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
    SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, EMAIL_FROM, EMAIL_TO
    NTFY_TOPIC, NTFY_SERVER

Checkpoint file: ~/.hermes/blogwatcher/last_check.json
"""

import argparse
import datetime
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional

CHECKPOINT_FILE = Path.home() / ".hermes" / "blogwatcher" / "last_check.json"

# ─── Notification backends ───────────────────────────────────────────────────

def notify_telegram(articles: list[dict]) -> bool:
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not bot_token or not chat_id:
        print("  [telegram] TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID not set, skipping")
        return False

    try:
        import requests
    except ImportError:
        print("  [telegram] requests not installed, skipping")
        return False

    lines = [f"📰 *New Articles ({len(articles)})*" if articles else "📰 No new articles"]
    for a in articles[:10]:  # cap at 10
        lines.append(f"• [{a['blog']}] {a['title']}\n  {a['url']}")
    if len(articles) > 10:
        lines.append(f"\n_…and {len(articles) - 10} more_")

    text = "\n".join(lines)
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{bot_token}/sendMessage",
            json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"},
            timeout=10,
        )
        r.raise_for_status()
        print(f"  [telegram] Sent {len(articles)} article(s)")
        return True
    except Exception as e:
        print(f"  [telegram] Failed: {e}")
        return False


def notify_email(articles: list[dict]) -> bool:
    import smtplib
    from email.message import EmailMessage

    host: str = os.environ.get("SMTP_HOST", "")
    port: int = int(os.environ.get("SMTP_PORT", "587"))
    user: str = os.environ.get("SMTP_USER", "")
    password: str = os.environ.get("SMTP_PASS", "")
    from_addr: str = os.environ.get("EMAIL_FROM", user)
    to_addr: str = os.environ.get("EMAIL_TO", user)

    if not all([host, user, password, to_addr]):
        print("  [email] SMTP env vars incomplete, skipping")
        return False

    lines = [f"New Articles ({len(articles)})" if articles else "No new articles", ""]
    for a in articles:
        lines.append(f"[{a['blog']}] {a['title']}")
        lines.append(f"  {a['url']}")
        lines.append("")

    body = "\n".join(lines)
    msg = EmailMessage()
    msg["Subject"] = f"[Blogwatcher] {len(articles)} new article(s)"
    msg["From"] = from_addr
    msg["To"] = to_addr
    msg.set_content(body)

    try:
        with smtplib.SMTP(host, port) as server:
            server.starttls()
            server.login(user, password)
            server.send_message(msg)
        print(f"  [email] Sent {len(articles)} article(s)")
        return True
    except Exception as e:
        print(f"  [email] Failed: {e}")
        return False


def notify_ntfy(articles: list[dict]) -> bool:
    topic = os.environ.get("NTFY_TOPIC")
    server = os.environ.get("NTFY_SERVER", "https://ntfy.sh")
    if not topic:
        print("  [ntfy] NTFY_TOPIC not set, skipping")
        return False

    try:
        import requests
    except ImportError:
        print("  [ntfy] requests not installed, skipping")
        return False

    if articles:
        lines = [f"📰 {len(articles)} new article(s):"]
        for a in articles[:5]:
            lines.append(f"• [{a['blog']}] {a['title']}")
        if len(articles) > 5:
            lines.append(f"  …and {len(articles) - 5} more")
        body = "\n".join(lines)
    else:
        body = "📰 No new articles"

    try:
        r = requests.post(
            f"{server}/{topic}",
            data=body.encode("utf-8"),
            headers={"Content-Type": "text/plain"},
            timeout=10,
        )
        r.raise_for_status()
        print(f"  [ntfy] Notified {len(articles)} article(s) to topic {topic}")
        return True
    except Exception as e:
        print(f"  [ntfy] Failed: {e}")
        return False


def send_notification(articles: list[dict], channels: list[str]) -> None:
    if not articles and "telegram" in channels:
        # Always send Telegram even for empty (heartbeat)
        channels = [c for c in channels if c != "email"]  # skip email for empty
    for ch in channels:
        if ch == "telegram":
            notify_telegram(articles)
        elif ch == "email":
            if articles:  # skip email for empty
                notify_email(articles)
        elif ch == "ntfy":
            notify_ntfy(articles)


# ─── Checkpoint helpers ───────────────────────────────────────────────────────

def load_checkpoint() -> dict:
    if CHECKPOINT_FILE.exists():
        try:
            return json.loads(CHECKPOINT_FILE.read_text())
        except Exception:
            pass
    return {}


def save_checkpoint(data: dict) -> None:
    CHECKPOINT_FILE.parent.mkdir(parents=True, exist_ok=True)
    CHECKPOINT_FILE.write_text(json.dumps(data, indent=2))


# ─── Keyword filtering ────────────────────────────────────────────────────────

def match_article(article: dict, keywords: list[str], match_any: bool) -> bool:
    """Return True if article matches keyword filter."""
    if not keywords:
        return True
    title = (article.get("title") or "").lower()
    blog = (article.get("blog") or "").lower()
    text = f"{title} {blog}"
    if match_any:
        return any(kw.lower() in text for kw in keywords)
    return all(kw.lower() in text for kw in keywords)


# ─── Parsing ─────────────────────────────────────────────────────────────────

def parse_scan_output(raw: str) -> list[dict]:
    """Parse blogwatcher-cli scan stdout into a list of new article dicts.

    blogwatcher-cli scan produces output like:
      Scanning 3 blog(s)...
      <blank line>
        my-blog
          Source: RSS | Found: 4 | New: 2
      <blank line>
      Found 2 new article(s) total!

    We then run `blogwatcher-cli articles --all` and diff against checkpoint.
    """
    articles = []
    lines = raw.strip().splitlines()
    for line in lines:
        line = line.strip()
        # Skip informational lines
        if not line or line.startswith("Scanning") or line.startswith("Found") or line.startswith("Total"):
            continue
        # Blog entry header: "  blog-name"
        #   or "    Source: RSS | Found: N | New: N"
        if line.startswith("  ") and not line.startswith("    "):
            # Blog name
            current_blog = line.strip()
        elif '"' in line or line.startswith("http"):
            # Could be a URL — parse from articles output instead below
            pass
    return articles


def get_articles_from_cli(all_articles: bool = False) -> list[dict]:
    """Call blogwatcher-cli articles and parse output."""
    cmd = [ "blogwatcher-cli", "articles" ]
    if all_articles:
        cmd.append("--all")
    try:
        raw = subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True)
    except subprocess.CalledProcessError as e:
        print(f"  blogwatcher-cli articles failed: {e}")
        return []
    except FileNotFoundError:
        print("  blogwatcher-cli not found in PATH")
        return []

    articles = []
    current_blog = None
    current_blog_url = None
    current_blog_category = None

    for line in raw.splitlines():
        line_stripped = line.strip()
        if not line_stripped:
            continue

        # Blog header
        if line_stripped.startswith("[") and "] [" in line_stripped and "] Blog:" in line_stripped:
            # Article line: [N] [new] Title
            #    Blog: name
            #    URL: https://...
            #    Published: YYYY-MM-DD
            #    Categories: ...
            m = re.match(r"\[\s*(\d+)\]\s*(?:\[new\])?\s*(.+)", line_stripped)
            if m:
                art_id = m.group(1)
                art_title = m.group(2).strip()
                articles.append({
                    "id": art_id,
                    "title": art_title,
                    "blog": current_blog or "unknown",
                    "url": current_blog_url or "",
                    "published": None,
                    "categories": current_blog_category,
                })
        elif line_stripped.startswith("Blog:"):
            if articles:
                articles[-1]["blog"] = line_stripped[5:].strip()
            else:
                current_blog = line_stripped[5:].strip()
        elif line_stripped.startswith("URL:"):
            if articles:
                articles[-1]["url"] = line_stripped[4:].strip()
        elif line_stripped.startswith("Published:"):
            if articles:
                articles[-1]["published"] = line_stripped[10:].strip()
        elif line_stripped.startswith("Categories:"):
            if articles:
                articles[-1]["categories"] = line_stripped[12:].strip()
        elif not line_stripped.startswith("[") and not line_stripped.startswith("Blog:") and \
             not line_stripped.startswith("URL:") and not line_stripped.startswith("Published:") and \
             not line_stripped.startswith("Categories:") and not line_stripped.startswith("Unread articles") and \
             not line_stripped.startswith("All articles") and not line_stripped.startswith("---"):
            # New blog name (no leading space, not a metadata line)
            if line_stripped and not line_stripped.startswith("("):
                current_blog = line_stripped

    return articles


# ─── Main logic ──────────────────────────────────────────────────────────────

def run_check(args) -> list[dict]:
    checkpoint = load_checkpoint()
    last_scan = checkpoint.get("last_scan")
    now = datetime.datetime.now().isoformat()

    # Run scan
    scan_cmd = ["blogwatcher-cli", "scan"]
    if os.environ.get("BLOGWATCHER_SILENT") == "1":
        scan_cmd.append("--silent")
    try:
        scan_raw = subprocess.check_output(scan_cmd, stderr=subprocess.STDOUT, text=True)
        print(f"blogwatcher-cli scan output:\n{scan_raw}")
    except subprocess.CalledProcessError as e:
        print(f"blogwatcher-cli scan failed: {e}")
        return []
    except FileNotFoundError:
        print("blogwatcher-cli not found in PATH. Install: go install github.com/JulienTant/blogwatcher-cli/cmd/blogwatcher-cli@latest")
        return []

    # Get articles (all, not just unread, to diff)
    all_arts = get_articles_from_cli(all_articles=True)

    # Diff against checkpoint — only truly NEW articles since last run
    known_ids = set(checkpoint.get("seen_ids", []))
    seen_this_run = set()
    new_articles = []
    for art in all_arts:
        art_id = art.get("id", "")
        seen_this_run.add(art_id)
        if art_id not in known_ids:
            new_articles.append(art)

    # Apply keyword filter
    keywords = [k.strip() for k in (args.keywords or "").split(",") if k.strip()]
    if args.keywords and not args.match_any and not args.match_all:
        # Default to match-any if --keywords specified without --match-*
        args.match_any = True

    filtered = [
        a for a in new_articles
        if match_article(a, keywords, getattr(args, "match_any", False))
    ]

    print(f"New articles (before filter): {len(new_articles)}")
    print(f"After keyword filter: {len(filtered)}")
    if keywords:
        print(f"  Keywords: {keywords}, match_any={getattr(args, 'match_any', False)}")

    # Show articles
    if filtered:
        print(f"\nNew articles matching filter:")
        for a in filtered[:20]:
            print(f"  [{a['id']}] [{a['blog']}] {a['title']}")
            print(f"         {a['url']}")
        if len(filtered) > 20:
            print(f"  ... and {len(filtered) - 20} more")
    elif new_articles:
        print(f"\nNew articles found but none matched keyword filter:")
        for a in new_articles[:10]:
            print(f"  [{a['id']}] [{a['blog']}] {a['title']}")

    # Update checkpoint
    save_checkpoint({
        "last_scan": now,
        "seen_ids": list(seen_this_run),
        "last_count": len(new_articles),
    })

    return filtered


# ─── CLI entry point ─────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Blogwatcher scan + notify script")
    parser.add_argument("--check", action="store_true", help="Run scan and check for new articles")
    parser.add_argument("--keywords", type=str, default="", help="Comma-separated keyword list to filter articles")
    parser.add_argument("--match-any", action="store_true", help="Notify if ANY keyword matches (default: all must match)")
    parser.add_argument("--match-all", action="store_true", help="Notify only if ALL keywords match")
    parser.add_argument("--notify", type=str, default="", help="Notification channel(s): telegram,email,ntfy (comma-separated)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be notified without sending")
    parser.add_argument("--force", action="store_true", help="Ignore checkpoint, force full re-scan")

    args = parser.parse_args()

    if not args.check:
        parser.print_help()
        return

    new_arts = run_check(args)

    if args.dry_run:
        print("\n[DRY RUN] Would notify:")
        for a in new_arts[:10]:
            print(f"  [{a['blog']}] {a['title']} — {a['url']}")
        return

    channels = [c.strip() for c in (args.notify or "").split(",") if c.strip()]
    if channels:
        send_notification(new_arts, channels)
    else:
        if new_arts:
            print(f"\nFound {len(new_arts)} new article(s). Use --notify to enable notifications.")
        else:
            print("\nNo new articles.")


if __name__ == "__main__":
    main()
