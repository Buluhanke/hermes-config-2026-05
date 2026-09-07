# 1688 拉环袋 sourcing 实战（2026-09-01）

## 完整运行配方

```bash
# 1) 起后台隐藏 CDP Chrome + cookie 注入
cd ~/.hermes/skills/1688-search/1688-search-cn-gb-region-skill/scripts
bash start_cdp_1688.sh

# 2) 搜索候选（拉环袋品类词，不用自封袋词）
python3 cdp1688_bag.py \
  --dims "18*15" \
  --cat "磨砂拉环袋" "拉链袋" "磨砂手提袋" \
  --pages 4 --gap 2.5 --maxverify 220 \
  --out store/lahuandou_18x15.json

# 3) 用户给链接时，直接核验不要先搜
# 优先 MCP（最快）
# MCP: mcp__alibaba_1688_scraper__get_product_detail_and_price(url="<用户链接>")
# MCP 失败用 desktop_preview 兜底
# desktop_preview action=open url="<用户链接>"
# desktop_preview action=read count=5000
```

## 已验证结果（18×15cm 磨砂拉环袋，2026-09-01）

用户给了链接 `791933298070`（苍南星喆），这家不在公开搜索池里。

| 商家 | 规格 | 价格 | 库存 | 链接 |
|---|---|---|---|---|
| **苍南县星喆包装**（温州） | 18×15 磨砂横版 14丝 EVA | **¥0.15** | 95万 | https://detail.1688.com/offer/791933298070.html |
| 义乌市图辉包装 | 20×15 黑色拉环 EVA磨砂 18丝 | ¥0.22 | 100万 | https://detail.1688.com/offer/742807798981.html |
| 义乌市丰沛包装 | 16/19×15 白色拉环 EVA磨砂 17丝 | ¥0.23 | 2.4万 | https://detail.1688.com/offer/624440703702.html |

最低价：星喆 ¥0.15（14丝，95万库存，2400好评）。

## 三个致命翻车点

1. **拉环袋 ≠ 自封袋**：品类词不能混用，`--cat` 选错词整类跳过。
2. **用户链接优先于搜索**：用户给了 `791933298070`，但我先搜了 59 个候选才去看链接——浪费时间，这家根本不在公开池里。
3. **MCP + desktop_preview 混合兜底**：CDP Chrome 登录态丢时，不要死等重注，先用 MCP 核验，同时用 desktop_preview 读详情页。
