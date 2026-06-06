# 股票行情实时查询（新浪API）

## 核心接口
```bash
curl -s "https://hq.sinajs.cn/list=sh601398" \
  -H "Referer: https://finance.sina.com.cn"
```

## 返回格式
```
var hq_str_sh601398="今开,昨收,现价,最高,最低,买入,卖出,成交量,...,时间";
```

## 解析示例（Python）
```python
import subprocess
result = subprocess.run(
    ['curl', '-s', 'https://hq.sinajs.cn/list=sh601398',
     '-H', 'Referer: https://finance.sina.com.cn'],
    capture_output=True, text=True
)
# 返回: var hq_str_sh601398="7.240,7.230,7.340,7.350,7.240,7.330,7.340,278948141,...,2026-06-05,15:00:00,00,";
fields = result.stdout.split('"')[1].split(',')
# fields[0]=今开, [1]=昨收, [2]=现价, [3]=最高, [4]=最低, [5]=买入, [6]=卖出, [7]=成交量
```

## 股票代码规则
- 上交所：`sh` 前缀，如 `sh601398`（工商银行）
- 深交所：`sz` 前缀，如 `sz000001`（平安银行）
- 北交所：`bj` 前缀

## 适用场景
| 场景 | 用搜索还是API | 原因 |
|---|---|---|
| **实时价格** | Sina API ✅ | 搜索结果可能旧，API最准 |
| 财经新闻 | anysearch/last30days | 搜新闻、公告 |
| 舆情/口碑 | last30days | 社媒情绪 |
| 技术分析 | anysearch | 图表、分析文章 |

## 搜索路由中的处理
遇到含"股票价格/股价/今日收盘"等词 → 可优先考虑新浪API
（目前search.py未自动识别，见下方待办）

## 注意
- 新浪API无需API Key，免费
- 需要 `Referer` header 否则可能被拦截
- 返回GBK编码，部分服务器需要转码
