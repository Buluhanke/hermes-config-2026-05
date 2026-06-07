---
name: skill-library-management
version: 1.1.0
description: Skill library hygiene and decision framework — evaluating what to install, when to install, and when to prune. Prevents skill bloat while maximizing utility per skill.
triggers:
  - "要不要装这个skill"
  - "现在装还是等要用时再装"
  - "这两个skill是不是重复的"
  - "我们安装的与实际使用的相差很大"
  - "熟记这些技能"
  - "72个skills太多了"
  - "今晚学习添加的这些东西哪些有必要装"
---

# Skill Library Management

> 管理技能库的安装/删除决策，防止技能膨胀
> 核心原则：宁缺毋滥，按需装载

## Core Principle: Less is More

Hermes目标不是拥有最多skills，而是拥有最精准的skills。72个skills中大量是：
- 一次性项目（1688业务类）
- 未验证就安装
- 功能与其他skills重叠

**每装一个新skill，系统开销增加（磁盘/内存/上下文）。不装才是默认选项。**

## Decision Tree

```
收到新skill安装请求
├── 来源可信度？
│   ├── 官方/知名作者 → 进入评估
│   └── 未知来源 → 先 vet，再用 skill-vetter
│
├── 与现有skills重叠？
│   ├── 完全重复 → 不装
│   ├── 部分重叠 → 对比优先已有/新装的取舍
│   └── 全新功能 → 进入资源评估
│
├── 资源评估（内存约束 Mac mini 24GB，空闲<3GB时谨慎）
│   ├── 轻量（<5MB）→ 可立即装
│   ├── 中量（5-50MB）→ 按需装
│   └── 重型（>50MB）→ 等明确任务再装
│
└── 最终决策：宁缺毋滥，按需装载
```

## 重叠检测规则（2026-06-04实测）

| 新技能 | 已有替代 | 决策 |
|--------|---------|------|
| agent-browser | hermes-rpa, browser_cdp | 不装 |
| product-spec-builder | planning-and-taYOUR_API_KEY | 不装 |
| ui-prompt-generator | design-md | 不装 |
| ui-ux-pro-max | popular-web-designs | 不装 |
| dev-builder | claude-code, codex, opencode | 不装 |
| ppt-generator | powerpoint | 先用powerpoint再决定 |
| find-skills | 全新 | ✅ 已装（2026-06-04） |
| skill-creator | 全新 | ✅ 已装（2026-06-04） |
| brainstorming | 全新 | ✅ 已装（2026-06-04） |
| humanizer-zh | 全新 | ✅ 已装（2026-06-04） |

## 当前技能库状态（2026-06-06更新）

```
总量：~187个SKILL.md（含嵌套子skill）
内置来源：~/.hermes/hermes-agent/skills/（74个SKILL.md，已落后291提交，2026-06-06 pull同步）
用户安装：~/.hermes/skills/（~113个用户独有SKILL.md）

已同步更新（2026-06-06）：
- apple/macos-computer-use ✅（+262行 → 201行，大幅精简）
- apple/apple-reminders ✅（+32行更新）
- autonomous-ai-agents/hermes-agent ✅（+360行更新，含references移动）
- devops/kanban-worker ✅（+9行更新）
- github/github-repo-management ✅（+175行更新）
- productivity/notion ✅（+276行更新）
- software-development/systematic-debugging ✅（+2行更新）
```

## 安装优先级

| 优先级 | 技能 | 大小 | 状态 |
|--------|------|------|------|
| P0 | hermes-agent源码同步 | — | ✅ 每月检查一次（2026-06-06首次） |
| P0 | skill-creator | <1MB | ✅ 已装 |
| P1 | brainstorming | <1MB | ✅ 已装 |
| P1 | humanizer | <1MB | ✅ 已装 |
| P1 | find-skills | <1MB | ✅ 已装 |
| P2 | deep-research | >50MB | ⏳ 等任务 |

## Hermes 源码 Skill 目录变化（2026-06-06 重要）

**官方仓库重大重组**：部分 skill 从 `skills/` 移入 `optional-skills/`（降级为可选）：
- creative/baoyu-*** 系列 → optional-skills/creative/
- gaming/* → optional-skills/gaming/
- mlops/research/dspy → optional-skills/mlops/research/
- software-development/subagent-driven-development → optional-skills/

**已删除（用户侧如有需移除）**：
- kanban-codex-lane（删除，无替代）
- spotify（删除，用户侧有独立副本）
- linear（删除，用户侧有独立副本）
- debugging-hermes-tui-commands（删除，用户侧有独立副本）
- writing-plans（删除，用户侧有独立副本）

**重命名/移动**：
- native-mcp（从 skills/mcp/ → autonomous-ai-agents/hermes-agent/references/）
- webhook-subscriptions（从 skills/devops/ → autonomous-ai-agents/hermes-agent/references/）

**同步命令**：
```bash
cd ~/.hermes/hermes-agent && git pull origin main
# 然后对比内置/用户侧差异，手动同步有更新的 SKILL.md
```

## Pitfall：同步技能时的 git 工作目录处理

- `git pull` 前必须先 `git stash` 掉本地未提交的修改（telegram.py、run.py 等），否则 pull 被拦
- stash 后 pull 成功，再 `git stash pop` 恢复
- 不要用 `git pull --rebase`：hermes 源码变更频繁，rebase 冲突概率极高
- macOS Apple git 2.15 不生效的 config（`http.version HTTP/1.1`），必须用 homebrew git：`export PATH=/opt/homebrew/bin:$PATH`
- 对比用户侧 vs 内置 skill 时，**用 Python 脚本**（`execute_code`）最可靠，shell 脚本中 `find ... -exec wc -l` 在 macOS 上可能输出乱码

## 已知重叠技能（待清理）

| 功能域 | 重叠技能 | 建议 |
|--------|---------|------|
| CDP浏览器自动化 | hermes-cdp-hardcore-type, browser-automation, cdp-browser-automation | 保留 hermes-cdp-hardcore-type（最强），其余待评估 |
| 视觉感知 | hermes-vision-agent, vision | 保留 hermes-vision-agent |
| 记忆管理 | hermes-memory-hpc, hermes-memory-hygiene | 保留 hermes-memory-hpc |
| 搜索路由 | anysearch, unified-search-routing, ddgs-searxng-agg-search | 保留 anysearch + ddgs 兜底 |
| 主动执行 | proactive-execution, proactive-self-evolution | 保留 proactive-execution |
| 技能管理 | skill-library-management, skill-vetter | 两者互补，都保留 |
| 跨平台 agent 感知 | hermes-agent-status-monitor (状态广播) + `cross_platform_skill.sh` 三件套 (白板+看板+索引, 2026-06-07) | **同家族兄弟架构, 暂不合并**: 状态广播管"在线+数量", 三件套管"事件流+审计+索引", 数据流和落点都不一样, 合并会让 SKILL.md 变臃肿。详情见 `hermes-agent-status-monitor/references/cross-platform-skill-awareness.md` |

## 删除时机

- 功能完全被新技能替代
- 业务类技能超过6个月未使用
- 与其他技能长期重叠且无差异化价值

## 参考工具

- `references/entity-deletion-checklist.md` — 删除插件/skill/MCP 实体时的标准化五步流程，含 Firecrawl 实际案例

## 验证命令

```bash
# 查看技能库大小
du -sh ~/.hermes/skills/
ls ~/.hermes/skills/ | wc -l

# 检查空闲内存（<3GB时谨慎安装）
vm_stat | grep "Pages free"
```

---

*Keep the library lean. Every skill should earn its place.*