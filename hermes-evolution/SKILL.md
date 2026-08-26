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

## 2026 自进化框架实战结论（2026-08-26 自学沉淀）

本轮全网自学抓到 6 个 2026 自改进 SOTA，已入库 fact_store（IDs 1186–1192）。对 Hermes 进化的可直接落地启示：

1. **HSI（分层自进化）**：冻结 backbone 也能端到端进化 harness（prompt/工具/记忆/验证逻辑）。三层 scope——任务 harness H、evolver 改写 H、meta-evolver 改写 evolver（最外层 anchor 冻结防无限自指）。两大瓶颈：**feedback-fidelity bound**（稀疏奖励无信号）和 **backbone capability bound**（harness 改不动模型天花板）。Hermes 对应：L3 Skill写=evolver，L4 Curator=meta-evolver，fact_store=archive。
2. **OEO（开放端优化）**：框架只持有 objective/permissions/budget/eval/governance 外部契约，把"如何改进"的 meta-policy 委托给足够强的 optimizer 在线自组。结论——**prescription 是 capability-dependent 脚手架**：强模型可不用预设 pipeline，中模型仍需 SkillOpt，弱模型连 OEO 接口都跑不动。Hermes 对应：skill 的 triggers/steps 是 prescription，弱模型应保留详细步骤，强模型可下放。
3. **MARS（元认知）**：单周期 self-improvement——principle-based reflection（抽象避错规则）+ procedural reflection（成功 step 策略），三阶段 Evaluation→Failure Allocation→Enhancement。计算开销远低于递归循环。Hermes 对应：每次任务后写 skill 就是 MARS 式单周期升华。
4. **MGM（Mendel Gödel Machine）**：archive-based，三类自修改算子——clonal / reaction-norm（跨任务）/ cross-lineage hybridization（跨 lineage）。理论证更快收敛；SWE-bench 68.3%→78.3%，Polyglot 50.8%→93.3%。**跨 lineage 杂交**是 Hermes 缺的：当前只做单 trajectory 升华，应开始对比不同 skill 变体。
5. **DGM-Hyperagents**：meta 级修改机制本身也可编辑→meta 改进跨域迁移并跨 run 累积。开放端 self-improvement 可推广到任意可计算任务，不限于 coding。
6. **WebArena 2026**：SOTA 74.3%(WebTactix/DeepSeek v3.2)，但 WebArena/WebVoyager 仅作 web baseline 已不够；OSWorld（真实桌面 OS）才是通用 computer-use 最近公开代理；生产就绪看 recovery/permissioning/verification/intervention rate。Hermes 的 computer_use 已对齐 OSWorld 路线（真实桌面控制），方向正确。

**本轮进化动作**：把"单 trajectory 升华"升级为"archive 对比升华"——同主题积累 3+ fact 时对比多个 skill 变体再固化，而非逐条照抄。
详细研究笔记（含 arXiv 链接、完整指标、Hermes 映射）见 `references/self-improvement-frameworks-2026.md`。

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
