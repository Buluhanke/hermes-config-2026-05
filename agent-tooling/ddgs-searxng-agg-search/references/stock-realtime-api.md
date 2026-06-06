# 实时行情API速查（2026-06-06 实测）

## A股 — 新浪行情接口

```bash
curl -s "https://hq.sinajs.cn/list=sh601398" \
  -H "Referer: https://finance.sina.com.cn"
```

参数：`sh601398` = 工商银行。`sh`=上海，`sz`=深圳。

返回字段（逗号分隔）：
```
name, 今开, 昨收, 现价, 最高, 最低, 买入, 卖出, 成交量, 成交额, ...
```

## 解析示例（工商银行 2026-06-05）

```python
data = "7.240,7.230,7.340,7.350,7.240,7.330,7.340,278948141"
fields = ['今开','昨收','现价','最高','最低','买入','卖出','成交量']
# 现价=7.34, 涨跌额=+0.11, 涨跌幅=+1.52%
```

## 港股 — 腾讯行情

```bash
curl -s "https://qt.gtimg.cn/q=hk00700"
```

## 美股 — 换算代码

```bash
# 苹果
curl -s "https://hq.sinajs.cn/list=usAAPL"
# 纳指
curl -s "https://hq.sinajs.cn/list=usNDX100"
```

## 关键区别

| 工具 | 用途 | 时效 |
|---|---|---|
| `search.py` (anysearch/last30days) | 新闻、公告、股评、消息面 | 搜索建索引，有延迟 |
| 新浪/腾讯行情API | 实时价格、K线数据 | 交易所推送，秒级 |
