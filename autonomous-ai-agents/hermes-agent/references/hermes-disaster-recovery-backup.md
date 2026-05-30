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

## Aliyun Drive 自动同步（rclone）

### 概述
目标：使用 rclone 将整个 Hermes 生态（约 41GB）同步到阿里云盘。
组件：hermes 配置（~3.4GB lean）、ollama 模型（~2.7GB）、Docker 镜像+卷（~30GB）、浏览器缓存（可选，~5GB）。

### 准备工作
1. **安装 rclone：** `curl https://rclone.org/install.sh | bash`
2. **获取阿里云盘 refresh_token：**
   - 打开 https://www.aliyundrive.com/ 扫码登录
   - 按 F12 打开开发者工具 → Application → Local Storage → 找 `refresh_token` 字段的值
   - 发给 Hermes 配置

### rclone 阿里云盘配置
```bash
rclone config
# 选择: n (New remote) → name: aliyun → 83 (Aliyun Drive) → 粘贴 refresh_token
```

### 待同步内容（大小估算）

| 路径 | 内容 | 大小 |
|------|------|------|
| `~/.hermes/` | config, skills, memories, state.db | ~3.4GB lean |
| `~/.ollama/models/` | qwen2.5:1.5b + qwen3-vl:2b | ~2.7GB |
| Docker volumes | hindsight, chromadb, n8n data | ~1.1GB |
| `~/.hermes/chrome-debug/` | Chrome 浏览器缓存（可选） | ~4.9GB |

总计（不含chrome）：~7-8GB，含chrome：~13GB。

### 同步脚本

```bash
#!/bin/bash
# sync-to-aliyun.sh — 增量同步到阿里云盘

RCLONE_REMOTE="aliyun:hermes-backup"
LOG="~/.hermes/logs/aliyun-sync.log"

log() { echo "[$(date '+%Y-%m-%d %H:%M')] $*" | tee -a "$LOG"; }

# 同步 hermes lean backup
log "Syncing hermes config..."
rclone sync ~/.hermes/config.yaml "$RCLONE_REMOTE/hermes/" --log-file "$LOG"
rclone sync ~/.hermes/skills/ "$RCLONE_REMOTE/skills/" --exclude "*.pyc" --log-file "$LOG"

# 同步 ollama 模型
log "Syncing ollama models..."
rclone sync ~/.ollama/models/ "$RCLONE_REMOTE/ollama-models/" --drive-chunk-size 64M --log-file "$LOG"

# 同步 Docker volumes（停容器保证一致性）
log "Syncing docker volumes..."
docker stop hermes-hindsight searxng hermes-ai-n8n-1 hermes-ai-chromadb-1 2>/dev/null
rclone sync /var/lib/docker/volumes/hermes-ai_chroma_data/_data "$RCLONE_REMOTE/chromadb/" --log-file "$LOG"
rclone sync /var/lib/docker/volumes/hermes-ai-n8n_n8n_data/_data "$RCLONE_REMOTE/n8n/" --log-file "$LOG"
docker start hermes-hindsight searxng hermes-ai-n8n-1 hermes-ai-chromadb-1 2>/dev/null

log "Sync complete."
```

### 定时任务
```bash
# 每天凌晨 3 点自动同步
hermes cron create "0 3 * * *" --name "daily-aliyun-backup" --prompt "Run: /Users/aimac/.hermes/scripts/sync-to-aliyun.sh"
```

### 注意事项
- 阿里云盘免费版容量 2GB-100GB（视会员等级）
- `rclone copy` vs `rclone sync`：copy=仅新增，sync=镜像同步（删除目标中源没有的文件）
- 首次运行加 `--dry-run` 预览
- Chrome 缓存变化频繁且体积大，建议单独排除或每周同步一次
- rclone 阿里云盘 driver (id: 83) 需要 refresh_token，不支持账号密码登录

### 获取 refresh_token 步骤（用户操作）
1. 浏览器打开 https://www.aliyundrive.com/ 并登录
2. F12 → Application → Local Storage → https://www.aliyundrive.com
3. 找到 `refresh_token` 的值，复制给 Hermes
4. Hermes 执行 `rclone config` 完成配置

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