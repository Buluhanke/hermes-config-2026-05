# AnySearch 验证输出（2026-07-13 实测）

## 通用搜索输出格式
```
## Search Results (N results, Xms)

### 1. Title
- **URL**: https://example.com
- Snippet text...
```
延迟约 1-2 秒，匿名访问正常。

## 垂直搜索-股票行情（A股/国际股）
金融数据返回结构化 JSON 而非文本片段：

```
### 1. 600519.SH 20260710 日线行情
- {"amount":6223343.642,"change":22.79,"close":1204.98,"high":1204.98,"low":1170.28,"open":1182.2,"pb":5.5606,"pe":18.2984,"pct_chg":1.9278,"trade_date":"20260710","ts_code":"600519.SH","turnover_rate":0.4177,"vol":52212.55}
```

关键字段：close(收盘价)、pct_chg(涨跌幅%)、pe(市盈率)、trade_date(交易日期)

国际股票查询示例：
```bash
python3 /tmp/anysearch-skill/anysearch-skill-main/scripts/anysearch_cli.py \
  search "AAPL" \
  --domain finance \
  --sub_domain finance.quote \
  --sdp "type=stock,symbol=AAPL,cn_code=" \
  --max_results 3
```
→ 返回 FinancialModelingPrep 的结构化数据（价格/市值/PE等）

## URL 提取
返回完整 Markdown 格式，包含页面标题和内容。

## batch_search 限制（重要）
匿名模式下几乎必定报 `Connection Error: Unable to reach the API endpoint`，但同一查询用 `search` 单条调用正常。配 API key 可解决。

错误示例（匿名用户）：
```bash
python3 .../anysearch_cli.py batch_search \
  --queries '[{"query":"NVDA","domain":"finance",...}]'
# → Connection Error
```

## curl 方式注册获取 API key
```bash
curl -s -X POST "https://api.anysearch.com/v1/auth/email/register" \
  -H "Content-Type: application/json" \
  -d '{"email": "you@example.com"}'
# 成功返回: {"code":0,"data":{"api_key":{"key":"as_sk_xxx","rate_limit":20}}}
# 密码会发到邮箱，key 在响应 body 里直接返回（一次性显示，过后只能从 dashboard 查看）
```

## API Key 持久化方案
- `.env` 放在 `~/.hermes/skills/anysearch/.env`（持久化，重启不丢）
- 自愈脚本 `anysearch_heal.sh` 每次从 skills 目录复制到 `/tmp/anysearch-skill/`
- CLI 启动时自动从 `.env` 加载，无需每次传 `--api_key`

## batch_search + API key 实测（2026-07-13）
```
CMD batch_search --queries '[{"query":"NVDA"},{"query":"TSLA"},{"query":"AAPL"}]'
→ Query 1: NVDA → 10 results, 675ms
→ Query 2: TSLA → 10 results, 662ms
→ Query 3: AAPL → 10 results, 682ms
总耗时: ~0.7s（并行，非串行）
```
配 key 后 batch 正常，匿名模式仍有偶发 Connection Error。

## get_sub_domains 返回 required params
漏传 required params 会报 backend validation error，必须先查再搜：
```bash
python3 .../anysearch_cli.py get_sub_domains --domain finance
# 返回该 domain 下所有 sub_domain 及所需参数
```
