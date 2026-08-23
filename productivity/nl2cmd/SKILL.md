---
name: nl2cmd
version: 0.1
description: |
  Natural Language → Shell Command. 用自然语言描述需求，AI生成适合当前macOS/Linux系统的shell命令，
  支持命令执行确认和命令解释。
triggers:
  - "自然语言转shell命令"
  - "生成命令行"
  - "帮我写命令"
  - "nl2cmd"
  - "这个命令是什么意思"
  - "解释命令"
trigger_type: user_command
tags: ["cli","shell","productivity","terminal","LLM"]
created: 2026-08-05
created_by: hermes-agent
pinned: false
---

# Natural Language → Shell Command

用自然语言描述你的需求，`nl2cmd` 生成精确的 shell 命令。

## 核心功能

| 功能 | 命令 | 说明 |
|---|---|---|
| 生成命令 | `nl2cmd "找出大于100M的文件"` | AI生成命令，用户确认后执行 |
| 解释命令 | `nl2cmd -e "tar -czf a.tgz ./src"` | 逐部分解释命令含义 |

## 前提条件

- `nl2cmd` 脚本已安装在 `~/.local/bin/nl2cmd`
- API key：从 `~/.hermes/.env` 的 `ZAI_API_KEY` 读取（GLM 模型，国内直连）

## 依赖安装

```bash
# 如果 ~/.local/bin/nl2cmd 不存在，手动创建：
# 脚本路径：~/.local/bin/nl2cmd
# 内容见 skill 关联脚本
chmod +x ~/.local/bin/nl2cmd
```

## 使用示例

```bash
# 查看当前目录文件
nl2cmd "查看当前目录文件"

# 查找大文件
nl2cmd "找出大于100M的文件"

# 统计代码行数
nl2cmd "统计当前目录的Python文件行数"

# 压缩目录
nl2cmd "压缩src目录"

# 解释已有命令
nl2cmd -e "rsync -avz --exclude='*.log' src/ dest/"

# Docker 清理
nl2cmd "清理所有已停止的Docker容器"

# Git 操作
nl2cmd "查看最近10次提交"
```

## 安全机制

1. **命令需确认**：生成后不会自动执行，用户按 `y` 确认后才执行
2. **危险命令警告**：`rm -rf /`、`dd if=`、`mkfs` 等会显示警告
3. **系统信息感知**：自动检测当前 OS (macOS/Linux)、Shell 类型、包管理器

## 技术细节

- 使用 `glm-4-flash` 模型（GLM via bigmodel.cn API）
- API key 从 `~/.hermes/.env` 自动读取 `ZAI_API_KEY`
- 权限错误属于正常（系统目录无权限）
