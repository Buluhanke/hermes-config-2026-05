# Hermes 完全灾难恢复备份

将 `~/.hermes/` 下所有自定义配置完整备份至独立的 GitHub 私有仓库，系统损坏或换电脑时可一键恢复。

## 与 `hermes-git-backup-script.md` 的区别

| 特性 | hermes-git-backup-script | 本方案 |
|------|-------------------------|--------|
| 仓库位置 | `~/.hermes/` 本身 | 独立的 `~/hermes-backup/` 仓库 |
| 备份范围 | 仅 `~/.hermes/` | `~/.hermes/` + `.env` + chrome-debug + launchd |
| .gitignore | 默认（忽略 .env） | **修改过，不忽略 .env 和 *.pkl 和 *.sqlite** |
| 用途 | 日常配置变更跟踪 | **灾难恢复**（系统损坏/换电脑） |
| RESTORE.md | 无 | 有完整恢复指南 |

## 备份内容

- `config.yaml` — Hermes 主配置（模型、platform、工具、技能等）
- `.env` — API keys、代理配置、系统密钥（**注意：这是敏感信息，仅适用于私有仓库**）
- `skills/` — 所有自定义技能
- `hermes-agent/` 下的自定义 py 文件（perception.py, redis_persistence.py, 修改后的 run_agent.py, todo_tool.py, web_tools.py 等）
- `scripts/` — 自定义脚本
- `cron/` — 定时任务配置
- `chrome-debug/` — Chrome 持久化 Profile（含 1688 等网站登录态，~324MB）
- launchd plist 文件（`com.aimac.*.plist`）

## 设置步骤

### 1. 创建备份仓库

```bash
mkdir -p ~/hermes-backup
cd ~/hermes-backup
git init
git remote add origin https://github.com/Buluhanke/hermes-MACmini26.05.git
```

### 2. 修改 .gitignore

对于灾难恢复的私有仓库，需要**允许**提交 .env 等敏感文件（因为恢复时需要它们）：

```gitignore
# 不要忽略 .env、*.pkl、*.sqlite（因为需要备份）
# 只忽略 venv/、node_modules/、*.pyc 等可重建的内容
venv/
node_modules/
*.pyc
__pycache__/
.DS_Store
```

### 3. 同步脚本 `sync_to_github.sh`

核心逻辑：
1. 从 `~/.hermes/` 复制自定义文件到 `~/hermes-backup/`
2. 复制 config.yaml、.env
3. rsync skills/、scripts/、cron/、chrome-debug/
4. 复制 hermes-agent 下 git 跟踪的未提交/修改的 py 文件
5. 复制 launchd plist
6. git add → commit → push（全静默，stdout 重定向到 /dev/null）

### 4. 设置定时任务（每天 3:00 自动同步）

```bash
# 复制脚本
cp ~/hermes-backup/sync_to_github.sh ~/.hermes/scripts/sync-hermes-backup.sh
chmod +x ~/.hermes/scripts/sync-hermes-backup.sh

# 用 cronjob tool 创建任务（no_agent=true，0 token 消耗）
cronjob(action='create', name='hermes-disaster-backup', schedule='0 3 * * *', script='sync-hermes-backup.sh', no_agent=True)
```

## 恢复步骤（系统损坏/换电脑后）

核心步骤（详见 RESTORE.md）：

```bash
git clone https://github.com/Buluhanke/hermes-MACmini26.05.git ~/hermes-backup
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
cp ~/hermes-backup/config.yaml ~/.hermes/config.yaml
cp ~/hermes-backup/.env ~/.hermes/.env
rsync -a ~/hermes-backup/skills/ ~/.hermes/skills/
rsync -a ~/hermes-backup/scripts/ ~/.hermes/scripts/
cp ~/hermes-backup/hermes-agent/*.py ~/.hermes/hermes-agent/
rsync -a ~/hermes-backup/chrome-debug/ ~/.hermes/chrome-debug/
for plist in ~/hermes-backup/launchd/*.plist; do cp "$plist" ~/Library/LaunchAgents/ && launchctl load -w "$plist"; done
cd ~/.hermes/hermes-agent && venv/bin/pip install redis boto3 baidu-aip
venv/bin/hermes gateway restart
```

## ⚠️ 重要注意事项

1. **私有仓库**：包含 .env（API keys）和 chrome-debug/（浏览器登录态），**绝对不能设为公开**
2. **安全取舍**：为了灾难恢复的便利性，放弃了常规 .gitignore 规则——不忽略 .env。这是经过用户确认的有意设计
3. **定时任务 0 token 消耗**：no_agent=true，纯 bash 脚本 + git，不调用 LLM
4. **Chrome 登录态必须提前建立**：恢复后新的 Chrome Profile 初始为空，需要先用持久化 Chrome（port 9333）登录 1688 等网站
5. **首次备份可能需要 400MB+**：主要是 chrome-debug（浏览器 Profile ~324MB）

## 文件路径

- 同步脚本（备份目录）：`~/hermes-backup/sync_to_github.sh`
- 同步脚本（定时任务调用）：`~/.hermes/scripts/sync-hermes-backup.sh`
- 恢复指南：`~/hermes-backup/RESTORE.md`
- .gitignore（修改版）：`~/hermes-backup/.gitignore`
