# Telegram Cron Push — env vars & recipe

Reference captured from `hermes-task-watchdog` cron runs. Save here so the next cron author doesn't re-discover these.

**Last revised: 2026-06-28 14:31 (v1.7.0).** The "Why not `hermes send`?" stance from v1.6.0 has been **reversed** for this user's current setup — `hermes send` is now the preferred path; curl is the fallback.

## Decision table: `hermes send` vs curl

Default to **`hermes send`** when gateway is up. Fall back to curl only if `hermes send` exits non-zero.

### Preferred path — `hermes send`
```bash
hermes send --to telegram "🚨 任务 [...] 停滞 143 分钟，是否需要干预？"
# Success → stdout: "Sent to telegram home channel (chat_id: 7359677525)"
# Exit code 0 = success, 1 = delivery/backend error, 2 = usage error
```

**Why this works in cron** (this user's setup): `hermes send` resolves creds via the user's profile config, not cron shell env. As long as the gateway is up (`pgrep -f hermes` returns ≥1 pid) and the target chat is configured in the profile, delivery succeeds. Sourcing `~/.hermes/.env` and hand-crafting curl is therefore redundant.

### Fallback path — curl with sourced env
Use only when `hermes send` exits non-zero. Recipe unchanged from v1.6.0:
```bash
set -a; source ~/.hermes/.env 2>/dev/null; set +a
BOT="${TELEGRAM_BOT_TOKEN:-}"
CHAT="${TELEGRAM_HOME_CHANNEL:-${TELEGRAM_CHAT_ID:-}}"
if [ -z "$BOT" ] || [ -z "$CHAT" ]; then
  echo "tg_creds_missing, write-only alert" >&2
  echo "ALERT: task stuck" >> "$task_file"
else
  resp=$(curl -s -X POST "https://api.telegram.org/bot${BOT}/sendMessage" \
    -d "chat_id=${CHAT}" -d "text=${msg}" -d "parse_mode=Markdown")
  msg_id=$(echo "$resp" | python3 -c "import sys,json; print(json.load(sys.stdin).get('result',{}).get('message_id',''))" 2>/dev/null)
fi
```

### Failure mode & traceback
- `hermes send` exit 1/2 → check gateway pid first (`pgrep -f hermes`); if gateway down, curl path may also fail — fall through to write-only alert.
- `curl: (6) Could not resolve host` or `HTTP 401 Unauthorized` from TG API → 95% env not sourced. Symptom: BOT empty string, if-guard skips, nothing sent. Try `hermes send` first; if that's also down, source `.env` then retry curl once.

## Env file location
- `~/.hermes/.env` — source of truth for all Hermes credentials
- Format: shell `KEY=VALUE` lines, some lines may contain non-exportable content (paths like `Chrome.app/...`); sourcing prints stderr warnings but Python still works

## Source recipe (cron context, fallback path only)
```bash
set -a
source ~/.hermes/.env 2>/dev/null
set +a
# Now TELEGRAM_BOT_TOKEN and TELEGRAM_HOME_CHANNEL are available
```

## Telegram-related env vars in `~/.hermes/.env`
| Variable | Purpose | Notes |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | Bot API token | Required for any TG push |
| `TELEGRAM_HOME_CHANNEL` | **Main chat id** for alerts | Numeric, e.g. `7359677525` |
| `TELEGRAM_CHAT_ID` | Alternate/legacy chat id | May or may not be set — try HOME first, fall back to CHAT_ID |
| `TELEGRAM_HOME_CHANNEL_THREAD_ID` | Thread id for grouping in main chat | **NOT a chat id** — do NOT use as recipient |
| `TELEGRAM_ALLOWED_USERS` | Auth allowlist for bot commands | Not for push |
| `HERMES_TELEGRAM_HTTP_POOL_*` | httpx pool tuning | Irrelevant for curl |

## Push recipe (Python, cron context — fallback only)
```python
import os, httpx
BOT = os.environ.get('TELEGRAM_BOT_TOKEN', '')
CHAT = os.environ.get('TELEGRAM_HOME_CHANNEL') or os.environ.get('TELEGRAM_CHAT_ID', '')
if BOT and CHAT:
    r = httpx.post(
        f"https://api.telegram.org/bot{BOT}/sendMessage",
        json={"chat_id": CHAT, "text": msg, "parse_mode": "Markdown"},
        timeout=10,
    )
    msg_id = r.json().get("result", {}).get("message_id")
```

## Changelog
- 2026-06-28 14:16 (v1.6.0): Original env-sourcing recipe; "Why not `hermes send`?" stance.
- 2026-06-28 14:31 (v1.7.0): Reversed stance — `hermes send` is now preferred in this user's setup (gateway up). curl retained as fallback. Added decision table and failure-mode matrix.
