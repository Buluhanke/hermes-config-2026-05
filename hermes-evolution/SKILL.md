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

### 旧 browser_* 工具引用迁移（2026-11-23）

Hermes v0.23+ 只保留 `browser_exec`(Python code + helpers)，旧 `browser_navigate/click/type/snapshot/vision/console/scroll/press` 全部移除。**迁移规则**：

- 脚本 `~/.hermes/scripts/migrate_browser_exec.py`（默认 dry-run，`--apply` 才写入），备份在 `~/.hermes/cache/scratch/browser-refs-backup-*/`。
- **语义改写而非机械改名**：`browser_navigate(url=...)` → `browser_exec(code="new_tab(...)")`;`browser_click(ref=...)` → `browser_exec(code="js('...click()')")`;`browser_type` → `fill_input(selector, ...)`;`browser_snapshot()` → `page_info()`;`browser_vision` → `capture_screenshot()` + vision_analyze;`browser_press` → `cdp('Input.dispatchKeyEvent', ...)`;`browser_scroll` → `js('window.scrollBy(...)')`。
- 裸 `browser_navigate https://url` 必须先于裸词替换处理，否则会被改成语法错的 `browser_exec https://url`。
- `browser_vision(question="...)")` 的正则必须整行匹配(`^...$` + MULTILINE)，否则引号内 `)` 会截断替换留下垃圾尾巴。
- **只改活跃 SKILL.md 的调用指令**；`references/`、`references/日期文件`、`.archive/` 是历史纪实，保留原文。历史架构描述行(如 `browser_click() → _run_browser_command()`)用 KEEP_LINES 白名单跳过。
- 迁移后抽检：grep `browser_exec (https|file|--)`、残留 `annotate=true`/`@eN` 等旧机制描述，手动修干净。

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
- **保留父本可回滚**：ARC-AGI-3 harness 研究（2610.30499v2）27 lineages 两次自修订后**无一保留父代能力**——改完必须能退回上一版（git commit 或备份），且"生成修订"与"决定部署"分开：先按 dev/自测分筛选快照，再部署，别改完直接上。
- **别只改 prompt**：MultiLoop（2611.15754）多 agent 只做 prompt 优化反 -2.65%，编排/结构不动则多 agent 特有问题不会消失。改结构优先于改措辞。

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

Layer 3: browser_exec
  → Hermes 唯一的浏览器自动化工具（旧 browser_* 工具集已移除，勿再引用）
  → 需要真实登录态时用镜像 CDP Chrome；动态页仍优先 Layer 1+2

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

## 2026-11-22 23:00 自学增量（cron 只读，固化于此）

**写门验证（FGSE，2611.14326）**：把每条经验当结构化假设——precondition / behavior change / expected effect / verifier——先临时应用，再过 target-transfer、falsification、archived-regression 三类探针才提交进持久记忆；WebArena 39.8、AppWorld 78.8，falsification failure 5.0%、regression damage 1.3%、有害提交 3.6%。→ 给 fact_gate 写前 check 和 skill "patch 后先自测，失败丢弃" 提供了论文级背书；下一步可加"回归探针"（不仅看新收益，也确认旧能力没坏）。

**评估可靠性才是瓶颈（Resolution Hypothesis，2611.23068）**：7 种进化方法、6 个模型、1000 万+ LLM calls——候选层"选择"区分有益/有害 artifact 的能力不比随机好，错误跨轮累积；方法层几个百分点的差距小于同方法两次独立运行的差异，很多排行榜名次靠运气。→ 进化报告只写可复现实测数字；skill 变体对比必须同条件多跑，别信单次分数；也印证"archive 对比升华"要配稳定 verifier 才有意义。

**验证器共进化（Verify by Doing，2611.15276）**：Actor 与 Evaluator 双 harness 在单任务内共进化、不需要外部反馈；用工具检查 artifact 和环境状态产生证据，Evaluator 采纳与 Actor 保留分开决策。→ 对应"先验证再宣布完成"，且验证逻辑本身也要能被更新。

**NorthCUA（2611.02102）**：开源 CUA 家族 Nano 9B / Mini 35B / Pro 397B（基座 Qwen3.5），Pro 在 OSWorld-Verified 88.64%、WebArena-Verified 73.89%，Mini 85.30% 超 Kimi-K3；Experience Flywheel 用可执行任务→已验证轨迹→递归自改进演化可复用 skill，Ultrafast 变体 2.3× 提速。→ "技能飞轮"路线拿到开源 SOTA 验证，方向与 L3/L4 一致。

**WebMCP（用户长期追踪项，更新上一轮判断）**：origin trial 已从 Chrome 149–156 延长到 149–162（最晚 2027-03-30 结束），11-04 API owners 把 usage 上限 0.5% 放宽到 2%；11-14 实测 Browser Use 目录 60 个头部站点，开 flag 时 47 站注册 213 工具，stock Chrome 156 仅 13 站暴露工具（21.7%），ChatGPT/IKEA/Cloudflare/Vercel 等 34 站无 token 导致 `document.modelContext` 不存在；API 定稿在 `document.modelContext`，declarative 表单属性 2026-10-08 移出规范；Edge 158（11-19）跟进 OT，Firefox 中立、WebKit 反对。→ 站点覆盖仍极低，远未到替代 CDP/Browser Use 的时候，继续按周期跟踪。

**Hermes 版本线补**：v0.23.0（11-05 "Hearth"，~1,950 PRs）新增 `hermes curator lock`（手工整理的 skill 可锁，任何工具含 `--yolo` 都改不动）、`hermes cron cancel` + per-job `--catch-up`、compaction 摘要 `UNVERIFIED:` 行、同一 cron 任务共享 prompt cache；v0.23.1（11-10，~618 PRs）。→ 用户自有且不该被 agent 改的 skill 可主动 lock；compaction 的 UNVERIFIED 标记对"不编造"有用；cron 缓存共享对每天多 job 的这台机器直接省 token。

**Benchmark 补充**：OSWorld-Verified 另一来源榜（2026-11-08）Kimi K3 84.8%、Gemini 3.6 Flash 83%、MiMo-V2.6-Pro 82%，全部厂商自报、无独立复现；同一模型 step budget 从 9.1%→23.0%，引用分数必须带 step cap 和 release。

## 2026-11-23 23:00 自学增量（cron 只读，固化于此）

> 13 条新结论全部过 `fact_gate.py check`=accept（score 53–71，max_similarity ≤0.07，无近重复）；fact_store 本轮实测仍只读，故固化于此，待主线程写入。

**工具路线获独立验证（最重要）**：browser-use 1.0（11-10 正式版）把 0.x 的 24 个浏览器动作砍成**单一 `python` 工具**——持久 REPL 内预置 harness helpers + raw CDP（Pydantic AI 驱动）。BU Bench v2.1 上同三个模型比 0.x 高 **14–33 分**、成本低 **2.7–5.2×**；代码 178 个 py 文件→43 个，删 136,905 行、加 29,601 行。→ **与 Hermes v0.23 把 browser_* 全删只留 `browser_exec` 是同一判断的独立复现**："给模型代码而不是动作菜单"能解锁 agent 自解 hung page、直呼私有 API 等菜单外行为。写自动化 skill 时坚定 code-first，勿回退到动作枚举。默认也变了：`llm=bu-fast`、云浏览器、`mode='ultrafast'`(AX-tree id)、`max_steps=100`。

**browser-use 补丁**：1.0.7（11-?）MCP 调用不再 60s 超时——长 `browser_exec` 50s 先回已产输出、空 code 调用取剩余，Cursor 等 60s 限客户端不再断；1.0.8（11-22）judge 作为 run 额外一轮从缓存读不重复计费、无 API key 的 headless/SSH 打设备授权链接、`bu.type` 不打印密码字段、`Browser(cdp_url=...)` **附着已开的那页而非新空白 tab**（对齐本机 CDP 复用习惯）、gateway 预留 token 32,768→16,384。

**Camofox v1.19.0（11-10）**：每个浏览器动作都成 agent 工具，HTTP API 与 MCP/OpenClaw 工具面 build-time parity gate 强制对称；新增 `camofox_upload`、`fullPage` 截图、每调用 `userId/sessionKey`、`evaluate` 的 `timeoutMs` 真生效。低层原语：坐标点击可断言 `expected_role`/`expected_accessible_name`（目标漂移即拒）、raw AX 树、storage state 导入导出、trusted drag、元素级滚轮。容器默认 non-root，缓存迁到 `/opt/camoufox-cache`——**硬编码 `/root/.cache/camoufox` 的部署要 repoint**。

**递归自改进框架集群（对 L3/L4 的方法论校准）**：
- **Flex-RSI（2611.08946）**：24 任务 18 模型，自改进在 150/177 runs（85%）提升、中位 +10.4 分；闭源中位 +14.9 vs 开源 +8.5——**只记成功/失败的反馈拖累开源模型**，标量评分更友好；编辑 harness 本身确实贡献增益；agent 自建解法的任务收益最大，单答案任务原地踏步。榜 flex-rsi.github.io。
- **BOXBOX（2611.09218）**：agent 触发式 harness 修订 + 内核热重载保上下文；PerfRace Speedup@4h **1.70×** vs 最强基线 1.54×、Frozen 1.442×；**离线 harness 优化 HE 1.281× 反低于 Frozen**——离线优化不保证泛化，任务内在线改才有持续收益。
- **生成≠部署**：ARC-AGI-3 harness 研究（2610.30499v2）27 lineages 两次修订仅 +2.80 held-out RHAE（95%CI 跨 0），**无修订保留父代能力**；事后按 dev 分从快照里挑升到 +4.53——印证 skill"patch 后先自测失败丢弃"还需加"保留父本可回滚"。
- **多 agent harness 共进化**：MAS-Loop（2610.38946）Orchestrator+trajectory-conditioned Refiner 做 bounded patch、同任务重跑测变化，Refiner 可迁移到外部生成的 MAS；HarnessNet（2610.15221）Agentron 单元+本地 optimizer+反馈逐层反传，达全局 optimizer 相当增益而 token 更少、换基座后仍有效；**MultiLoop（2611.15754）只有 10 训练样本即 +4.6%（71.88%），但编排失败大多持续，仅 prompt 优化反 -2.65%——只改 prompt 不动结构是死路**；IAPO（2611.07495）交互项占编排可达增益一半、删掉掉 7–17 分；DualEvolve（2611.04439）外层用 grader 给"过程质量分"更新 harness+skill 规则，64 组全胜 DeepEvolve +7.6%HR@5/+9.0%NDCG@5。

**WebMCP（用户长期追踪项，规范级更新）**：**2026-11-23 发布 Draft Community Group Report**——`ModelContext` 接口定稿为 `registerTool`/`getTools`/`executeTool` + `ontoolchange`/`ontoolactivated`/`ontoolcancel` 事件；Chrome 159 加 `outputSchema`（execute 返回按 schema 校验）、Chrome 153 支持 AbortSignal 注销工具而不打断执行中调用；`getTools({fromOrigins})` 显式列源才可跨源。OT 仍延至 Chrome 162（2027-03-30），状态 **Proposed 无 ship 里程碑**。→ 规范在收敛但站点覆盖仍极低，继续按周期跟踪，未到替代 CDP 时点。

**Benchmark 校准（引用必带 step cap/release）**：OSWorld-Verified（11-23 读）Intelligence-Indeed Agent 90.2%（100 步+coding 动作）居首、通用模型 Claude Fable 5 86%（1M 上下文/100 步）、人类基线 72.4%；OSWorld 2.0 v2.1 榜首 Claude Opus 5 max **44.33% binary / 77.67% partial**（500 步），框架 44.44% binary（450 步）——注意同模型 v2026.08.08 只有 31.43%，**分数不可跨 release 比**；WebArena 86.1%（Narada AI Code）超人类 78.24%，最佳开源 74.3%（DeepSeek v3.2）。

## 版本迁移与技术增量（指针）

- Hermes v0.23.0 起旧 `browser_*` 工具全删、只剩 `browser_exec`；盘点迁移清单与 WebMCP / UI-Venus / ARISE / Anchor / MetaAct 等 2026-11 研究结论见 `references/browser-agent-research-2026.md`。写自动化 skill 时勿再引用旧工具名。
- 新工具可用性（browser-use / Camofox / cua-driver 等）与自改进框架细节见 `references/self-improvement-frameworks-2026.md` 和 `references/browser-agent-research-2026.md`，SKILL.md 不重复流水账。

## 每日进化前置自检
- **不绑定任何模型是用户铁律**：cron 任务不 pin、config 不设 `fallback_model` / `fallback_providers` 锁定，给什么模型就用什么模型、跟随当前主模型。模型失效时手动切换，不做自动轮替，也不要自动恢复 fallback 链——旧版"fallback 为空就恢复三链"的自检已废弃，它会违背这条铁律。
- 失效进化任务的正确修法是 `cronjob_manage(action='update', pinned=false)` 取消 pin + `hermes config unset fallback_model` 清隐藏绑定，而不是换一个模型 pin 上。**pin 免费模型必翻车**：免费额度到期就 404、地区受限就 403，cron 静默停摆且用户看不到 last_status。
- 不要用直接编辑 config.yaml 的方式改配置（安全护栏会拒绝），用 `hermes config set/unset`；cron 上下文 fact_store 只读，决策写入本 skill 或报告。
- **本机 git 必须走 `/usr/bin/git`**：PATH 里的 `/usr/local/bin/git` 是 x86 二进制，在 ARM Mac 上报 `Bad CPU type in executable`，所有 `git add/commit/status` 都会失败。技能大本营 `~/.hermes/skills` 的提交统一用绝对路径。
- 验证进化任务是否真跑：`cronjob_manage(action='run')` 手动触发一次并读输出文件，别只看 `last_status`。
- 给 `no_agent=true` 的 cron 写脚本时，stdout 会被原样投递为消息：凡输出 JSON 必须给**合法且完整**的精简摘要，明细另写报告文件。**严禁用 `json.dumps(payload)[:N]` 截断**——截断后的 JSON 在消费端 `json.loads` 直接失败，而这类错误只会在下一次手动触发时才暴露。脚本写完必须立刻手动跑一次 wrapper，确认 stdout 可被解析。

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
4. 并行用 delegate_task 跑知识线，主线程同时做冗余线，最后合并验证。**别用 fork 前的 stats 快照报新增 fact ID**——子 agent 仍在写入时快照是过期的，ID 段会报错；等 delegation 回报里的 `fact_ids` 数组为准，再写进 skill 和最终结论。

### 方向二：清除冗余（存量）—— 铁律是"先断根，再删除"
1. **盘点**：先跑 `python3 <本 skill>/scripts/redundancy_audit.py` 一次拿全量数字（活跃技能数、结晶垃圾、完全重复组、极小/无描述文件、`without_keywords`、埋藏事实数），再决定是否动手；脚本不可用时用 `find ~/.hermes/skills -name SKILL.md` 兜底。
2. **找源头**：`grep -rI 'Auto-crystallized from fact_store' ~/.hermes/scripts ~/.hermes/cron` → 定位生成器与调用它的 wrapper。**只删产物不断根，垃圾必然长回来**——结晶型技能会随每晚学习循环重新繁殖。
3. **断根改造**：让生成器产物落到 `~/.hermes/knowledge/crystallized/*.md`（知识库），不再写 `skills/*/SKILL.md`；去掉破坏性 sentinel（v2 会把 `retrieval_count=-999` 永久废掉知识召回）；靠产物文件存在性去重。
4. **恢复损失**：`UPDATE facts SET retrieval_count=1 WHERE retrieval_count=-999` 把被旧机制埋掉的事实恢复检索；也可直接跑 `python3 <本 skill>/scripts/fact_gate.py restore`。
5. **删除**：`git rm` 而不是 `rm`（必须可回滚），只删明确垃圾（auto-crystallized 单条 fact 复述、字节级重复）；工具自身双目录（如 ui-ux-pro-max 的 `.claude/skills` 与 `cli/assets/skills`）**不是冗余**，删了会破坏工具。
6. **补检索入口**：关键词存在 `facts.tags` 列的 `keywords: ` 前缀里，**没有独立的 keywords 列**（查 `keywords` 列会报 no such column）。`fact_store enrich` 只列出待补事实、不自动写入，批量补齐要么逐条 `update`、要么直接改 `facts.tags`（后者快，但必须把原 tags 挪到 `orig_tags:` 保留）。`without_keywords` 必须归零。
7. **验证**：重跑生成器确认产物进知识库不进技能库；再跑一次必须 0 新建（幂等）；`git commit` + push。

**完成判定（全部满足才算进化完）**：auto-crystallized 技能数=0；`without_keywords`=0；`retrieval_count=-999` 的埋藏事实数=0；生成器二次运行新建数=0；产物落在 knowledge/ 而非 skills/；`git status` 干净。

⚠️ 判断冗余时看"有没有可执行内容"：单条 fact 复述 = 垃圾（知识留在 fact_store 即可）；有步骤/脚本/触发器 = 真技能，保留。

### 配套：fact_store 写入门控（2026-11-22）

清除冗余之后必须给入口装门，否则噪声很快又累积回来。实现：`~/.hermes/scripts/fact_gate.py`（纯 stdlib，零 LLM）。

1. **写前门控（每次 add 前必跑）**：`python3 fact_gate.py check --content "..." --category "..."` → `verdict=accept|review|reject`。
   - 重复门（ARISE 2611.23588 的本地近似）：候选与**已被召回过**的高质量 fact 做中英 token Jaccard，≥0.78 直接 reject。
   - 噪声门：`测试` / `[标签]+空泛句` / 裸论文标题 / arXiv 自动摘要，短且无可验证信号 → reject。
   - 可验证信号加分：数字、百分比、路径、仓库名、版本号、模型名、named entity。
   - `reject` 就不要写；`review` 要补数字/出处后再写。
2. **留存审计（周期）**：`python3 fact_gate.py audit [--apply]`。Anchor（2611.10382）的本地近似：用 `retrieval_count` / `helpful_count` 判断记忆是否真被决策用过。三档 KEEP / WATCH / ARCHIVE_CANDIDATE。
   - **铁律：`--apply` 只在 tags 追加 `gate:archive-candidate`，绝不删除、绝不改 content**，可回滚；幂等（第二次 0 新建）。
   - 完整明细报告在 `~/.hermes/fact_gate_report.md`。
   - 专门收窄过归档规则：无数字但有实质内容的框架名/基准名不能被误伤。
3. **周期调度**：cron `b5568e72bddf` = `fact-gate-weekly`，每周日 04:00（错开 03:00 净化），`no_agent=true` 纯脚本、不调用任何模型、deliver=local。用户铁律：不绑定任何模型 —— 门控天生不需要模型。
4. **恢复被埋事实**：`python3 fact_gate.py restore` 把旧机制留下的 `retrieval_count=-999` 恢复为 1。

**验收标准**：`audit` 报 KEEP/WATCH/ARCHIVE 三档，归档候选只含明确噪声（自动摘要、测试记录、空泛标签），打标记后 content 零改动；写前 `check` 对有效事实给 review/accept、对 `测试` 类噪声与空泛标签必须 reject 并命中 near_duplicate。具体条数现场查，不写死。

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
