# .hermes 仓库重建执行计划

## 背景
`.hermes` 仓库本地 20GB（总大小），`.git` 目录 5.6GB（超 GitHub 5GB 限制），远程已超限无法推送。filter-branch 无法有效缩减远程大小，必须完整重建仓库。

## 关键数据（2026-05-29）
- `du -sh ~/.hermes` = 20GB 总内容
- `du -sh ~/.hermes/.git` = 5.6GB
- 最大目录：chrome-debug/(5GB)、hermes-agent/(3.5GB)、state-snapshots/(1.8GB)、sessions/(921MB)
- `skills/` 仓库（独立）已修复，force push 成功
- `hermes-agent/` 有独立 `.git`，是独立子仓库

## 执行步骤

### Step 1：分析本地内容
```bash
du -sh ~/.hermes && echo "---" && du -sh ~/.hermes/.git
du -sh * | sort -hr | head -20
```
目的：确认哪些目录是大的、哪些需要写入 .gitignore

### Step 2：删除 GitHub 旧仓库（不可逆！）
通过 GitHub 网页 Settings → Danger Zone 删除，或：
```bash
gh repo delete Buluhanke/hermes-config-2026-05 --yes
```

### Step 3：处理嵌套独立 git 仓库
hermes-agent 目录有自己独立的 `.git`，需要转为普通目录：
```bash
# 方案A：删除hermes-agent/.git（hermes-agent配置会丢失，需重新配置）
rm -rf ~/.hermes/hermes-agent/.git

# 方案B：迁移到备份位置
mkdir -p ~/hermes-agent-backup
mv ~/.hermes/hermes-agent/.git ~/hermes-agent-backup/
```
**检查**：`git -C ~/.hermes/hermes-agent rev-parse --show-toplevel` 有输出 = 独立仓库

### Step 4：编写 .gitignore
```bash
cat > ~/.hermes/.gitignore << 'EOF'
# 大型缓存/调试目录（会随使用膨胀）
chrome-debug/
sessions/
state-snapshots/
logs/
*.log
state.db
state.db-wal
state.db-shm

# Python
__pycache__/
*.pyc
venv*/
.venv*/
*.egg-info/

# macOS
.DS_Store
*.swp

# 临时文件
*.tmp
*.bak
EOF
```

### Step 5：删除旧 git 并重建
```bash
cd ~/.hermes
rm -rf .git
git init
git remote add origin https://github.com/Buluhanke/hermes-config-2026-05.git
git add .            # .gitignore 中的路径会被排除
git commit -m "Initial commit - clean repo"
```

### Step 6：推送
```bash
GIT_TERMINAL_PROMPT=0 git push -u origin main
```

## 风险
- **不可逆**：删除 GitHub 仓库后无法恢复
- **丢失历史**：所有 git 历史丢失
- **hermes-agent 配置**：如果删除了其独立 .git，需要重新配置 agent
- **skills/ 子目录**：hermes-agent 是 skills/ 下的一个子目录，重建后需要确认路径结构正确

## 替代方案
如果不想完全重建，可以：
1. 保留 skills/ 目录的独立同步（skills/ 本身已修复）
2. .hermes 根目录内容（有hermes-agent、scripts、cron等）用 rsync 或手动备份到别处
3. 只推送 skills/ 到独立仓库
