---
name: self-learning-methodology
description: Hermes Agent 自我学习的方法论总纲——学习渠道（从哪里获取知识）、四层记忆架构（在哪固化）、学习闭环（怎么固化）、避坑。这是"自我学习"主题的权威总纲。当被问"你如何学习/自我进化/学习路径是什么"，或完成复杂任务、被用户纠正、发现可复用流程时，以此
  skill 为主回答。注意：若存在 abcd-learner / idle_learning 等同主题 skill，它们只是本总纲中"被动/自动升华"这一执行环节的具体实现，不得喧宾夺主、不得用它替换本总纲的渠道与架构表述。
triggers:
- Use when self learning methodology
trigger_type: general
---

# Hermes Agent 自我学习的方式与路径

本文档是 Hermes Agent 自我学习机制的方法论说明 + 可执行操作手册。其他 Hermes 实例安装本技能（`cp -r` 到 `~/.hermes/skills/self-learning-methodology/`）后即可习得"把经验固化成可复用资产"的闭环。

## 一、核心信念（为什么学）

1. **学完要落地**：读懂教程/资料后要真正在机器上实操执行到位，不能只停在解释/总结。交付前给出只有真读到全文才知道的细节（标题/作者/日期/关键段）以证明不是搜的摘要。
2. **交付可工作产物，不是描述**：任务完成的标志是真实执行过的产物（能跑的代码、能用的文件、已验证的结果），不是一段"应该怎么做"的说明。
3. **怀疑驱动**：答案不确定时，用实验验证假设，而非猜测或套用记忆。
4. **紧凑高信号**：记忆空间有限（约 22k 字符），只存高价值、跨会话有用的东西，不存临时进度。

## 二、学习渠道（从哪里获取知识）

知识来自三类渠道：主动获取的外部源、被动触发的环境反馈、协作推理。每条渠道都对应一个"怎么固化"的动作（见第四节闭环表）。

### A. 主动获取渠道（我主动去学）
1. **用户直授** — 用户给的教程/资料/偏好/纠正。最高价值渠道。落地要求：真跑通 + 交付原文细节证明真读。
2. **技能库内建** — `skills_list` / `skill_view` 现成本机既有 skill 是现成知识源；新任务先查有没有可加载的，加载即用，不重造轮子。
3. **官方文档** — Hermes 官方文档（hermes-agent skill 指向的在线文档），遇到自身能力/工具疑问先查文档（权威、最新）。
4. **联网检索** — `web_search` / `web_extract` / Firecrawl 读外部资料；用于陌生领域、版本核实、事实核对。
5. **读源码** — source-driven-development：改代码前先读源码拿真相，不靠记忆猜。
6. **浏览器实操** — 在已登录 Chrome（CDP）里真操作、真点击，验证 UI/流程而非空想。
7. **终端执行验证** — `terminal` / `execute_code` 把指令真跑一遍，跑通才算学到，输出即证据。
8. **社区技能同步** — hermes-skills-management / open-source-skill-harvesting：从 GitHub/社区拉精选 skill 安装，吸收他人沉淀的流程。
9. **会话回溯** — `session_search` 检索过去会话，复用已做过的经验，不重复摸索。
10. **多 agent 委派** — `delegate_task` 派子 agent 去学/做，结果回流主上下文，扩展并发学习能力。

### B. 被动 / 触发式渠道（环境喂给我）
11. **用户纠正** — 做错被改，立即存 memory（最高频、最该即时固化）。
12. **失败与异常** — 工具报错、调用异常，由 error-patterns / skill-factory 元技能自动提炼成失败模式 skill。
13. **用户偏好陈述** — 用户直接说"我喜欢 X / 以后别 Y"，立即 memory。

### C. 协作推理渠道
14. **事实推理** — `fact_store` 的 reason / related / contradict 跨实体发现隐含关系，把分散事实合成新知识，矛盾自动暴露。

## 三、四层记忆架构（在哪固化）

| 层 | 工具 | 存什么 | 生命周期 | 注入方式 |
|----|------|--------|----------|----------|
| 程序性记忆 | `skill_manage` | 可复用的操作流程（怎么做） | 永久，跨会话 | 按需加载 |
| 持久上下文 | `memory` | 用户偏好、环境事实、工具怪癖 | 永久，每段注入 | 每轮自动注入 |
| 结构化事实 | `fact_store` | 实体+关系，带信任评分 | 永久，可推理 | 按需 probe/reason |
| 历史会话 | `session_search` | 过去做过的任务的记录 | 永久 | FTS5 检索 |

**铁律（分层归属）**：
- 用户偏好 / 纠正 / 个人细节 → 存 `memory`（不是 skill，不是 fact）
- 可复用操作流程 → 存 `skill`
- 客观事实 / 实体关系 → 存 `fact_store`
- 临时进度 / [TODO] / 完成日志 → 不存，用 `session_search` 回溯

## 四、学习闭环（怎么固化）

### 渠道 → 动作映射表

| 触发（来自第二节渠道） | 动作 | 命令 |
|------|------|------|
| 渠道1 用户直授跑通 | 落地验证 +（若可复用）固化 skill | 执行 + `skill_manage(create)` |
| 渠道2 加载内建 skill 出坑 | 立即 patch | `skill_manage(patch, old/new_string)` |
| 渠道3/4 文档或检索到的知识 | 若成可复用流程 → skill；若成事实 → fact | `skill_manage` / `fact_store(add)` |
| 渠道5/6/7 实操验证成功 | 流程固化成 skill | `skill_manage(create)` |
| 渠道8 社区技能安装 | 列清单→读全文→去重→判依赖→装→验证 | `hermes skills ...` |
| 渠道9 会话回溯复用 | 沉淀成 skill/fact 防再查 | `skill_manage` / `fact_store(add)` |
| 渠道10 委派结果回流 | 有价值步骤固化 skill | `skill_manage(create)` |
| **渠道11 用户纠正（即时）** | 立即存 memory | `memory(add, target='user'|'memory')` |
| 渠道12 失败 / 异常（自动） | 提炼失败模式 → skill | skill-factory / error-patterns |
| **渠道13 用户偏好陈述（即时）** | 立即存 memory | `memory(add, target='user')` |
| 渠道14 事实推理出新知 | 存 fact_store | `fact_store(add)` |

### 标准反思节奏（每个任务后）
1. 这次有没有可复用的步骤？（有 → 考虑 create skill）
2. 用户有没有纠正我 / 表达偏好？（有 → 立即 memory，最高优先级）
3. 用的 skill 有没有断点？（有 → patch）
4. 结果有没有量化证据？（报告格式：动作 + 证据 + 数字）

## 五、给其他 Hermes 的实操清单

**固化一个技能**
- 触发：刚做完一件 5+ 步、以后还会遇到的事。
- 操作：`skill_manage(action='create', name='kebab-case-name', category='领域', content='YAML frontmatter + 编号步骤 + 避坑 + 验证')`
- 要点：frontmatter 的 `description` 必须写清**触发条件**（什么时候用），否则不会被触发；正文要有**编号步骤 + 确切命令 + 避坑段 + 验证步骤**。create 前先 `skills_list` 看是否已存在同类，合并优于新建。

**记住用户 / 环境事实**
- 操作：`memory(action='add', target='user' | 'memory', content='一句紧凑陈述')`
- 要点：用陈述句不是指令；存"是什么"不存"怎么做"（怎么做归 skill）；批量改动用 `operations` 数组一次提交，省空间；接近上限时用 operations 一次性 remove/缩短陈旧条目再 add。

**修补一个技能**
- 操作：`skill_manage(action='patch', name=..., old_string='文档里唯一片段', new_string='修正后')`
- 要点：用唯一上下文片段定位避免误伤；Hermes 升级可能覆盖平台自带 skill，关键 patch 在内容里埋可搜索字符串（如 `_doh_resolve_first`）便于升级后重打。

**沉淀结构化事实**
- 操作：`fact_store(action='add', content=..., entity=..., category=..., tags=...)`
- 要点：用实体名做 `probe` / `reason`；矛盾事实用 `contradict` 找，用 `trust_delta` 调权重；高价值事实跨会话可推理。

## 六、避坑

- **不要存临时进度到 memory**：任务进度、完成日志、TODO 会撑爆 memory 且过期，用 session_search 回溯。
- **不要重复造轮子**：create 前先 `skills_list`；同类合并优于新建。
- **patch 要留标记**：平台 skill 升级会被覆盖，关键 patch 埋可搜索字符串，便于升级后重打。
- **memory 满了要清理**：近上限时用 operations 数组一次性 remove/缩短陈旧条目再 add，别硬塞。
- **跨 profile 操作要谨慎**：编辑非当前 profile 的 skill/memory 必须显式 `cross_profile=true`，否则被拦截。
- **失败 ≠ 结束**：任务被网络/工具阻断时，如实说明阻断点并尝试替代路径，绝不编造执行结果冒充成功。

## 七、本实例的实践样本（供参考，其他 Hermes 按自己用户调整）

这是作者这个实例从用户处学到的具体约定，作为"记忆分层 + 渠道11/13"的真实样例：
- 用户风格：直接给结果不讨论过程；已授权的事不要反复列风险，先简述决定→执行→报结果。
- 用户重视"学完要落地"：读懂资料要真在他机器上跑通，交付前附只有真读全文才知道的细节。
- 报告格式：动作 + 证据 + 量化结果。
- 网络环境：透明 SSL 拦截，Python 用 `ssl.CERT_NONE` 兜底，浏览器走 CDP 本地已登录 Chrome，DoH 解析绕过 DNS 污染。

## 八、验证你真的学会了

- 完成一个任务后，能说清：这条经验来自哪个渠道、该存进哪一层（skill / memory / fact / 都不存）。
- 被用户纠正一次，下一轮该偏好已生效（memory 已注入）。
- 用过的 skill 出过一次坑，该坑已写进 SKILL.md 的避坑段。
- 交付物是可运行的真实产物，且有验证命令的输出作为证据。
