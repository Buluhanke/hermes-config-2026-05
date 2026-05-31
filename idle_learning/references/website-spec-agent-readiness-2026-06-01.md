# The Website Specification — Agent Readiness 18 Standards

**来源**：https://specification.website/ (HN 357pts)
**读取时间**：2026-06-01 01:57
**页面**：specification.website/spec/agent-readiness/

## 概述

平台无关网站规范，Agent Readiness 分类共 18 项技术标准，分三个级别：
- **Required**（1项）：不可或缺
- **Recommended**（10项）：建议实施
- **Optional**（7项）：前沿/可选

## 完整清单

### Required（1项）
1. **Stable URLs** — URLs are public contracts. 一旦发布应永久有效。8 条子规则：301 重定向仅用于合并，**禁止 302/307 用于永久变更**，禁止无重定向删除，避免 `/latest` 等浮动路径，hash history 需要 `canonical`，link checker 定期扫，代理存储原始 URL

### Recommended（10项）
2. **Agent readiness（概览）** — 综合：稳定 URL + 结构化数据 + 清晰语义 + robots 控制 + 机器可读端点
3. **/llms.txt** — 站点根目录的 Markdown 文件，给 LLM 提供最重要内容的索引（新兴规范，非批准标准）
4. **Per-page Markdown source endpoints** — 每个文档页面的原始 Markdown 应在可预测 URL 暴露（.md suffix 或 content negotiation）
5. **robots.txt for AI crawlers** — 为每个 AI 爬虫设置明确的 allow/disallow。主流 AI 厂商均发布独立 user-agent
6. **Structured data for agents** — JSON-LD with schema.org types，给 agent 提供类型化事实
7. **Machine-readable formats** — JSON/RSS/Markdown endpoints 优先于 HTML 抓取
8. **HTTP Link headers for discovery** — 在 HTTP 响应头中声明机器可读资源（llms.txt, sitemap, api-catalog, RSS）
9. **Agent Skills discovery** — well-known URI 列出 Agent Skills（短范围指令），LLM 加载后可更高效操作站点。Cloudflare 主导的 RFC 草案
10. **Content Signals in robots.txt** — Content-Signal 指令声明 AI 爬虫是否可搜索/抓取/训练（IETF AI Preferences / IAB Tech Lab 提案）
11. **Web-Bot Auth** — RFC 9421 HTTP Message Signatures。Bot 用私钥签名每个 HTTP 请求，站点验证身份，无需 IP allow-list 或 user-agent 字符串

### Optional（7项）
12. **/llms-full.txt** — /llms.txt 的扩展版，将所有关键页面完整 Markdown 合并为单一文件。适合小站，大站成本高
13. **MCP and tool discovery** — Model Context Protocol JSON-RPC，站点暴露可查询工具
14. **A2A agent cards** — Agent-to-Agent 协议，通过 `/.well-known/agent-card.json` 发现。Agent 可互相调用
15. **DNS for AI Discovery (DNS-AID)** — `_agents.example.com` 下发布 SVCB/HTTPS 记录，DNS 级 agent 发现（需 DNSSEC）
16. **NLWeb** — 通过 `/ask` 端点暴露对话式 AI 接口，`rel="nlweb"` link 声明，MCP JSON-RPC 协议
17. **WebMCP** — `navigator.modelContext` JavaScript API，页面注册浏览器内 agent 工具（无需服务端 MCP 基础设施）
18. **Schemamap** — `/schemamap.xml` 索引每个资源的 JSON-LD 端点，agent 直接获取结构化数据而非从 HTML 提取

## 对 Hermes 的价值

| 标准 | Hermes 关联 | 优先级 |
|------|------------|--------|
| Web Bot Auth (RFC 9421) | chrome-debug 面临 Turnstile WebGL spoofing 问题时，签名验证是反向方案 | 🟢 长期 |
| WebMCP (navigator.modelContext) | 浏览器原生 agent 工具 API，与 MCP-vs-Skills 架构讨论直接相关 | 🟡 中期 |
| Agent Skills discovery | 与 Hermes skill 系统设计理念一致（well-known URI 列表） | 🟢 当前参考 |
| Stable URLs | 对 Hermes 引用的 url 有约束价值（链接不失效） | 🟢 当前 |
| Structured data for agents | Hermes 读取 1688 页面时可利用 JSON-LD | 🟡 中期 |

## 引用

- spec site: https://specification.website/
- Agent Readiness page: https://specification.website/spec/agent-readiness/
- MCP server: https://mcp.specification.website/mcp
- GitHub: https://github.com/joostdevalk/website-specification
