#!/usr/bin/env python3
"""
YouTube Channel Monitor — RSS-based new video detection.

Tracks YouTube channels via RSS feeds, maintains a checkpoint file,
and optionally notifies via Telegram when new videos are detected.

Usage:
    python3 monitor_channel.py --add "CHANNEL_URL_OR_ID"
    python3 monitor_channel.py --check-all
    python3 monitor_channel.py --channel "CHANNEL_ID" --check
    python3 monitor_channel.py --list
    python3 monitor_channel.py --remove "CHANNEL_ID"
    python3 monitor_channel.py --resolve "https://www.youtube.com/@username"

Checkpoint: ~/.hermes/youtube-content/channel_checkpoints.json
Notify: set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID env vars, use --notify

Install: pip install feedparser requests
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

try:
    import feedparser
except ImportError:
    print("Error: feedparser not installed. Run: pip install feedparser", file=sys.stderr)
    sys.exit(1)

try:
    import requests
except ImportError:
    print("Error: requests not installed. Run: pip install requests", file=sys.stderr)
    sys.exit(1)

# ── Paths ──────────────────────────────────────────────────────────────────────

SKILL_DIR = Path(__file__).parent.parent
CHECKPOINT_FILE = Path.home() / ".hermes" / "youtube-content" / "channel_checkpoints.json"
CHECKPOINT_FILE.parent.mkdir(parents=True, exist_ok=True)

# ── Helpers ────────────────────────────────────────────────────────────────────

def load_checkpoints() -> dict:
    if CHECKPOINT_FILE.exists():
        with open(CHECKPOINT_FILE) as f:
            return json.load(f)
    return {"channels": {}}

def save_checkpoints(data: dict):
    with open(CHECKPOINT_FILE, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def extract_channel_id(url_or_id: str) -> str | None:
    """
    Accepts:
      - https://www.youtube.com/@username
      - https://www.youtube.com/channel/UCxxxxx
      - https://www.youtube.com/c/customname
      - https://www.youtube.com/user/username
      - https://www.youtube.com/shorts/...
      - Raw UCxxxxx 11-char ID
    Returns the UC-xxxxx channel ID via RSS resolution.
    """
    url_or_id = url_or_id.strip()

    # Already a channel ID
    if re.match(r"^UC[a-zA-Z0-9_-]{21}$", url_or_id):
        return url_or_id

    # YouTube RSS feed for a channel ID
    channel_id_patterns = [
        r"youtube\.com/channel/([a-zA-Z0-9_-]{24})",
        r"youtube\.com/user/([a-zA-Z0-9_-]+)",
        r"youtube\.com/@([a-zA-Z0-9_-]+)",
        r"youtube\.com/c/([a-zA-Z0-9_-]+)",
    ]
    for pattern in channel_id_patterns:
        m = re.search(pattern, url_or_id)
        if m:
            identifier = m.group(1)
            return resolve_channel_id(identifier, pattern_type=pattern)
    return None

def resolve_channel_id(identifier: str, pattern_type: str = None) -> str:
    """
    Resolve a user handle, custom URL, or username to a UC- channel ID
    by fetching the YouTube channel page.
    """
    # Build channel RSS URL directly — YouTube maps @username to UC ID via RSS
    if "@" in identifier or pattern_type and "@" in pattern_type:
        # Try to get the RSS — YouTube redirects /@name to the canonical channel
        # We fetch the page and look for the channel ID meta tag
        try:
            resp = requests.get(
                f"https://www.youtube.com/{identifier}",
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=10,
                allow_redirects=True,
            )
            # Look for channelId in the page meta
            m = re.search(r'"channelId":"(UC[a-zA-Z0-9_-]{21})"', resp.text)
            if m:
                return m.group(1)
            # Fallback: look in canonical URL
            m2 = re.search(r'href="https://www\.youtube\.com/channel/(UC[a-zA-Z0-9_-]{21})"', resp.text)
            if m2:
                return m2.group(1)
        except Exception as e:
            print(f"[warn] Could not resolve @ handle: {e}", file=sys.stderr)

    # For /user/ style, try RSS directly
    rss_url = f"https://www.youtube.com/feeds/videos.xml?user={identifier}"
    try:
        resp = requests.get(rss_url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        m = re.search(r"yt:channelId:(UC[a-zA-Z0-9_-]{21})", resp.text)
        if m:
            return m.group(1)
    except Exception:
        pass

    # For UC IDs already, return as-is
    if re.match(r"^UC[a-zA-Z0-9_-]{21}$", identifier):
        return identifier

    return None

def get_channel_rss(channel_id: str) -> str:
    return f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"

def get_channel_info_from_feed(feed) -> dict:
    """Extract channel name and latest video count from parsed feed."""
    return {
        "title": feed.feed.get("title", "Unknown"),
        "video_count": len(feed.entries),
    }

def check_channel(channel_id: str) -> dict:
    """Fetch RSS, return dict with channel info and entries."""
    rss_url = get_channel_rss(channel_id)
    feed = feedparser.parse(rss_url)
    if feed.bozo:
        return {"error": f"Failed to parse RSS for {channel_id}: {feed.bozo_exception}"}
    info = get_channel_info_from_feed(feed)
    return {
        "channel_id": channel_id,
        "title": info["title"],
        "videos": [
            {
                "video_id": entry.get("id", "").replace("yt:video:", ""),
                "title": entry.get("title", ""),
                "published": entry.get("published", ""),
                "link": entry.get("link", ""),
            }
            for entry in feed.entries
        ],
    }

def diff_new_videos(channel_id: str, current_entries: list, checkpoints: dict) -> list:
    """Return entries newer than the last checkpoint for this channel."""
    last_check = checkpoints["channels"].get(channel_id, {}).get("last_video_id")
    if not last_check:
        # First run: report all videos, mark the newest
        if current_entries:
            return current_entries
        return []
    # Find all videos newer than checkpoint (they appear newest-first in RSS)
    new = []
    for entry in current_entries:
        if entry["video_id"] == last_check:
            break
        new.append(entry)
    return new

def send_telegram(message: str):
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not bot_token or not chat_id:
        print("[warn] TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set, skipping notification", file=sys.stderr)
        return
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    try:
        r = requests.post(url, json={"chat_id": chat_id, "text": message, "parse_mode": "HTML"}, timeout=10)
        if r.status_code != 200:
            print(f"[warn] Telegram API error: {r.status_code} {r.text}", file=sys.stderr)
    except Exception as e:
        print(f"[warn] Telegram notification failed: {e}", file=sys.stderr)

def format_new_videos_message(channel_title: str, new_videos: list) -> str:
    lines = [f"<b>🆕 New videos on: {channel_title}</b>"]
    for v in new_videos:
        lines.append(f"• <a href=\"{v['link']}\">{v['title']}</a>")
    return "\n".join(lines)

# ── Commands ───────────────────────────────────────────────────────────────────

def cmd_add(url_or_id: str):
    channel_id = extract_channel_id(url_or_id)
    if not channel_id:
        print(f"Error: Could not resolve channel ID from: {url_or_id}")
        sys.exit(1)

    data = load_checkpoints()

    # Fetch current feed to get title
    result = check_channel(channel_id)
    if "error" in result:
        print(f"Error: {result['error']}")
        sys.exit(1)

    if channel_id in data["channels"]:
        print(f"Channel already tracked: {result['title']} ({channel_id})")
        return

    data["channels"][channel_id] = {
        "title": result["title"],
        "last_video_id": result["videos"][0]["video_id"] if result["videos"] else None,
        "added_url": url_or_id,
    }
    save_checkpoints(data)
    print(f"✅ Added: {result['title']} ({channel_id})")
    print(f"   Latest video: {result['videos'][0]['title'] if result['videos'] else 'none'}")

def cmd_remove(channel_id_or_url: str):
    channel_id = extract_channel_id(channel_id_or_url)
    data = load_checkpoints()

    # Find by URL or ID
    found = None
    for cid, info in data["channels"].items():
        if cid == channel_id or info.get("added_url", "").strip() == channel_id_or_url.strip():
            found = cid
            break
    if not found:
        print(f"Channel not found in watch list: {channel_id_or_url}")
        sys.exit(1)
    title = data["channels"][found]["title"]
    del data["channels"][found]
    save_checkpoints(data)
    print(f"✅ Removed: {title} ({found})")

def cmd_list():
    data = load_checkpoints()
    if not data["channels"]:
        print("No channels in watch list. Add one with --add CHANNEL_URL")
        return
    print(f"Monitored channels ({len(data['channels'])}):")
    for cid, info in data["channels"].items():
        print(f"  [{cid}] {info['title']}")
        print(f"       Last checked video: {info.get('last_video_id', 'none')}")

def cmd_check(channel_id: str, notify: bool = False):
    data = load_checkpoints()

    # Resolve if needed
    cid = extract_channel_id(channel_id) or channel_id
    if cid not in data["channels"]:
        print(f"Channel not in watch list. Add with --add first.")
        sys.exit(1)

    result = check_channel(cid)
    if "error" in result:
        print(f"Error checking channel: {result['error']}")
        sys.exit(1)

    new_videos = diff_new_videos(cid, result["videos"], data)

    if new_videos:
        print(f"🆕 {len(new_videos)} new video(s) on {result['title']}:")
        for v in new_videos:
            print(f"  • {v['title']} ({v['published']}) — {v['link']}")

        # Update checkpoint
        data["channels"][cid]["last_video_id"] = result["videos"][0]["video_id"]
        save_checkpoints(data)

        if notify:
            msg = format_new_videos_message(result["title"], new_videos)
            send_telegram(msg)
            print("\n📬 Telegram notification sent.")
    else:
        print(f"✅ No new videos on {result['title']}")

def cmd_check_all(notify: bool = False):
    data = load_checkpoints()
    if not data["channels"]:
        print("No channels in watch list. Add one with --add CHANNEL_URL")
        return

    total_new = 0
    for cid in list(data["channels"].keys()):
        result = check_channel(cid)
        if "error" in result:
            print(f"[{cid}] Error: {result['error']}")
            continue
        new_videos = diff_new_videos(cid, result["videos"], data)
        if new_videos:
            print(f"\n🆕 {len(new_videos)} new on {result['title']}:")
            for v in new_videos:
                print(f"  • {v['title']} — {v['link']}")
            data["channels"][cid]["last_video_id"] = result["videos"][0]["video_id"]
            total_new += len(new_videos)
            if notify:
                msg = format_new_videos_message(result["title"], new_videos)
                send_telegram(msg)
        else:
            print(f"✅ {result['title']}: no new videos")

    save_checkpoints(data)
    if total_new > 0 and notify:
        print(f"\n📬 {total_new} new video(s) notified via Telegram.")
    elif not notify:
        print(f"\nRun with --notify to enable Telegram alerts.")

def cmd_resolve(url: str):
    channel_id = extract_channel_id(url)
    if channel_id:
        print(f"Channel ID: {channel_id}")
    else:
        print(f"Could not resolve channel ID from: {url}")
        sys.exit(1)

# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="YouTube Channel Monitor")
    parser.add_argument("--add", metavar="URL_OR_ID", help="Add channel to watch list")
    parser.add_argument("--remove", metavar="URL_OR_ID", help="Remove channel from watch list")
    parser.add_argument("--check", action="store_true", help="Check specific channel for new videos")
    parser.add_argument("--check-all", action="store_true", help="Check all watched channels")
    parser.add_argument("--list", action="store_true", help="List all watched channels")
    parser.add_argument("--resolve", metavar="URL", help="Resolve a YouTube URL to channel ID")
    parser.add_argument("--notify", action="store_true", help="Send Telegram notification for new videos")
    parser.add_argument("--channel", metavar="CHANNEL_ID", help="Channel ID for --check")

    args = parser.parse_args()

    if args.add:
        cmd_add(args.add)
    elif args.remove:
        cmd_remove(args.remove)
    elif args.list:
        cmd_list()
    elif args.check:
        if not args.channel:
            parser.error("--check requires --channel CHANNEL_ID")
        cmd_check(args.channel, notify=args.notify)
    elif args.check_all:
        cmd_check_all(notify=args.notify)
    elif args.resolve:
        cmd_resolve(args.resolve)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
