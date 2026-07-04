#!/usr/bin/env python3
"""
hermes-agent release monitor — alerts on new GitHub releases.

Catches the gap we hit 2026-06-27: local借鉴清单 stalled at v0.16.0 (2026-06-23)
while upstream shipped v0.17.0 "Reach Release" (2026-06-19). No auto-alert = silent
drift for days. This script closes that loop.

Use:
    python3 hermes_release_monitor.py --repo NousResearch/hermes-agent
    python3 hermes_release_monitor.py --state-file ~/.hermes/hermes_release_state.json

State is persisted to ~/.hermes/hermes_release_state.json (created on first run).
On new release: prints + exits 0. On no change: prints "up to date" + exits 0.
On network/GitHub error: exits 1 with reason.

Ponytail constraints:
    - stdlib only (urllib + json). No `gh` CLI dependency, no PyPI deps.
    - ~60 lines. Single file, no helpers, no class.
    - Configurable repo via argv, default = hermes-agent (the one we care about).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request

DEFAULT_REPO = "NousResearch/hermes-agent"
STATE_FILE = os.path.expanduser("~/.hermes/hermes_release_state.json")
API = "https://api.github.com/repos/{repo}/releases/latest"


def fetch_latest(repo: str) -> dict:
    url = API.format(repo=repo)
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json",
                                                "User-Agent": "hermes-release-monitor"})
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.load(r)


def load_state(path: str) -> dict:
    if not os.path.exists(path):
        return {}
    try:
        return json.load(open(path))
    except (OSError, json.JSONDecodeError):
        return {}


def save_state(path: str, data: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    json.dump(data, open(tmp, "w"), indent=2)
    os.rename(tmp, path)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo", default=DEFAULT_REPO)
    p.add_argument("--state-file", default=STATE_FILE)
    args = p.parse_args()

    try:
        rel = fetch_latest(args.repo)
    except urllib.error.HTTPError as e:
        print(f"[ERROR] GitHub API HTTP {e.code}: {e.reason}", file=sys.stderr)
        return 1
    except urllib.error.URLError as e:
        print(f"[ERROR] network: {e.reason}", file=sys.stderr)
        return 1

    tag = rel["tag_name"]
    name = rel["name"]
    published = rel["published_at"]
    body = (rel.get("body") or "").strip()

    state = load_state(args.state_file)
    last_tag = state.get("last_tag")
    last_seen = state.get("last_seen_at", 0)

    if tag == last_tag:
        print(f"[OK] up to date: {tag} ({published}) — last seen {time.ctime(last_seen)}")
        return 0

    # New release.
    print(f"[NEW] {args.repo} → {tag}")
    print(f"      name: {name}")
    print(f"      published: {published}")
    print("---")
    # First 30 lines of release notes (avoid spam).
    for ln in body.splitlines()[:30]:
        print(ln)
    if len(body.splitlines()) > 30:
        print(f"... ({len(body.splitlines()) - 30} more lines, fetch full: {rel.get('html_url')})")

    save_state(args.state_file, {
        "last_tag": tag,
        "last_seen_at": time.time(),
        "last_name": name,
        "last_published": published,
    })
    return 0


if __name__ == "__main__":
    sys.exit(main())