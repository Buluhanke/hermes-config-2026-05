---
name: hermes-daily-learning
description: Hermes Agent 每日学习指南与知识库积累
triggers:
  - 每日学习
  - 自我提升
  - Hermes技巧
version: 2026-05-17
---

# Hermes Agent 每日学习指南

## 核心学习路径
官方文档 → GitHub → Discord英文社区 → 中文社区 → 技能市场

## 一、官方资源（优先级最高）

| 资源 | 网址 | 核心价值 |
|------|------|---------|
| 官方文档 | https://hermes-agent.nousresearch.com/docs | 架构、API、技能开发、自我学习机制 |
| GitHub | https://github.com/NousResearch/hermes-agent | 源码、更新日志、issue讨论 |
| Discord | Nous Research Discord | 实时答疑、功能预览 |
| 官方技能库 | `hermes skills browse` | 62+官方技能，可直接安装 |

## 二、中文社区

| 资源 | 网址 |
|------|------|
| Hermes Agent 中文社区 | hermesagent.org.cn |
| Hermes AI 中文站 | hermesai.top |

## 三、技能市场

| 平台 | 网址 |
|------|------|
| AgentSkills.io | agentskills.io（500+社区技能，可直接导入） |
| 虾评 | xiaping.coze.com（470+精品Skill，有排行榜和评测） |
| SkillHub | skillhub.cn（Top 50） |

导入社区技能：`hermes skills import <name>`，观察 Hermes 如何在使用中自动优化。

## 四、学习阶段

### 入门
- 官方Quick Start + 中文社区入门教程
- 尝试简单任务，观察自动生成技能过程

### 进阶
- 学习技能开发规范，编写自定义技能
- 研究自我学习机制，调整Nudge Engine参数

### 精通
- 贡献GitHub代码
- 分享技能到社区
- 探索与其他工具集成（Ollama、OpenClaw等）

## 五、日常学习机制

**cronjob**: 每日08:00巡检 `proactive-morning-scan`（job_id: proactive-morning-scan）

**每阶段目标：**
1. 阅读1篇官方文档章节
2. 检查是否有新技能/新版本
3. 实践1个小任务
4. 记录学到的新知识点到Obsidian

## 七、GitHub 优质项目研究法

研究新项目时的标准流程：

```
1. git clone --depth=1 <repo> 到 /tmp
2. ls 查看结构，找 SKILL.md / README.md / scripts/
3. 读 SKILL.md（描述核心价值）+ README（前100行了解能力）
4. 扫关键脚本（cdp-proxy.mjs 等核心实现）
5. 识别：对 Hermes 的价值（直接可用 / 思路借鉴 / 架构参考 / 存档）
6. 判断优先级：Tier1（直接可用）/ Tier2（思路借鉴）/ Tier3（存档）
```

**"对我们有什么用处？"** 这个问题是过滤标准——不是所有项目都要深究。

### Release Note 考古法（针对已有项目，非新项目）

当检查已经跟踪的项目（如 hermes-agent）的更新时，不要只看最新版：

1. 读当前最新 release + 上一个版本 release notes
2. 搜索第三方深度解读：`dev.to <项目名> v<版本> review`、`<项目名> v<版本> 深度分析`
3. 重点找**被官方 notes 一笔带过但架构层面变更较大的**原语类功能（非 UI/表面功能）
4. 问自己："这个功能改了 agent 做事的方式吗？" — 如果是，优先级提高两级
5. 将发现写入 Obsidian + 更新价值映射表

**PITFALL：官方 release notes 倾向于突出用户可见的新功能，最有价值的架构变更往往藏在 "Misc" 或 3 行以内。必须读第三方解读补盲。**

### Post-Release 热修复扫描（针对已跟踪项目）

每次巡检时，如果距上次扫描已超过 3 天，额外执行：

```bash
# 检查最新 release 之后是否有 hotfix merged（一般在 release tag 后 1-2 天内）
site:github.com/NousResearch/hermes-agent after:2026-05-16 hotfix
site:github.com/NousResearch/hermes-agent after:2026-05-16 fix
site:github.com/NousResearch/hermes-agent after:2026-05-16 security

# 搜索关键词：P0/P1 fix, revert, rollback（发现回退的变更）
```

**典型热修复信号**：
- release 后 24-48 小时内有 P0/P1 security/bug fix PR merged
- 有 `fix: ... revert` 模式（说明上一个 fix 有问题）
- release notes 里有"rolled back"或"reverted"提到

**主动功能分支扫描（补充）**：除热修复外，每次巡检还应检查是否有 force-pushed 的 `feat/*` 或 `codex/*` 分支——force-push 意味着该功能正在活跃开发，可能即将合并。信号：`git fetch` 时看到 ` (forced update)` 标记。

典型案例（2026-05-26）：
- `feat/whatsapp-cloud-api` 分支 force-pushed → WhatsApp Cloud API 新平台即将合并
- `codex/fix-*` 系列分支（dingtalk/discord/feishu/qq-group/webhook/websocket/dashboard）→ 多个平台授权漏洞修复正在审查

### Commit级深挖法（已有项目巡检必备）

对已跟踪项目（hermes-agent），**不要只看 release notes**。每次巡检应额外检查：

```bash
# 1. 查最新 release 之后的 commit 记录（不在 release notes 里的架构变更）
git log --oneline --since="2026-05-16" origin/main | head -20

# 2. 查特定 commit 改了什么（只看 commit message 不够，要看 diff 规模）
git log --oneline -30 origin/main
git show <commit_sha> --stat  # 看文件数和增删行数，+3000 行重构 = 重要架构变更

# 3. 识别高价值 commit 信号
#    - 大文件数（57文件）+ 大增删量（+3149行）= 架构重构
#    - 新增工具/技能/平台 = 功能落地
#    - "refactor"/"rewrite" = 核心逻辑变更
```

**判断优先级**：
- 架构重构（大文件数+大diff）> 新功能 > 小修复
- 问自己："这个变更改了 agent 做事的方式吗？" — 如果是，Tier1

**⚠️ Release notes 的固有局限**：官方 notes 倾向报 UI/用户可见功能，架构性底层变更（如 Provider Modules 重构）经常只出现在 Misc 段 2-3 行。Commit 级深挖才能发现全貌。

**2026-05-28 早巡检结果**：
```
### Post-v0.XX.X 热修复（May XX）
- **#[PR号] 简短描述**：影响说明
- **回退标记**：`/subgoal` 等功能被回退，实际不可用
```

**2026-05-26 巡检结果**：
- v0.14.0（2026-05-16）发布后 **10 天仍无 patch** ✓ 无热修复
- `feat/whatsapp-cloud-api` 分支 force-pushed → WhatsApp Cloud API 新平台即将合并
"references/hermes-self-trust-problem.md",
    "references/hermes-updates-2026-05-28.md",
    "references/v0.14.0-full-highlights-2026-05-26.md",
- `/subgoal` 简化版重生，`/goal checklist` 已回退（#23813）
- Brave Search 免费搜索 provider 已加入
- Skill Bundles 官方文档已完善（bundle 不安装技能，只是 slash 命令别名）

**2026-05-28 早巡检结果**：
- v0.14.0（2026-05-16）发布后 **12 天仍无 patch** ✓ 无热修复
- v0.14.0 完整数据：**808 commits · 633 merged PRs · 165,061 insertions · 215 贡献者**（来源：GitHub release 页面）
- `codex/fix-*` 授权漏洞修复 **8 个 PR 仍在审查中**（dingtalk、discord、feishu、qq-group、webhook、websocket、dashboard）
- `feat/whatsapp-cloud-api` 分支 force-pushed → WhatsApp Cloud API 即将合并
- Node.js 20 EOL 应对：#4876 升级捆绑 Node.js 20→22（Docker 镜像，4月起生效）
- xAI OAuth (xai-oauth) 对标准 SuperGrok 用户返回 403（#26847，已记录待官方修复）

### Skill Bundles 落地确认

`hermes bundles` 配置目录：`~/.hermes/skill-bundles/.yaml`

**采购一键加载 bundle 示例**（待创建）：
```yaml
bundle_name: procurement-1688
skills:
  - 1688-automation-flow
  - 1688-price-negotiation
  - supplier-relationship
description: 迅龙贸易 1688 采购全套技能
```
使用：`hermes bundles load procurement-1688`

**⚠️ Cron 环境限制**：cron 定时任务环境**无 Memory 写入权限**（`memory` 工具不可用），Obsidian 写入也可能受限。产出只能写文件到本地路径（`~/Obsidian/...`），无法调用 `memory store`。巡检前先确认文件写入路径是否可访问。

### 本次研究存档

| 仓库/文章 | 价值 | Tier |
|------|------|------|
| dev.to/hermes-under-the-hood | 6层prompt架构、provider transport族系、记忆三层设计 | **Tier1 — 见 `references/hermes-architecture-under-the-hood.md`** |
| dev.to/context-studios-agent-os | Agent Runtimes→Operating Systems转变分析，Hermes从编码助手转向Agent OS | **Tier1 — 见 `references/2026-05-23-community-findings.md`** |
| OnlyTerp/hermes-optimization-guide | GitHub 321★，24章节Hermes优化指南 | **Tier2 — 见 `references/2026-05-23-community-findings.md`** |
| hermesagents.net | 技能深度分析网站，9篇新文覆盖watchers/osint等 | **Tier1 — 见 `references/2026-05-23-community-findings.md`** |
| BlakeCrosley/hermes-agent-v013-reference | 28章实操配置参考（Tenacity/多Agent/Provider），ls-la风格 | **Tier1 — 见 `references/blakecrosley-v013-reference-guide.md`** |
| MarkTechPost 2026编码Agent排名 | Hermes #1（224B日Token/114K Stars/4 CVEs），对比OpenClaw #2 | **Tier1 — 见 `references/blakecrosley-v013-reference-guide.md`** |

**2026-05-29 早巡检发现**：
- v0.14.0（2026-05-16）发布后 **13 天仍无 patch** ✓ 无热修复
- **ntfy platform adapter 已合并入 main（未 release）**：PR #13866，81 tests，HTTP pub-sub 自托管通知平台，**QQ/微信备用通知通道候选**，需等下一版本发布
- `feat/whatsapp-cloud-api` 分支持续 force-pushed → WhatsApp Cloud API 即将发布
- 99 commits ahead of latest tag，建议检查是否有 break-change
