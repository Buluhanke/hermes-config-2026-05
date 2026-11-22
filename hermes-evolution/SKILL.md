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

## 2026-11-22 新知识增量（并行知识线，fact 1385–1396）

- **Hermes v0.23.0 Hearth（11-05，~1950 PR）**：Webapp + 单 gateway 统一会话、`/rewind`；**旧 `browser_*` 工具全删，浏览器自动化只剩 `browser_exec`**；内置技能 58→44、插件 600→1050；默认模型 GLM-5.3。→ 行动项：清理技能库里残留的 `browser_navigate`/`browser_click`/`browser_snapshot` 引用（本次已盘点，见下方迁移清单）。
- **WebMCP 2026-11 格局（用户长期追踪项）**：Brave Leo 在 Nightly 1.102.2 默认开启（PR #40616 于 11-12 合并）；ChatGPT 桌面 8-25 起首个主流默认开启 site tools；WebKit 反对、Firefox 仍用旧 `navigator`。→ 仍未到替代 browser_exec/CDP 的切换点，继续跟踪。
- **guard 机制得到实证**：MetaAct（2611.20655，github BaiCubed/MetaAct）把自进化编译成 GEAR 可执行动作 guard，ScienceWorld 违规 70%→0%、WebShop 40%→1%。印证本轮 `step_verifier.guard_spec` 方向正确。
- **记忆要门控，不能全记**：ARISE（2611.23588）留出集准确率门控自进化记忆，SOP-Bench +10.9pp、τ²-bench +5.8pp，超 GEPA 4.5pp 且调用少 4.0%；Anchor（2611.10382）重放源决策筛选记忆，ALFWorld 96.27%（+19.9%）且少留 41% 记忆卡。→ 本轮补了 408 条关键词，下一步应给 fact_store 加写入门控而非无限累积。
- **诚实边界**：UI-Venus-2（蚂蚁 11-13）WebVoyager 90.8/93.4，但 OSWorld 2.0 binary 仅 0.0%/2.8%——网页强 ≠ 长程桌面强。自进化技能泛化研究（2609.39148）：21 个训练提升技能仅 5 个完整迁移，LLM judge 一致率 86% 却难预测单次编辑。→ 印证"删单条 fact 复述垃圾"是对的：那种技能本就迁移不了。
- 其余：Pro² Agent（MLE-Bench 24h 70.7%/48h 76.0%）、Mage-VL-Cowork 4B（OSWorld-Verified 66.0%）、TokenEconomizer（成本 -18.4~30.9%）、MemoWM（-53.9% 经历专属信息）、TT-MBRL（R2I 42→54.1 SOTA）。

**旧 browser_* 引用迁移清单（2026-11-22 盘点，活跃技能）**：`research/grounded-citations`、`web-search-default`、`web/crawl4ai`、`3-statement-model`、`dcf-model`、`creative/sketch`、`software-development/dogfood`（表格仍是旧名）、`hermes-browser-local-login`、`humanization-engine`、`chrome-cdp-control`（部分为 fallback 语义，勿盲替）。统一改为 `browser_exec` 或 `mcp__chrome_devtools_mcp__*`（CDP），参见 `research/agent-landscape-2026` 已记录的破坏性变更。

## 每日进化前置自检
- **不绑定任何模型是用户铁律**：cron 任务不 pin、config 不设 `fallback_model` / `fallback_providers` 锁定，给什么模型就用什么模型、跟随当前主模型。模型失效时手动切换，不做自动轮替，也不要自动恢复 fallback 链——旧版"fallback 为空就恢复三链"的自检已废弃，它会违背这条铁律。
- 失效进化任务的正确修法是 `cronjob_manage(action='update', pinned=false)` 取消 pin + `hermes config unset fallback_model` 清隐藏绑定，而不是换一个模型 pin 上。**pin 免费模型必翻车**：免费额度到期就 404、地区受限就 403，cron 静默停摆且用户看不到 last_status。
- 不要用直接编辑 config.yaml 的方式改配置（安全护栏会拒绝），用 `hermes config set/unset`；cron 上下文 fact_store 只读，决策写入本 skill 或报告。
- 验证进化任务是否真跑：`cronjob_manage(action='run')` 手动触发一次并读输出文件，别只看 `last_status`。

## 调研驱动进化（用户说「找更强方案进化」时走这条）

不是出一份报告，必须走完「清点→调研→对比→落地→验证→固化」闭环：
1. 清点家底：`find ~/.hermes/skills -name SKILL.md` 统计总数/顶层分组，读核心脚本现状，先确认自己已有什么。
2. 四路并行搜：最新研究 / SOTA benchmark / 开源工具 / 自改进机制。每路取 5-10 条，只记可量化的关键数字，别抄摘要。
3. 对比现状分三类：已覆盖 / 部分覆盖 / 未覆盖。只落地「未覆盖且 ROI 最高」的 1-3 个，不贪多。
4. 新工具决策：已有等价能力就**抄设计不换栈**（装新工具只会碎片化）；只有确实无等价物才装。
5. 落地必须零 LLM 依赖、纯本地可跑，跨模型可移植优先于模型特定行为。
6. 验证两道门：模块自检（如 `step_verifier.py selftest`）+ 端到端模拟（如 `perception-decision-engine/scripts/step_verifier_v2_sim.py` 4/4）。模拟必须覆盖成功 / 静默失败 / 前置拦截 / 外部证据否决四类。
7. 收尾四件事：更新相关 SKILL.md、把脚本备份进 `scripts/`（别只留临时目录）、git commit 到技能大本营、fact_store 记一条可检索结论。
- 呈现给用户：结论 + 对比表 + 落地项 + 验证数字，不要过程流水账。

## 双方向自我进化

用户定义：进化 = ①获取新知识 ②清除冗余。两个方向必须都走完，只做一半不算进化。

### 方向一：获取新知识（增量）
1. 5-8 组全网搜索，覆盖最新研究 / SOTA benchmark / 开源工具 / 自改进机制；只取可验证数字（AUC、延迟、分数、版本、仓库名），不抄摘要。
2. 写 fact_store 前先 `search`/`probe` 查重；`add` 时必带 `entities` + 3-8 个 `keywords`（含同义词/翻译），否则事实检索不到。
3. 新知识要落到 skill：能改代码的改代码，不能改的写"第二轮调研"章节，标明已落地/未落地。
4. 并行用 delegate_task 跑知识线，主线程同时做冗余线，最后合并验证。

### 方向二：清除冗余（存量）—— 铁律是"先断根，再删除"
1. **盘点**：先跑 `python3 <本 skill>/scripts/redundancy_audit.py` 一次拿全量数字（活跃技能数、结晶垃圾、完全重复组、极小/无描述文件、`without_keywords`、埋藏事实数），再决定是否动手；脚本不可用时用 `find ~/.hermes/skills -name SKILL.md` 兜底。
2. **找源头**：`grep -rI 'Auto-crystallized from fact_store' ~/.hermes/scripts ~/.hermes/cron` → 定位生成器与调用它的 wrapper。**只删产物不断根，垃圾必然长回来**——结晶型技能会随每晚学习循环重新繁殖。
3. **断根改造**：让生成器产物落到 `~/.hermes/knowledge/crystallized/*.md`（知识库），不再写 `skills/*/SKILL.md`；去掉破坏性 sentinel（v2 会把 `retrieval_count=-999` 永久废掉知识召回）；靠产物文件存在性去重。
4. **恢复损失**：`UPDATE facts SET retrieval_count=1 WHERE retrieval_count=-999` 把被旧机制埋掉的事实恢复检索（本次恢复 44 条）。
5. **删除**：`git rm` 而不是 `rm`（必须可回滚），只删明确垃圾（auto-crystallized 单条 fact 复述、字节级重复）；工具自身双目录（如 ui-ux-pro-max 的 `.claude/skills` 与 `cli/assets/skills`）**不是冗余**，删了会破坏工具。
6. **补检索入口**：关键词存在 `facts.tags` 列的 `keywords: ` 前缀里，**没有独立的 keywords 列**（查 `keywords` 列会报 no such column）。无该前缀的事实检索不到：批量写 `keywords: k1, k2, ...` 到 tags，原 tags 挪到 `orig_tags:` 保留，`without_keywords` 必须归零。
7. **验证**：重跑生成器确认产物进知识库不进技能库；再跑一次必须 0 新建（幂等）；`git commit` + push。

**完成判定（全部满足才算进化完）**：auto-crystallized 技能数=0；`without_keywords`=0；`retrieval_count=-999` 的埋藏事实数=0；生成器二次运行新建数=0；产物落在 knowledge/ 而非 skills/；`git status` 干净。

⚠️ 判断冗余时看"有没有可执行内容"：单条 fact 复述 = 垃圾（知识留在 fact_store 即可）；有步骤/脚本/触发器 = 真技能，保留。

## 持续进化 Checklist

- [x] fact_store 持续写入（条数用 `fact_store stats` 现场查，不写死）
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
| 记忆（fact_store） | ✅ 持续写入，条数现场查 |
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
