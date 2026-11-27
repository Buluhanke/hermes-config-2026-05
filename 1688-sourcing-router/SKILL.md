---
name: 1688-sourcing-router
description: 1688 找品统一路由——6 个 lineage 归一为「CDP 主驱动 + 品类分流 + 避坑铁律」，消除 lineage 漂移。Use when 任何 1688 找品/比价/选品任务先来判断走哪条路径、用哪个脚本。
version: "1.0"
author: Nous Research
license: MIT
group: 1688
metadata:
  hermes:
    tags: [1688, sourcing, router, 1688-cdp]
    related_skills:
      - 1688-search-cn-gb-region-skill
      - 1688-bag-sourcing
      - 1688-matrix-dimension-sourcing
      - 1688-cdp-product-fetch
      - 1688-price-extraction
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

## When to Use

**Use when any task asks for 1688 product sourcing, price comparison, or candidate selection** — the first decision is always: 3D box/盒/袋 (3D) vs 2D soft packaging (2D), then `cdp1688.py` vs `cdp1688_bag.py`. This skill is the router + single source of truth; the underlying lineage skills are loaded on demand, not re-implemented.

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
8. **降速防验证码 + 搜页通道优先级（PC唯一主通道，--mobile是濒死时的最后兜底）**：
   - 每详情页 `--gap 2.5~8s`；搜页被 PC 拦 → 指数退避（15/30/45/60s）重试 PC
   - **PC 仍被拦？→ 等待消退再重试，不是切 mobile**（坑62：移动端搜页 `m.1688.com` 对多数尺寸词返回**纯推荐垃圾**——整个结果区被「趋势商机/猜你喜欢」接管，逐一核验全是非纸盒。mobile 只在 PC 搜页**完全失灵**且你急用时才最后兜底，且必须接受 mobile 候选质量远低于 PC）
   - 同一 9222 同一时刻只跑一个 `cdp1688` 循环（并行会清空结果）。
9. **登录态静默丢失是头号假阴性**：搜出"全是其他品"/0 命中 → 先探 detail 页是否跳 taobao.com。填 `preflight_1688.py` 当探针。`chrome-cdp-profile` 独立实例风控极严，根本解法 = 用户保持默认 Chrome 已登 1688，或 `--reverify` 只验已知 ID 池。
10. **正则零反斜杠**：写 `.js` 用 `[0-9]`/`[ ]` 替 `\d`/`\s`（write_file/heredoc 会双写反斜杠致语义错）。JS 一律独立文件读入（AppleScript `as «class utf8»`），不内联（会被转义吞）。
11. **输出铁律**：先给结论+链接+价格表，再补必要说明。不铺原理/坑位/分析墙。
12. **多词多页必走两段式，禁一次性跑主驱动**：`cdp1688.py` 的 `.ids.json` 在**所有**搜索完成后才落盘；`--cat` 3-4 词 × `--pages` 3-4 时搜索循环常耗满 600s 前台超时且**零落盘**（白跑）。正确做法：① 轻量脚本 `Target.attachToTarget` 复用已开搜页，逐词逐页抓 ID 并**每页增量落盘**到 `<out>.ids.json`（复用 `cdp1688.EXTRACT`）；② `cdp1688.py --dims ... --resume <out>.ids.json` 跳过搜索直接核验。搜索页 `search_page_captcha()` 易误判，先 attach 实测 `outerHTML` 是否真含"验证码"再决定退避。
13. **核验尾段登录墙早停**：核验后期详情页连续返回 `evaluate -> dict`（登录墙）时，命中已增量落盘，直接 kill 进程用现有结果，别等跑完；此时 `inject_cookies.py` 常读 0 cookie（默认 Chrome 无登录态），重启 CDP 实例也清不掉账号/IP 级风控。地域在 `province=江苏,浙江,上海` 搜页阶段已服务端筛掉，不必再逐条抓详情页 `location`（登录墙下抓不到）。

## 已验证样例（证明 lineage 有效）
- `46*26*10cm 加高飞机盒`：用户给 `752445610436` 即命中（全角组合串写法），¥3.81 现货，13 款长 42-54。
- `14*20cm 白边*12丝 自封袋 义乌`：18 家含尺寸，白边(含红边)+12丝 精确双中 3 家（`685142110437` 等）。
- `16*16*16cm 纸箱 江浙沪`：6 家真命中，剔除 1 个广告文案误中（`751990874462`）。

## 决策 SOP（30 秒定位）
```
1. 2D 软包装? → cdp1688_bag.py | 否则 → cdp1688.py
2. 跑 preflight_1688.py，PASS 才开 main
3. 用户给链接? → 先验他的线索（reverify_pool 模式）别从零狂扫
4. **0 命中时自动切近邻定制兜底（不询问，直接跑）**：
   ```
   精确0命中 → 近邻尺寸(find_near.py) + 定制厂推荐 → 结论表(含近邻尺寸+定制渠道)
   ```
   用户说"也可以找XX尺寸"时 → 立刻并行跑，不等用户追问。近邻尺寸定义：目标尺寸任一轴±3cm内有现货的厂家，即推荐为「可定制切此尺寸」。结论表须同时含：①近邻现货(有该尺寸)②定制渠道(有相近轴可切)③不单独报"无货"。

5. **多尺寸并行**：用户说"也可以找18*15*10的" → `--dims "18*14*10" "18*15*10"` 同时传入并行搜、并行验，一次出对比表。
6. 出结论表（ID|规格|单价|库存|卖家|链接），不堆分析
```


## 市场对标与可替代性

本章给 1688 找品的商业/半商业方案建立量化对标，帮助用户做「自建 vs 买服务」决策。

| 方案 | 拉取方式 | 无需代理 | 深度核验 | 登录态要求 | 个人可用性 |
|---|---|---|---|---|---|
| **本机 CDP 方案**（cdp1688.py + skuMapOriginal） | 浏览器后台实例 + WebSocket | 否 | 最高（规格多写法 + 顺序无关 + 全页兜底） | 需 1688 登录态 | ✅ 零风控 |
| 1688-Scraper-MCP（DrissionPage） | 浏览器 CDP / 模拟 | 部分 | 中（DOM 点 chip 抠价，有风控痕迹） | 需 1688 登录态 | ⚠️ 详情页可用 |
| Accio Work（阿里官方 MCP） | 官方 API + 自然语言 | 部分 | 中（资质审核+多渠道） | 无 | ❌ 企业专用 |
| AutoDS | 整合多平台 | 部分 | 中（说话重写+下单） | 部分 | ❌ 平台绑定 |
| Workus | 全链路采购 | 部分 | 中（人工检查） | 部分 | ❌ 团队/企业 |
| Sorsa | 50+ 平台问答 | 否 | 低（问答式） | 无 | ⚠️ 部分 |
| Jungle Scout | 亚马逊零售情报 | 否 | 低（亚马逊专属） | 无 | ❌ |

**结论更新（2026-11 全网复调后修正）**：本机自研 CDP 脚本不再是首选。首选开源 `1688-cli`（155 stars / MIT / npm i -g 1688-cli，2026-08 仍活跃），已解决自研踩过的全部坑：`search --deeppro` 搜索即批量抓详情；翻页走「点击下一页」而非 `&beginPage=N`（后者换新 pageId 返回约75%重复，是搜索阶段卡死主因）；mtop 拦截非 DOM；持久 profile 一次登录管数周；punish/x5sec 风控分类；批量 `offer <ids...>`；JSON 输出。命令：`1688 search "15*15*15cm纸箱" --max 100 --deeppro`。彻底免浏览器/免风控走付费 API：silklinedata `/v1/1688/search`（$0.0048/条，一次返回 offerId/price/tierPrices/supplierName/shopUrl/province/city/isAd = 单价+链接+店铺+所在地全字段）；api.sh 1688 search（60条/页，shop.name + shop.url + 月销）；onebound item_search/item_get（area + seller_nick + SKU）；JustOneAPI get-item-detail（companyName + delivery.location + 阶梯价）。官方开放平台 alibaba.product.get 只能查自己产品，不适合找外部货源。反爬新思路（油猴页面端采集）：PageHarvest（5 stars MIT）、CaltonRen/1688Collector（油猴翻页+域名字段）、jiyun/1688（80 stars，SingleFile 存 HTML 后本地解析）。1688-Scraper-MCP（13 stars）DrissionPage + location_filter/only_factory 本地过滤只回前5条省 token。

## 真人模式 SOP（用户定义流程，2026-11 复盘定稿）
用户定义：搜页推荐出来的条目即真实候选，逐个打开详情页找目标尺寸记录反馈。核心原则：**搜页即真相源，详情页只补尺寸**。
1. 搜页一次拿全：2-3 个关键词（精确尺寸词如 `15*15*15cm纸箱` + 品类词如 `正方形纸箱`），每个 2 页。从 DOM 卡片 `[data-offer-grid-cell]` 一次性提取 offerId + **店铺名（卡片 innerText 最后一行）** + 卡片价 + 商品链接，每页增量落盘。
2. 详情页只做一件事：在 SKU 里找目标尺寸，命中记录该 SKU 单价。**不抓 location、不抓 companyName**（搜页已给，且登录墙下必失败）。登录墙跳过，连续5个才停。
3. 输出表直接拼第1步的店铺名+链接 + 第2步的尺寸单价，无需事后补抓。
4. 禁加品类硬卡 CARTON_SIG：用户明确「搜页推荐的店铺就是真实的」，额外过滤会误杀。
5. **异常早停**：连续 evaluate 返回 dict（登录墙）立即 kill，用已落盘结果。

## 【最优方案】1688-cli 已安装且登录态就绪（2026-11 实测，取代所有自研脚本）
本机已装 `1688-cli@0.1.47`（`/Users/aimac/.local/lib/node_modules/1688-cli`，bin 名是 `1688` 不是 `1688-cli`；调用用 `node "$(npm root -g)/1688-cli/dist/cli.js"`，因 PATH 无软链）。**它的 default profile 已登录**（doctor 显示"罗庆富 memberId 176760586, cached"），有独立 `~/.1688/profiles/default/` + daemon，不依赖 9333、不需重新登录。

**实测一次调用即返回全部所需字段**（单价 text/min/max、店铺 supplier.name + shopUrl、所在地 location.province/city、工厂/回头率/销量/商品链接）：
```bash
node "$(npm root -g)/1688-cli/dist/cli.js" search "15*15*15cm纸箱" \
  --max 20 --province 浙江 --sort price-asc --json
# 常用：--pick 'offers[*].offerId,offers[*].price.text,offers[*].supplier.name,offers[*].location,offers[*].url'
# 深抓SKU：--deeppro（搜索后逐条抓详情，重试3次，间隔6-10s）
# 过滑块：--headed（开窗口手动滑）
```
实测 `--province 浙江` 返回 10 条全是浙江（义乌/金华/苍南），`--province 江苏` 返回 4 条全江苏，`--sort price-asc` 价格从 ¥0.06 升序。

**为何是最优**：一次调用拿全字段（无需事后补店铺/所在地）、内置翻页风控（点击下一页避开 beginPage 75% 重复坑）、独立持久 profile（互不污染）、JSON/`--pick` agent 友好、daemon 预热。彻底解决 2026-11 那次全部问题：搜索超时零落盘、登录墙、店铺补抓绕远、x5sec 软风控、self 脚本割裂。

**调用铁律**：
1. 先 `node ... doctor` 确认 session=ok，否则要重新扫码（不是用 9333）。
2. 找品默认走 1688-cli；只有需要精确 SKU 矩阵/组合串尺寸核验时才回退 `cdp1688.py`（连 9333）。
3. `--json` 输出直接 Python json.loads 解析，按 dimension 关键词过滤标题+SKU。
3. **别密集并发**：一次 6-9 个连续 search 会触发 `DAEMON_PAUSED`（连续失败暂停到某时刻）继而 `NOT_LOGGED_IN`，**且需重新扫码**（违背不重登录铁律）。恢复只能 `daemon reload`，但 session 已失效则救不回。正确节奏：单次 search 间隔 ≥5s，一次最多 3 个词。
4. 结果表直接 cli 已含的 price+supplier+location+url，无需开详情页补。
5. **cli 搜页价格是卡片起批价，绝不是目标尺寸价**（2026-11 教训：曾把 ¥0.10 卡片价当 15*15*15 价报出，实际该 SKU 是 ¥0.61——页面默认选中别的尺寸如"13号"）。**必须从详情页 skuMapOriginal 按 specAttrs 精确匹配目标尺寸抠 price**。新版 ant-design 页 `PRICE_JS` 的 targetPrice 返空，别依赖；直接正则 `"specAttrs":"([^"]*)"[^}]{0,400}?"price":"([0-9.]+)"` 扫 skuMapOriginal（price 也可能在 specAttrs 之前，两种顺序都匹配）。实测 7 家都抠到精确价（¥0.48–1.10）。

## 真人模式首选脚本 human_mode.py（2026-11 实测通过，已被 1688-cli 取代为兜底）
用户定义真人模式 = 搜页推荐的即真实候选，逐条开详情页找尺寸。`scripts/human_mode.py` 固化此流程：阶段1 从 `[data-offer-grid-cell]` 卡片**一次拿全**（ID+标题+店铺名+卡片价+链接，每页增量落盘）；阶段2 逐条详情页只补目标尺寸 SKU（`cdp1688.CDP.get_sku`），命中即用阶段1的店铺名+价直接出表。默认连 9333 已登录实例，零注入零新建。实测：2词×1页=113候选，核验12条命中4条（¥0.44–1.09），1.5s间隔无验证码。
```bash
bash start_cdp_1688.sh   # 9333在线即复用
python3 human_mode.py --dims "15*15*15" --kw "15*15*15cm纸箱" "正方形纸箱" --pages 2 --maxverify 60 --out store/human_15cube.json
```
复杂矩阵/组合串尺寸仍需 `cdp1688.py`（5类写法+容差+品类硬卡更全）；简单目标尺寸优先 `human_mode.py`。

### ID 池精确抠价脚本 verify_dim_pool.py（2026-11 新增，cli 搜索后必经）
1688-cli 搜页卡片价是起批价，绝不能当目标尺寸价。先用 cli `search ... --json` 拿 offers 落盘，再跑 `scripts/verify_dim_pool.py --dim "16*16*16" --pool offers.json --out hits.json`：连 9333 常驻实例、逐条详情页从 skuMapOriginal 按 specAttrs 精确匹配（target_perms 顺序无关 + extract_sizes_from_spec 5 类写法）抠 price/stock，店铺/所在地/链接从 cli 结果透传，每 3 条增量落盘、登录墙连续 5 条早停、结束关 tab。实测 28 候选 → 8 命中（¥0.69–0.80），江苏落选品抽查确认 137 个 SKU 全是邮政编号尺寸、真无目标尺寸而非漏检。

### 滑块解锁能力：实测通过（2026-11）
`cdp1688.human_slide()` 用 CDP `Input.dispatchMouseEvent`（isTrusted=true）做拟人拖动：变速缓动 + 随机抖动 + 终点回弹。**真实滑块页实测一次通过**（阿里 nc 文案"请按住滑块，拖动到最右边"，定位 x=833/y=539/dist=258px，拖动后滑块标记消失、页面恢复 47 个商品、会话未封）。触发方式：连续 `navigate` 同一搜页 URL 约 5 次后风控出滑块（高频 1.2s 间隔不一定触发，登录态健康时正常搜索基本不出）。
- `human_slide()` 前置检测只看 HTML 是否含"验证码"字样，无此字样直接返回 True（不会白拖）。
- 主驱动 `cdp1688.py` 搜页/详情页检测到验证码已自动调 `human_slide`（2 次尝试），失败才退避 15/30/45/60s。
- **真人模式 human_mode.py 暂未接 human_slide**：当前用 9333 健康登录态基本不触发，若后续频繁撞滑块再加。
- **坑：主动高频测滑块会把会话玩进 x5sec 软风控**（2026-11 实测）。搜页 HTML 藏 `punish?x5secdata=...capslide...`，正文空、卡片 0，但详情页完全正常。此时 `human_slide()` 返回 **假阳性 True**（页面无"验证码"字样直接 return，实际没解）。解法：① 别主动压测滑块；② 搜页被 x5sec 封时改走 `--resume` 用已有 ID 池 + 详情页通道（详情页不受影响）；③ 等几小时让 x5sec 自然消退才有新搜页候选。
- **误判铁律（2026-11 用户纠错）**：报"等待滑块/需要手动解锁"前，必须先用数据证明——实测 `document.body.innerText` 含"滑块/拖动"文案 且 `JS_FIND_SLIDER` 返回 `ok:true` 才算真滑块。只凭"没抓到数据"就甩给用户手动滑是错的：2026-11 一次误判中，详情页 SKU 141KB 正常、搜页 60 卡片正常、1688-cli 登录态 cached，根本无滑块。`human_slide` 已加 x5sec 识别（软风控返 False 不假阳性）。

### 浏览器实例铁律（2026-11 用户纠错，最高优先）
**绝不新建无头/临时实例、绝不注入 cookie。** 用户 1688 登录态在**已登录的常驻实例** `~/.chrome_1688_scraper`（端口 **9333**，headful），Cookies 458KB、登录态长期有效。2026-11 曾误用新建的 `chrome-cdp-profile`（9222）+ `inject_cookies.py`（读到 0 cookie）导致登录态失效、全程验证码/登录墙、结果残缺——根因就是换了实例。
- 主驱动/探针默认端口统一 **9333**（cdp1688.py、preflight_1688.py 已改）。
- `start_cdp_1688.sh` 改为：9333 在线直接复用；不在线才用同一 profile 拉起（登录态仍在）。**不注入 cookie、不 headless、不新建 profile**。
- 详情页遇登录墙直接跳过（连续 5 个才停），**禁止自动重注入**（污染干净会话且读到 0）。
- 任何任务结束**不关 9333 实例**，保持常驻供下次复用。

本次反例（耗时约40分钟）：搜页只抓ID丢店铺名→事后补抓6分钟；4词×4页→600s超时零落盘；核验抓location→登录墙白费；登录墙尾段等进程自然结束→空转8分钟。按此 SOP 预计 5-8 分钟。

**数据来源边界**：本机无住宅代理 → 接口直连（MTOP）仍走不通，维持「真浏览器后台 CDP + skuMapOriginal 监听」为最优解。1688 MTop 签名公式（公开逆向）为：`sign=MD5(_m_h5_tk前半 + & + t毫秒 + & + appKey(12574478) + & + data)`，token TTL~24h 需刷新，但中国住宅代理仍是必需条件。
