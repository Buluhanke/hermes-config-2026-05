# AI 搜索能力突破（2026-07-10 研究）

## 核心事件：Google I/O 2026（5月19日）

Google 宣布「Search IS AI now」，搜索框本身就是 AI 对话入口，不再是关键词匹配。

**Gemini Spark** — 7×24 个人 AI agent，常驻内存，持续工作

## 主要新能力

| 能力 | 代表产品 | 状态 |
|------|---------|------|
| AI Mode 全面上线 | Google AI Mode | 2026年上线 |
| 个人 Agent 常驻 | Gemini Spark | 7×24 运行 |
| Agent 集成搜索（提问即触发多步任务） | Google AI Mode | 早期 |
| 实时爬取+引用 | Perplexity | 已成熟 |
| 联网搜索 | ChatGPT Search | 已成熟 |

## 搜索质量对比

- **Google AI Mode** — 全面覆盖，源头可信
- **Perplexity** — 研究场景最强，引用最规范
- **ChatGPT Search** — 日常最快，Plus 用户免费
- **DeepSeek** — 推理能力强，联网是附加功能
- **Kimi** — 中文理解好，超长上下文

## 对 Hermes 的启示

现有工具已覆盖：
- `web_search_plus` — 多引擎聚合（web_search + research 模式）✅
- Chrome CDP — 浏览器控制，AI 网站对话 ✅
- 11 个 AI 网站全部已登录 ✅

**差距**：还没有 agent 级别的多步任务自动执行链（规划→搜索→整理→通知）

## 研究问题时的工具链

```
web_search_plus(mode='research')  → 深度研究（5-10个源）
browser_navigate → AI 网站对话  → 交叉验证
```

**最佳实践**：
1. `web_search_plus research` 拿基础数据
2. DeepSeek/Kimi/Gemini 各问一次同一问题
3. 交叉验证，取最优答案
