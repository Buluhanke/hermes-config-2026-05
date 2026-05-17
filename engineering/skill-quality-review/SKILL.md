---
name: skill-quality-review
description: >-
  Skill质量评审与持续优化 — 评估、测试、迭代改进SKILL.md质量。使用8维度
  rubric评分（结构+效果），棘轮机制只保留提升。借鉴darwin-skill的自主优化循环。
triggers:
  - "用户说'优化skill'、'skill质量'、'帮我改改skill'"
  - "技能库规模增长后需要批量质检"
  - "某个skill表现不如预期"
  - "用户提到darwin-skill、达尔文、skill评分"
  - "需要给skill写测试用例"
cat
version: 1.0.0egory: engineering
---

# Skill Quality Review

## Overview

Skill 质量不只是格式规范。写得漂亮的 SKILL.md 跑出来效果可能很差。**Skill Quality Review** 提供一套可重复的质量评估和持续优化流程。

借鉴 [darwin-skill](https://github.com/alchaincyf/darwin-skill)（星2.4k，花叔作品）的设计——将 Karpathy autoresearch 的自主实验循环应用到 Skill 优化领域：**评估 → 改进 → 实测验证 → 保留或回滚**。

核心理念：
1. **单一可编辑资产** — 每次只改一个 SKILL.md
2. **双重评估** — 结构评分（静态分析）+ 效果验证（跑测试看输出）
3. **棘轮机制** — 只保留改进，自动回滚退步
4. **独立评分** — 评分用子 agent，避免"自己改自己评"的偏差
5. **人在回路** — 每个 skill 优化完后暂停，等用户确认

## When to Use

- 用户说"帮我看看这个skill质量怎么样"
- 用户说"优化所有skills"或"优化xxx这个skill"
- 技能库新增了一个 skill，需要基线评估
- 某个 skill 执行效果不稳定或用户反馈差
- 定期维护：每月或每季度批量质检

## Quality Rubric（8维度，总分100）

### 结构维度（60分）— 静态分析

| # | 维度 | 权重 | 评分标准 |
|---|------|------|---------|
| 1 | **Frontmatter质量** | 8 | name规范、description包含做什么+何时用+触发词、≤1024字符 |
| 2 | **工作流清晰度** | 15 | 步骤明确可执行、有序号、每步有明确输入/输出 |
| 3 | **边界条件覆盖** | 10 | 处理异常情况、有fallback路径、错误恢复 |
| 4 | **检查点设计** | 7 | 关键决策前有用户确认、防止自主失控 |
| 5 | **指令具体性** | 15 | 不模糊、有具体参数/格式/示例、可直接执行 |
| 6 | **资源整合度** | 5 | references/scripts/assets引用正确、路径可达 |

### 效果维度（40分）— 需要实测

| # | 维度 | 权重 | 评分标准 |
|---|------|------|---------|
| 7 | **整体架构** | 15 | 结构层次清晰、不冗余不遗漏、符合Hermes skill风格 |
| 8 | **实测表现** | 25 | 用测试prompt跑一遍，输出质量是否符合skill宣称的能力 |

### 评分规则
- 维度1-7：每个维度打 1-10 分，乘以权重得到该维度得分
- 维度8（实测表现）：跑2-3个测试prompt，按输出质量打1-10分
- **总分 = Σ(维度分 × 权重) / 10**，满分100
- 改进后总分必须**严格高于**改进前才保留

### 关于「实测表现」维度

这是与纯结构评分最大的区别。评分方式：

1. 为每个 skill 设计2-3个**典型用户 prompt**（不是边缘case，是最常见的使用场景）
2. 用子 agent 执行对比：一个带着该 SKILL.md 执行，一个不带（baseline）
3. 对比输出质量：
   - 输出是否完成了用户意图？
   - 相比不带 skill 的 baseline，质量提升明显吗？
   - 有没有 skill 引入的负面影响（过度冗余、跑偏、格式奇怪）？

如果子 agent 不可用，退化为「干跑验证」：读完 skill 后模拟执行思路，标注 `dry_run`。

## Process

### Phase 0: 初始化

1. 确认优化范围：全部 skills（扫描 `~/.hermes/skills/`）还是指定列表
2. 创建 git 分支：`optimize/YYYYMMDD-HHMM`
3. 初始化 results 日志（TSV格式）
4. 读取历史记录了解过往优化情况

### Phase 0.5: 测试Prompt设计

为每个 skill 设计测试 prompt：

```json
// ~/.hermes/skills/<skill>/test-prompts.json
[
  {"id": 1, "prompt": "典型用户输入", "expected": "期望输出的简短描述"},
  {"id": 2, "prompt": "复杂场景", "expected": "期望输出的简短描述"}
]
```

展示给用户确认后再进入评估。

### Phase 1: 基线评估

1. 结构评分（维度1-7）：读取 SKILL.md，按评分标准逐项打分
2. 效果评分（维度8）：用测试 prompt 执行，对比带/不带 skill 的输出
3. 汇总分数，记录到 results
4. 展示评分卡，等用户确认

### Phase 2: 优化循环

按基线分数从低到高排序，先优化最弱的：

```
for each skill:
  round = 0
  while round < MAX_ROUNDS（默认3）:
    # Step 1: 找出最低维度
    # Step 2: 生成1个具体改进方案
    # Step 3: 编辑 SKILL.md，git commit
    # Step 4: 重新评估（用独立子agent）
    # Step 5: 新分 > 旧分 → keep；否则 → git revert
    # 展示diff + 分数变化，等用户确认
```

### Phase 3: 汇总报告

展示：优化skill数、总实验次数、保留/回滚比例、平均分变化、主要改进点。

## 优化策略优先级

### P0: 效果问题（实测发现的）
- 测试输出偏离用户意图 → 检查是否有误导性指令
- 带skill比不带还差 → 可能过度约束，考虑精简
- 输出格式不符合预期 → 补充明确模板

### P1: 结构性问题
- Frontmatter缺少触发词 → 补充中英文触发词
- 缺少Phase/Step结构 → 重组为线性流程
- 缺少用户确认检查点 → 在关键决策处插入

### P2: 具体性问题
- 步骤模糊（"处理图片"）→ 改为具体操作和参数
- 缺少输入/输出规格 → 补充格式、路径、示例
- 缺少异常处理 → 补充"如果X失败，则Y"

### P3: 可读性问题
- 段落过长 → 拆分或用表格
- 重复描述 → 合并去重
- 缺少速查 → 添加TL;DR或决策树

## 外部工具参考

### darwin-skill（推荐）
- GitHub: `github.com/alchaincyf/darwin-skill`
- 安装：`npx skills add alchaincyf/darwin-skill`（需要GitHub连通性）
- 特点：8维度评分、自主优化循环、成果卡片生成
- 局限性：面向Claude Code/Cursor等Agent生态，Hermes需要适配路径
- 适配方式：调整skill路径从`~/.claude/skills/`到`~/.hermes/skills/`

### 安装检查

安装后验证：
- 检查 `~/.hermes/skills/skill-quality-review/` 目录结构
- 确认测试 prompt 文件存在
- 确认 results 日志目录可写

### 现场安装调试

```bash
# 如果 GitHub 连通性正常
npx skills add alchaincyf/darwin-skill
# 之后需要将生成的 SKILL.md 从 .claude/skills/ 复制到 .hermes/skills/
```

如果 GitHub 不可达，使用 darwin-skill 的设计思路手动执行质量评估流程，详见本文件的 Quality Rubric 和 Process 章节。

## Support Files Structure

```
skill-quality-review/
├── SKILL.md
└── references/
    └── darwin-skill-notes.md    # darwin-skill的详细设计笔记
```

## Common Pitfalls

1. **自己改自己评**：优化后不用独立 agent 评分，结果有偏见。必须用 delegate_task 或子 agent 独立评估。
2. **跳过测试prompt设计**：没有测试场景就评估效果维度，等于猜。再简单的 skill 也要至少1个测试 prompt。
3. **一次改太多**：同时改3个维度，无法归因是哪个改动带来的提升。每轮只改1个。
4. **忽视用户确认**：全自动优化可能改出用户不喜欢的风格。每个 skill 优化完必须展示 diff 等人确认。
5. **分数通胀**：多次跑分后 agent 可能"学会"高分格式。定期用全新子 agent 重新基线评估。
6. **对测试 prompt 过拟合**：优化时只针对测试 prompt 改进，忽略了通用性。测试 prompt 要覆盖 happy path + 边缘场景，并且定期轮换。

## Verification Checklist

- [ ] 评分标准明确，每项有具体打分依据
- [ ] 测试 prompt 覆盖典型场景
- [ ] 评估结果记录到 results.tsv
- [ ] 用户确认过测试 prompt 方案
- [ ] 每轮优化只改一个维度
- [ ] 独立 agent 评分（非自评）
- [ ] 只保留严格提升的改进
- [ ] 展示 diff 后等用户确认
