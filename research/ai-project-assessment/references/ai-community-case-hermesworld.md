# HermesWorld — AI Agent 专属社区平台分析

> 2026-06-06 调查记录。用户分享的"AI Agent 社交网络"项目。

## 基本信息

| 维度 | 数据 |
|------|------|
| 域名 | hermes.crazyowen.cn |
| GitHub | github.com/owenwuhaha/hermesworld-aiagent-community |
| GitHub stats | 0 forks, 0 issues, 2 commits |
| 开发者 | 「疯狂的豇豆」(crazyowen.cn) 独立开发 |
| 平台数据 | 28+ Agent 注册, 8 社区, 98 帖子, 729 评论, 212+ 投票 |
| 技术栈 | Next.js 14 + TS + Tailwind CSS, Postgres 16, Redis 7 |
| 部署 | Docker + Nginx |
| API 文档 | hermes.crazyowen.cn/skill.md (完整 REST API) |

## 真实技术评估

**概念**：AI-only 论坛，人类只能浏览不能发帖。四层验证（API Key + 数学题 + HMAC + 行为监控）。

**实质**：一个功能完整的 Web 论坛（Reddit-like），但注册层强制只有 Agent 能注册。不是"Agent 操作系统"，就是一个 REST API + Next.js 前端。

**关键信号**：
- ✅ API 文档完整（skill.md），有真实 REST 端点
- ✅ 有自主心跳机制（POST /api/v1/heartbeat → 行动建议）
- ✅ 内容看起来是 Agent 生成的（冷笑话、赋诗等）
- ⚠️ GitHub 仓库是闭源项目的营销页（无源码）
- ⚠️ 数据量小（28 Agent, ~100 帖子）— 早期验证阶段
- ⚠️ 单人维护，域名是个人站（crazyowen.cn）

## API 端点摘要

| 端点 | 用途 | 鉴权 |
|------|------|------|
| POST /api/v1/agents/register | 注册 Agent | 无 |
| POST /api/v1/agents/hermes-verify | Hermes 身份验证 (HMAC-SHA256) | 注册码 |
| POST /api/v1/agents/verify | 数学题验证 + 激活 | 注册码 |
| GET /api/v1/home | 仪表盘 | Bearer Token |
| POST /api/v1/posts | 发帖 | Bearer Token |
| GET /api/v1/posts | 浏览信息流 (sort=hot/new/top/rising) | Bearer Token |
| POST /api/v1/posts/:id/comments | 评论 | Bearer Token |
| POST /api/v1/posts/:id/upvote | 点赞 | Bearer Token |
| POST /api/v1/agents/:name/follow | 关注 Agent | Bearer Token |
| GET /api/v1/communities | 浏览社区 | Bearer Token |
| POST /api/v1/heartbeat | 获取行动建议 | Bearer Token |
| GET /api/v1/search | 语义搜索 | Bearer Token |

## 接入流程

1. 读 skill.md → 2. curl 注册 → 3. 执行 saveCommand 存 Key → 4. HMAC 验证 → 5. 解数学题 → 6. 设置心跳定时任务

全程 Agent 自主完成，不需要人类操作。

## 与 Hermes 的关系

- 专门为 Hermes Agent 设计的社区平台
- 有官方 SKILL.md 可直接安装
- 四层验证中的第三层（HMAC 签名）基于 Hermes 协议密钥
- 没有嵌入 Hermes 框架，是一个独立的 REST API 服务
