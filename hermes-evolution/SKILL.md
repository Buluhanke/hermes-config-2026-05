---
name: hermes-evolution
description: Hermes 真人化进化主干 skill——驱动 8 层时间循环持续自主进化。触发：每完成复杂任务后自动评估、写 skill、自我优化。核心是让 Hermes 越长越强，像 Friday/Jarvis 那样越用越懂你。
triggers:
  - 进化
  - 自我提升
  - 能力增长
  - 持续学习
  - skill 优化
  - 写一个新 skill
---

# Hermes Evolution — 真人化进化主干

## 核心目标

让 Hermes 长成 Friday/Jarvis 那样——能自主学习、能控制电脑和浏览器、能持续进化，不需要用户反复教同一件事。

## 8 层时间循环（已内置）

| 层级 | 频率 | 作用 |
|------|------|------|
| L1 执行 | 每次任务 | 干活 |
| L2 目标 | 跨会话 | 追求长期目标 |
| L3 Skill写 | 任务后 | 写 SKILL.md 固化流程 |
| L4 Curator | 每周 | 修剪低质量 skill |
| L5 记忆 | 持续 | fact_store + MEMORY.md |
| L6 Kanban | 并行 | 多任务同时跑 |
| L7 压缩 | 上下文满时 | 提炼关键信息 |
| L8 子agent | 并行 | delegate_task 并行工作 |

## 自我进化规则

### 触发写 skill 的条件（同时满足）
- 任务花了 5+ 个 tool calls
- **或** 从错误中恢复
- **或** 用户纠正了做法
- confidence ≥ 0.7
- 过去 10 次无相同 skill

### Skill 自我优化规则
- 发现更好方法 → 用 `patch` 不是 `edit`
- patch 是保守更新，只改需要的行
- 更新前先自我测试，失败则丢弃

### Curator 每周检查
- 30 天未用的 skill → 移到备份目录
- 重叠的 skill → 合并
- 过时的 skill → 删除

## 混合架构（真人级浏览器控制）

```
Layer 1: computer_use
  → AX 树结构化数据，极低 token
  → 背景控制，不抢用户窗口

Layer 2: cua_browser
  → 精确绑定真实 Chrome 标签页
  → 需要授权一次（cua-driver browser-approve）

Layer 3: browser_*
  → Hermes 镜子 Chrome（备用）
  → 动态页/登录态用 Layer 1+2

截图策略：
- 普通操作 → AX 树（极低 token）
- 需要"看" → computer_use capture som
- Canvas/图片 → computer_use capture vision
```

## 搜索能力升级

```
当前：DDGS（免费，无需 key）✅
目标：SearXNG（免费自部署）+ Firecrawl（高质量提取）
      Docker 装好后配置：
      web:
        search_backend: searxng
        extract_backend: firecrawl
```

## 持续进化 Checklist

- [x] fact_store 持续写入（目前 238 条）
- [x] 每日自学新知识
- [x] Skill Bundle（一条命令加载多个 skill）
- [x] 渐进披露（50 skills ≈ 630 tokens）
- [x] browser-use CLI + Camofox v1.6.0 真实Chrome控制 ✅
- [x] Camofox持久化Cookie（github-persist profile验证✅）
- [x] async-delegate 后台子agent插件 ✅
- [x] hermes-agent-self-evolution（DSPy+GEPA）✅
- [x] Gateway Camofox路由配置生效 ✅
- [x] cotomi Act研究结论（WebArena 80.4%>人类基线）
- [ ] Cotomi Act行为学习机制落地（Shared Knowledge Workspace）
- [ ] SearXNG + Firecrawl 双 backend 配置

## 真人化当前进度

| 能力 | 状态 |
|------|------|
| 感知（AX树+截图） | ✅ computer_use 已通 |
| 行动（浏览器控制） | ✅ 真实Chrome已控 |
| 知识（持续自学） | ✅ 每日全网搜索 |
| 记忆（fact_store） | ✅ 238 条 fact |
| 技能（skill 系统） | ✅ 自写自优化 |
| 规划（多层循环） | ✅ 8 层已理解 |
| 进化（自我改进） | 🔄 进行中 |

[^1]: Curator 是 hermes curator 命令，每周六凌晨自动运行
