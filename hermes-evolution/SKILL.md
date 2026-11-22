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

## 2026-11-21 自学增量（cron 只读，固化于此）

**Hermes 版本线**（cron 不可写 fact_store，记录在此供下次检索）：
- v0.23.2（11-16）：~1,989 PRs；durable subagents 可跨 gateway 重启存活并续聊；`hermes fallback check`；`hermes update --force`；per-job cron 选项（wrap_response / fresh thread）；plugin APIs `ctx.fork_session` / `ctx.redact_text()` / `ctx.register_idle_task`；Gemini Interactions API 默认用于 Gemini 3+；安全修复 CVE-2026-130164。
- v0.23.3（11-19，补丁版）：**rolls up ~370 PRs（是聚合不是回滚**，上一轮报告误写"回滚"已纠正）；prompt-cache 生命周期控制器（闲置对话在 1h 缓存到期前压缩、缓存工具结果归档、cache_ttl=auto）；主动 tool-result prune 默认开启；GPT-6.2 Astra/Sol 上 OpenRouter+Nous Portal；存储层拆到 persistence interface + SQLite 后端。

**自改进框架 2026-11 集群**（对 L3/L4 的直接启示）：
- Harnesses That Improve Themselves（2611.22299）：4 可编辑组件（context/state、control、action、verify/recover）+ 4 阶段循环（诊断→提议补丁→验证过滤→部署/路由）；结论 **modular updates + validation gate 胜过 full-harness rewrite**，需防 prompt bloat / benchmark gaming / evaluator tampering。→ Hermes L3 patch 保守更新 + 先自测正是这条。
- GUARD（2611.23476）：无 grader RSI，directional regret 区分"新破坏的"与"未解决的"，Soft-HURT gate 只在收益>回归时晋升 → 对应 skill 的"先自测失败丢弃"规则，可加"非回归缓冲"。
- RSI-Env（2611.01736）：Host Controller 把评估/版本记录设为 Improver 只读 → 强化"evaluator 必须在沙箱外"铁律。Open-General Self GPQA 65.2→73.2、SimpleQA 82→85→88。
- SIM / Self-Improvement Memory（2611.18856）：给优化器（非策略）按"重复出现的问题"分组存 edit 的 rationale + 预测/实测结果，10 次独立运行平均 +2.36 分（p=0.003）→ 印证 skill 已写的"archive 对比升华"，fact_store 应记 edit 的 why+预测vs实测，不只记结论。
- Evolver（2611.07595）：结构化 Gene 资产把探索经验变持久能力，成功率 +4.38pp、token -24.24%。
- Elite（2611.21056）：explore-then-integrate，合并互补机制而非选单一子代；SWE-bench Pro 60→85.6%，零候选任务评估、比 DGM 快 8.8x → 支撑跨 lineage 杂交，优先于单 trajectory 升华。

**Benchmark 现状**（避免引用过时论文数）：OSWorld 2.0 v2.1 官方榜首 44.33% binary / 77.67% partial（论文时 20.6% 已过时）；OSWorld-Verified 榜首 90.19%、通用模型 claude-fable-5 85.96%（人类基线 ~72%）；WebArena-Pro（2611.17955，300 任务/20 站点/多模态音视频）最强 Codex+GPT-6.1-Sol 与 Claude Code+Opus-5.5 均 62.3%；WebArena 榜首 86.1%（Narada AI Code）、最佳开源 74.3%（DeepSeek v3.2）。

## 每日进化前置自检（2026-11-21 加入）
- 进化开始前先跑 `hermes fallback list`：若为空（`No fallback providers configured`），用 `hermes config set fallback_providers '[...]'` 恢复 gemini/deepseek/zai 三链，再 `hermes fallback check --live` 确认 exit 0。config.yaml 会被周期性重写清空 fallback，曾导致 cron 连续 12 次失败。
- 不要用直接编辑 config.yaml 的方式恢复（安全护栏会拒绝）；cron 上下文 fact_store 只读，决策写入本 skill 或报告。

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

## Jarvis Core 集成（新增 2026-10-17）

### 总体架构

```
┌─────────────────────────────────────────────────────────────┐
│                    JARVIS CORE (总枢纽)                      │
│  识别大脑 (state.db + fact_store + mempalace)                │
│  行动中枢 (browser + shell + app)                            │
│  知识获取 (web + 研究 + 爬虫)                                │
│  持续学习 (self-evolution + A/B + 创造)                      │
└─────────────────────────────────────────────────────────────┘
```

### 统一入口

用户任何能力请求都经过 `agent-reach` 路由：
| 请求类型 | 路由到 | 示例 |
|---|---|---|
| 查会话/对话 | state.db | "谁提到了 Flask 升级" |
| 深度研究 | deep-research | "对比 AI agent 框架" |
| 浏览器操作 | browser-cdp-control | "打开 Chrome 点到 1688" |
| 命令执行 | hermes_execution.py | "列出所有 .py 文件" |
| 持续学习 | jarvis_daily_learn.sh | 每日 9:00 自动 |

### 控制面板

Jarvis 启动脚本：`~/.hermes/scripts/jarvis_start.sh`（4 步自检）
每日闭环：`~/.hermes/scripts/jarvis_daily_learn.sh`（6 步：扫描→固化→分析→更新）

### 每日学习闭环（jarvis_daily_learn.sh）

```
1. 扫描 state.db → 提取 24 小时对话
2. 提取核心信息 → 写入 fact_store
3. 分析失败模式（失败/报错 关键字）
4. 更新相关 SKILL.md（基于证据）
5. 运行自动化测试（evidence-loop）
6. 如通过 → 固化学习；如失败 → lesson_store
```

### 能力矩阵（Capability Matrix）

见 `jarvis-core/SKILL.md` 章节 8。

### 禁忌（Principles to avoid）

见 `jarvis-core/SKILL.md` 章节 9。
