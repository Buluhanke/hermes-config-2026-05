---
name: writing-plans
description: "Write implementation plans: bite-sized tasks, paths, code."
version: 1.1.0
author: Hermes Agent (adapted from obra/superpowers)
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [planning, design, implementation, workflow, documentation]
    related_skills: [subagent-driven-development, test-driven-development, requesting-code-review]
---

# Writing Implementation Plans

## Overview

Write comprehensive implementation plans assuming the implementer has zero context for the codebase and questionable taste. Document everything they need: which files to touch, complete code, testing commands, docs to check, how to verify. Give them bite-sized tasks. DRY. YAGNI. TDD. Frequent commits.

Assume the implementer is a skilled developer but knows almost nothing about the toolset or problem domain. Assume they don't know good test design very well.

**Core principle:** A good plan makes implementation obvious. If someone has to guess, the plan is incomplete.

## When to Use

**Always use before:**
- Implementing multi-step features
- Breaking down complex requirements
- Delegating to subagents via subagent-driven-development

**Don't skip when:**
- Feature seems simple (assumptions cause bugs)
- You plan to implement it yourself (future you needs guidance)
- Working alone (documentation matters)

## Bite-Sized Task Granularity

**Each task = 2-5 minutes of focused work.**

Every step is one action:
- "Write the failing test" — step
- "Run it to make sure it fails" — step
- "Implement the minimal code to make the test pass" — step
- "Run the tests and make sure they pass" — step
- "Commit" — step

**Too big:**
```markdown
### Task 1: Build authentication system
[50 lines of code across 5 files]
```

**Right size:**
```markdown
### Task 1: Create User model with email field
[10 lines, 1 file]

### Task 2: Add password hash field to User
[8 lines, 1 file]

### Task 3: Create password hashing utility
[15 lines, 1 file]
```

## Plan Document Structure

### Header (Required)

Every plan MUST start with:

```markdown
# [Feature Name] Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan taYOUR_API_KEY-task.

**Goal:** [One sentence describing what this builds]

**Architecture:** [2-3 sentences about approach]

**Tech Stack:** [Key technologies/libraries]

---
```

### Task Structure

Each task follows this format:

````markdown
### Task N: [Descriptive Name]

**Objective:** What this task accomplishes (one sentence)

**Files:**
- Create: `exact/path/to/new_file.py`
- Modify: `exact/path/to/existing.py:45-67` (line numbers if known)
- Test: `tests/path/to/test_file.py`

**Step 1: Write failing test**

```python
def test_specific_behavior():
    result = function(input)
    assert result == expected
```

**Step 2: Run test to verify failure**

Run: `pytest tests/path/test.py::test_specific_behavior -v`
Expected: FAIL — "function not defined"

**Step 3: Write minimal implementation**

```python
def function(input):
    return expected
```

**Step 4: Run test to verify pass**

Run: `pytest tests/path/test.py::test_specific_behavior -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/path/test.py src/path/file.py
git commit -m "feat: add specific feature"
```
````

## Writing Process

### Step 1: Understand Requirements

Read and understand:
- Feature requirements
- Design documents or user description
- Acceptance criteria
- Constraints

### Step 2: Explore the Codebase

Use Hermes tools to understand the project:

```python
# Understand project structure
search_files("*.py", target="files", path="src/")

# Look at similar features
search_files("similar_pattern", path="src/", file_glob="*.py")

# Check existing tests
search_files("*.py", target="files", path="tests/")

# Read key files
read_file("src/app.py")
```

### Step 3: Design Approach

Decide:
- Architecture pattern
- File organization
- Dependencies needed
- Testing strategy

### Step 4: Write Tasks

Create tasks in order:
1. Setup/infrastructure
2. Core functionality (TDD for each)
3. Edge cases
4. Integration
5. Cleanup/documentation

### Step 5: Add Complete Details

For each task, include:
- **Exact file paths** (not "the config file" but `src/config/settings.py`)
- **Complete code examples** (not "add validation" but the actual code)
- **Exact commands** with expected output
- **Verification steps** that prove the task works

### Step 6: Review the Plan

Check:
- [ ] Tasks are sequential and logical
- [ ] Each task is bite-sized (2-5 min)
- [ ] File paths are exact
- [ ] Code examples are complete (copy-pasteable)
- [ ] Commands are exact with expected output
- [ ] No missing context
- [ ] DRY, YAGNI, TDD principles applied

### Step 7: Save the Plan

```bash
mkdir -p docs/plans
# Save plan to docs/plans/YYYY-MM-DD-feature-name.md
git add docs/plans/
git commit -m "docs: add implementation plan for [feature]"
```

## Principles

### DRY (Don't Repeat Yourself)

**Bad:** Copy-paste validation in 3 places
**Good:** Extract validation function, use everywhere

### YAGNI (You Aren't Gonna Need It)

**Bad:** Add "flexibility" for future requirements
**Good:** Implement only what's needed now

```python
# Bad — YAGNI violation
class User:
    def __init__(self, name, email):
        self.name = name
        self.email = email
        self.preferences = {}  # Not needed yet!
        self.metadata = {}     # Not needed yet!

# Good — YAGNI
class User:
    def __init__(self, name, email):
        self.name = name
        self.email = email
```

### TDD (Test-Driven Development)

Every task that produces code should include the full TDD cycle:
1. Write failing test
2. Run to verify failure
3. Write minimal code
4. Run to verify pass

See `test-driven-development` skill for details.

### Frequent Commits

Commit after every task:
```bash
git add [files]
git commit -m "type: description"
```

## Common Mistakes

### Vague Tasks

**Bad:** "Add authentication"
**Good:** "Create User model with email and password_hash fields"

### Incomplete Code

**Bad:** "Step 1: Add validation function"
**Good:** "Step 1: Add validation function" followed by the complete function code

### Missing Verification

**Bad:** "Step 3: Test it works"
**Good:** "Step 3: Run `pytest tests/test_auth.py -v`, expected: 3 passed"

### Missing File Paths

**Bad:** "Create the model file"
**Good:** "Create: `src/models/user.py`"

## Procurement Task Plan Template

适用于采购任务的分解与执行，如询价、采购订单跟进、交付验收等。

### Header

```markdown
# [采购任务名称] 采购计划

> **For Hermes:** Use subagent-driven-development skill to execute this plan taYOUR_API_KEY-task.

**采购目标：** [一句话描述采购什么、为什么]

**采购类型：** [原材料 / 设备 / 服务 / 外包]

**预算范围：** [RMB X ~ Y]

**关键时间节点：**
- 询价截止：YYYY-MM-DD
- 供应商确认：YYYY-MM-DD
- 交付验收：YYYY-MM-DD

---
```

### Task Structure

```markdown
### Task N: [采购步骤名称]

**目标：** 完成[具体采购动作]

**涉及供应商：** [供应商名称列表]

**Step 1: 询价准备**
- 整理采购规格：`data/采购规格_YYYYMMDD.md`
- 确认技术要求、数量、交期
- 确定询价供应商名单（≥3家）

**Step 2: 发送询价**
- 通过邮件/系统发送询价单
- 记录发送时间：`logs/rfq_YYYYMMDD.md`

**Step 3: 收集报价**
- 跟进未回复供应商
- 汇总报价对比表：`data/quote_comparison_YYYYMMDD.xlsx`

**Step 4: 供应商评估**
- 价格维度（X%权重）
- 质量维度（Y%权重）
- 交期维度（Z%权重）
- 综合评分表：`data/supplier_score_YYYYMMDD.md`

**Step 5: 发出采购订单**
- 生成PO编号：PO-YYYY-NNNN
- 发送供应商确认
- 归档合同：`contracts/PO-YYYY-NNNN.pdf`

**Step 6: 跟进交付**
- 关键节点检查（Day 3/7/14）
- 记录异常：`logs/delivery_issues.md`

**Step 7: 验收入库**
- 核对规格数量
- 质量抽检
- 更新库存台账：`data/inventory.csv`
```

---

## Supplier Development Plan Template

适用于供应商开发、评估、准入、绩效管理全流程。

### Header

```markdown
# [供应商名称] 开发计划

> **For Hermes:** Use subagent-driven-development skill to execute this plan step-by-step.

**供应商信息：**
- 名称：[供应商全称]
- 类型：[制造商 / 贸易商 / 服务商]
- 主营：[核心产品/服务]
- 规模：[大型 / 中型 / 小型]

**开发目标：**
- 短期：[X个月内完成准入]
- 长期：[建立战略合作关系]

**当前阶段：** [潜在供应商 / 评估中 / 已准入 / 战略合作]

---
```

### Task Structure

```markdown
### Phase 1: 供应商初筛

**目标：** 筛选出符合基本要求的候选供应商

**Task 1.1: 背景调查**
- 工商信息核验：天眼查/企查查
- 成立时间、注册资本、法人
- 经营异常记录

**Task 1.2: 资质审查**
- 营业执照、生产许可证、ISO认证
- 行业特定资质（如有）
- 财务报表摘要

**Task 1.3: 产能评估**
- 工厂规模、员工人数
- 设备清单
- 月产能上限

### Phase 2: 技术评估

**目标：** 验证供应商技术能力是否满足要求

**Task 2.1: 样品测试**
- 发技术规格书、图档
- 要求打样（1-3件）
- 样品评估报告：`reports/sample_eval_YYYYMMDD.md`

**Task 2.2: 工厂审计**
- 现场审核清单：`templates/audit_checklist.md`
- 质量管理体系评估
- 生产能力验证
- 审核报告：`reports/audit_YYYYMMDD.pdf`

### Phase 3: 商务准入

**目标：** 完成合同签订和系统录入

**Task 3.1: 价格谈判**
- 成本分析
- MOQ、付款条件、交货条款
- 框架协议草稿

**Task 3.2: 合同签订**
- 主合同/质量协议/保密协议
- 交付条款、验收标准
- 违约责任

**Task 3.3: 系统准入**
- 录入供应商管理系统
- 银行账户、税务信息
- 启用采购权限

### Phase 4: 绩效管理

**目标：** 持续监控和改进供应商表现

**Task 4.1: 月度绩效**
- 交期达成率
- 质量合格率
- 响应速度评分
- 绩效台账：`data/supplier_performance_YYYYQ1.csv`

**Task 4.2: 年度评审**
- 综合评级（A/B/C/D）
- 问题点整改跟踪
- 下一年度合作计划
```

---

## Automated Inspection Plan Template

适用于设备/系统自动化巡检任务的规划与执行，如IoT设备点检、生产线监控、安全巡检等。

### Header

```markdown
# [巡检系统/设备名称] 自动化巡检计划

> **For Hermes:** Use subagent-driven-development skill to implement this plan step-by-step.

**巡检目标：** [描述要巡检什么、达成什么效果]

**巡检对象：** [设备类型/编号、区域范围]

**自动化程度：** [全自动化 / 半自动化（人工确认）]

**巡检频率：** [实时 /  hourly / daily / weekly]

**关键阈值：**
- 温度 > X°C → 报警
- 振动 > Y mm/s → 预警
- 其他：[具体阈值]

---
```

### Task Structure

```markdown
### Phase 1: 巡检点定义

**目标：** 梳理所有需要巡检的点位和指标

**Task 1.1: 资产梳理**
- 设备清单：`data/assets_YYYYMMDD.csv`
- 关键设备标识（Tag编号）
- 安装位置坐标

**Task 1.2: 巡检指标定义**
- 传感器类型：[温度/湿度/振动/电流/其他]
- 采集频率
- 正常范围、预警阈值、告警阈值
- 指标定义表：`data/metrics_def.md`

**Task 1.3: 巡检路径规划**
- 巡检顺序优化
- 每个点位的检查动作
- 预期停留时间

### Phase 2: 自动化实现

**目标：** 实现数据采集和状态监控自动化

**Task 2.1: 传感器部署**
- 传感器选型
- 安装位置确认
- 接线/通信配置
- 测试点：`tests/sensor_deploy.md`

**Task 2.2: 数据采集**
- 采集程序开发：`src/collector/sensor_collector.py`
- 数据格式定义
- 异常数据过滤规则

**Task 2.3: 状态监控平台**
- 实时数据看板
- 历史数据趋势图
- 告警规则引擎：`src/rules/alarm_rules.py`

**Task 2.4: 告警通知**
- 告警分级（P1/P2/P3）
- 通知渠道：[邮件/短信/钉钉/微信]
- 通知模板：`templates/alarm_template.md`

### Phase 3: 巡检执行与优化

**目标：** 运行并持续优化巡检系统

**Task 3.1: 试运行**
- 并行人工巡检 vs 自动化对比
- 差异分析报告：`reports/pilot_comparison_YYYYMMDD.md`
- 阈值调优

**Task 3.2: 巡检报告**
- 自动生成日报/周报/月报
- 报告模板：`templates/inspection_report.md`
- 定时推送

**Task 3.3: 异常闭环**
- 告警触发 → 工单创建
- 维修处理 → 验证确认
- 闭环记录：`data/incident_log.csv`

**Task 3.4: 系统维护**
- 传感器校准计划
- 备份策略
- 巡检系统巡检（监控本身）
```

---

## Execution Handoff

After saving the plan, offer the execution approach:

**"Plan complete and saved. Ready to execute using subagent-driven-development — I'll dispatch a fresh subagent per task with two-stage review (spec compliance then code quality). Shall I proceed?"**

When executing, use the `subagent-driven-development` skill:
- Fresh `delegate_task` per task with full context
- Spec compliance review after each task
- Code quality review after spec passes
- Proceed only when both reviews approve

## Remember

```
Bite-sized tasks (2-5 min each)
Exact file paths
Complete code (copy-pasteable)
Exact commands with expected output
Verification steps
DRY, YAGNI, TDD
Frequent commits
```

**A good plan makes implementation obvious.**
```