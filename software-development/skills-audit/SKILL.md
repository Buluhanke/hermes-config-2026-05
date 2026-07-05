---
name: skills-audit
description: Systematically audit a group of related skills against current industry benchmarks. Compare alternatives, identify maintenance gaps, score quality, and produce a prioritized improvement report. Use when asked to audit, review, compare, or evaluate one or more skills.
version: 1.0.0
created: 2026-07-05
category: software-development
type: capability
triggers:
  - "审计 skill"
  - "对比 skill"
  - "review skills"
  - "audit this skill"
  - "compare X skill with Y"
  - "skills report"
  - "skill quality review"
metadata:
  hermes:
    tags: [skills, auditing, quality, maintenance, review]
    related_skills: [ai-skill-discovery-research, skill-manage]
---

# Skills Audit — 系统化 Skill 审计方法论

## 何时使用

当用户要求对一组合意相关的skills进行审计、对比、评估时加载。
不适用于单个skill的快速patch（直接patch即可）。

## 审计维度

| 维度 | 评估内容 |
|------|---------|
| **维护状态** | 最后更新时间、GitHub提交记录、依赖库活跃度 |
| **功能完整性** | 覆盖场景是否全面，fallback是否合理 |
| **行业对比** | 同类工具最新状态（star数、替代品、维护频率） |
| **可执行性** | 命令是否有效，路径是否正确，依赖是否满足 |
| **独特价值** | 与其他skill是否重复，差异化是否清晰 |
| **用户体验** | 触发词是否准确，文档是否清晰易读 |

## 三阶段审计流程

### Phase 1: 信息收集

1. **读取所有目标skill内容**（`skill_view`）
2. **联网调研**：
   - 搜索每个skill底层工具的GitHub状态（stars、最后commit、maintainer活跃度）
   - 搜索同类工具2025-2026最新对比
   - 搜索工具的行业排名或benchmark
3. **建立对比矩阵**：工具名、功能、优劣势、维护状态

### Phase 2: 分析评估

对每个skill打分（1-5⭐）：
- ⭐ 差（功能缺失或维护停滞）
- ⭐⭐ 较差（有价值但需重大更新）
- ⭐⭐⭐ 一般（可用但有改进空间）
- ⭐⭐⭐⭐ 好（高质量，细节可优化）
- ⭐⭐⭐⭐⭐ 优秀（接近完美）

对每个skill输出：
- 核心优势
- 关键问题
- 与同类相比的独特价值
- 优化建议

### Phase 3: 报告输出

报告结构：
```
# [类别] Skills 审计报告

## 汇总评分表
| Skill | 评分 | 核心问题 |

## 分类详细分析
### [类别名]
#### Skill A ⭐⭐⭐（3/5）
现状评估 / 对比同类 / 可改进点 / 优化建议
...

## 优先级汇总
🔴 高优先级（立即处理）
🟡 中优先级（季度内）
🟢 低优先级（持续改进）

## 行业趋势（联网调研发现）
```

## 评分标准参考

### 5⭐ — 优秀
- 覆盖全面，文档详尽
- 维护活跃或维护模式标注清晰
- 与同类工具相比有明确差异化
- 无已知阻塞问题

### 4⭐ — 良好
- 整体高质量，细节可优化
- 缺少一个次要功能或一个细节可以改进
- 无维护停滞风险

### 3⭐ — 一般
- 功能可用但有明显改进空间
- 文档不完整或部分内容过时
- 与同类相比无显著优势

### 2⭐ — 较差
- 核心功能缺失或严重过时
- 底层依赖已弃用或停滞
- 需要较大工作量才能达到可用

### 1⭐ — 差
- 功能完全不可用
- 维护停滞且无替代说明
- 强烈建议弃用

## 维护状态判断标准

| 状态 | 判断依据 |
|------|---------|
| 🟢 活跃 | 6个月内有大版本更新，GitHub有活跃提交 |
| 🟡 一般 | 6-12个月无更新，但无明显停滞迹象 |
| 🔴 停滞 | 12个月以上无更新，最后commit显示maintainer不活跃 |
| ⚠️ 弃用 | 作者明确宣布停止维护，无人fork接棒 |

## 行业调研必查项

对于每个skill对应的底层工具，检查：
1. **GitHub stars** 和趋势（增长还是下降）
2. **最后commit日期** 和commit频率
3. **最新版本/发布日期**
4. **同类工具排名**（trending、benchmark）
5. **2025-2026新出现的替代品**

## 报告保存

审计完成后，将报告保存到用户可访问的位置：
```
/Users/aimac/hermes-skills-audit-[日期].md
```

## 输出后行动

审计报告完成后，**主动更新skills**：
1. 发现维护停滞的skill → 添加 maintenance_warning 到 metadata
2. 发现过时路径/命令 → patch skill对应段
3. 发现skill之间重叠 → 记录，由 curator 合并处理
4. 发现全新类别的最佳实践缺失 → 建议创建新skill
