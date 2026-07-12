# Hermes Skills 快速索引（2026-07-13）

## 一、核心工作流（真实可执行，有操作步骤）

| Skill | 触发词 | 功能 |
|--------|--------|------|
| `abcd-learner` | 知识落地/升华/idle-learning E阶段 | fact→skill升华，fact_id列名，body=content |
| `anysearch` | 垂直搜索/金融数据/学术/安全情报/批量并行 | 23个垂直领域+通用+URL提取，免费20QPS |
| `avoid-ai-writing` | 去AI味/去除AI写作痕迹/AI-isms | 49模式检测+重写，detect/edit/iterate三种模式 |
| `deep-research` | 深度调研/多源研究/战略研究 | 9阶段深度调研，≥3独立源三角验证 |
| `dossier` | 尽职调查/实体研究/背景调查/人/公司 | 决策级实体研究报告，12个月活动时间线 |
| `pulse` | 脉搏/近期趋势/社区讨论/Reddit/HN | 多源近期情报，30天窗口+跨平台模式分析 |
| `officecli` | Word/Excel/PPT编辑/转换格式 | Office文档CLI读写，支持.docx/.xlsx/.pptx |
| `minimax-pdf` | 生成PDF/专业排版 | 视觉质量+品牌Identity |
| `minimax-docx` | 生成Word/专业文档 | 专业DOCX创建编辑 |
| `minimax-xlsx` | 生成Excel/数据分析 | Excel读写分析 |
| `ppt-generation` | 生成PPT/演示文稿 | 专业PPT生成 |
| `write-product-spec` | 写产品规格/PRD/产品文档 | PRODUCT.md规范 |
| `hermes-observability` | LLM可观测性/token消耗/延迟/错误率 | SQLite traces追踪 |
| `hermes-skills-management` | 安装skill/技能管理/诊断 | Hermes Hub十大类技能 |
| `litreview` | 文献综述/学术搜索 | PubMed/arXiv多源学术调研 |
| `grants` | NIH grant/科研经费申请 | 临床研究grant分析 |
| `self-improving-agent` | 自我改进/记忆优化/CLAUDE.md | MEMORY.md→CLAUDE.md升级 |

## 二、行为准则框架（触发后加载为决策参考）

| Skill | 触发场景 |
|--------|------|
| `star-4d-学习循环` | 遇到新问题/学习新知/失败复盘 → Search→Try→Adjust→Record |
| `反思式增量prompt进化` | SOUL.md/AGENTS.md修改 → 单次≤1500token，内存<300MB |
| `代码化-规则化` | 同一操作出现3次 → 硬编码函数，不走LLM推理 |
| `坑点检索飞轮` | 修复前查~/.hermes/.pitfalls_checklist.txt，修复后写入 |
| `失败驱动记忆进化` | 失败时 → 存"已验证+有后果"的坑，绑定场景+触发条件 |
| `executive-mentor` | 战略决策/创始人困境/对抗性思维 |

## 三、领域知识（idle-learning自动生成，内容是知识陈述非操作步骤）

| Skill | 核心内容 |
|--------|------|
| `ai代理-工作流知识化` | 工作流知识化=LLM自动化落地关键路径 |
| `多模态推理-vlm垂直深化` | VLM→自动驾驶事故评测新热点 |
| `模型优化-量化非等价` | LLM量化需统计表征，精度损失系统性偏差 |
| `知识架构-工作流语义持久性` | 知识表示从检索→可执行流程 |
| `评测垂直化-车载vlm` | 垂直领域基准=核心竞争力 |
| `失败驱动记忆进化` | 只存已验证有后果的坑，绑定场景+触发条件 |

## 四、错误模式（auto_skill_from_failure自动生成，触发即查）

- `error-patterns-最新日期.md` — TimeoutError/ConnectionError/Import error/JSON parse/Permission denied/CDP attach failed
- 触发词：任意报错名称

## 五、触发检索优先级

遇到任务时，先匹配本索引的**触发词**栏，直接 `skill_view(name)` 加载完整内容。

```
优先级顺序：
1. 报错？ → error-patterns（报错关键词）
2. 调研/研究？ → deep-research / dossier / pulse / anysearch
3. 文档生成？ → officecli / minimax-docx / ppt-generation
4. Hermes自身？ → hermes-skills / hermes-observability / abcd-learner
5. 学习框架？ → star-4d / 反思式增量 / 代码化
6. 写作去AI味？ → avoid-ai-writing
```

## 六、已知内容空洞的skill（需补充步骤）

以下skill只有标题+一句话描述，触发时需要用LLM展开：
- `ai代理-工作流知识化` → 展开：工作流应持久化存储为.md/.yaml，LLM按步骤执行
- `多模态推理-vlm垂直深化` → 展开：VLM评测用垂直基准（事故场景VQA），不用通用MMMU
- `模型优化-量化非等价` → 展开：量化后需做统计偏差回归，不做等价假设
- `知识架构-工作流语义持久性` → 展开：RAG→可执行工作流，知识用流程图表示
- `评测垂直化-车载vlm` → 展开：建立事故场景评测集，数据来自真实事故报告

## 七、crontab 1-7点自学任务（全部可手动触发）

```bash
# 1点
bash ~/.hermes/scripts/daily_patrol.sh
# 2点
bash ~/.hermes/scripts/deep_research.sh 'AI 搜索最新进展 2026'
# 3点
bash ~/.hermes/scripts/self_evolution_daily_learn.sh
# 4点
/usr/bin/python3 ~/.hermes/scripts/idle_learning_orchestrator.py
# 5点
/usr/bin/python3 ~/.hermes/scripts/active_learner.py
# 6点
bash ~/.hermes/scripts/daily_evening_summary.sh
# 01:00（Hermes cron）
bash ~/.hermes/scripts/idle_learning_wrapper.sh
```
