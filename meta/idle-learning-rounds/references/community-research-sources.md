# Hermes Agent 社区研究 — 信息来源可靠性指南

**状态**: 已验证 (2026-07-02 cron 社区巡逻实测)
**用途**: idle_learning 变体步骤1「Search 社区」时快速判断某来源是否值得抓取

## 信息来源矩阵

### ✅ SSR / 可直接抓取（web_extract / curl 成功）

| 来源 | URL | 内容类型 | web_extract 结果 | 获取方式 |
|---|---|---|---|---|
| 知乎 | `zhuanlan.zhihu.com/p/...` | 中文深度教程 | ✅ 成功，返回 ~5k 字 | `web_search` 找链接 → `web_extract` |
| CSDN (AI Agent 社区) | `agent.csdn.net/...` | 技术教程 | ✅ 成功 | `web_search` 找链接 → `web_extract` |
| 菜鸟教程 | `www.runoob.com/ai-agent/hermes-agent.html` | 入门指南 | ✅ 成功 | `web_search` 找链接 → `web_extract` |
| 36氪 | `www.36kr.com/p/...` | 产品分析/评测 | ✅ 成功 | `web_search` 找链接 → `web_extract` |
| 博客园 | `www.cnblogs.com/...` | 个人技术博客 | ✅ 成功 | `web_search` 找链接 → `web_extract` |
| 绿联NAS社区 | `club.ugnas.com/...` | 部署日志 | ✅ 成功 | `web_search` 找链接 → `web_extract` |
| Hermes 中文社区 | `hermesagent.org.cn/en/docs/...` | 官方文档中文镜像 | ✅ SSR, `web_extract` 5k chars (LLM截断) | `web_extract` 优先, 截断时用 `browser_console` 分段提取 |
| Hermes 官方 Docs | `hermes-agent.nousresearch.com/docs/...` | 官方文档 | ✅ SSR, `web_extract` 5k chars (LLM截断) | `web_extract` 优先, 截断时 `browser_console` 续取 |
| GitHub Releases | `github.com/NousResearch/hermes-agent/releases` | 版本更新 | ✅ 纯 markdown | `web_extract` 或 `curl` |
| GitHub README | `github.com/NousResearch/hermes-agent` | 仓库主页 | ✅ 纯 markdown | `web_extract` 或 `curl` |
| SecurityLab | `www.securitylab.ru/blog/...` | 俄语深度评测 | ✅ SSR | `web_extract` |
| Medium | `medium.com/...` | 英文技术博客 | ✅ SSR | `web_extract` |

### ⚠️ 部分可用的（需要备用方案）

| 来源 | URL | 内容类型 | web_extract 结果 | 备用方案 |
|---|---|---|---|---|
| Docusaurus 官方 Tips 页 | `hermes-agent.nousresearch.com/docs/guides/tips/` | 官方技巧 | ✅ 前 ~5k 字 (LLM 截断) | `browser_console` CDP 分段提取剩余文本 |
| Reddit | `reddit.com/r/hermesagent/` | 社区讨论 | ⚠️ 可能被 Cloudflare 挡 | 用 web_search 找索引内容 |

### ❌ 不可抓取的（跳过，别试）

| 来源 | URL | 原因 | 替代方案 |
|---|---|---|---|
| Hermes 中文论坛 | `hermesagent.org.cn/forum` | 腾讯频道，仅显示二维码+说明文字，无公开内容 | 跳过的信息本身有用：确认了社区讨论在微信/QQ私密频道 |
| AI 对话站 (deepseek/chatglm) | `chat.deepseek.com`, `chatglm.cn` 等 | 浏览器远程代理无登录态 → 撞登录墙 (SOUL.md 说的「已登录」指本地 Chrome profile, Browserbase 用不上) | `web_extract` 抓官方 docs / self-reasoning / Ponytail YAGNI |
| AI 对话站 (gemini/GPT) | `gemini.google.com`, `chatgpt.com` 等 | 同上面，Browserbase 无本地登录态 | 同上 |
| agentskills.io | `agentskills.io/` | Next.js SPA, 返回 107KB JS 入口 + 404 HTML | 跳过, 走 GitHub 源 (awesome-hermes-skills) |
| cocoloop hub | `cocoloop.ai/hub` | SPA, 客户端渲染 | 跳过, 走 GitHub 源 |

## 中文搜索关键词使用建议

`web_search` (DuckDuckGo backend) 搜索中文 Hermes 内容效果好：

| 搜索意图 | 推荐 query | 预期结果 |
|---|---|---|
| 入门指南 | `Hermes Agent 入门 安装 配置 2026` | 知乎 / 菜鸟教程 / CSDN |
| 社区讨论 | `Hermes Agent 社区 技巧 2026年7月` | 知乎 / 36氪 / 博客园 |
| 最新动态 | `Hermes Agent 最新 版本 动态 2026` | 知乎周报 / CSDN |
| 中文社区资源 | `Hermes Agent 中文 社区 论坛 QQ` | hermesagent.org.cn |
| 特定技巧 | `Hermes Agent AGENTS.md 上下文 文件 配置` | 知乎 / 官方文档 |
| 进阶玩法 | `Hermes Agent 隐藏 技能 配置 技巧` | 知乎 / 博客园 |

## SearXNG 注意事项

**中文 Hermes 搜索使用 `mcp_searxng_web_search` 时：**
- 中文 query 在 SearXNG `general` 类目下返回 0 结果（2026-07-02 cron 确认）
- 同一 query 用 `web_search` (DuckDuckGo) 返回 10 条结果
- **1 call 即切**：1 次 SearXNG MCP 返回空 → 0 思考切 `web_search`，不要重复尝试

## 为什么这页存在

`search_community` 是 idle_learning 4 步变体中最容易"卡引擎"的一步。这份参考设计为**先看表再调引擎**的快速决策表——知道哪个来源能出东西，哪个来源 100% 是死路，省掉反复试错。
