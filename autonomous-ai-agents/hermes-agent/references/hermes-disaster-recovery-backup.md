# Hermes 灾备恢复指南

## 核心原则

**GitHub 存元数据，云盘存大文件。**

GitHub 单文件 250MB 限制，git push 超过 100MB 就可能触发 `curl 16 HTTP2 framing layer` 错误。完整备份 (~4GB) 无法通过 git 推送。

## Lean Backup 方案（GitHub）

只备份**不可重建的核心数据**，1-2MB，轻松 push。

### 备份内容

```
~/.hermes/
├── memories/          # MEMORY.md, USER.md（用户偏好、运行环境）
├── supplier_memory/   # 供应商记忆
├── cron/jobs.json    # 定时任务配置
├── autonomous-ai-agents/  # Agent 配置
├── scripts/          # 自定义脚本
├── config.yaml       # 主配置
├── SOUL.md           # 人格定义
├── channel_directory.json
```

### 不备份（可重建）

- `venv/` `venv311/` `.venv/` — `pip install -e .` 重建
- `skills/` — `hermes skills install` 重新装
- `sessions/` — 对话记录不需要
- `cache/` `logs/` `replays/` — 运行时产物
- `auth.json` `1688_cookies.json` — 敏感文件，永不提交
- `mlops/` — Docker volume，大文件走云盘

### 重建流程

```bash
# 1. 克隆备份
git clone https://github.com/Buluhanke/hermes-backup-v2.git ~/hermes-backup

# 2. 恢复核心文件到 ~/.hermes/
cp -r ~/hermes-backup/memories/ ~/.hermes/
cp -r ~/hermes-backup/supplier_memory/ ~/.hermes/
cp -r ~/hermes-backup/cron/ ~/.hermes/
cp -r ~/hermes-backup/autonomous-ai-agents/ ~/.hermes/
cp ~/hermes-backup/config.yaml ~/.hermes/
cp ~/hermes-backup/SOUL.md ~/.hermes/

# 3. 重建 venv（如需要）
cd ~/.hermes/hermes-agent
python3.11 -m venv venv
venv/bin/pip install -e . -i https://pypi.tuna.tsinghua.edu.cn/simple
```

## 自动备份脚本

```bash
#!/bin/bash
# sync-hermes-backup.sh — 同步 lean backup 到 GitHub

SRC=~/.hermes
TMP=/tmp/hermes-lean-backup
REPO=https://github.com/Buluhanke/hermes-backup-v2.git

rm -rf $TMP
mkdir -p $TMP

# 精选文件（不备份 venv/cache/logs/sessions）
cp $SRC/config.yaml $TMP/
cp $SRC/SOUL.md $TMP/
cp $SRC/channel_directory.json $TMP/
cp -r $SRC/memories/ $TMP/
cp -r $SRC/supplier_memory/ $TMP/
cp -r $SRC/cron/ $TMP/
cp -r $SRC/autonomous-ai-agents/ $TMP/
cp -r $SRC/scripts/ $TMP/

# 写入 .gitignore
cat > $TMP/.gitignore << 'EOF'
__pycache__/
*.pyc
venv/
venv311/
.env
auth.json
1688_cookies.json
*.local.json
credentials.*
logs/
cache/
replays/
chrome-debug/
EOF

cd $TMP && git init -b main && git add .
git commit -m "Lean backup $(date +%Y-%m-%d_%H-%M)"
git remote add origin $REPO
git push -u origin main --force
```

## 大文件备份方案（云盘）

Hindsight Docker volume + mlops 数据走 rclone 到 Google Drive 或阿里云盘：

```bash
# 查 Docker volume 路径
docker volume inspect hindsight_hindsight-data

# 打包上传（不通过 git）
tar czf /tmp/hindsight-backup.tar.gz -C /var/lib/docker/volumes/hindsight_hindsight-data/_data .
rclone copy /tmp/hindsight-backup.tar.gz google-drive:hermes-backup/

# 恢复
rclone copy google-drive:hermes-backup/hindsight-backup.tar.gz /tmp/
tar xzf /tmp/hindsight-backup.tar.gz -C /var/lib/docker/volumes/hindsight_hindsight-data/_data
```

## GitHub 仓库重建步骤

当仓库乱了（误提交大文件/敏感文件），重建干净仓库：

```bash
# 1. 建新仓库
gh repo create Buluhanke/hermes-backup-v2 --private

# 2. 准备 lean backup 到临时目录
# （按上面"备份内容"选择性复制）

# 3. 初始化 git（不要用 -b，macOS git 版本太老不支持）
cd /tmp/hermes-lean-backup
git init
git branch -m main   # 或用 symbolic-ref
git add .
git commit -m "Lean backup init"

# 4. 关联并推送
git remote add origin https://github.com/Buluhanke/hermes-backup-v2.git
git push -u origin main
```

**注意：** `gh repo create --source` 要求已有 commit，先 commit 再 push。

## GitHub 大文件清除（如已误提交）

```bash
# 移除大文件历史
git filter-branch --tree-filter 'rm -f path/to/large-file' HEAD
# 或用 BFG Repo-Cleaner
bfg --delete-big-files --blade 100M

# 强制推送
git push origin main --force
```

## 定时备份 cron

```bash
# 每天凌晨 3 点自动 push
0 3 * * * /Users/aimac/.hermes/scripts/sync-hermes-backup.sh >> /Users/aimac/.hermes/logs/backup.log 2>&1
```