# Skills 维护指南

## 两类 Skills 的区别

Hermes Agent 的 skills 有两种来源，维护方式完全不同：

### 1. Hub 安装的 Skills（`hermes skills install`）
- 从 Hermes Skills Hub 安装，存储在 `$HERMES_HOME/skills/` 但有独立 git 历史
- 支持 `hermes skills check` 和 `hermes skills update` 自动更新
- 分布在 `~/.hermes/skills/` 下各自独立的子目录

### 2. 文件直接 clone 的 Skills（git clone）
- 直接 git clone 到 `$HERMES_HOME/skills/` 目录，**没有独立的 git remote**
- 实际上这些 skills 的 remote 指向配置仓库（如 `Buluhanke/hermes-config-2026-05`），不是上游原始仓库
- **`hermes skills check` 对这类 skills 无效**——命令只检查 Hub 安装的技能
- **没有任何自动同步机制**，需要手动 `git pull` 更新

## 检查文件型 Skills 是否有更新的正确方法

```bash
# 在 skills 目录统一检查并 pull
cd ~/.hermes/skills && git fetch --all
for dir in */; do
  git -C "$dir" pull 2>/dev/null || echo "Not a git repo: $dir"
done
```

## 批量更新脚本

创建 `scripts/batch_update_skills.sh`：

```bash
#!/bin/bash
cd ~/.hermes/skills
for dir in */; do
  [ -d "$dir/.git" ] && git -C "$dir" pull origin main 2>&1 | grep -v "^Already up to date" || echo "Skipping $dir"
done
```

## 定时自动更新

```bash
# 创建 launchd 或 cron 任务，每天凌晨执行
# launchd plist 示例：
# Label: ai.hermes.skills_update
# ProgramArguments: [/bin/bash, /Users/mac/.hermes/scripts/batch_update_skills.sh]
# RunAtLoad: false
# StartCalendarInterval: {Hour: 3, Minute: 0}
```

## 当前安装的 Skills 来源

所有 37 个 skills 均通过 git clone 安装，来自配置仓库 `Buluhanke/hermes-config-2026-05`。这些不是上游原始仓库的更新，而是跟随整个配置仓库同步。如果上游配置仓库有更新，手动 `git pull` 即可。

如需获取上游 NousResearch/hermes-agent 官方的 skills 最新版，需从 `https://github.com/NousResearch/hermes-agent` 的 `skills/` 目录单独拉取。
