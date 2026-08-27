---
name: 1688-sourcing-router
description: 1688 找品统一路由——6 个 lineage 归一为「CDP 主驱动 + 品类分流 + 避坑铁律」，消除 lineage 漂移。Use when 任何 1688 找品/比价/选品任务先来判断走哪条路径、用哪个脚本。
version: "1.0"
category: 1688
triggers:
  - "1688找品"
  - "1688搜索"
  - "找XX的1688货源"
  - "去1688搜XX"
  - "1688比价"
  - "哪个1688 skill 该用"
l1: 1688
l2: router
l3: core
---

# 1688 找品统一路由（6 lineage 杂交固化）

本 skill 是**路由层 + 唯一真相源**。它把散落 6 处的规则归一，标注哪些 lineage 已退休。
**底层 lineage（按需要 skill_view 加载全文，不要重复实现）：**
- `1688-search/1688-search-cn-gb-region-skill` — 主 lineage（3D 纸箱/包装盒/彩盒/纸袋），含 `cdp1688.py` 终结者驱动
- `1688-bag-sourcing` — 2D 软包装变体（自封袋/塑料袋），含 `cdp1688_bag.py`
- `1688-matrix-dimension-sourcing` — 矩阵尺寸补丁（已并入主 lineage 的 `verify_carton_matrix.js`）
- `1688-cdp-product-fetch` / `1688-price-extraction` — 单页抓取/抠价旧档（被 `cdp1688.py` 的 skuMapOriginal 监听取代）
- `ecommerce/1688-sourcing` — **已退休**（停在 2026-08-19 computer_use 模拟点击旧时代，规则已被 CDP lineage 推翻）

## 体系一图

```
1688 找品任务
  │
  ├─ 3D 箱/盒/袋（纸箱/彩盒/飞机盒/纸袋/牛皮纸袋） ──→ 主 lineage
  │     └─ 驱动: cdp1688.py（Python 裸 WebSocket CDP，Chrome 151 兼容，零 Playwright）
  │
  └─ 2D 软包装（自封袋/塑料袋/PE/opp/白边/丝厚） ──→ 1688-bag-sourcing
        └─ 驱动: cdp1688_bag.py（同架构 2D 变体，尺寸顺序无关 + 厚度按同条spec）
```

## Lineage 退休裁定（MGM cross-lineage 结论）

| 旧 lineage | 状态 | 取代者 | 原因 |
|---|---|---|---|
| AppleScript `execute javascript` 驱动默认 Chrome | 退休（脆弱） | `cdp1688.py` 后台隐藏实例 | 默认 Chrome 被关 JS 开关即瘫；需前台窗口；会抢焦点 |
| `drive_playwright.js` | 退休（崩溃） | `cdp1688.py` | Chrome 151 移除 `Browser.setDownloadBehavior`，connectOverCDP 直接抛错 |
| `1688-sourcing`（ecommerce） | 退休 | 本路由 + 主 lineage | 仍教 computer_use 模拟点击+油猴脚本，已证伪（坑13/15/41） |
| `verify_carton.js` / `price_clean3.js` | 降级保留 | `cdp1688.py` 内置 skuMapOriginal | DOM 点 chip 抠价有风控痕迹；skuMapOriginal 零点击更稳 |
| `1688-cdp-product-fetch` / `1688-price-extraction` | 参考档 | `cdp1688.py` 的 SKU 监听 | 同架构但零散，已收编进主驱动 |
| `verify_carton_matrix.js` | 已并入 | `cdp1688.py` 的 `extract_sizes_from_spec` | 矩阵/轴名连写/全角组合串 5 类写法全内置 |

## 唯一主驱动用法（新任务一律走这）

**3D 任务：**
```bash
cd ~/.hermes/skills/1688-search/1688-search-cn-gb-region-skill/scripts
# 前置探针（必跑，FAIL-FAST 防登录态丢失白跑）
python3 preflight_1688.py --cdp http://127.0.0.1:9222
# 起后台隐藏 Chrome + 注入登录态（不抢焦点）
bash start_cdp_1688.sh
# 主驱动
python3 cdp1688.py --dims "46*26*10" \
  --cat "加高飞机盒" "宽26高10飞机盒" "纸箱" "瓦楞纸箱" "画框纸箱" "平邮箱定制" \
  --prov "" --pages 4 --gap 2.5 --maxverify 220 --out store/result.json
```
**2D 任务（自封袋）：** 同目录 `cdp1688_bag.py`，参数见 `1688-bag-sourcing`。

## 跨 lineage 通用铁律（从 6 处杂交提纯，最高优先）

1. **alibaba.com ≠ 1688.com**：绝不打开 alibaba.com（跨境站），只在 1688.com 标签页作业。
2. **绝不自加未请求的地域限制**：用户没说"江浙沪"就不加 `--prov`，默认全国（`--prov ""`）。曾因自加被骂"什么乱七八糟的"。
3. **搜索入口铁律**：只用 `s.1688.com/selloffer/offer_search.htm?keywords=<GBK>` 端点；禁 `s/1688search`（重定向清空）；关键词必须 GBK 编码（非 UTF-8 乱码）；用户给过的 URL 直接复用别改。
4. **尺寸 5 类写法全覆盖**（凡"用户说某家有、脚本说没有"→ 先疑写法漏，不疑用户）：
   ① 连写 `25*13*32` ② 轴名连写 `(竖)25长*13侧*32高` ③ 矩阵 `8x8（长宽）;9cm（高）` ④ 半角组合串 ⑤ **全角组合串 `宽【26cm】高【10cm】;特硬;长【46cm】`**
   且**顺序无关匹配**（`target_perms` 全排列）。
5. **SKU 权威 = `skuMapOriginal` 结构化 JSON**（整页 outerHTML 优先，非 DOM 文本 / 非 innerText / 非点 chip）。价格库存从目标尺寸那条 spec 直读。
6. **品类硬卡防假阳性**：3D 须命中纸箱/彩盒/飞机盒类词且非礼盒信号；2D 须 `BAG_PLASTIC` 且非茶叶/铝箔/牛皮纸。只验尺寸不验品类会收礼盒/茶叶袋。
7. **不抢焦点三铁规**：拉 Chrome 加 `-n -g -j`；详情页走后台 tab + `Runtime.evaluate` 零 UI；登录态 cookie 注入免显窗。
8. **降速防验证码**：每详情页 `--gap 2.5~8s`；搜页被拦→先 `--mobile`（m.1688.com 候选翻 10 倍无码）→ 再指数退避（15/30/45/60s）→ 最后才等。同一 9222 同一时刻只跑一个 `cdp1688` 循环（并行会清空结果）。
9. **登录态静默丢失是头号假阴性**：搜出"全是其他品"/0 命中 → 先探 detail 页是否跳 taobao.com。填 `preflight_1688.py` 当探针。`chrome-cdp-profile` 独立实例风控极严，根本解法 = 用户保持默认 Chrome 已登 1688，或 `--reverify` 只验已知 ID 池。
10. **正则零反斜杠**：写 `.js` 用 `[0-9]`/`[ ]` 替 `\d`/`\s`（write_file/heredoc 会双写反斜杠致语义错）。JS 一律独立文件读入（AppleScript `as «class utf8»`），不内联（会被转义吞）。
11. **输出铁律**：先给结论+链接+价格表，再补必要说明。不铺原理/坑位/分析墙。

## 已验证样例（证明 lineage 有效）
- `46*26*10cm 加高飞机盒`：用户给 `752445610436` 即命中（全角组合串写法），¥3.81 现货，13 款长 42-54。
- `14*20cm 白边*12丝 自封袋 义乌`：18 家含尺寸，白边(含红边)+12丝 精确双中 3 家（`685142110437` 等）。
- `16*16*16cm 纸箱 江浙沪`：6 家真命中，剔除 1 个广告文案误中（`751990874462`）。

## 决策 SOP（30 秒定位）
```
1. 2D 软包装? → cdp1688_bag.py | 否则 → cdp1688.py
2. 跑 preflight_1688.py，PASS 才开 main
3. 用户给链接? → 先验他的线索（reverify_pool 模式）别从零狂扫
4. 0 命中? → 查登录墙 → 补宽词(彩盒定制/纸袋/牛皮纸) → 试 --mobile → 近邻定制兜底(find_near.py)
5. 出结论表（ID|规格|单价|库存|卖家|链接），不堆分析
```
