---
name: git-workflow-and-versioning
description: Git工作流与版本管理 — 分支策略、提交规范、协作流程的完整规范。
triggers:
  - "需要开始一个新功能或修复"
  - "准备合并分支到主分支"
  - "提交信息不清晰或不规范"
  - "遇到merge冲突"
  - "需要回滚代码"
  - "发布新版本"
  - "创建PR或review PR"
  - "创建Issue或管理Issue"
  - "需要cherry-pick特定提交"
  - "需要用bisect定位问题提交"
  -
version: 1.0.0 "项目中包含git子模块"
---

# Git Workflow and Versioning

## Overview

Git是代码协作的基石。不规范的Git使用会导致：代码丢失、冲突难解、回滚困难、发布混乱。规范的Git工作流让协作流畅、可追溯、可回滚。

本技能涵盖：分支策略、提交规范、协作流程、版本发布、回滚、PR规范、Issue格式、Cherry-pick、Git Bisect、子模块管理。

## When to Use

- 开始任何新功能或修复任务
- 合并任何分支前
- 发布任何版本前
- 遇到merge冲突时
- 需要回滚代码时
- 代码审查完成后

## Process

### Phase 1: 分支管理

#### 1.1 分支命名规范
```
格式：<类型>/<ticket-id>-<简短描述>

类型：
- feature/     新功能
- fix/        错误修复
- hotfix/     紧急修复
- refactor/   重构
- docs/       文档更新
- test/       测试相关
- chore/      杂项任务

示例：
- feature/PROJ-123-user-authentication
- fix/PROJ-456-login-timeout
- hotfix/PROJ-789-security-patch
```

#### 1.2 创建分支
- 始终从最新的主分支创建
- 确认本地主分支已同步
- 创建后立即push到远程（备份）

```bash
git checkout main
git pull origin main
git checkout -b feature/PROJ-123-my-feature
git push -u origin feature/PROJ-123-my-feature
```

#### 1.3 分支同步
- 定期将主分支合并到功能分支（避免最后大量冲突）
- 使用rebase保持历史线性（如果团队规范允许）

```bash
git fetch origin
git merge origin/main
# 或使用rebase（需要谨慎）
git rebase origin/main
```

### Phase 2: 提交规范

#### 2.1 提交信息格式
```
<类型>(<范围>): <简短描述>

[可选的正文]

[可选的脚注]
```

类型：
- `feat`: 新功能
- `fix`: 错误修复
- `docs`: 文档
- `style`: 格式（不影响代码）
- `refactor`: 重构
- `perf`: 性能优化
- `test`: 测试
- `build`: 构建
- `ci`: CI/CD
- `chore`: 杂项

示例：
```
feat(auth): add OAuth2 login support

- implement Google OAuth2 flow
- add user session management
- integrate with existing JWT system

Closes #123
```

#### 2.2 提交原子性原则
- 每个提交是一个独立的完整逻辑单元
- 错误修复和功能不要混在一个提交
- 先拆分，再提交

#### 2.3 提交频率
- 每完成一个独立的小功能就提交
- 不要等到一天结束才提交
- 提交是备份，不是完成标志

### Phase 3: Merge流程

#### 3.1 Merge vs Rebase
- **Merge**：保留完整历史，适合公共分支
- **Rebase**：保持线性历史，适合私有分支

#### 3.2 解决冲突
- 识别冲突范围，不要盲目接受某一侧
- 和涉及的代码作者沟通（如果不清楚意图）
- 测试解决后的代码

#### 3.3 Merge检查清单
- [ ] 功能测试通过
- [ ] 代码已评审
- [ ] 分支已同步主分支
- [ ] 提交信息规范
- [ ] 无不必要的文件

### Phase 4: 版本发布

#### 4.1 语义化版本（SemVer）
```
主版本.次版本.修订号
MAJOR.MINOR.PATCH

- MAJOR: 不兼容的API变更
- MINOR: 向后兼容的功能添加
- PATCH: 向后兼容的bug修复
```

#### 4.2 发布流程
- 从主分支创建发布分支
- 在发布分支上做最后修复
- 合并到主分支和发布标签
- 删除发布分支（归档）

```bash
git checkout -b release/v1.2.0
# 做release准备和最后修复
git checkout main
git merge release/v1.2.0
git tag -a v1.2.0 -m "Release v1.2.0"
git push origin main --tags
```

### Phase 5: 回滚

#### 5.1 轻微回滚（单个提交）
```bash
git revert <commit-hash>
git push origin main
```

#### 5.2 硬回滚（紧急情况）
```bash
git reset --hard <commit-hash>
git push --force
# ⚠️ 警告：force push要谨慎，确保团队知道
```

#### 5.3 Hotfix流程
```bash
# 从tag创建hotfix分支
git checkout -b hotfix/PROJ-789 v1.2.0
# 修复后合并到main和tag
git checkout main
git merge hotfix/PROJ-789
git tag -a v1.2.1 -m "Hotfix v1.2.1"
```

### Phase 6: PR规范模板

#### 6.1 PR描述模板
创建PR时使用以下模板，保持描述一致性：

```markdown
## 变更摘要
<!-- 简要说明这个PR做什么，不超过3句话 -->

## 背景
<!-- 为什么需要这个变更？关联的Issue是什么？ -->

## 变更内容
<!-- 列出具体改动点 -->
- [ ] 功能1：xxx
- [ ] 功能2：xxx

## 影响范围
<!-- 哪些模块/功能会受影响？ -->
- API兼容性问题
- 数据库迁移需求
- 配置变更

## 测试验证
<!-- 如何验证这些变更？ -->
- [ ] 单元测试：覆盖了xxx
- [ ] 集成测试：xxx
- [ ] 手动测试步骤：xxx

## 截图/录屏
<!-- UI变更必须附上截图 -->

## 相关链接
- Issue: #123
- 设计文档: https://...
```

#### 6.2 PR Review检查清单
Reviewer在审批PR时检查：

- [ ] **功能正确性**：代码逻辑是否正确实现需求
- [ ] **代码质量**：命名清晰、无重复代码、无硬编码
- [ ] **安全性**：无敏感信息泄露、输入验证
- [ ] **性能**：无明显的性能问题
- [ ] **测试覆盖**：新增代码有对应的测试
- [ ] **文档更新**：API变更已更新文档
- [ ] **向后兼容**：不破坏现有功能
- [ ] **提交规范**：提交信息符合规范

#### 6.3 PR Size指南
| PR大小 | 行数 | 建议 |
|--------|------|------|
| XS | < 50行 | 鼓励，适合快速review |
| S | 50-200行 | 理想大小 |
| M | 200-500行 | 可接受，需要详细描述 |
| L | 500-1000行 | 建议拆分 |
| XL | > 1000行 | 必须拆分 |

**拆分策略**：
- 按功能模块拆分
- 先基础设施后业务逻辑
- 大的重构拆为"重构准备"+"实际重构"

### Phase 7: Issue格式

#### 7.1 Issue模板
在项目根目录创建 `.github/ISSUE_TEMPLATE/` 目录：

**Bug报告模板** (`bug_report.md`):
```markdown
---
name: Bug Report
about: 报告一个Bug
title: '[Bug] '
labels: bug
assignees: ''
---

## Bug描述
<!-- 清晰描述问题 -->

## 复现步骤
1. Go to '...'
2. Click on '...'
3. Scroll down to '...'
4. See error

## 预期行为
<!-- 描述期望的结果 -->

## 实际行为
<!-- 描述实际的结果 -->

## 环境信息
- OS: [e.g. macOS 14.0]
- Version: [e.g. 1.2.3]

## 日志/截图
<!-- 附上相关日志或截图 -->

## 严重程度
- [ ] P0: 系统崩溃、数据丢失
- [ ] P1: 核心功能不可用
- [ ] P2: 功能缺陷但有 workaround
- [ ] P3: 轻微问题
```

**功能请求模板** (`feature_request.md`):
```markdown
---
name: Feature Request
about: 提出一个新功能
title: '[Feature] '
labels: enhancement
assignees: ''
---

## 功能描述
<!-- 简要描述想要的功能 -->

## 使用场景
<!-- 在什么情况下会用到这个功能？ -->

## 期望的行为
<!-- 详细描述期望的功能 -->

## 替代方案
<!-- 是否有其他实现方式？ -->

## 其他
<!-- 其他相关信息 -->
```

#### 7.2 Issue标签系统
```
类型标签:
- bug: Bug报告
- enhancement: 功能增强
- feature: 新功能
- documentation: 文档
- refactor: 重构
- test: 测试

优先级标签:
- P0: 紧急优先
- P1: 高优先级
- P2: 中优先级
- P3: 低优先级

状态标签:
- blocked: 被阻塞
- needs-review: 需要review
- in-progress: 进行中
- ready-to-test: 待测试
```

#### 7.3 Issue与分支关联
```
分支命名包含Issue编号，PR会自动关联
feature/PROJ-123-login-flow
fix/PROJ-456-null-pointer

提交信息引用Issue
fix: resolve null pointer in login (closes #456)
```

### Phase 8: Cherry-pick策略

#### 8.1 何时使用Cherry-pick
- **适用场景**：
  - 将bug修复从主分支应用到发布分支
  - 将某个特功能分支中的单个提交应用到其他分支
  - 在分支错过merge后补救

- **不适用场景**：
  - 需要大量提交迁移 → 使用merge或rebase
  - 涉及复杂的依赖提交 → 不建议cherry-pick

#### 8.2 Cherry-pick标准流程
```bash
# 1. 找到需要cherry-pick的提交
git log --oneline feature/PROJ-123
# 输出: a1b2c3d fix: resolve null pointer

# 2. 切换到目标分支
git checkout release/v1.2.0

# 3. 执行cherry-pick
git cherry-pick a1b2c3d

# 4. 如果有冲突，解决后
git add .
git cherry-pick --continue

# 5. 推送
git push origin release/v1.2.0
```

#### 8.3 批量Cherry-pick
```bash
# 连续范围的提交
git cherry-pick start..end

# 非连续提交（使用pick保留，drop丢弃）
git rebase -i <before-first-commit>

# 示例：保留commit A和C，丢弃B
pick A feat: add feature A
pick B refactor: intermediate change
pick C feat: add feature C

# 改为：
pick A feat: add feature A
drop B refactor: intermediate change
pick C feat: add feature C
```

#### 8.4 Cherry-pick冲突处理
```bash
# 1. 查看冲突文件
git status

# 2. 手动解决冲突，标记为已解决
git add <resolved-file>

# 3. 继续或中止
git cherry-pick --continue   # 继续
git cherry-pick --abort      # 取消整个cherry-pick
```

#### 8.5 追踪Cherry-pick来源
```bash
# 在提交信息中记录原始提交
git cherry-pick -x a1b2c3d
# -x 会在提交信息中添加一行：Original-commit: a1b2c3d

# 使用message保留来源信息
git cherry-pick -m 1 a1b2c3d
# -m 1 表示保留原始提交的commit message
```

#### 8.6 Cherry-pick vs Merge对比
| 场景 | 推荐 | 原因 |
|------|------|------|
| Bug修复需要同步到多个发布分支 | Cherry-pick | 独立版本管理 |
| 功能需要完整同步 | Merge | 保留完整历史 |
| 发布分支需要安全补丁 | Cherry-pick | 避免引入其他变更 |
| 大型功能同步 | Merge | 避免大量冲突 |

### Phase 9: Git Bisect快速定位

#### 9.1 二分查找原理
Git bisect使用二分搜索算法，在已知"好"和"坏"的提交之间自动定位问题提交。

平均时间复杂度：O(log n)，1000个提交只需约10次测试。

#### 9.2 手动Bisect流程
```bash
# 1. 开始bisect会话
git bisect start

# 2. 标记当前版本为坏
git bisect bad

# 3. 标记一个已知好的版本
git bisect good v1.0.0

# 4. Git自动checkout到中间的提交，测试
# ... 测试后发现这个版本也有问题 ...

# 5. 标记为坏，Git继续二分
git bisect bad
# ... 重复直到找到问题提交 ...

# 6. 完成后返回起点
git bisect reset
```

#### 9.3 自动Bisect脚本
对于有测试用例的项目，使用自动测试：

```bash
# 使用测试脚本自动判断好坏
git bisect start
git bisect bad HEAD
git bisect good v1.0.0
git bisect make test-script.sh

# test-script.sh 示例：
#!/bin/bash
# 返回0表示good，非0表示bad
npm test -- --grep "critical test"
```

**更简洁的写法**：
```bash
git bisect start HEAD v1.0.0 --no-checkout
while git bisect skip 2>/dev/null; do
  npm test && git bisect good || git bisect bad
done
git bisect reset
```

#### 9.4 跳过可疑提交
```bash
# 跳过当前提交（无法测试或不确定）
git bisect skip

# 跳过某个范围
git bisect skip 3..5
```

#### 9.5 Bisect典型工作流
```bash
# 场景：发现生产环境有bug，但不知道是哪次提交引入的
# 已知：v2.1.0正常，v2.2.0有问题

git bisect start
git bisect bad v2.2.0
git bisect good v2.1.0

# Git自动checkout到中间版本
# 测试后：
git bisect bad  # 还是有bug
# 继续...
# 最终找到问题提交

# 查看结果
git bisect log  # 查看完整的bisect历史

# 清理
git bisect reset
```

#### 9.6 Bisect回放与可视化
```bash
# 查看bisect决策过程
git bisect visualize --format=short

# 使用git log查看bisect范围
git log --oneline --bisect
```

### Phase 10: 子模块管理

#### 10.1 添加子模块
```bash
# 添加子模块到指定目录
git submodule add https://github.com/org/repo.git libs/external

# 指定分支
git submodule add -b main https://github.com/org/repo.git libs/external

# 添加后初始化（首次克隆需要）
git submodule init
git submodule update

# 一句话完成（克隆时）
git clone --recurse-submodules https://github.com/org/main-repo.git
```

#### 10.2 更新子模块
```bash
# 更新到远程最新
cd libs/external
git checkout main
git pull origin main

# 或者在主仓库中更新所有子模块
git submodule update --remote libs/external

# 更新所有子模块
git submodule update --remote --recursive
```

#### 10.3 切换子模块版本
```bash
# 查看子模块可用版本
cd libs/external
git fetch
git log --oneline origin/main

# 切换到特定版本
git checkout v1.2.0

# 返回主仓库，提交变更
cd ..
git add libs/external
git commit -m "chore: update external lib to v1.2.0"
```

#### 10.4 克隆含子模块的仓库
```bash
# 方法1：完整递归克隆
git clone --recurse-submodules https://github.com/org/main-repo.git

# 方法2：先克隆主仓库，再初始化子模块
git clone https://github.com/org/main-repo.git
git submodule init
git submodule update

# 方法3：选择性克隆（深度1，避免下载全部历史）
git clone --depth 1 --recurse-submodules https://github.com/org/main-repo.git
```

#### 10.5 删除子模块
```bash
# 1. 从git中移除
git submodule deinit libs/external
git rm libs/external

# 2. 提交变更
git commit -m "chore: remove external dependency"

# 3. 删除本地残留文件（可选）
rm -rf libs/external
```

#### 10.6 子模块常见问题处理

**问题1：子模块提交未同步**
```bash
# 在子模块中提交后，主仓库显示"new commits"
git submodule update --remote libs/external
git add libs/external
git commit -m "chore: sync external lib"
```

**问题2：子模块指向 detached HEAD**
```bash
cd libs/external
git checkout main
cd ..
git add libs/external
git commit -m "chore: update external lib pointer"
```

**问题3：子模块冲突**
```bash
# 主仓库合并时子模块冲突
# 解决方法：进入子模块，解决冲突，然后更新指针
cd libs/external
git checkout main
git merge feature-branch
git push
cd ..
git add libs/external
git commit -m "Merge resolved"
```

**问题4：子模块远程变更丢失**
```bash
# 强制更新到远程最新
git submodule update --remote --force libs/external
```

#### 10.7 子模块工作流建议
- **频繁变更的依赖** → 考虑用包管理器（npm/cargo/pip）
- **稳定的内部库** → 子模块适用
- **跨仓库共享代码** → 子模块适用
- **避免深层嵌套** → 最多1层子模块
- **CI/CD中子模块** → 确保配置SSH或deploy key

## Common Rationalizations

| 常见借口 | 真相 | 反制 |
|---------|------|------|
| "提交信息随便写，反正自己能看懂" | 3个月后的自己也看不懂 | 规范提交信息是协作的基础 |
| "等代码完全完成再提交" | 中途代码没有备份，风险极大 | 小步提交，每个完成的逻辑单元都提交 |
| "rebase会弄乱历史，不用" | 历史线性的价值远大于rebase的风险 | 制定团队规范，明确哪些分支可以rebase |
| "force push没问题，反正我自己用" | force push会覆盖其他人的工作 | 永远不要对主分支force push |
| "merge冲突太多，先放着" | 冲突拖越久越难解决 | 尽早merge，主分支更新时及时同步 |

## Red Flags

- 分支名包含特殊字符或中文
- 提交信息是"asdfadsf"或"xxx"
- 提交包含大量不相关的改动
- 分支超过2周未合并
- 直接在main分支开发
- 合并前不检查冲突
- 发布版本没有tag

## Verification

验证清单：

- [ ] 分支命名符合规范
- [ ] 提交信息符合规范（类型+描述）
- [ ] 每个提交是原子性的
- [ ] 合并前已同步主分支
- [ ] 合并前代码已评审
- [ ] 发布版本有对应tag
- [ ] hotfix有完整流程记录
- [ ] 回滚方案已记录
- [ ] PR描述完整（摘要/背景/影响/测试）
- [ ] PR大小适中（建议<500行）
- [ ] Issue模板填写完整
- [ ] Issue与分支/PR正确关联
- [ ] Cherry-pick记录原始提交（-x参数）
- [ ] Bisect定位后问题提交已确认
- [ ] 子模块版本已锁定并记录
