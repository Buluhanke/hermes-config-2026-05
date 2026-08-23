# Hermes self-check / audit template (macOS)

Run the probes in this template when the user asks "what can Hermes do?", "is anything broken?", or right after a migration. Group results into three buckets: **works as-is**, **needs attention** (real bug), **blocked by environment** (egress IP, missing brew, etc. — don't claim you can fix it).

## 1. Configuration inventory

```bash
# Read the current config and inventory what's there
python3 - <<'PY'
import yaml, json
c = yaml.safe_load(open('/Users/kk/.hermes/config.yaml'))
print("model:", c.get('model'))
print("toolsets:", c.get('toolsets'))
print("plugins.enabled:", c.get('plugins',{}).get('enabled'))
print("browser:", c.get('browser'))
print("web:", c.get('web'))
print("mcp_servers:", c.get('mcp_servers'))
PY

# Which .env keys are actually set?
for k in $(grep -oE '^[A-Z_]+=' ~/.hermes/.env 2>/dev/null | sed 's/=$//'); do
  echo "$k: set"
done

# Toolset status (the real one — config.toolsets may be empty string meaning "all defaults")
hermes tools list
```

## 2. Browser (Chrome CDP) probe

```bash
# Process + port + launchd
pgrep -fl "remote-debugging-port=9222" | head -1
curl -s -m 3 http://127.0.0.1:9222/json/version | python3 -c "import sys,json;v=json.loads(sys.stdin.read());print('Browser:',v['Browser'])"
launchctl list | grep chrome-cdp

# Profile mirror freshness
stat -f "%Sm" "$HOME/.hermes/chrome-profile-mirror/Default"
stat -f "%Sm" "$HOME/Library/Application Support/Google/Chrome/Default"
```

Then `python3 scripts/cdp_smoke_test.py` from `chrome-cdp-control` — verifies cookies, navigate, read, write, screenshot, close.

## 3. MCP probe

```bash
# Check no zombie processes (chrome-devtools-mcp and its watchdog)
pgrep -fl "chrome-devtools-mcp\|mcp_stdio_watchdog" 2>/dev/null || echo "none"
```

## 4. agent-reach probe

```bash
# What the binary claims
agent-reach doctor --json
agent-reach doctor

# Real probe on the "free" channels — don't trust doctor alone, the egress IP can blackball them
curl -s -m 5 "https://www.v2ex.com/api/topics/hot.json" | python3 -c "import sys,json;d=json.loads(sys.stdin.read());print(f'V2EX: {len(d)} topics')"
python3 -c "import feedparser;d=feedparser.parse('https://hnrss.org/frontpage');print(f'RSS: {len(d.entries)} entries')"
yt-dlp --version
curl -s -o /dev/null -w "B站: %{http_code}\n" -m 5 "https://api.bilibili.com"
curl -s -o /dev/null -w "Jina: %{http_code}\n" -m 5 "https://r.jina.ai/https://example.com"
```

If `agent-reach doctor` says ✅ but `curl` returns 401/403, the channel is blocked at the egress IP (typically Cloudflare-customer / datacenter ASNs). Don't waste time fixing it — record as "blocked by environment."

## 5. Network egress (one-line sweep)

```bash
for u in "https://www.v2ex.com/api/topics/hot.json" "https://www.google.com" "https://www.youtube.com" "https://api.bilibili.com" "https://r.jina.ai/https://example.com" "https://api.github.com/zen" "https://huggingface.co" "https://api.openai.com"; do
  code=$(curl -s -o /dev/null -w "%{http_code}" -m 5 "$u")
  echo "  $code  $u"
done
```

## 6. State DB + files

```bash
python3 -c "
import sqlite3
c = sqlite3.connect('/Users/kk/.hermes/state.db')
print('integrity:', c.execute('PRAGMA integrity_check').fetchone()[0])
print('tables:', len([r[0] for r in c.execute(\"SELECT name FROM sqlite_master WHERE type='table'\")]))
"
ls ~/.hermes/config.yaml.bak.*  # backups present?
```

## Output template

```
## Works as-is
- [list]

## Needs attention (real fix possible)
- [list with action]

## Blocked by environment (no fix here)
- [list — egress IP / missing brew / paid-only]

## Recently changed
- [list with timestamp]
```

## 5. Firecrawl (web tools)

```bash
# Key present in .env?
grep "FIRECRAWL_API_KEY" ~/.hermes/.env

# Quick scrape test via Python SDK
python3 -c "
import os, sys
sys.path.insert(0, '/Users/kk/.hermes/hermes-agent/venv/lib/python3.11/site-packages')
from firecrawl import Firecrawl
key = os.getenv('FIRECRAWL_API_KEY','')
if not key or len(key) < 10:
    print('KEY MISSING or too short')
else:
    fc = Firecrawl(api_key=key)
    r = fc.scrape('https://example.com', formats=['markdown'])
    print('Scrape OK:', r.get('metadata',{}).get('title','?'))
" 2>&1
## After the audit

If anything in "Needs attention" involves Chrome profile staleness, run `chrome-cdp-control`'s `scripts/sync_profile_mirror.sh` (it does a dry-run preview first — confirm, then rsync + cache cleanup). Safe to re-run on a cadence.

**Firecrawl next steps**: If the key is missing, direct the user to [firecrawl.dev](https://firecrawl.dev) → sign up → copy API key. The agent can write it to `.env` once the user shares it.

Write the report to `~/Desktop/hermes-audit-<date>.md` so the next session can diff against it.