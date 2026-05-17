---
name: git-workflow
description: "Git工作流与版本管理 — 分支策略/提交规范/代码审查/冲突处理"
version: 1.0.0
tags: [git, 工作流, 版本管理, 分支, 提交规范]
author: Hermes Agent
---

# Git工作流

## 分支策略

### 推荐分支模型（GitFlow简化版）
```
main          — 生产环境代码，只合并不直接提交
├── develop   — 开发主干，所有功能集于此
│   ├── feature/xxx  — 功能分支，完成后合并回develop
│   └── release/xxx  — 发布分支，测试通过合并到main
└── hotfix/xxx       — 紧急修复，直接合并到main和develop
```

### Hermes实际应用
- `hermes-config` 公开仓库：main分支存放文档模板
- `hermes-backup` 私有仓库：main分支存放实际配置
- `hermes-skills` 私有仓库：按category分组feature分支

### 分支命名规范
```
feature/功能名               # 新功能
fix/问题描述                 # bug修复
docs/文档类型               # 文档更新
refactor/重构内容           # 代码重构
hotfix/紧急问题             # 紧急修复
```

## 提交规范（Conventional Commits）

### 格式
```
<type>(<scope>): <subject>

[optional body]

[optional footer]
```

### Type类型
| Type | 说明 | 示例 |
|------|------|------|
| feat | 新功能 | feat(skills): 添加1688议价skill |
| fix | 修复bug | fix(vision): 修复SSIM误报 |
| docs | 文档更新 | docs: 更新README |
| style | 格式调整 | style: 格式化代码 |
| refactor | 重构 | refactor(procurement): 简化询价流程 |
| test | 测试 | test: 添加单元测试 |
| chore | 维护 | chore: 升级依赖版本 |

### 示例
```
feat(procurement): 添加供应商红黑榜动态管理

- 新增评分维度：质量/交期/价格/服务/沟通
- 红榜条件：连续3次无纠纷+评分>4.6
- 黑榜条件：纠纷率>5%或质量问题>2次
- 自动更新看板供应商卡片颜色

Closes #123
```

## 代码审查流程

### PR创建检查
- [ ] 代码符合提交规范
- [ ] 有对应的测试
- [ ] 文档已更新
- [ ] 没有敏感信息泄露

### 审查要点
- 功能正确性：代码是否实现了需求
- 代码质量：可读性/可维护性/性能
- 安全漏洞：注入/泄露/权限问题
- 测试覆盖：新增代码有测试

### 合并条件
- 至少1人review通过
- 所有CI检查通过
- 无冲突分支

## 冲突处理

### 原则
- 优先rebase而非merge（保持线性历史）
- 冲突时与相关开发者沟通后解决
- 测试通过后再提交

### 操作流程
```bash
# 1. 切到目标分支
git checkout develop

# 2. 拉取最新
git pull origin develop

# 3. 切回功能分支
git checkout feature/xxx

# 4. rebase到最新develop
git rebase develop

# 5. 解决冲突后
git add .
git rebase --continue

# 6. 强制推送（仅自己的分支）
git push --force-with-lease origin feature/xxx
```

## 标签管理

### 版本号规范（Semantic Versioning）
```
v主版本.次版本.修订号
v1.0.0
│   │   └─ 修订号：bug修复
│   └─ 次版本：新功能（向后兼容）
└─ 主版本：破坏性变更（不向后兼容）
```

### 标签操作
```bash
# 打标签
git tag -a v1.0.0 -m "正式版本发布"

# 推送标签
git push origin v1.0.0

# 查看标签
git tag -l
```

## Hermes场景应用

### hermes-config公开仓库
- 用途：文档模板、配置标准
- 分支：只有main（简洁）
- 协作：PR合并

### hermes-backup私有仓库
- 用途：实际配置备份
- 分支：main + daily-backup自动提交
- 策略：每日自动备份，GitHub私有仓

### hermes-skills私有仓库
- 用途：技能库
- 分支：按category分feature
- 合并：review后合并到main