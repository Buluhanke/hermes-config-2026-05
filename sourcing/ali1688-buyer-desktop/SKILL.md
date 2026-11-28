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

mtop 需要签名，不能无脑直调；**让页面 UI 触发**（填词+提交）再从 CDP 抓 `Network.getResponseBody` 或读渲染 DOM 拿结果，是当前最可行路径。2026-11-28 实测：接口已抓到，但 React 受控输入+提交交互未调通（textarea 用原生 setter 填值后回车/按钮点击未触发 deepsearch 出结果），待继续调试。

## 找品策略

- `deepth_search` 与旧 scraper **互补**：AI 返回结构化总结+精确 SKU 价；scraper 适合批量尺寸核验/skuMapOriginal。按任务选。
- 用户铁律不变：不自加未请求筛选（江浙沪等）、结果给「ID|规格|单价|链接」干净表、价格必须目标 SKU 精确价。
