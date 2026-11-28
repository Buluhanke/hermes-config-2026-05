---
name: ali1688-buyer-desktop
description: 用1688买家工作台做AI找货/卖家聊天/内置CDP，及9333端口排查。
version: 1.0.0
author: Hermes Agent
license: MIT
tags: [1688, ai选品, 找货, cli, cdp]
metadata:
  hermes:
    tags: [1688, ai选品, 找货, cli, cdp]
    related_skills: [1688-sourcing-router, 1688-search-cn-gb-region-skill]
---

# 1688 买家工作台桌面客户端（源采·AI）

## When to Use

用户要用 1688 买家工作台客户端做 AI 深度找货、联系卖家、内置 CDP 浏览器自动化，或排查它的 9333 agent 端口冲突时使用。

## 它是什么

macOS 客户端 `/Applications/Ali1688Buyer.app`，版本 11.02.14YM（2026-09）。
Qt + CEF 壳（Chromium 108），三个模块：`Ali1688Buyer` / `WW`(旺旺) / `Ali1688YuanCai`(源采AI)。
登录态在 `~/Library/Application Support/WW1688CEF/User Data`，账号目录 `罗庆富#8#176760586`。
界面：源采·AI 生意采购工作台，「全能助手 / 快速搜索」+ AI 输入框，底部「每日订阅更新 / AI盯资源 / 模板案例」。

## 官方 Agent 接口

客户端内置文档（本地就有）：
```
/Applications/Ali1688Buyer.app/Contents/Resources/cli/
  SKILL.md 1688-cli
  references/{product-search,browser-cdp,chat,contacts,cli-transport}.md
```
协议：`POST http://127.0.0.1:9333/tools/call`，body `{"tool":"<名>","arguments":{...}}`；或 `1688-cli <tool> --args '<json>' -o result.json`。成功顶层 `result`，失败 `error`。

工具：
- `deepth_search` — AI 深度找货。参数 `desc`(必填)、`reRank`、`pageNum`、`priceIdx`、`ptsServiceListIdx`(free_post/no_reason_to_return_7d/yfx)、`itemIcSearchTags`("1988226"=一件代发)、`is24hourSend`/`is48hourSend`/`isHighSales`/`goodReview`/`onePcsSale` 等。返回 `offer_id` + `basic_info`(AI商品总结) + `price_info`(精确单价) + `seller_info`(公司/发货地/评分)。**比旧 scraper 卡片价准得多**。
- `browser_open`/`browser_cdp`/`browser_list_pages`/`browser_overlay`/`browser_close` — 内置 CDP 浏览器，pageId 标识。
- `open_chat`/`send_chat_message`/`silent_send_message` — 卖家聊天；nick 不加 cnalichn 前缀。
- `search_contact` — 联系人搜索。

## ⚠️ 9333 端口冲突（本机已踩）

客户端 agent HTTP 服务固定 9333，而 1688 scraper Chrome 常驻实例也是 9333（~/.chrome_1688_scraper）。端口被占时客户端**静默不启动 agent 服务**（无报错、无监听、`/health` 无响应、CLI 返回空）。

排查：
```bash
lsof -nP -iTCP:9333 -sTCP:LISTEN
curl -s http://127.0.0.1:9333/health          # 客户端在时返回 JSON
curl -s http://127.0.0.1:9333/json/version    # 返回 Chrome/... 即 scraper 占着
```
迁端口（实测可行，同 profile 登录态保留）：
```bash
pkill -f "remote-debugging-port=9333"
open -n -g -j -a "Google Chrome" --args --remote-debugging-port=9334 \
  "--remote-allow-origins=*" --user-data-dir="$HOME/.chrome_1688_scraper" about:blank
# 重启 Ali1688Buyer 让它占 9333
```
用完迁回 9333（用户铁律：常驻不关）。

**当前状态（2026-11-28）**：Mac 版 agent 服务即使 9333 空出仍未起来，原因待查（可能 Mac 版未开放或需 App 内开关）。遇事先验证，别假设能用。scraper 已恢复 9333。

## 官方下载地址

静态 `latest-updater.dmg` 是 2022 旧版(0.0.7)。最新版走 mtop：`mtop.ali.cbu.wireless.merchant.getStableVersion`，参数 `{"platform":"buyer_pc_mac"}`（不是 "mac"）。2026-09 返回 v11.02.14YM（Win 用 buyer_pc_win）。

## 网页版同源接口（可绕过客户端 agent 服务）

`cai.1688.com` 是同一套 AI 工作台的网页版，在 9333 scraper Chrome 里已登录（账号 yiwuxunlong）。
界面：全能助手 / 快速搜索（找货源 / 以图搜款）/ 批量找货 / 竞店追踪 / 生意研究 等。
AI 输入框是受控 textarea，需 React 原生 setter + input 事件填值，再触发提交才能出结果。

抓到的核心 mtop 接口：
- `mtop.alibaba.cbu.ai.yuancai.deepsearch.router` — AI 深度找货，参数 `{"type":"offer","query":"<描述>"}`（type 还有 company 等）。
- `mtop.alibaba.cbu.ai.native.gateway.ai.chat.scene.history.list` — 助手历史。
- `mtop.alibaba.cbu.ai.native.gateway.ai.starry.entrance` — 入口/建议，参数 `{"serviceName":"userSuggestionService","params":"{}"}`。

mtop 需要签名（appKey=12574478，sign=md5(token&t&appKey&data)，token 来自 `_m_h5_tk` cookie）。可在页面内 `fetch(带签名的完整URL,{credentials:'include'})` 成功调用，返回 `{"result":"fast_search"}` 路由结果。

**完整找货链路（2026-11-28 实测跑通）：**
1. `cai.1688.com` → 点「快速搜索」(DIV x≈1175,y≈244)
2. textarea（宽>100，placeholder 含「精准描述找货源」）用 React 原生 setter 填词 + dispatch input 事件 → 回车
3. 触发 `deepsearch.router`，随后**自动开新标签页** `cai.1688.com/newOfferSearchResult?q=<词>&intention=deep_search|fast_search`（这就是之前以为"没结果"的原因——结果在另一个 tab，不在原页）
4. 结果页初为空壳，需再点页面内「搜索」按钮 → 加载出筛选维度（极速发货/一件代发/超级工厂/48h发货等）+ 商品列表表头（起批量/90天销量/核心属性/店铺信息）
5. 商品行数据异步填充；「帮我搜索」是渐变按钮内文字，非叶子节点，要找父元素点击

**关键**：`intention=deep_se` = AI 深度对比筛选，`fast_se` = 快速列表。搜索词自动进「搜索历史」。

**签名直调模板**（页面内 fetch，credentials:include，token 从 document.cookie 的 `_m_h5_tk` 取 `值.split('_')[0]`）：
```
https://h5api.m.1688.com/h5/mtop.alibaba.cbu.ai.yuancai.deepsearch.router/1.0/
 ?jsv=2.7.5&appKey=12574478&t=<ms时间戳>&sign=<md5(token&t&appKey&data)>
 &v=1.0&type=originaljson&dataType=json&timeout=30000&showErrorMsg=true
 &api=mtop.alibaba.cbu.ai.yuancai.deepsearch.router&data=<urlencode(json)>
```
注意：`router` 只是路由，真正商品列表接口是结果页再点「搜索」后才发，待继续抓。

## ✅ 已跑通：AI 找货自动化脚本（2026-11-28 定稿）

**首选方案** `scripts/cai_find.py`（自包含、零签名、真人式、稳定）：
```bash
python3 ~/.hermes/skills/sourcing/ali1688-buyer-desktop/scripts/cai_find.py "46*26*10cm纸箱" --limit 20
python3 .../cai_find.py "14*20cm 白边自封袋 12丝" --json   # JSON 输出
python3 .../cai_find.py "..." --intention deep_search       # AI 深度对比模式
```
输出：`offerId | 精确单价 | 店铺 | 标题 | 链接(https://detail.1688.com/offer/<ID>.html)`。

**原理（关键，别再走弯路）**：
1. 直接打开结果页 `cai.1688.com/newOfferSearchResult?q=<词>&intention=fast_search|deep_search`（URL 编码用 utf-8）。页面**自动加载**商品卡片，不需要点任何按钮。
2. 轮询 `[class*=offerCardItemMainWrapper]` 卡片出现（约 4-8 秒，AI 慢时更久）。
3. **从卡片的 React fiber 链**（`__reactFiber$xxx` → 逐层 `memoizedProps`）提取 `offerId`/`title`/`price`——这是唯一能拿到 offerId（=链接）的可靠来源；DOM 兜底店铺/销量/回头率。
4. DOM 的 class 名带 hash 后缀（如 `offerCardItemTitleText--U6eulQN6`），必须用 `includes` 匹配，不能用精确选择器。
5. 标题可能含 `<font color=red>` 标签，输出前正则清洗。

**踩过的坑（勿重试）**：
- ❌ 点主页「搜索」按钮：坐标会漂移（刷新后 y 从 244→206），React 受控输入+回车极不稳定，时而触发时而不触发。
- ❌ `chat.entrance` SSE 抓包：`acs.m.taobao.com` 域名，`FAIL_SYS_ILLEGAL_ACCESS`，签名直调也不行；SSE body 流未结束取到空，时序难控。
- ❌ 主页 textarea 填词：受控组件需原生 setter，且提交不可靠。
- ✅ 正解：直接开结果页 + 等卡片渲染 + React fiber 取数。像真人看页面，不依赖任何接口/签名/点击。

**限制**：返回的是 AI 推荐商品（未必严格匹配所有规格，如尺寸/厚度/白边需自己按标题判断）；要核验精确 SKU 规格价仍用旧 scraper 的 skuMapOriginal。两者互补。

## 找品策略

- `cai_find.py` 用于 AI 语义找货（模糊描述、找方向、找店铺）；旧 scraper 用于精确尺寸 SKU 核验。
- 用户铁律不变：不自加未请求筛选（江浙沪等）、结果给「ID|规格|单价|链接」干净表、价格必须目标 SKU 精确价。
