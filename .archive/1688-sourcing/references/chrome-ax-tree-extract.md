# Chrome AX 树商品数据提取法

## 背景

当 `computer_use capture` 成功返回 AX 树但 CDP JS 评估失败（空内容）时，从 AX 元素快照 JSON 文件中解析商品数据。

## AX 树文件位置

```
~/.hermes/cache/computer_use/elements_<hash>.json
```

capture 成功后输出会告知路径。文件是标准 JSON，结构：
```json
{"app": "", "window_title": "", "total_elements": N, "elements": [...]}
```

`elements` 是字典列表，每个字典格式：
```json
{"index": 126, "role": "AXLink", "label": "商品标题 ¥1.23 ...", "bounds": [x, y, w, h], "app": ""}
```

## 解析流程（Python）

```python
import json, re

with open('/path/to/elements_<hash>.json') as f:
    data = json.load(f)

elements = data['elements']

# 1. 按 y 坐标分区（商品卡片通常在 y=300-820）
# 2. 按 price indicator（¥ 或 全网）筛选
# 3. 按 x 坐标分列（多列布局时）

products = []
for el in elements:
    if el.get('role') == 'AXLink' and el.get('label'):
        label = el.get('label', '')
        bounds = el.get('bounds', [])
        if len(bounds) >= 2:
            y, x = bounds[1], bounds[0]
            if 300 < y < 820 and ('¥' in label or '全网' in label):
                parts = label.split('¥')
                title = parts[0].strip()[:100] if parts else label[:100]
                price = parts[1].split()[0] if len(parts) > 1 else ''
                company_m = re.search(r'([^\s\n]{4,50}公司[^\s\n]*)', label)
                company = company_m.group(1).strip() if company_m else ''
                products.append({'title': title, 'price': price,
                                 'company': company, 'y': y, 'x': x})

# 去重（按标题前25字）
seen = set()
unique = [p for p in sorted(products, key=lambda x: (x['y'], x['x']))
         if (p['title'][:25] not in seen, seen.add(p['title'][:25]))]
```

## 关键坐标参考（1688 搜索结果页）

| 区域 | y 范围 | 说明 |
|------|--------|------|
| 商品卡片主体 | 395-410 | AXLink 含完整商品信息 |
| 商品标题 | 565-620 | AXStaticText 标题文字 |
| 价格整数 | 633 | AXStaticText 单数字 "1" |
| 价格小数 | 637 | AXStaticText ".61" |
| 销量 | 640 | AXStaticText "全网9.2万+" |
| 保障标签 | 660 | AXStaticText "退货包运费" |
| 公司名 | 682 | AXLink 店铺名 |

## 适用场景

✅ computer_use capture 成功但 CDP JS 评估返回空
✅ osascript 对 Chrome 执行 JS 超时
✅ 只需要商品标题/价格/店铺名（不需要深入交互）

❌ 需要点击/滚动/翻页等交互操作（用 computer_use 元素索引）
❌ 需要阶梯价/详细规格（需要进入详情页）
