---
name: xueqiu-stock-quote
description: Use when pulling Xueqiu stock quotes or analyzing a ticker.
version: 1
author: hermes
license: mit
metadata:
  hermes:
    tags: [finance, xueqiu, stock, a-share, hk-share, realtime-quote]
    related_skills: [browser-cdp-control, hermes-browser-local-login]
---

# Xueqiu (雪球) Real-Time Stock Quotes

## When to Use
User asks "X股票会涨吗 / 分析一下 / 现在什么价 / 实时行情" for a Chinese A-share or HK-share ticker,
or wants Xueqiu-based analysis. In this environment **Xueqiu is already connected** — the user said
"我们已经接入了雪球". Prefer Xueqiu live data over web_search snapshots (which lag and disagree).

## Environment fact (this user)
- Xueqiu is reached through the **`chrome_cdp` MCP**, which drives an authenticated local Chrome on
  port **9333** (not 9222 — 9222's `/json/list` is empty; 9333 has the live tabs).
- A Xueqiu ticker tab (e.g. `https://xueqiu.com/S/SH601398`) is typically already open and logged in.
- The MCP server occasionally goes "unreachable after 3 consecutive failures" — wait ~50s and retry;
  it recovers on its own. Do NOT assume it's permanently dead.

## Method (the working path — verified this session)
1. Ensure a page is selected in `chrome_cdp`. Use `list_pages`; if none selected, the Xueqiu tab
   usually is. If the MCP is down, skip to the fallback below.
2. `navigate_page` to the **JSON quote API URL** (not the SPA page):
   `https://stock.xueqiu.com/v5/stock/quote.json?symbol=SH601398&extend=detail`
   This renders as plain JSON text in the browser — no SPA mount needed, login cookie travels with it.
3. `take_snapshot` and read the `StaticText` body — it is the full JSON. Parse `data.quote.*`.

This beats every alternative tried:
- **Anonymous `fetch`/web access to the API fails** with `{"error_code":"400016"}` — needs the
  login cookie, which only the authenticated browser has.
- **Reading the SPA page** (`xueqiu.com/S/SH601398`) directly fails: backgrounded tabs stay
  `busy`/`loading`, `document.body` is empty, and `Runtime.evaluate` times out. Don't go down this road.
- **`evaluate_script` with an in-page `fetch`** also times out (CORS/background throttling). Skip it.

## Symbol format
- Shanghai A-share: `SH600000`, `SH601398` (ICBC). Shenzhen A-share: `SZ000001`.
- HK-share: `HK00700` (Tencent). Append `&extend=detail` for the full field set.

## Key `data.quote` fields (full dictionary in references/quote-api-fields.md)
`current` 现价 · `percent` 涨跌幅% · `chg` 涨跌额 · `last_close` 昨收 · `open`/`high`/`low` ·
`amplitude` 振幅 · `volume` 手 · `amount` 成交额(元) · `pe_ttm`/`pe_lyr` · `pb` 市净率 ·
`dividend` 每股分红 · `dividend_yield` 股息率% · `eps` · `navps` 每股净资产 · `high52w`/`low52w` ·
`limit_up`/`limit_down` · `market_capital` 总市值 · `float_market_capital` 流通市值 ·
`turnover_rate` 换手率%. `data.others.pankou_ratio` 盘口比 (negative = 卖压占优).
`data.market.status` = "交易中"/"已收盘".

## Analysis framing (user asks "会涨吗?")
Give: (1) the real-time line (current / percent / intraday range), (2) why it's moving or not
(bank sector, index, 中报 date, dividend logic), (3) an honest non-directional read — quote the
narrow amplitude / 盘口比 / low turnover as "缩量观望" rather than claiming a direction. End with a
**disclaimer**: 盘面分析非投资建议, 以收盘数据为准. Do NOT overclaim a rise/fall from a single snapshot.

## Pitfalls
- **`taibu` MCP is NOT Xueqiu.** The `taibu` aggregator (`mcp.mingai.fun/mcp`) is a Chinese
  metaphysics/divination tool (八字/紫微/塔罗/占卜) — 15 tools, zero stock data. Don't mistake it
  for the Xueqiu connection.
- Snapshots from web_search (TradingView, 金投网, 搜狐) disagree and lag by a day or more. Trust the
  Xueqiu live API read above all.
- `take_snapshot` on the JSON URL returns the JSON as one `StaticText` node — parse it, don't eyeball.

## Fallback if `chrome_cdp` MCP stays down
Drive CDP directly: system `python3` has `websocket-client` 1.9.0. Connect to a target's
`webSocketDebuggerUrl` from `http://127.0.0.1:9333/json/list`, `Target.attachToTarget`, then
`Page.navigate` to the JSON API URL and poll `Runtime.evaluate` of `document.body.innerText`. NOTE:
attached/backgrounded SPA tabs are unreliable this way (stuck busy) — the MCP's `navigate_page` +
`take_snapshot` is the robust path; only use raw CDP if the MCP is truly unreachable and you open a
fresh `Target.createTarget` then navigate.
