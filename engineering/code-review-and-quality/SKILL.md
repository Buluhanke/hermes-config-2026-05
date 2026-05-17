---
name: code-review-and-quality
description: 代码评审规范化 — 有结构、有标准、有反馈的评审流程。不是走过场，是质量门禁。
triggers:
  - "代码合并前必须评审"
  - "发现潜在bug或安全问题"
  - "代码风格/可读性有问题"
  - "需要理解陌生代码"
  - "发现重复代码或技术债"
---

# Code Review and Quality

## Overview

代码评审是质量门禁，不是社交礼仪。评审者和作者都有责任确保评审产生实质价值。好的评审在10-30分钟内产生明确的质量提升，差的评审只是增加开发时间和挫败感。

## When to Use

- 任何代码合并到主分支之前
- 发现潜在bug、安全问题、性能问题
- 代码可读性差，难以维护
- 需要理解不熟悉的代码
- 重构前后对比评审

## Process

### Phase 1: 作者准备评审

#### 1.1 自审先行
- 变更前先完整阅读自己的代码
- 检查：变量命名、注释、函数长度
- 运行所有测试，包括新增的测试
- 确认diff大小合理（建议<400行）

#### 1.2 编写评审描述
- 这次变更做什么？
- 为什么需要这个变更？
- 怎么验证这个变更？（测试方式）
- 有什么特别需要评审者注意的？

#### 1.3 准备上下文
- 提供相关的设计文档
- 标注可能的争议点
- 说明测试覆盖情况

### Phase 2: 评审者执行评审

#### 2.1 理解变更意图
- 先读评审描述，理解为什么
- 如果意图不清晰，要求作者解释
- 不要假设评审描述以外的需求

#### 2.2 分层评审
- **L1（必须）**：正确性、安全性
  - bug存在吗？
  - 边界条件处理了吗？
  - 有安全漏洞吗？
  - 会引入性能倒退吗？
- **L2（应该）**：可读性、可维护性
  - 命名清晰吗？
  - 函数长度合理吗？
  - 注释必要吗？
  - 重复代码？
- **L3（可以）**：优化空间
  - 有更简洁的实现？
  - 可以进一步抽象？

#### 2.3 区分问题级别
- **Blocker（必须修复）**：正确性问题、安全漏洞
- **Major（强烈建议）**：可读性问题、潜在bug
- **Minor（可选）**：风格偏好、优化建议
- **Nit（极微小）**：拼写、格式

#### 2.4 提供可操作的反馈
- 说明问题，不是只指出问题
- 给出修改建议，不只是批评
- 标注具体代码行，不只是说"这模块有问题"

### Phase 3: 作者响应反馈

#### 3.1 分类响应
- 接受修改：说明会修改
- 拒绝但解释：为什么这个不需要改
- 讨论：提出替代方案或进一步解释

#### 3.2 逐条处理
- 每个反馈都要有明确的"接受/拒绝/讨论"状态
- 避免一次性回复"好的我全部改了"而不标明改了哪些

#### 3.3 重新提交
- 修复合并后标注每个反馈的处理结果
- 需要重新评审的重大变更要明确说明

### Phase 4: 评审完成

#### 4.1 评审者确认
- 确认所有blocker已修复
- 确认所有major已处理（有记录）
- 给出最终Approval

#### 4.2 记录经验
- 记录这次评审中学到的东西
- 识别团队共同的代码质量问题
- 更新评审标准或规范

## Common Rationalizations

| 常见借口 | 真相 | 反制 |
|---------|------|------|
| "这只是小改动，不用评审了" | 小改动往往是bug高发区 | 小改动评审成本最低，更应该评审 |
| "代码能跑通测试就行了" | 测试不能覆盖正确性、可读性、安全性 | 评审是测试的补充，不是替代 |
| "评审浪费时间，我直接合并" | 评审发现的bug修复成本是开发时的10倍 | 记录评审发现的问题及其严重性 |
| "评审意见太多了，回复不过来" | 说明代码质量本身有问题 | 从源头提高代码质量，减少评审意见 |
| "我信任这个人的代码，不用看了" | 信任不能替代检查 | 至少做L1评审 |

## Red Flags

- 评审意见全是nitpick，没有实质问题
- 评审者只说"LGTM"没有具体内容
- 评审时间<5分钟（说明没仔细看）
- diff超过1000行没有分批评审
- 同一个问题被提出多次但没有修复
- 作者拒绝所有minor意见而不解释
- 评审后发现严重bug

## Verification

验证清单：

- [ ] 作者已完成自审
- [ ] 评审描述清晰说明了变更目的
- [ ] L1问题（正确性、安全性）已全部处理
- [ ] L2问题（可读性）已全部处理或有记录
- [ ] 所有反馈都有明确的"接受/拒绝/讨论"状态
- [ ] 测试覆盖率没有下降
- [ ] 没有引入新的警告
- [ ] 评审者给出了具体的评审内容，不是"LGTM"

---

## AI辅助Review工具

AI工具可以加速评审过程，但不能替代人工评审。AI擅长模式识别和约定检查，但缺乏业务上下文和架构理解。

### 工具对比

| 工具 | 定位 | 优点 | 局限 |
|------|------|------|------|
| **GitHub Copilot** | IDE内实时辅助 | 集成IDE，实时建议 | 仅局部代码，不看全局 |
| **CodeRabbit** | PR评审助手 | 自动总结变更，检测重复 | 上下文理解有限 |
| **Cody (Sourcegraph)** | 代码智能助手 | 跨仓库理解，上下文丰富 | 需要Sourcegraph部署 |
| **ChatGPT/Claude** | 通用LLM | 可提问，可解释复杂逻辑 | 需要明确prompt |
| **SonarQube** | 静态分析平台 | 规则全面，CI集成 | 需配置规则 |

### AI辅助评审流程

#### 1. Copilot in IDE（作者自查阶段）

```bash
# 启用 Copilot 进行实时审查
# 在IDE中开启 inline suggestions 和 whole-line completions
```

**作者自查prompt模板：**
```
请审查以下代码变更，重点关注：
1. 潜在的bug或边界条件遗漏
2. 安全漏洞（SQL注入、XSS、敏感信息泄露）
3. 性能问题（N+1查询、大循环、低效算法）
4. 违反本项目代码规范的地方

代码：
[粘贴代码]
```

#### 2. CodeRabbit（PR自动评审）

```yaml
# .cody.yaml 配置示例
review:
  summary: true
  auto_title: true
  auto_description: true
  collapse_walkthrough: false
  sequence_diagrams: true
  high_level_summary: true
  poem: false
```

#### 3. Claude PR Review（深度分析）

```bash
# 使用 Claude CLI 进行PR评审
claude code review --diff-file changes.diff --context "业务背景：用户下单流程优化"
```

**深度评审prompt：**
```
你是一位资深代码评审专家。请分析以下PR：

## 变更内容
[粘贴diff]

## 业务上下文
[描述业务场景]

## 评审重点
1. 架构设计是否合理
2. 是否有更好的实现方式
3. 潜在的风险点
4. 测试覆盖是否充分

请用以下格式输出：
- **[Blocker]**: 必须修复的问题
- **[Major]**: 强烈建议修复
- **[Minor]**: 建议优化
- **[Question]**: 需要澄清的问题
- **[Suggestion]**: 改进建议
```

### AI使用原则

1. **AI是辅助，不是替代**：最终决策在人
2. **验证AI输出**：AI会犯错，特别是类型安全和空指针
3. **提供上下文**：给AI越多上下文，输出质量越高
4. **分阶段使用**：AI适合L1/L2检查，人工专注L3架构评审
5. **注意敏感信息**：不要把未发布代码发给外部AI服务

### 常见AI误判

| AI误判 | 实际情况 | 处理方式 |
|--------|----------|----------|
| "缺少空检查" | 框架已保证非空 | 添加注释说明调用契约 |
| "建议使用const" | 故意可变 | 保留并加注释解释 |
| "可以简化" | 简化后丢失业务语义 | 保留原实现并解释 |
| "有SQL注入风险" | 已使用参数化查询 | 添加安全注释说明 |

---

## 自动化CI集成

代码评审应与CI/CD流水线深度结合，实现自动化质量门禁。

### 典型CI流程

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Commit    │───▶│  Pre-PR    │───▶│    PR       │───▶│   Merge     │
│   Push      │    │   Check     │    │   Review    │    │   Gate      │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
      │                   │                 │                 │
      ▼                   ▼                 ▼                 ▼
  触发钩子           Lint/类型检查      AI评审+人工       最终检查
                   单元测试            分支保护          部署验证
```

### GitHub Actions 配置

#### 1. Pre-PR检查（提交前）

```yaml
# .github/workflows/pre-pr.yml
name: Pre-PR Checks

on:
  push:
    branches: [main, develop]
  pull_request:
    types: [opened, synchronize]

jobs:
  quality-gate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Run linters
        run: |
          npm run lint
          npm run type-check

      - name: Run unit tests
        run: npm run test:unit -- --coverage

      - name: Check code coverage
        run: |
          COVERAGE=$(cat coverage/coverage-summary.json | jq '.total.lines.pct')
          if (( $(echo "$COVERAGE < 80" | bc -l) )); then
            echo "Coverage $COVERAGE% is below 80%"
            exit 1
          fi

      - name: Detect secrets
        uses: trufflesecurity/trufflehog@main
        with:
          path: ./
          base_depth: 2
```

#### 2. PR评审辅助

```yaml
# .github/workflows/ai-review.yml
name: AI Code Review

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  ai-review:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout PR
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Run CodeRabbit
        uses: coderabbitai/ai-pr-reviewer@latest
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        with:
          review_simple_changes: false
          review_commented_files_only: true
          path_filters: |
            !**/*.test.ts
            !**/*.spec.ts
            !dist/**
            !node_modules/**

      - name: Update PR description
        if: always()
        run: |
          # 标记AI评审完成
          gh pr comment ${{ github.event.pull_request.number }} \
            --body "AI automated review completed. Please check the comments above."
```

#### 3. Merge Gate（合并门禁）

```yaml
# .github/workflows/merge-gate.yml
name: Merge Gate

on:
  pull_request:
    types: [labeled]

jobs:
  merge-requirements:
    runs-on: ubuntu-latest
    if: contains(github.event.pull_request.labels.*.name, 'ready-to-merge')
    steps:
      - name: Check approval status
        run: |
          APPROVALS=$(gh pr view ${{ github.event.pull_request.number }} --json reviews -q '.reviews | length')
          REQUIRED=2
          if [ "$APPROVALS" -lt "$REQUIRED" ]; then
            echo "Need at least $REQUIRED approvals, got $APPROVALS"
            exit 1
          fi

      - name: Check blocking reviews
        run: |
          BLOCKERS=$(gh pr view ${{ github.event.pull_request.number }} --json reviews -q \
            '.reviews[] | select(.state == "CHANGES_REQUESTED") | .author.login')
          if [ -n "$BLOCKERS" ]; then
            echo "Blocking reviews from: $BLOCKERS"
            exit 1
          fi

      - name: Verify CI passed
        run: |
          STATUS=$(gh pr view ${{ github.event.pull_request.number }} --json statusCheckRollup -q '.statusCheckRollup | length')
          if [ "$STATUS" -eq 0 ]; then
            echo "No CI checks completed"
            exit 1
          fi

      - name: Check merge conflict
        run: |
          if gh pr view ${{ github.event.pull_request.number }} --json mergeable -q '.mergeable' != "true"; then
            echo "PR has merge conflicts"
            exit 1
          fi
```

### 分支保护规则

| 规则 | 配置 |
|------|------|
| 最少评审人数 | 2人（1人可针对hotfix） |
| 必须通过检查 | CI全部通过 |
| 禁止强制推送 | main分支禁止force-push |
| 线性历史 | 启用rebase only |
| 状态检查 | 包含 coverage gate |

### GitLab CI 示例

```yaml
# .gitlab-ci.yml
code-review:
  stage: test
  image: node:20
  script:
    - npm ci
    - npm run lint
    - npm run test:unit -- --coverage
    - npm run security-scan
  coverage: '/Lines\s*:\s*(\d+\.\d+)%/'
  rules:
    - if: '$CI_PIPELINE_SOURCE == "merge_request_event"'

merge-check:
  stage: verify
  script:
    - echo "Checking merge eligibility..."
    - mr_status=$(curl --silent "$CI_API_V4_URL/projects/$CI_PROJECT_ID/merge_requests/$CI_MERGE_REQUEST_IID" | jq -r '.detailed_merge_status')
    - if [ "$mr_status" != "mergeable" ]; then exit 1; fi
  rules:
    - if: '$CI_PIPELINE_SOURCE == "merge_request_event"'
  when: manual
```

---

## Review指标体系

数据驱动的评审改进需要持续追踪关键指标。

### 核心指标

#### 1. 评审效率指标

| 指标 | 定义 | 目标 | 告警阈值 |
|------|------|------|----------|
| **MTTR** | Mean Time To Review（从PR创建到首次评审的时间） | < 4小时 | > 24小时 |
| **评审周期** | 从PR创建到合并的平均时间 | < 24小时 | > 72小时 |
| **评审时长** | 单次评审花费的时间 | 10-30分钟 | < 5分钟或 > 2小时 |
| **反馈响应时间** | 作者响应评审意见的平均时间 | < 4小时 | > 24小时 |

#### 2. 评审质量指标

| 指标 | 定义 | 目标 | 告警阈值 |
|------|------|------|----------|
| **Bug逃逸率** | 评审后线上发现的bug数 / 总bug数 | < 5% | > 15% |
| **Blocker发现率** | 评审发现的blocker数 / 总评审数 | > 0.3 | = 0（说明评审不深入） |
| **评审意见采纳率** | 被接受的评审意见 / 总评审意见 | > 80% | < 60% |
| **Reopen率** | 因质量问题重新打开的PR比例 | < 5% | > 10% |

#### 3. 代码质量指标

| 指标 | 定义 | 目标 | 告警阈值 |
|------|------|------|----------|
| **测试覆盖率** | 新代码的测试覆盖比例 | > 80% | < 70% |
| **重复率** | 代码重复比例 | < 3% | > 5% |
| **圈复杂度** | 新增代码的平均圈复杂度 | < 10 | > 15 |
| **公告警告数** | 新引入的lint/sonarqube警告 | 0 | > 0 |

### 指标收集脚本

```bash
#!/bin/bash
# scripts/review-metrics.sh

# 收集评审指标
collect_metrics() {
  local repo=$1
  local start_date=$2
  
  echo "=== Review Metrics ==="
  
  # PR数量
  echo "Total PRs: $(gh pr list --state merged --since $start_date --repo $repo --json number | jq 'length')"
  
  # 平均评审时间
  echo "Avg Review Time: $(gh pr list --state merged --since $start_date --repo $repo --json createdAt,mergedAt | \
    jq -r '.[] | .mergedAt + " " + .createdAt' | \
    awk '{split($1,a,":"); split($2,b,":"); print (mktime(a[1])-mktime(b[1]))/3600}' | \
    awk '{sum+=$1; count++} END {print sum/count " hours"}')"
  
  # Blockers found
  echo "Blockers Found: $(gh pr list --state merged --since $start_date --repo $repo | \
    grep -c '\[Blocker\]')"
}

# 生成报告
generate_report() {
  cat <<EOF > metrics-report.md
# Code Review Metrics Report
Generated: $(date)

## Summary
$(collect_metrics "$1" "$2")

## Trends
- PR Volume: TBD
- MTTR Trend: TBD
- Bug Escape Rate: TBD

## Action Items
- TBD
EOF
}
```

### 指标仪表盘配置

```yaml
# grafana/dashboards/code-review.json
{
  "dashboard": {
    "title": "Code Review Metrics",
    "panels": [
      {
        "title": "MTTR (Hours)",
        "type": "stat",
        "targets": [
          {
            "expr": "avg(github_pr_time_to_first_review_hours)",
            "legendFormat": "MTTR"
          }
        ],
        "fieldConfig": {
          "thresholds": {
            "steps": [
              {"value": 0, "color": "green"},
              {"value": 4, "color": "yellow"},
              {"value": 24, "color": "red"}
            ]
          }
        }
      },
      {
        "title": "PR Merge Cycle Time",
        "type": "timeseries",
        "targets": [
          {
            "expr": "histogram_quantile(0.5, github_pr_cycle_time_seconds)",
            "legendFormat": "p50"
          },
          {
            "expr": "histogram_quantile(0.95, github_pr_cycle_time_seconds)",
            "legendFormat": "p95"
          }
        ]
      },
      {
        "title": "Bug Escape Rate",
        "type": "gauge",
        "targets": [
          {
            "expr": "bugs_escaped_to_production / total_bugs * 100",
            "legendFormat": "Escape Rate %"
          }
        ],
        "fieldConfig": {
          "min": 0,
          "max": 100,
          "thresholds": {
            "steps": [
              {"value": 0, "color": "green"},
              {"value": 5, "color": "yellow"},
              {"value": 15, "color": "red"}
            ]
          }
        }
      }
    ]
  }
}
```

### 指标驱动的改进

| 指标告警 | 根因分析 | 改进措施 |
|----------|----------|----------|
| MTTR > 24h | 评审者忙碌或PR描述不清晰 | 明确on-call评审者，提供PR模板 |
| Bug逃逸率 > 15% | 评审质量不足 | 增加评审培训，强化L1检查 |
| 采纳率 < 60% | 评审意见质量低/不合理 | 评审者培训，强调可操作反馈 |
| Reopen率 > 10% | 修复不充分或评审不彻底 | 要求regression测试，评审后检查 |

---

## 常见问题模式库

将常见评审问题归类，便于快速识别和标准化反馈。

### 代码正确性问题模式

#### P1: 空指针/类型安全

**模式识别：**
```java
// ❌ 典型问题
user.getProfile().getAddress().getCity();  // 每层都可能NPE

// ✅ 修复方式
Optional.ofNullable(user)
    .map(User::getProfile)
    .map(Profile::getAddress)
    .map(Address::getCity)
    .orElse("Unknown");
```

**标准反馈模板：**
> [Blocker] 这里存在空指针风险。`user.getProfile()` 可能返回 null，后续链式调用会抛 NPE。
> 
> 建议：使用 Optional 处理，或添加非空断言并说明调用契约。

---

#### P2: 边界条件遗漏

**模式识别：**
```python
# ❌ 典型问题
def get_user_age(users, index):
    return users[index]['age']  # 未检查 index 范围

# ✅ 修复方式
def get_user_age(users, index):
    if index < 0 or index >= len(users):
        raise IndexError(f"Index {index} out of range")
    return users[index]['age']
```

**标准反馈模板：**
> [Blocker] 边界条件未处理。当 `index` 超出数组范围时会抛出未捕获的异常。
> 
> 建议：添加范围检查，或使用 `list.get(index, default)` 模式。

---

#### P3: 并发问题

**模式识别：**
```java
// ❌ 典型问题
private int counter = 0;
public void increment() {
    counter++;  // 非原子操作，多线程不安全
}

// ✅ 修复方式
private AtomicInteger counter = new AtomicInteger(0);
public void increment() {
    counter.incrementAndGet();
}
```

**标准反馈模板：**
> [Blocker] `counter++` 在多线程环境下不是原子操作，存在竞态条件。
> 
> 建议：使用 `AtomicInteger` 或 `synchronized` 保护临界区。

---

### 安全问题模式

#### S1: 注入漏洞

**模式识别：**
```sql
-- ❌ 典型问题（SQL注入）
"SELECT * FROM users WHERE name = '" + username + "'"

-- ✅ 修复方式（参数化查询）
"SELECT * FROM users WHERE name = ?"
pstmt.setString(1, username);
```

**标准反馈模板：**
> [Blocker-Security] 存在 SQL 注入风险。用户输入直接拼接到 SQL 语句中，攻击者可通过 `' OR '1'='1` 绕过认证。
> 
> 建议：使用参数化查询（PreparedStatement）。

---

#### S2: 敏感信息泄露

**模式识别：**
```javascript
// ❌ 典型问题
console.log("Password reset token:", token);
logger.info("User password:", user.password);

// ✅ 修复方式
logger.info("Password reset initiated for user:", userId);
```

**标准反馈模板：**
> [Blocker-Security] 敏感信息（password/token）被记录到日志或控制台。
> 
> 建议：移除或打码敏感字段，使用 `logger.info("event", {userId})` 而非记录完整对象。

---

#### S3: 权限检查缺失

**模式识别：**
```python
# ❌ 典型问题
def delete_user(user_id):
    db.delete_user(user_id)  # 没有检查当前用户权限

# ✅ 修复方式
def delete_user(user_id, current_user):
    if not current_user.is_admin:
        raise PermissionError("Admin required")
    db.delete_user(user_id)
```

**标准反馈模板：**
> [Blocker-Security] 关键操作缺少权限检查。任何认证用户都可以删除任意用户。
> 
> 建议：在执行前验证当前用户权限。

---

### 可读性问题模式

#### R1: 过长函数

**模式识别：**
```
函数超过50行，没有单一职责，多个抽象层级混合
```

**标准反馈模板：**
> [Major] 函数 `processOrder` 超过50行，混合了数据验证、业务逻辑、数据库操作、响应格式化多个职责。
> 
> 建议：拆分为 `validateOrder`, `executeOrder`, `formatResponse` 三个函数，每个不超过30行。

---

#### R2: 魔法数字

**模式识别：**
```python
# ❌ 典型问题
if user.age > 18 and user.score > 75:
    approve(user)

# ✅ 修复方式
ADULT_AGE = 18
MIN_APPROVAL_SCORE = 75

if user.age > ADULT_AGE and user.score > MIN_APPROVAL_SCORE:
    approve(user)
```

**标准反馈模板：**
> [Minor] 魔法数字降低了代码可读性，后续维护者无法理解数字含义。
> 
> 建议：提取为命名常量 `MAX_RETRY_COUNT`, `DEFAULT_PAGE_SIZE` 等。

---

#### R3: 误导性命名

**模式识别：**
```python
# ❌ 典型问题
def get_data():  # get还是create？返回什么？
    return db.query("SELECT ...")

# ✅ 修复方式
def fetch_user_by_id(user_id):  # 清晰表达意图
    return db.query("SELECT * FROM users WHERE id = ?", user_id)
```

**标准反馈模板：**
> [Major] 函数 `get_data` 命名模糊，无法从名称推断其行为和返回值。
> 
> 建议：重命名为 `fetch_active_users` 或 `load_user_config`，具体取决于实际行为。

---

### 性能问题模式

#### T1: N+1查询

**模式识别：**
```python
# ❌ 典型问题
users = db.query("SELECT * FROM users")
for user in users:
    user.orders = db.query(f"SELECT * FROM orders WHERE user_id = {user.id}")

# ✅ 修复方式
users = db.query("""
    SELECT u.*, o.* FROM users u
    LEFT JOIN orders o ON u.id = o.user_id
""")
```

**标准反馈模板：**
> [Major-Performance] 存在 N+1 查询问题。对 N 个用户执行了 1+N 次数据库查询。
> 
> 建议：使用 JOIN 或 `SELECT ... WHERE user_id IN (...)` 一次查询获取所有数据。

---

#### T2: 重复计算

**模式识别：**
```python
# ❌ 典型问题
def calculate_metrics(data):
    total = sum(item['value'] for item in data)  # 第一次遍历
    avg = total / len(data)
    max_val = max(item['value'] for item in data)  # 第二次遍历
    min_val = min(item['value'] for item in data)  # 第三次遍历

# ✅ 修复方式
def calculate_metrics(data):
    values = [item['value'] for item in data]
    total, max_val, min_val = sum(values), max(values), min(values)
    avg = total / len(values)
    return {'total': total, 'avg': avg, 'max': max_val, 'min': min_val}
```

**标准反馈模板：**
> [Minor-Performance] 同一数据集遍历三次，效率低下。
> 
> 建议：一次遍历计算所有指标，或使用 `statistics` 模块的 `mean()`, `max()`, `min()`。

---

### 架构问题模式

#### A1: 循环依赖

**模式识别：**
```
module_a → module_b → module_c → module_a
```

**标准反馈模板：**
> [Blocker-Architecture] 检测到循环依赖：`auth` → `user` → `billing` → `auth`。
> 
> 建议：提取公共接口到 `auth-types` 模块，打破循环。

---

#### A2: 违反单一职责

**模式识别：**
```python
# ❌ 典型问题
class UserManager:
    def create_user(self): ...
    def send_welcome_email(self): ...  # 邮件逻辑
    def log_activity(self): ...  # 日志逻辑
    def generate_report(self): ...  # 报表逻辑

# ✅ 修复方式
class UserManager: ...
class EmailService: ...
class ActivityLogger: ...
class ReportingService: ...
```

**标准反馈模板：**
> [Major] `UserManager` 承担了创建用户、发送邮件、记录日志、生成报表多个职责。
> 
> 建议：拆分为 `UserService`, `EmailService`, `ActivityLogger`, `ReportGenerator` 四个类。

---

### 问题模式库维护

建立团队专属问题模式库，持续迭代：

```markdown
# 团队代码评审模式库

## 新增模式贡献指南

1. 遇到有价值的问题模式时，记录到本库
2. 使用统一模板：
   - 模式名称
   - 典型代码（❌ 和 ✅ 对比）
   - 判定规则
   - 标准反馈模板
3. 定期（每月）回顾和优化模式库
4. 评审前快速查阅本库，提高反馈一致性

## 模式库索引

| 类别 | 模式数 | 最近更新 |
|------|--------|----------|
| 正确性 | 12 | 2026-01 |
| 安全性 | 8 | 2026-01 |
| 可读性 | 15 | 2026-02 |
| 性能 | 6 | 2026-01 |
| 架构 | 4 | 2026-01 |
```

---

## 附录：快速参考卡

### 评审检查清单（10分钟版本）

```
□ 代码逻辑是否正确？
□ 边界条件是否处理？
□ 有安全漏洞吗？（注入、权限、敏感信息）
□ 命名清晰吗？
□ 函数长度合理（<50行）？
□ 有必要的注释吗？
□ 测试覆盖充分吗？
□ 没有重复代码？
□ 性能可接受吗？
□ 符合团队代码规范？
```

### 反馈语气指南

| 情况 | 推荐语气 | 示例 |
|------|----------|------|
| Blocker问题 | 直接、严肃 | `[Blocker] 这会导致用户数据泄露，必须修复` |
| Major问题 | 明确但建设性 | `[Major] 建议使用参数化查询防止注入` |
| Minor问题 | 轻描淡写 | `[Minor] 可以考虑提取魔法数字` |
| 优化建议 | 开放性 | `[Suggestion] 如果使用缓存，QPS可提升10x` |
| 提问 | 好奇性 | `[Question] 这里的异常处理逻辑是故意的吗？` |

### 评审时长指南

| PR规模 | 建议时长 | 说明 |
|--------|----------|------|
| < 100行 | 5-10分钟 | 快速浏览，重点检查逻辑 |
| 100-400行 | 15-30分钟 | 完整评审，按L1/L2/L3分层 |
| > 400行 | 分批评审 | 建议拆分为多个PR |
