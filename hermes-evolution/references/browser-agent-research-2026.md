# 浏览器Agent研究 — 2026年最新

## Webwright（微软研究院）⭐ 最推荐

**核心思路**：Agent不是预测坐标，而是写Python Playwright脚本，一次性执行完整工作流

```
传统方式（慢，每步都截图推理）：
click(element) → capture → click(element) → capture → ...

Webwright方式（快，脚本一次性执行）：
生成脚本 → 执行 → 验证结果
```

**Benchmark结果**：
- Odysseys: 60.1%（前SOTA 44.5%）
- Online-Mind2Web: 86.67%（GPT-5.4）
- 比逐像素点击快5-10倍

**对Hermes的启发**：
- cua_browser操作前先生成脚本，而不是逐个AX树节点点击
- 脚本可缓存复用，下次同类型任务直接加载

---

## Qwen-CUA（阿里，2026年8月论文）

**核心思路**：纯视觉computer use，截图+键鼠，no DOM/AX树

**Benchmark**：
- OSWorld-Verified: 86.2%（领先大多数专有系统）
- OSWorld 2.0: 18.5/48.4
- Qwen-CUA-Max（万亿参数）: 87.6%

**关键设计**：
- 20张截图上下文，旧截图折叠成块（降低token消耗）
- 混合专家MoE骨干（397B参数）
- 每步截图发给视觉模型推理

**对Hermes的启发**：和混合架构结合，普通操作用AX树，需要"看"时才截图

---

## cotomi Act（行为知识学习）

**核心思路**：观察用户浏览行为，自动构建任务看板+wiki

**Benchmark**：
- WebArena: 80.4%（超过人类基准78.2%）

**关键设计**：
- 自适应延迟观察（减少冗余截图）
- 行为→知识管道
- 双向编辑：用户和Agent共同维护

**对Hermes的启发**：idle_learning可以观察用户搜索行为自动构建知识库

---

## TOCTOU漏洞（安全）

**问题**：页面在"规划"和"执行"之间发生变化

```
Agent读取DOM（整洁）→ 规划点击位置 → 页面更新 → 点击到错误位置
```

**影响**：100%的浏览器Agent框架都会触发

**防御**：预执行验证（执行前检查DOM是否变化），开销<0.05秒可忽略

**对Hermes的启发**：所有browser操作前加DOM稳定性检查

---

## 2026-11 格局更新（过渡验证 / 能力边界）

**WebMCP（用户长期追踪项）**：Brave Leo 在 Nightly 1.102.2 默认开启（PR #40616 合并）；ChatGPT 桌面起首个主流默认开启 site tools；WebKit 反对、Firefox 仍用旧 `navigator`。→ 站点覆盖与无头支持仍不足，**未到替代 browser_exec/CDP 的切换点**，继续跟踪。

**网页强 ≠ 桌面长程强**：UI-Venus-2 WebVoyager 90.8/93.4，但 OSWorld 2.0 binary 仅 0.0%/2.8%。→ 网页导航分数不能外推到真实桌面操作；评测看 OSWorld 类长程任务而非 WebVoyager。

**动作 guard 得到实证**：MetaAct 把自进化编译成可执行动作 guard，ScienceWorld 违规 70%→0%、WebShop 40%→1%。→ 印证执行前 guard（陈旧目标拦截）比事后判断更值。

**记忆门控与筛选**：ARISE 留出集准确率门控 +10.9pp 且调用更少；Anchor 重放源决策筛选，+19.9% 且少留 41% 记忆卡。→ 记忆只记被决策真正用过的，别无限累积。

**自进化技能泛化有限**：21 个训练提升技能仅 5 个完整迁移，LLM judge 一致率 86% 却难预测单次编辑。→ 单条事实复述型技能本就迁移不了，删它们不是损失。

**Benchmark 现状**（避免引用过时论文数）：OSWorld 2.0 v2.1 官方榜首 44.33% binary / 77.67% partial；OSWorld-Verified 榜首 90.19%、通用模型 claude-fable-5 85.96%（人类基线 ~72%）；WebArena 榜首 86.1%、最佳开源 74.3%（DeepSeek v3.2）。

---

## 2026-08-17 实测补充

### GitHub Top工具星标（生态影响力）

| # | 工具 | Stars | 核心能力 |
|---|------|-------|---------|
| 1 | browser-use | 109K | SOTA浏览器Agent DOM+CDP |
| 2 | awesome-hermes-agent | 5.3K | 353个技能插件索引 |
| 3 | hermes-agent-self-evolution | 5K | DSPy+GEPA自动优化skills |
| 4 | awesome-hermes-skills | 412 | 即装技能库 |
| 5 | MCP (官方) | 官方 | 100+服务器连接 |
| 6 | Camofox | 社区 | Firefox抗检测+持久化 |
| 7 | cua-driver | 内置 | 背景桌面控制 |

### cotomi Act（2026-08-17 补充）

- WebArena 80.4% > 人类基线78.2% ✅ 真正超越真人
- 行为观测：被动观察用户浏览 → 蒸馏成结构化知识
- Shared Knowledge Workspace：人+Agent共同编辑
- 方向：让Agent从"执行者"变"懂你的同事"

### 超人性能关键指标

```
真人瓶颈：5-10秒/操作，记忆碎片，单线程，注意力分散
Agent优势：0延迟，完美记忆，并行任务，24/7，零干扰
```

### 已安装验证（2026-08-17）

| 工具 | 验证结果 |
|------|---------|
| browser-use CLI v0.1.4 | ✅ Chrome CDP连接正常 |
| Camofox v1.6.0 | ✅ localhost:9377 运行 |
| Camofox持久化 | ✅ cookies写入~/.camofox/profiles/{SHA256}/ |
| async-delegate plugin | ✅ 已装入~/.hermes/plugins/ |
| hermes-agent-self-evolution | ✅ pip install -e完成 |
| CAMOFOX_URL环境变量 | ✅ 已写入~/.hermes/.env |
| Hermes Gateway Camofox路由 | ✅ 已重启生效 |

### async-delegate 架构

```
delegate_async tool → 后台spawn hermes chat → task_id立即返回
                                         ↓
                              ~/.hermes/async-tasks/{task_id}.done
                                         ↓
                              Watcher线程检测完成 → 注入结果到原会话
```
inject_mode: "queue"(默认，不打断当前对话) 或 "steer"(穿插进工具循环)。

### hermes-agent-self-evolution 架构

```
执行traces → GEPA优化器 → 候选变异 → 约束门(测试/大小限制)
                    ↓
              最佳variant → PR against hermes-agent
```
Phase 1 (✅): Skill文件优化
Phase 2-4 (🔄): Tool描述→System Prompt→Tool代码逐层优化
