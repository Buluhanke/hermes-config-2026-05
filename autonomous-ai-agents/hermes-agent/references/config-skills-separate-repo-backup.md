# Hermes 配置+技能 Git 备份到独立仓库

`~/.hermes/` 目录本身就是 Hermes Agent 的 Git 仓库（remote 指向 hermes-agent 上游），
**不能**直接在 `~/.hermes/` 里提交 config + skills 并推到用户自己的备份仓库。

正确做法：在独立目录初始化备份仓库。

## 标准流程

```bash
# 1. 创建备份目录
mkdir -p ~/hermes-backup
cd ~/hermes-backup
git init

# 2. 写 .gitignore（排除 .env、日志、session 文件等敏感数据）
echo '.DS_Store
.env
*.log
sessions/
*.pkl
*.sqlite
__pycache__/
' > .gitignore

# 3. 设置 git 用户信息
git config user.name "Buluhanke"
git config user.email "buluhanke@users.noreply.github.com"

# 4. 拷贝 config + skills
cp ~/.hermes/config.yaml ./
mkdir -p skills
cp -R ~/.hermes/skills/* ./skills/

# 可选：拷贝其他自定义文件
cp ~/.hermes/hermes-agent/perception.py ./   # 统一感知层

# 5. 首推
git remote add origin https://github.com/Buluhanke/hermes-MACmini26.05.git
git add -A
git commit -m "backup $(date +%Y-%m-%d)"
git push -u origin master
```

## 每日同步脚本

`~/hermes-backup/sync_to_github.sh`:

```bash
#!/bin/bash
set -e
BACKUP_DIR="$HOME/hermes-backup"
REMOTE="origin"
BRANCH="master"

cp "$HOME/.hermes/config.yaml" "$BACKUP_DIR/config.yaml"
rm -rf "$BACKUP_DIR/skills"
mkdir -p "$BACKUP_DIR/skills"
cp -R "$HOME/.hermes/skills/"* "$BACKUP_DIR/skills/" 2>/dev/null

# 可选：追加其他文件更新
[ -f "$HOME/.hermes/hermes-agent/perception.py" ] && \
  cp "$HOME/.hermes/hermes-agent/perception.py" "$BACKUP_DIR/perception.py"

cd "$BACKUP_DIR"
git add -A
git diff --cached --quiet && exit 0  # 无变更跳过
git commit -m "Backup $(date +%Y-%m-%d_%H:%M)"
git push "$REMOTE" "$BRANCH"
```

## 注意事项

| 项目 | 说明 |
|------|------|
| **不推 .env** | .gitignore 已排除，API key 不泄露 |
| **不推源码** | hermes-agent 源码在 `~/.hermes/` 中由 git 独立管理 |
| **备份库和源码库分离** | 用户配置不污染 agent 源码的提交历史 |
| **新增文件** | 如新增 skill，copy 到备份目录后执行同步脚本即可 |
| **恢复** | 克隆备份库 + 手动拷贝 config/skills 回 `~/.hermes/` |

## 与前一个备份方案的区别

之前的 `references/hermes-git-backup-script.md` 方案假设 `~/.hermes/` 自身就是用户仓库。
本用户场景中 `~/.hermes/` 是 Hermes Agent 源码仓库，所以改用独立目录方案。
