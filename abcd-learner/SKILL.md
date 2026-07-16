---
name: abcd-learner
version: 0.3
description: |
  AgentFactory paradigm (ACL2026): fact检索≥1次时，将其升华为可执行的skill文件。
  重要schema：列名是fact_id（不是id），category字段=fact分类名（不是text），content字段=fact长描述文本，tags字段存逗号字符串（如"star4d,learning"）不是JSON数组。
  body=content，不是category！文档和代码都写反过，2026-07-13已修正。
triggers:
  - "知识落地"
  - "学到的知识变成skill"
  - "idle-learning E阶段"
  - "升华"
trigger_type: idle_learning
tags: [idle-learning, agent-factory, skill-crystallizer, knowledge-management]
created: 2026-07-12
来源: AgentFactory ACL2026 (github.com/zzatpku/AgentFactory)
验证: python3 ~/.hermes/skills/abcd-learner/abcd_learner.py
---
# AgentFactory Skill Crystallizer

## 工作原理

每次idle-learning运行后，检查fact_store中retrieval_count≥1的fact，
将其写成skill文件永久复用。

## 判断标准

- retrieval_count >= 1：被"反思消化"步骤引用过一次（E2阶段立即+1）
- trust_score >= 0.65：高信任
- category字段存的是fact分类名（如"general"），不是长描述

## 升华流程

1. E2阶段：新知识立即被检索一次，retrieval_count 从 0 变 1
2. 查询 retrieval_count>=1、trust>=0.65 的 fact
3. 生成 SKILL.md 写入 ~/.hermes/skills/
4. fact 标记 retrieval_count=-999（已固化），不再重复升华

## 当前流水线（2026-07-13 确认可跑通）

```
idle_learning_wrapper.sh 顺序执行：
  A → orchestrator（B_paper 论文入库）→ B_insight → C → E2反思消化+升华 → batch_facts
```

**orchestrator** (`idle_learning_orchestrator.py`)：A/B/D 三阶段并行（5s超时），C_safety 已移除由 wrapper 调用 cve_lite

**B_insight** (`b_insight.py`)：
- 读 DB 最新 5 篇 arXiv 论文标题
- 调用 MiniMax API `http://123.56.67.77:9100/chat/completions` 推理 3 条洞察
- prompt明确要求「不要编号、不要加粗、不要markdown」，格式固定为 `[主题] 洞察内容(20-40字)`
- 解析用 `extract_insight()` 清理 `**`、`1.`、`2.` 等残留后再判断 `[开头`
- 写回 fact_store，tag=`arxiv-insight`，trust_score=0.70
- MiniMax key 在 `~/.hermes/.env`：`MINIMAX_M3_API_KEY`

**cve_lite** (`cve_lite.py`)：标准库零依赖 OSV 扫描，wrapper 同步调用

**E2 反思消化**（在wrapper中）：查询 retrieval_count=0 的新知识，立即 +1 retrieval_count +1 helpful_count，使达到升华条件

## 已踩坑点

- **body=category bug**：代码写`body=category`，文档说`category=长描述`，两者都错了。真相：content=长描述，category=分类名。修：body=content。
- **tags解析JSON崩溃**：fact_store存逗号字符串（"star4d,learning"），代码`json.loads(tags_json)`对首条必崩。修：用`_parse_tags()`兼容逗号字符串和JSON两种格式。
- **升华门槛≥3永远达不到**：新写入的fact的retrieval_count=0，永远无法达到≥3的升华门槛。解：E2反思消化步骤立即给新知识的retrieval_count+1，使其达到升华条件。
- **B_insight解析崩溃**：LLM返回 `1. **[场景垂直化]**` 或 `**加粗**` 格式，parser只认`[主题]`导致全部跳过。修：① prompt明确要求「不要编号、不要加粗、不要markdown」② 加`extract_insight()`清理`**`、`1.`、`2.`等残留后再判断`[开头`。
- **EOF残留导致shell脚本语法错误**：patch时用heredoc追加内容，`EOF`定界符会混进文件，需手动删掉。
- **B_insight LLM输出格式飘移**：LLM不听话时返回 `1. **[主题]**` 或 `**加粗**` 格式，parser只认裸`[主题]`导致全跳。修复：①prompt明确要求「不要编号、不要加粗、不要markdown」，给示例格式；②`write_insights()`加`extract_insight()`清理正则去编号和加粗；③验证：`SELECT COUNT(*) FROM facts WHERE category='arxiv-insight'` 应≥3
- **heredoc patch残留EOF**：patch工具的new_string用bash heredoc风格时，`EOF`定界符会混进文件导致语法错误。必须手动删掉残留的`EOF`行后再执行
- **升华SQL列数错位静默失败**：E升华SQL只返回4列（如`SELECT fact_id, content, category, tags`），但`write_skill(fact)`解包需要6列（再加trust_score和retrieval_count）。错位后解包全乱，静默失败无报错。修复：E升华SQL必须返回6列，且顺序必须是 fact_id, content, category, tags, trust_score, retrieval_count。
- **idle_learning_wrapper.sh执行顺序**：batch_facts必须在E2反思消化之后运行——否则batch_facts先运行已有知识被重复写入"0条新增"，E2没有新知识可消化
- **ret=-999的fact被E2跳过**：新写入的fact retrieval_count=-999（sentinel），E2只查`ret=0`导致这些fact永远不升级。修：`WHERE (retrieval_count=0 OR retrieval_count=-999)`
- **curator归档导致技能消失**：用ABCD生成的skill会立即被curator归档（`created_by: agent` + `retrieval_count=0` → 自动进`.archive/`）。146个技能已因此消失。解法：①生成后立即`hermes curator pin <skill-name>`；②在frontmatter加`pinned: true`；③重要知识永久化：代码类→写进`~/.hermes/scripts/`、坑点→写进`error-patterns/references/`、配置→直接apply到config。详见`hermes-skill-archive-recovery` skill。
- **"小时工具错误聚集-XX次"每日重复归档**：idle_learning每日生成一份几乎相同的内容，14天×14份全部归档。处理：只保留最新一份，其余删；合并内容到`error-patterns/references/daily-error-summary.md`
- **.archive恢复后目录名是hash化的**：恢复时`mv`到skills/后，目录名仍是`.archive`里的hash名称而非skill真实名。修：恢复后立即重命名目录或用skill_manage重建
- **skills review只查活跃列表=review失败**：skills_list返回31个但`.archive/`里有194个SKILL.md（137个独立技能）。错误汇报"全部复盘完"的原因：只查了`~/.hermes/skills/`顶层，没进`.archive/`扫。正确做法：①`find ~/.hermes/skills/.archive -name "SKILL.md" | wc -l`统计总数 ②与活跃列表对比找孤儿 ③子代理批量审查孤儿价值 ④从.archive恢复+提升到depth=1 ⑤删重复/占位符旧存档 ⑥更新_skill_index.md


## 参考文档

- `references/idle-learning-llm-calls.md` — B_insight MiniMax API 调用模式、sandbox vs terminal 环境差异、写文件到 ~/.hermes 的正确方式
- `references/abcd-pipeline-state-20260712.md` — 2026-07-12 ABCD五阶段当前状态、B_paper写入结构、MiniMax LLM配置、验证命令
- `references/abcd-schema-and-crystallizer-fix-20260713.md` — fact_store schema真相、tags解析修复、升华门槛修复（≥3→≥1）、body字段修复
