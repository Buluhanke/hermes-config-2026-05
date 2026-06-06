# 硬盘彻底坏了 — Hermes 完整恢复 SOP (30 分钟版)

> 场景：新电脑/硬盘全坏/重装系统,目标是从零恢复到跟原 Hermes 配置**一模一样**的状态。
> 适用范围：用户有 `hermes_backup.sh` 在坚果云跑过 ≥1 次,且 GPG 密码在密码管理器里有记录。
> 不适用范围：坚果云账号也丢了 + GPG 密码也丢了(见最后"最坏情况")。

## 时间线

| 阶段 | 操作 | 时间 | 关键命令 |
|------|------|------|----------|
| 1 | 新电脑装 macOS + brew + python3.11 + node + gpg + rclone | 5 min | `brew install python@3.11 node gpg rclone` |
| 2 | 创建同用户名账号 `aimac`(关键!否则路径全错) | 2 min | 系统设置 → 用户 |
| 3 | 装 hermes-agent 源码 | 3 min | `git clone ... + python3.11 -m venv + pip install` |
| 4 | 配置 rclone + 拉坚果云加密分卷 | 5 min | `hermes_setup_jianguoyun.sh` + `rclone copy` |
| 5 | 跑 `hermes_restore.sh` 解密+解压+修权限 | 5 min | 输 GPG 密码 |
| 6 | 验证健康(state.db / config / .env / skills 数量) | 2 min | `verify_hermes_backup.py` |
| 7 | 重建 Keychain + 重新跑 launchd 周备份 | 2 min | `--keychain-set` + `launchctl load` |
| 8 | 立即手动跑一次完整备份(双保险) | 5 min | `hermes_backup.sh` |
| **总计** | | **~30 min** | |

## Step 1: 新电脑装基础工具

```bash
# 装 Homebrew(如果没有)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 装必要工具
brew install python@3.11 node gpg rclone git

# 验证
python3.11 --version  # 应 ≥ 3.11
gpg --version         # 应 ≥ 2.4
rclone version        # 应 ≥ 1.65
node --version        # 应 ≥ 18
```

## Step 2: 创建同用户名(关键!)

```bash
# 系统设置 → 用户与群组 → 新建用户
# 用户名必须填 aimac(跟原 .hermes 路径一致)
# 如果新电脑用户名不同,所有脚本里的 ~/.hermes 都要改成 ~/新用户名/.hermes
```

**为什么不省略这一步**:`hermes-agent` 内部很多代码硬编码 `$HOME/.hermes`、launchd plist 路径是绝对路径。改用户名 = 大量 sed 工作。

## Step 3: 装 hermes-agent 源码

```bash
mkdir -p ~/.hermes
cd ~/.hermes
git clone https://github.com/NousResearch/hermes-agent.git
cd hermes-agent

# 切回老 commit(可选 — 旧电脑的 commit 在 manifest 里)
# 旧 commit: f66a929(看 manifest 或跑 git log)
# git checkout f66a929  # 或保持 main 分支最新
git log --oneline -3

# 重建 venv
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 前端依赖(用 TUI 才需要)
cd ui-tui && npm install && cd ..
```

## Step 4: 拉坚果云加密分卷

### 4.1 配置 rclone(只第一次)

```bash
# 如果 restore.sh 还没从源码拉下来,先用 hermes_setup_jianguoyun.sh
# 如果已经 git clone 了,直接用 ~/.hermes/hermes-agent/scripts/hermes_setup_jianguoyun.sh
# 如果都还没有,先:
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/hermes_setup_jianguoyun.sh | bash
# 然后输入坚果云账号 + 32 位应用密码
```

### 4.2 下载最新备份

```bash
mkdir -p ~/Desktop/hermes-restore
cd ~/Desktop/hermes-restore

# 看远端有什么
rclone lsf jianguoyun:hermes-backups/ | head -20

# 拉最新一份
LATEST_TS=$(rclone lsf jianguoyun:hermes-backups/ | grep -oE 'hermes-[0-9]+-[0-9]+' | sort -u | tail -1)
echo "拉取: $LATEST_TS"
rclone copy jianguoyun:hermes-backups/ ~/Desktop/hermes-restore/ \
    --include "${LATEST_TS}.*" --progress

# 确认分卷都齐了
ls -lah ~/Desktop/hermes-restore/
```

## Step 5: 跑 restore.sh

```bash
# 把 restore.sh 弄到手(从 git clone 的源码,或直接 curl)
# 选项 A: 用源码
ls ~/.hermes/hermes-agent/scripts/hermes_restore.sh

# 选项 B: 直接 curl
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/hermes_restore.sh -o /tmp/restore.sh
chmod +x /tmp/restore.sh

# 跑(交互式 — 会问 3 个问题)
bash ~/.hermes/hermes-agent/scripts/hermes_restore.sh \
    ~/Desktop/hermes-restore/hermes-*.tar.gz.gpg.part000
```

**会问的 3 个问题**:
1. `确认拼接并解密? (yes/no)` → 输 `yes`
2. `GPG 密码:` → 输**你当初 --keychain-set 时设的密码**(找密码管理器)
3. `目标 .hermes 已存在,继续? (yes/no)` → 输 `yes` (会覆盖刚 git clone 的空 hermes-agent 之外的目录)

**自动健康检查**:
```
✓ config.yaml
✓ state.db (391M)
✓ .env
✓ skills/ (68 个技能)
✓ memory
✅ 还原完成!
```

## Step 6: 验证(必须,不能信 title 报成功)

```bash
# 跑 verify 脚本(已经写好,在 skills 目录)
python3 ~/.hermes/hermes-agent/skills/devops/hermes-portable-backup/scripts/verify_hermes_backup.py \
    ~/Desktop/hermes-restore/ --keychain

# 或手动 5 步:
diff -q ~/Desktop/hermes-restore-test/config.yaml ~/.hermes/config.yaml
# (无输出 = 完全一致)

# SQLite 关键计数
python3 -c "
import sqlite3
c = sqlite3.connect('$HOME/.hermes/state.db')
print('sessions:', c.execute('SELECT COUNT(*) FROM sessions').fetchone()[0])
print('messages:', c.execute('SELECT COUNT(*) FROM messages').fetchone()[0])
"
# 应 = 你记忆中的数字(如 2166 / 123126)
```

## Step 7: 重建自动备份

```bash
# 1. 把 GPG 密码写到新电脑的 Keychain
bash ~/.hermes/scripts/hermes_backup.sh --keychain-set

# 2. 重新挂载 launchd 周备份 plist
cat > ~/Library/LaunchAgents/com.hermes.weekly-backup.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key><string>com.hermes.weekly-backup</string>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Weekday</key><integer>0</integer>
        <key>Hour</key><integer>3</integer>
        <key>Minute</key><integer>0</integer>
    </dict>
    <key>ThrottleInterval</key><integer>43200</integer>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>-l</string>
        <string>-c</string>
        <string>/Users/aimac/.hermes/scripts/hermes_backup.sh >> /Users/aimac/.hermes/.backups/launchd.log 2>&1</string>
    </array>
    <key>WorkingDirectory</key><string>/Users/aimac</string>
    <key>StandardOutPath</key>
    <string>/Users/aimac/.hermes/.backups/launchd.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/aimac/.hermes/.backups/launchd.log</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin</string>
        <key>HOME</key><string>/Users/aimac</string>
        <key>HERMES_HOME</key><string>/Users/aimac/.hermes</string>
    </dict>
</dict>
</plist>
EOF

launchctl load ~/Library/LaunchAgents/com.hermes.weekly-backup.plist
launchctl list | grep hermes  # 确认加载
```

## Step 8: 立即手动备份一次(双保险)

```bash
bash ~/.hermes/scripts/hermes_backup.sh
```

这会把"新电脑的环境"打成第一份新时间戳的备份,后续周日凌晨 3 点 launchd 自动续上。

---

## ⚠️ 验证 6 个关键数字(让你心里有数)

还原成功后,**这 6 个数字应该跟备份前完全一致或近似**:

| 项 | 典型值 | 怎么查 |
|----|--------|--------|
| state.db 大小 | ~391M | `ls -lah ~/.hermes/state.db` |
| sessions 表行数 | 2166 | `sqlite3 ~/.hermes/state.db 'SELECT COUNT(*) FROM sessions'` |
| messages 表行数 | 123,126 | `sqlite3 ~/.hermes/state.db 'SELECT COUNT(*) FROM messages'` |
| skills 数量 | 68 | `ls ~/.hermes/skills/ | wc -l` |
| .env 变量数 | 79 | `grep -c '^[A-Z_]*=' ~/.hermes/.env` |
| hermes-agent commit | f66a929 或最新 | `cd ~/.hermes/hermes-agent && git rev-parse HEAD` |

如果差很多(尤其 sessions/messages 少一截),说明还原不完整,要排查。

---

## 🆘 最坏情况(没备份 / 密码丢了)

### Case A: 坚果云没备份
**结果**:
- ❌ state.db 全丢(对话记忆)
- ❌ skills 全丢(你改过的技能)
- ⚠️ hermes-agent 源码能 git clone 重新装
- ⚠️ 如果你开过 macOS Time Machine,可能从那救

**预防(现在就该做)**:
1. TeraBox / 123 云盘 / 阿里云盘 **双备份**
2. 加密 U 盘离线备份
3. `state.db` 单独 export 到 GitHub 私有仓(每周 cron)

### Case B: GPG 密码丢了
**结果**:加密包**完全无解**(AES-256 暴力破解到宇宙毁灭)

**唯一救法**:
- 找最近一次新电脑刚启动时 Keychain 的导出
- 或翻你**纸质密码本**

**预防**:
- GPG 密码**必须**写在 1Password / Bitwarden
- 不写就当裸奔

### Case C: .env 里的 API key 全丢
**结果**:需要逐个去平台重申请

**时间成本**:
- DeepSeek / GLM / 豆包 / Gemini:10 分钟/个
- Telegram Bot (@BotFather):5 分钟
- 飞书/微信/QQ 机器人:30 分钟/个
- 百度网盘/阿里云盘 API:15 分钟/个

**总成本**:1-2 小时,看平台数

**预防**:`.env` 单独 GPG 加密一份,存到 1Password Secure Note(不是文档,是 Secure Note 类型)。

---

## 📋 完整保险 checklist(4 件都做了才算真稳)

- [ ] GPG 密码写在密码管理器(1Password / Bitwarden)
- [ ] `.env` 单独 GPG 加密后存到 1Password Secure Note
- [ ] 加密 U 盘离线备份一份
- [ ] 异地云盘(TeraBox / 123 网盘)做第二份
- [ ] **把这份 SOP + 坚果云账号 + GPG 密码 + hermes 仓地址告诉一个你信任的人**(纸质/保险柜/1Password 紧急访问)

最后一条最关键:硬盘坏了 = 一切电子设备都可能一起坏(火灾/水灾/地震)。**异地、异人、异介质**三保险才能真正睡得着。

---

## 关键提醒(给 AI 代理)

恢复 SOP 涉及**大量不可逆操作**(`rm -rf ~/.hermes`、覆盖现有数据)。**用户亲自跑**最稳,AI 代理:

- ❌ 不要替用户跑 `rm -rf` 或覆盖操作
- ✅ 可以生成脚本让用户自己跑
- ✅ 可以解释每一步在干什么、为什么
- ✅ 跑完后让用户**亲自**验证 6 个关键数字

详见 `verification-before-reporting` skill — "恢复"类操作"看 log 报成功"远远不够。
