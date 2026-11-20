---
name: jd-category-scraping
description: 'Use when scraping JD.com category tree and product counts.'
version: 1.0.0
author: user
license: MIT
metadata:
  hermes:
    tags: [jd, scraping, ecommerce, category]
    related_skills: [blocked-page-recovery]
---

# JD Category Scraping

## When to Use

When user needs JD.com full category tree with per-category product counts.

## Procedure

1. Fetch category tree: `https://dc.3.cn/category/get` (JSON, gbk). Recursively collect leaf nodes where `n` contains `list.jd.com`.
2. Clean URL: keep only `cat=` param, drop `pvid`/`ev` (session params trigger freq control).
3. For each leaf, create a CDP tab via Target.createTarget on browser-level websocket (port 9222), navigate, wait load (+scroll), extract document.body.innerText. Match websocket responses by id.
4. Parse total pages: regex `共(\d+)`. Count = (pages-1)*60 + last-page `.gl-item` count (navigate to `&page={pages*2-1}`).
5. Rate limit 4s between requests. Retry 3x on failure. Incremental write every 5 items to `~/.hermes/cache/jd_cat_count.json`.
6. Close each tab via `Target.closeTarget` immediately after use (prevent window accumulation).

## Pitfalls

- Freq control is IP-level: "访问频繁导致无法搜索". Wait 1-2h or use proxy/VPN. Not a code bug.
- URL must be cleaned of pvid/ev; otherwise freq control triggers instantly.
- `.gl-item` selector may vary; verify on first page before bulk run.
- Use CDP (port 9222) with login cookie, not raw requests (JD blocks unauthenticated).
- Never accumulate tabs; close each immediately.
- `dc.3.cn/category/get` returns gbk; decode with `gbk` ignore.
- Walk recursion must guard non-dict/list nodes (None, str, int) or it crashes.
- URL params use `%2C` (encoded comma); unquote to `,` or JD won't parse cat.
- CDP tab creation: `/json/new` returns 405 in Chrome 156+; use `Target.createTarget` via browser-level websocket, close via `Target.closeTarget`.
- `document.body.innerText` may be empty until JS renders; wait 5-10s + scroll.
- Total pages regex is `共(\\d+)` (new JD UI), not `共<b>N</b>`.
- Fetch `BROWSER_ID` from `/json/version` webSocketDebuggerUrl; don't hardcode.
- websocket recv ordering is not guaranteed; match responses by `id` field.
- 9222 Chrome must be logged into JD; otherwise empty/freq-control pages.
- Incremental write every 5 items; resume via `done` dict keyed by URL.
