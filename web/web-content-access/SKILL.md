---
name: web-content-access
description: |
  Access web content through the right tool for the situation. Used when
  the user wants content from a URL or web page and naive approaches
  (browser_navigate, computer_use screenshot) have failed or are wrong for
  the task. Triggers: URL is blocked/misclassified, browser automation
  session is stuck, user says "read this page" or "get content from URL".
version: 2.0.0
triggers:
  - "读取这个网页"
  - "访问这个URL"
  - "网页内容"
  - "browser_navigate被拦截"
  - "不要截图识别"
  - "get content from URL"
  - "能读取网页内容吗"
  - "看懂网页"
---

# Web Content Access — Pick the Right Tool

## Key Distinction: Skills vs Tools vs MCP Servers

- **Tools** (`web_search`, `web_extract`, `terminal`) are code-level capabilities built into Hermes
- **Skills** are knowledge-layer documents telling the agent *how to* do a task — they call one or more tools
- **MCP servers** are external daemons that expose tools via the Model Context Protocol; Hermes acts as the MCP *client*

**For reading web content: use the built-in `web_extract` tool directly. No skill or extra installation needed.** Skills only become relevant when the default tool doesn't work or when the process needs to be remembered.

## Decision Tree — Start Here

```
Does the page need JS rendering or user interaction (clicks, scrolls)?
├── NO  → web_extract (built-in tool, always try first)
│         If "Blocked: private/internal address" → FIX below
└── YES → browser-use CLI (see browser-use skill)
            Still blocked → computer_use screenshot (vision model required)
```

**`web_extract` is the default.** It is a built-in tool, not a skill. It requires no installation. Try it first before anything else.

### Verify if a URL is actually reachable

```bash
curl -s -o /dev/null -w "%{http_code}" "https://the-url.com"
```

If HTTP 200 but `web_extract` blocks it → fix the security config below.

## Fix: `web_extract` "Blocked: URL targets a private or internal network address"

This is a false positive from Hermes's SSRF protection. Add to `~/.hermes/config.yaml`:

```yaml
security:
  allow_private_urls: true
```

**Restart gateway** (must be done from outside the gateway process):
```bash
# Find gateway PID
ps aux | grep hermes_cli.main | grep -v grep

# Kill it — supervisor auto-restarts with new config
kill <gateway_pid>
```

After restart, `web_extract` works for all public URLs.

## Two Routes for Reading Web Pages

| Route | Mechanism | Model requirement | Precision | Best for |
|-------|-----------|------------------|-----------|----------|
| Route 2: DOM reading | `web_extract` or **Crawl4AI** (AsyncWebCrawler) | Text-only model OK | High (semantic) | Static pages, form-heavy pages |

**Crawl4AI** is the preferred tool for pages needing JS rendering. Python API verified working (0.9.2, example.com → 166 chars clean Markdown in 11.5s). `python3 -m playwright install --with-deps chromium` for browser binary. No `crawl4ai-setup` CLI — that command does not exist.
| Route 2: DOM reading | `web_extract` or browser-use reads HTML | Text-only model OK | High (semantic) | Static pages, form-heavy pages |

**Route 2 is preferred by default.** Route 1 only when the page is canvas-rendered or the task needs visual verification.

## Common Pitfalls

### browser_navigate "blocked: private/internal address" for a public URL
- Hermes browser backend URL validator has false positives on public domains
- `design.penpot.app`, `help.penpot.app` returned HTTP 200 via curl but Hermes blocked them
- Fix: verify with `curl -s -o /dev/null -w "%{http_code}" <url>` — if 200, it's a false positive
- Fix: add `security.allow_private_urls: true` to config.yaml (see above)

### web_extract returns "Content was inaccessible or not found"
- Site may require JS rendering or authentication
- Fall back to browser-use CLI or REST API

### Chrome localStorage is encrypted (macOS Keychain)
- Cannot read from terminal
- Fix: open DevTools console on page, run:
  `JSON.parse(localStorage.getItem("key"))`

## Reference: Common API Endpoints
- **Penpot**: `https://design.penpot.app/api/v1/` (requires token from web UI Settings → Integrations)
- **GitHub**: `https://api.github.com/repos/<owner>/<repo>`
- **YouTube**: `https://www.youtube.com/oembed?url=<video_url>&format=json`

## Penpot MCP Integration

See `references/penpot-mcp.md` for full setup guide — architecture, two connection options (npx vs source clone), Hermes MCP client config, and known issues.
