---
name: hermes-skills-management
description: Hermes Hub 技能安装与管理 — 搜索、安装、诊断十大类常用技能的标准流程
version: "1.0"
metadata:
  hermes:
    tags: [skills, hub, install, management]
    category: agent-tooling
triggers:
  - 安装十大Skills / 打工人必装 / 安装技能清单
  - hermes skills install 失败 / 超时 / 找不到
  - 搜索 hub 技能 / 查某技能是否在 hub 上
  - hermes skills search / browse / inspect
when-to-use: 当需要为 Hermes 安装新技能、或诊断已装技能的健康状态时
dependencies:
  - hermes CLI (hermes skills)
---

# Hermes Skills Management

## Hub 安装命令格式

```bash
# 按优先级尝试以下路径：
# 1. skills.sh (最快)
hermes skills install skills-sh/<owner>/<repo>/<skill-name> --force

# 2. official (内置可选)
hermes skills install official/<category>/<skill-name> --force

# 3. GitHub 直链 (最慢，易超时)
hermes skills install github:<owner>/<repo>/<skill-name> --force
hermes skills install https://raw.githubusercontent.com/<owner>/<repo>/main/... --name <name> --force

# 4. 直接 URL
hermes skills install https://example.com/SKILL.md --name <name> --force
```

## 搜索技能

```bash
# 搜索所有源
hermes skills search <keyword>

# 只搜 skills.sh (最快)
hermes skills search <keyword> --source skills-sh

# 只搜 official
hermes skills search <keyword> --source official

# 预览再装
hermes skills inspect <identifier>
```

## 已知问题与应对

| 问题 | 原因 | 解决方案 |
|------|------|---------|
| GitHub 直链超时 | 网络限制 | 换 skills-sh 标识符，或多试几次（有时重试成功） |
| community skill 被 block | dangerous verdict | 换另一个 source（如换 owner/repo） |
| 安装成功但 skills_list 找不到 | curator 归档 | 检查 `~/.hermes/skills/<name>/` 是否存在 |
| skills.sh 超时 | 索引服务慢 | 换官方 official 或直接用 GitHub 标识符 |

## 打工人十大Skills安装记录

参见 `references/top10-skills-install-log.md`

---

## 安装命令参考（快速上手）

```bash
# ✅ 已验证成功
hermes skills install skills-sh/101-skills/skills/agent-browser --force
hermes skills install skills-sh/vercel-labs/skills/find-skills --force
hermes skills install skills-sh/anthropics/skills/skill-creator --force
hermes skills install official/creative/creative-ideation --force
hermes skills install skills-sh/zinohome/cozyengine/ui-prompt-generator --force

# ⚠️ 超时试重试（有时重试成功）
hermes skills install github:MiniMax-AI/skills/minimax-docx --force
hermes skills install github:MiniMax-AI/skills/minimax-pdf --force
hermes skills install github:MiniMax-AI/skills/minimax-xlsx --force
```
