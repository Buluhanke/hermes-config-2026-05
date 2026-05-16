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
---

# Git Workflow and Versioning

## Overview

Git是代码协作的基石。不规范的Git使用会导致：代码丢失、冲突难解、回滚困难、发布混乱。规范的Git工作流让协作流畅、可追溯、可回滚。

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
