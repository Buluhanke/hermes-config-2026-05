# Firecrawl — Web scraping & extraction for AI agents

Firecrawl is an AI-native web scraping API that bypasses basic anti-scraping and returns clean Markdown — the format AI agents work with best. Hermes's `web_search` tool is backed by Firecrawl; once an API key is set, `web_search` and `web_extract` Just Work.

## What it does

| Endpoint | Use |
|---------|-----|
| `scrape` | Single URL → Markdown/HTML/JSON. Bypasses JS challenges + basic anti-bots. |
| `crawl` | Full site crawl, respects robots.txt, configurable depth. |
| `map` | Fast sitemap-equivalent — get all URLs from a domain. |
| `search` | Web search (keyword → URL list, then each can be scraped). |
| `interact` | Browser-level interaction (clicks, fills) for JS-rendered pages. |

## Free tier

- **1,000 credits/month** — no credit card required.
- `scrape` = 1 credit/page; `search` = 2 credits/10 results; `interact` = 2 credits/browser-minute.
- Enough for ~1,000 page scrapes/month or ~500 searches/month.

## Setup

### 1. Get API key

1. Go to [firecrawl.dev](https://firecrawl.dev) → Sign up (free).
2. Dashboard → API Key → copy.

### 2. Write key to `.env`

```bash
# Option A: edit directly (ask the agent to do this)
hermes config edit    # won't work — security policy blocks patch on config.yaml
# Use sed to append:
grep -q "FIRECRAWL_API_KEY" ~/.hermes/.env && \
  sed -i '' 's/^# FIRECRAWL_API_KEY=.*/FIRECRAWL_API_KEY=your_key_here/' ~/.hermes/.env || \
  printf '\n# Firecrawl API Key - Web search, extract, and crawl\nFIRECRAWL_API_KEY=your_key_here\n' >> ~/.hermes/.env

# Option B: echo (faster for agent to execute)
KEY="fc-key-..."
grep -q "FIRECRAWL_API_KEY" ~/.hermes/.env && \
  sed -i '' "s|^# FIRECRAWL_API_KEY=.*|FIRECRAWL_API_KEY=$KEY|" ~/.hermes/.env || \
  printf '\nFIRECRAWL_API_KEY=%s\n' "$KEY" >> ~/.hermes/.env
```

### 3. Verify

**Critical: use the Hermes venv Python, not system `python3`.** System Python 3.11 hits `TypeError: unsupported operand for |: 'type' and 'type'` from urllib3's union-type syntax incompatibility.

```bash
# ✓ Correct — Hermes venv python
~/.hermes/hermes-agent/venv/bin/python3 -c "
from firecrawl import Firecrawl
fc = Firecrawl(api_key='your_key_here')
result = fc.scrape('https://example.com', formats=['markdown'])
data = result.model_dump()  # returns a dict; .get() works on this
print('Title:', data.get('metadata', {}).get('title'))
print('OK')
"

# ✗ Wrong — system python3 hits urllib3 TypeError
python3 -c "from firecrawl import Firecrawl"  # DON'T
```

Also verify from within Hermes's own toolcheck:

```bash
cd ~/.hermes/hermes-agent
HERMES_HOME=~/.hermes ~/.hermes/hermes-agent/venv/bin/python3 -c "
from tools.web_tools import check_firecrawl_api_key
print('Hermes Firecrawl available:', check_firecrawl_api_key())
"
```

### 4. Activate in Hermes

**`.env` is read at Hermes process startup** — not lazily per tool call. You MUST start a new session for the key to be picked up:

- CLI: exit and re-run `hermes`, or just `/new` in the running session
- Desktop app: restart the app (the backend picks up the new env on next session)

After `/new`, `web_search` and `web_extract` route through Firecrawl automatically. No other config needed.

## Hermes tool: web_search

Once key is set, these tools are live:
- `web_search` — search the web, get URLs + snippets.
- `web_extract` — extract page content (markdown/text).

Both route through Firecrawl automatically. The `web` toolset must be enabled (`hermes tools list` → should show `web`).

## Integration with agent-reach

- Firecrawl is NOT a replacement for `agent-reach` — they complement each other:
  - **agent-reach**: Chinese/vertical platforms (V2EX, B站, 小红书, GitHub code search) where agent-reach has a native adapter.
  - **Firecrawl**: General web scraping (news, docs, blogs, paywalled content, JavaScript-rendered pages).
- For a URL that blocks simple `curl`, try Firecrawl first — it's designed for exactly this.

## Pitfalls

- **Egress IP matters.** Firecrawl's infrastructure may return different results from your local IP. If a page is region-locked, Firecrawl may not bypass it either.
- **Credit monitoring**: Track usage at [firecrawl.dev/dashboard](https://firecrawl.dev/dashboard). Free tier = 1,000/month — scrape 1,000 pages and you're done until next month.
- **PDF parsing costs extra credits** (same as page credits but billed per PDF page).
- **Enhanced mode** (+4 credits/page) gives structured extraction — worth it for complex pages.
- **Rate limits**: Free tier has low concurrency (2 concurrent). Don't hammer in a loop.
- **Self-hosted alternative**: If you want zero dependency on external API, `firecrawl/firecrawl` (GitHub, ~151k stars) is open source and can be run locally. Set `FIRECRAWL_API_URL=http://localhost:3002` instead of `FIRECRAWL_API_KEY` in `.env`.

- **Pydantic `Document` vs dict**: `fc.scrape()` returns a Pydantic `Document` model, not a plain dict. Call `.model_dump()` first to get a dict, then `.get()`. Directly calling `.get()` on the return value raises `AttributeError: 'Document' object has no attribute 'get'`.

- **`web_search` is Firecrawl-backed on this machine**: `web_search` and `web_extract` both route through Firecrawl when the key is set. The `web` toolset must be enabled. No separate skill install needed.
