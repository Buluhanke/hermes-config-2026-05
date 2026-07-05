---
name: web-search-paths
description: Hermes 联网搜索固化路径 — 接到搜索任务时走这条路径，像重启网关一样明确
trigger: 触发词包括"搜索一下"/"查一下"/"联网"/"网上"/"搜"/"search"/"look up"
version: 1.1.0
author: hermes-digital-resident
created: 2026-07-06
validated: 2026-07-06（工商银行搜索实战验证）
---

# Web Search Paths — 联网搜索固化路径

## 核心原则（修订版 2026-07-06）

用户说"搜索" → 立即走本 skill 定义路径，**不使用** browser_navigate + 手动翻页，除非本 skill 明确指定的场景。

**额外铁律：任何技术实现类任务，先搜现成方案再动手写代码。** 搜索关键词："best practice 2026 / production ready / github stars top"。找到后验证 star 数 + 最后更新时间 + 维护活跃度，再决定用哪个。只有确认没有现成方案时才自己写代码。

**Ponytail 6步决策梯子在此场景的应用：**
1. 这东西真的需要写代码吗？→ 先搜现成工具/skill
2. 标准库/原生能力覆盖了？→ 用现有工具链
3. 已装的依赖能解决？→ 用现成方案
4. 社区有现成 skill？→ 直接安装（`hermes skills install`）
5. 能用一条命令解决？→ 不写脚本
6. 写完才：最小能 work 的代码

**案例（2026-07-06）**：需要接管用户真实 Chrome → 找到了 pasky/chrome-cdp-skill（3.1k stars），不需要自己写脚本。

---

## 路径一：通用搜索（最高优先级）

**触发：** 任何开放式搜索任务

**工具：** `web_search_plus`

**调用方式：**
```
web_search_plus(
  query="<用户问题>",
  provider="auto",        # 智能路由，按查询类型自动选最佳 provider
  depth="normal",         # 普通搜索；研究类任务用 "deep"
  count=5                # 默认返回 5 条
)
```

**归约规则：**
- `provider="auto"` 时，系统自动选：Serper(新闻/购物) / Tavily(研究) / Exa(语义) / Brave(通用)
- 不需要手动猜 provider，auto 会自动判断
- 研究类任务（3+ 源交叉验证）→ `depth="deep"` + `count=10`

**输出处理：**
- 提取 title + url + description
- 命中用户预登录 AI 站点（gemini.google.com / chat.deepseek.com / chatgpt.com 等）→ 优先 `browser_navigate` 提取内容
- 多源矛盾 → 标注"待验证"，不强行统一

---

## 路径二：内容提取（网页 → 结构化文本）

**触发：** 已知 URL、需要提取页面内容

**工具：** `web_extract`（Trafilatura + Firecrawl 后端）

**调用方式：**
```
web_extract(
  urls=["https://example.com/page"],
  char_limit=15000  # 默认截断，可调大
)
```

**优先后端：**
- `extract_backend: firecrawl` — 已配置，支持 JS 渲染
- 失败时降级到 `web_extract_plus(provider="linkup")`

**归约规则：**
- 提取成功 → 直接用 markdown 内容，不走 VLM 总结
- 提取失败（非 200）→ 记录错误，尝试 browser_navigate 兜底
- PDF 链接 → 直接传 URL 到 `web_extract`，自动处理

---

## 路径三：AI 网站查知识

**触发：** 用户问的问题涉及已登录的 AI 网站知识

**已登录站点：**
- https://gemini.google.com/app
- https://www.doubao.com/chat
- https://chatglm.cn/main/alltoolsdetail
- https://chat.deepseek.com/
- https://chatgrawl.com/
- https://grok.com/

**工具：** `browser_navigate` + `browser_snapshot`

**调用方式：**
```
browser_navigate(url="<目标站点>")
browser_snapshot()  # 提取页面内容
```

**归约规则：**
- AI 网站优先走 browser_navigate，可直接拿到对话内容
- 不需要 login，因为浏览器已保持登录态
- 页面是聊天界面 → 用 browser_snapshot 提取当前可见消息

---

## 路径四：复杂研究（组合模式）

**触发：** 跨多个源、需要交叉验证的研究任务

**调用序列：**
1. `web_search_plus(depth="deep", count=10)` — 广度搜索
2. 收集 top URLs
3. `web_extract(urls=[...])` — 批量提取内容
4. 汇总矛盾点，标注待验证

**deliver 语义：**
- 研究结果 → 写入 fact_store + 推送 Telegram
- 不只返回结果，要带"这个结论来自 X 个源，Y 个矛盾"

---

## 工具选择决策表

| 场景 | 工具 | 原因 |
|------|------|------|
| 开放式搜索（"查一下 X 是什么"） | `web_search_plus` | auto 路由最省力 |
| 已知 URL 提取内容 | `web_extract` | 直接拿 markdown |
| AI 网站对话内容 | `browser_navigate` | 登录态保留 |
| 复杂研究（3+ 源） | `web_search_plus(deep)` + `web_extract` | 广度 + 深度 |
| PDF/论文 | `web_extract(url)` | 直接处理 URL |
| 兜底（以上全失败） | `browser_navigate` | 最后一搏 |

**铁律：禁止截图OCR。** 浏览器可见内容必须用 CDP Runtime.evaluate 提取 DOM 文本，或用 browser_snapshot 读 AX tree。只有在 DOM 提取返回空/乱码 时才允许截图。

**流程：CDP Runtime.evaluate（最快）→ browser_snapshot AX树（次快）→ browser_vision截图（兜底）**

用户说"不要截图OCR，懂得识别浏览器内容" = 触发词，0思考走 CDP 路径，不走截图。

---

## 常见错误

### ❌ 错误 1：跳过了 web_search 直接 browser_navigate
**正确：** 先 `web_search_plus` 找 URL，再 `web_extract` 提取

### ❌ 错误 2：用 VLM 总结提取的内容
**正确：** `web_extract` 出来的 markdown 直接用，不需要 VLM 再总结

### ❌ 错误 3：研究任务返回结果就结束
**正确：** 研究任务必须写 fact_store + 推送，否则 0 价值产出

---

## web_extract 失败模式与兜底策略

### 已知拦截站点（2026-07 实测）
以下站点对 `web_extract` / `web_extract_plus` 返回 `Unauthorized`，需要降级：

| 站点类型 | 示例 | 拦截原因 |
|----------|------|----------|
| 财经门户（需登录） | moomoo.com, tradingagents-cn.com | token 验证 |
| 研报聚合 | chaguwang.cn, jrj.com.cn | 封禁爬虫 |
| 部分 JS 渲染页 | 股票分析页 | 静态抓取失效 |

### 降级链（严格按顺序）
```
web_extract
  → web_extract_plus(provider="linkup")
  → web_extract_plus(provider="tavily")
  → browser_navigate + browser_snapshot
  → 搜索结果摘要直接用（最终兜底）
```

### 铁律
**搜索结果摘要已含足够信息时，直接用搜索结果回答，不强求完整提取页面。**
本次工商银行案例：搜索结果已含 AI 评分（90% 看多）、目标价（¥8.7）、机构预测（15家均值）、广发证券观点，无需进一步提取页面。强行提取失败 → 降级成功，不卡死。

---

## 验证清单

搜索任务完成后自问：
- [ ] 调用了 `web_search_plus`（或其他指定工具）吗？
- [ ] 结果是否命中 AI 网站 → 走了 browser_navigate 路径？
- [ ] 提取内容是 markdown 格式直接用吗？
- [ ] 研究类任务 → fact_store 写入 + Telegram 推送了吗？
- [ ] web_extract 失败时是否走了降级链（linkup → tavily → browser_navigate → 直接用搜索结果）？

---

## 与其他 Skill 的关系

- `community-first-research` — 社区优先搜索，组合使用时走本 skill 的工具链
- `browser-cdp-control` — 浏览器控制兜底，本 skill 走不通时调用
- `hermes-see-act` — 看屏幕决策，搜索意图识别后走本 skill
