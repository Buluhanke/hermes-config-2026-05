# Xueqiu `quote.json` API — Field Dictionary

Endpoint:
`https://stock.xueqiu.com/v5/stock/quote.json?symbol=SH601398&extend=detail`
(credentials required — only works from the authenticated chrome_cdp browser session)

Response shape: `{ "data": { "market": {...}, "quote": {...}, "others": {...}, "tags": [...] }, "error_code": 0 }`

## data.market
- `status_id` / `status` — "交易中" / "已收盘" (or 休市). `region`: "CN". `delay_tag`: 0 = real-time.

## data.quote (the main block)
| field | 中文 | meaning |
|---|---|---|
| `current` | 现价 | last price |
| `chg` | 涨跌额 | current − last_close |
| `percent` | 涨跌幅 | % change |
| `last_close` | 昨收 | previous close |
| `open` | 今开 | open |
| `high` | 最高 | day high |
| `low` | 最低 | day low |
| `high52w` / `low52w` | 52周高/低 | 52-week range |
| `amplitude` | 振幅 | (high−low)/last_close % |
| `volume` | 成交量 | in 手 (100 shares/lot) |
| `amount` | 成交额 | in 元 (CNY) |
| `turnover_rate` | 换手率 | % of float traded |
| `avg_price` | 均价 | VWAP |
| `pe_ttm` | 市盈率(TTM) | trailing PE |
| `pe_lyr` | 市盈率(静) | last-year PE |
| `pe_forecast` | 预测PE | forward PE |
| `pb` | 市净率 | price / book |
| `eps` | 每股收益 | EPS |
| `navps` | 每股净资产 | book value per share |
| `dividend` | 每股分红 | dividend per share (TTM) |
| `dividend_yield` | 股息率 | % yield |
| `profit` | 净利润 | TTM net profit (元) |
| `profit_four` | 四季利润 | |
| `profit_forecast` | 预测利润 | |
| `market_capital` | 总市值 | total mkt cap (元) |
| `float_market_capital` | 流通市值 | float mkt cap (元) |
| `total_shares` | 总股本 | |
| `float_shares` | 流通股 | |
| `limit_up` / `limit_down` | 涨停/跌停 | price limits |
| `pledge_ratio` | 质押比 | pledged-share ratio |
| `timestamp` | 时间戳 | ms epoch |
| `currency` | 币种 | "CNY" |
| `exchange` | 交易所 | "SH"/"SZ"/"HK" |
| `code` | 代码 | "601398" |
| `name` | 名称 | "工商银行" |
| `type` | 类型 | 11 = A-share |

## data.others
- `pankou_ratio` — 盘口比 (negative = 委卖 pressure dominates; positive = 委买)
- `cyb_switch`, `is_extend_to_1530` — session flags

## data.tags
Array of `{description, value}` e.g. 沪股通 / 融 / 空 — liquidity & connect flags.

## Notes
- `volume`/`amount` may be null for non-trading sessions; check `data.market.status`.
- For HK stocks values are in HKD and shares differ (lot_size differs); same field names.
