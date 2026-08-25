---
name: 1688-bag-sourcing
description: "1688 自封袋/塑料袋 2D软包装 sourcing。Use when 找塑料自封袋/opp袋/拉链袋等2D软包装。"
category: ecommerce
version: 1
author: hermes-agent
license: mit
metadata:
  hermes:
    tags: [1688, sourcing, 自封袋, 塑料袋, ecommerce]
    related_skills: [1688-search/1688-search-cn-gb-region-skill]
---

# 1688 自封袋 / 塑料袋 2D 软包装 sourcing

## When to Use
用户在 1688 找 **2D 软包装**（自封袋/塑料袋/PE袋/opp袋/拉链袋/封口袋/骨袋），尤其带尺寸(宽*高)、白边/红边、丝厚度(如12丝)等规格。3D 纸箱/包装盒类任务走 `1688-search-cn-gb-region-skill`。

## 触发场景
用户在 1688 找 **2D 软包装**：自封袋、塑料袋、PE袋、opp袋、拉链袋、封口袋、骨袋等。
典型 query：`14*20cm 白边*12丝 塑料自封袋`、`白边自封袋`、`opp自封袋 加厚`。
尺寸是 **2D 宽*高**（如 14*20cm），不是 3D 箱规。若任务是 3D 纸箱/包装盒，走 `1688-search-cn-gb-region-skill`（3D + 省份筛选），本 skill 是 2D 变体。

> ⚠️ 本 skill 是 `1688-search-cn-gb-region-skill` 的 **2D 兄弟篇**。主驱动 `cdp1688_bag.py` 与补验脚本 `cdp1688_bag_reverify.py` 实际落在用户自有 skill 的 `scripts/` 目录：
> `~/.hermes/skills/1688-search/1688-search-cn-gb-region-skill/scripts/`
> 本 skill 不复制脚本，只记录 2D 专属领域规则 + 复用指针（见下「驱动与脚本」）。

## 五大领域铁律（2026-08-25 实战固化）

1. **红边 = 白边（用户当场纠正，最高优先）**：搜「白边自封袋」时，"白边"信号**必须同时匹配 白边 / 红边 / 加宽边**。用户原话：「基本上有红边的都有白边」。只匹配"白边"二字会漏掉整批红边款（红边款恰恰是白边工艺的另一种叫法）。脚本里 `white = ("白边" in x) or ("红边" in x) or ("加宽边" in x)`。

2. **2D 尺寸顺序无关**：`14*20 == 20*14 == 14×20 == 14x20`。匹配用 `target_perms_2d(dim)` 生成全排列集合比对，正则 `([0-9.]+)[xX×*]([0-9.]+)` 抽宽*高。注意：必须排除看起来像 3D 的串（后面紧跟 `*数字` 的），塑料袋 SKU 里偶尔混 3D 写法。

3. **丝厚度 = 规格权威，且必须精确匹配那条 SKU（致命坑）**：1丝=0.01mm。厚度信号 `([0-9.]+)\s*丝` 抽。但**严禁从整页文本模糊并厚度**——页面其他段可能是 12丝，目标尺寸那条却是 10丝，模糊并会把 10丝款误判成 12丝。正确做法：只从 `skuMapOriginal` 目标尺寸**那条 specAttrs** 抽厚度（见 `cdp1688_bag.py` 的 `parse_sku_json` + 按归一化 spec 精确匹配）。实战翻车：`775671146977` 标了 12丝 实际 spec 是 `7号14*20【10丝（白边）】`，模糊并误中。

4. **义乌市 = 1688 定位字段的「浙江省金华市」**：1688 的 `location` JSON 字段只标到地级市，义乌（县级市，金华代管）显示为 `浙江省金华市`。所以"地区=义乌"的硬卡 = `location` 含 `浙江省` 且含 `金华市`，**绝不能**用页面正文里的"义乌"（营销文案到处写义乌发货，但营业执照可能在广东/河北）。筛选用结构化 `"location":"..."` 字段，不用正文。

5. **品类硬卡 + 排礼盒**：`BAG_SIG = 自封袋|塑料袋|PE袋|opp袋|封口袋|拉链袋|包装袋|骨袋`；`GIFT_SIG = 礼盒|礼品盒|开窗|烫金|巧克力|...` 命中礼盒信号直接跳过（塑料袋搜索池会混入食品盒/礼盒）。

## 驱动与脚本（复用指针，不复制）
主驱动 `cdp1688_bag.py`（`~/.hermes/skills/1688-search/1688-search-cn-gb-region-skill/scripts/`）：
- 参数：`--dims "14*20" --cat "白边自封袋" "塑料自封袋" ... --city 义乌 --prov "<浙江GBK>" --pages 4 --gap 2.5 --maxverify 220 --out store/bag_14x20_yiwu.json`
- 已内建：2D 顺序无关匹配、丝厚度抽、义乌(金华)硬卡、白边含红边、skuMapOriginal 优先 outerHTML 抓取、验证码退避。
- 前置：后台隐藏 CDP Chrome（`start_cdp_1688.sh` 起 + cookie 注入，不抢焦点）。

补验脚本 `cdp1688_bag_reverify.py`（同目录）：重搜同样关键词，跳过已验 ID，只验剩余候选；重点在**登录墙中断后补验**。

## 坑位（2D 专属）

**A. reverify 的 skip-set 结构必须和主脚本一致（2026-08-25 实战 bug）**：主脚本 `save_state()` 写 `hits: {'14*20': [...]}`（按 dim 分桶 dict），但补验脚本读 `d.get('hits',[])` 当 list → 结构不匹配 → skip-set 恒空 → 重验了全部 157 个（无害但浪费 ~15 分钟）。修复：补验脚本读 skip 时按 `d.get('hits',{}).get('14*20',[])` 取 ID。两条脚本的 hits 落盘结构必须统一。

**B. 登录墙中途静默丢失 → 验证截断（坑39 的 2D 版）**：后台 CDP 实例的 1688 登录态会在批量核验中途掉（详情页跳 taobao.com，连续 5 次 LOGIN-WALL 即停）。本次主跑 157 候选只验到 ~100 个（第18个起撞墙）。识别：`document.title` 含"淘宝网"或 `location.href` 含 taobao。修复：**重跑 `start_cdp_1688.sh` 重新注入 80 个 cookie**（新实例），再跑 `cdp1688_bag_reverify.py` 补验剩余候选。两次独立核验结果重合即可信。

**C. PC 搜页候选有限，移动端翻 10 倍**：`s.1688.com/selloffer` 单页 ~15 候选且易撞验证码；`m.1688.com/offer_search.html?keywords=<GBK>&page=N` 单页 ~130-145 且无码。白边*12丝 这种窄特征款，PC 池可能就 1 条，移动端能挖到更多义乌货源。需要时给主驱动加 `--mobile`（已在 `cdp1688.py` 实现，bag 版按需移植）。

**D. macOS 无 `timeout` 命令**：后台跑长任务别包 `timeout 1500 ...`，会 `command not found`。直接裸跑 + `background=true` + `notify_on_complete`。

**E. 输出铁律（用户风格，最高优先）**：先给结论 + 链接 + 价格表，再补必要说明。不要先铺原理/坑位/分析墙。表格列：商品ID | 规格 | 单价 | 白边 | 12丝 | 是否目标。

## 实战样例（2026-08-25，已验证）
任务：`14*20cm 白边*12丝 塑料自封袋`，地区=义乌市。
- 搜 4 词 × 4 页 + 核验 157 候选（两次独立核验，含登录墙补验），义乌(金华)命中 18 个 14*20 自封袋。
- **白边(含红边) + 真·12丝 双中唯一精确命中**：`685142110437`（spec `14*20 *红边12丝*透明`，¥6.50/100只装，义乌市方卓包装）→ 链接 `https://detail.1688.com/offer/685142110437.html`
- 邻近款（白边但非12丝）：`775671146977`(10丝白边)、`941296464253`(5丝红边)；`846874790590`/`964776286173`/`768365700880`(12丝但透明无白边)。
- 完整运行配方 + 已验证结果表见 `references/bag_sourcing_technique.md`。
