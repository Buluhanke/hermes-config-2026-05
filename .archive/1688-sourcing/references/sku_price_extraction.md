# skuMapOriginal 价格提取：精准匹配规则

## 核心结构（已确认，2026-09-08）

1688 详情页 `skuMapOriginal` 数组元素顺序：
```
{"specId":"...","saleCount":0,"discountPrice":"0.56","canBookCount":930189,"specAttrs":"17.5*17.5*8.5cm;三层加硬","price":"0.56","priceAmount":1,"skuId":5939148147131,"isPromotionSku":false}
```

**`discountPrice` 和 `canBookCount` 出现在 `specAttrs` 前面。**

## 提取算法

对每个候选 `specAttrs` 匹配目标尺寸时：

1. 找到 `specAttrs` 字段的字符位置 `dim_pos`
2. 在 `sku_section[max(0, dim_pos-500) : dim_pos]` 范围内找最近的 `discountPrice`
3. 同理在附近找 `canBookCount`
4. **折扣价（discountPrice）距离 `specAttrs` 必须在 250 字符以内**，否则属于上一个 SKU 条目

```python
dim_idx = sku_section.find(target_dim)  # 如 "17.5*17.5*8.5cm"
search_region = sku_section[max(0, dim_idx-500):dim_idx]
disc_m = re.search(r'"discountPrice":"([^"]+)"', search_region)
stock_m = re.search(r'"canBookCount":(\d+)', search_region)
price = disc_m.group(1) if disc_m else "?"
stock = stock_m.group(1) if stock_m else "?"
```

## 常见错误

| 错误写法 | 问题 |
|---|---|
| `re.search(r'discountPrice.*?specAttrs.*?target_dim', ...)` | 方向反了，price 不在 specAttrs 后面 |
| 只找 `priceAmount` 而非 `discountPrice` | `priceAmount` 是固定值(1)，要的是 `discountPrice` |
| 不限制距离 | 可能匹配到前一个 SKU 的价格 |

## `browser_exec` 快速提取模板

`browser_exec` 内用 Python `re`，与上述算法等价：

```python
import re, time
for offer_id in ["634522031289","751990874462"]:
    goto_url(f"https://detail.1688.com/offer/{offer_id}.html")
    wait_for_load()
    time.sleep(4)
    html = js("document.documentElement.outerHTML")
    sku_start = html.find('"skuMapOriginal"')
    sku_end = html.find('"unit":"个"', sku_start)
    sku_section = html[sku_start:sku_end+20]
    dim_idx = sku_section.find("17.5*17.5*8.5")  # 目标尺寸
    if dim_idx >= 0:
        region = sku_section[max(0, dim_idx-500):dim_idx]
        disc_m = re.search(r'"discountPrice":"([^"]+)"', region)
        stock_m = re.search(r'"canBookCount":(\d+)', region)
        print(f"{offer_id}: ¥{disc_m.group(1) if disc_m else '?'} x{stock_m.group(1) if stock_m else '?'}")
    time.sleep(2)
```

## 注意：部分 ID 用 `17.5x` 而非 `17.5*`

同一个搜索结果里不同 ID 可能用不同记号：`17.5*17.5*8.5` 和 `17.5x17.5x8.5` 都存在。
搜索时双记号合并去重，或对每个 ID 先判断用哪种记号再搜索 specAttrs。
