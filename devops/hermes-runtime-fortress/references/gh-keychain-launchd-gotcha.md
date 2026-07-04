# gh keychain + launchd 认证失效陷阱（2026-07-04 落地，2026-07-04 更新）

## 现象

```bash
# 交互终端（用户 GUI session）—— 正常
$ gh auth status
✓ Logged in to github.com account Buluhanke (keyring)   ← 表面 OK
$ gh api user --jq '.login'
Buluhanke                                              ← 实际能用

# launchd 环境 —— gh api 失败
$ bash ~/.hermes/scripts/hermes_backup_github_push.sh
✗ gh 没登录                                           ← 但 launchd log 里 gh status 也显示 OK

# 验证真实 token 状态
$ gh auth token
no oauth token found for github.com                    ← 根因在这里！
$ security unlock-keychain -p "" ~/Library/Keychains/login.keychain-db
security: SecKeychainUnlock login.keychain-db: exit 51  ← keychain 锁了
```

## 根因

`gh auth status` 读取 `~/.config/gh/hosts.yml` 元数据（user 名字段），**不验证 keychain 里的 token 是否仍有效**。

```
hosts.yml:     github.com:\n    user: Buluhanke     ← gh auth status 靠这个显示 OK
keychain:     token 已失效（密码变了 / keychain 需要 unlock）← gh api 查这里 → 401
```

launchd 进程运行在独立 session 环境里（无 GUI keychain 访问），token 查 keychain → 401。

## 诊断 SOP（按顺序执行）

```bash
# 1. gh auth status — 读 hosts.yml，显示 OK 不可靠
gh auth status

# 2. gh auth token — 才是真实 token 状态
gh auth token
# 根因现象: "no oauth token found for github.com"

# 3. gh api user --jq '.login' — 最终验证
gh api user --jq '.login'
# 根因现象: 401 Requires authentication

# 4. security unlock-keychain — 查 keychain 是否锁了
security unlock-keychain -p "" ~/Library/Keychains/login.keychain-db
# 根因现象: exit 51 "The user name or passphrase...not correct"

# 5. env | grep -i "GH_\|GITHUB_" — 找环境变量里的 PAT
env | grep -i "GH_\|GITHUB_"
# 期望: GITHUB_MCP_TOKEN=gho_... 或 GITHUB_PERSONAL_ACCESS_TOKEN=gho_...（40位）
```

## 修复方案（优先级: A > B > C）

### 方案 A（本次实测成功）：用环境变量里的 PAT 兜底 ✅

发现：Hermes 运行环境中 `GITHUB_MCP_TOKEN`（40位 PAT）已存在于进程环境变量，脚本直接 `export GH_TOKEN` 即可绕过 keychain，**无需用户操作**。

**脚本修改**（在 `hermes_backup_github_push.sh` 开头 `export PATH` 后加）：
```bash
export PATH="/opt/homebrew/bin:$PATH"

# 优先用环境变量里的 PAT（launchd 环境下 keychain 读不到）
if [ -n "$GITHUB_MCP_TOKEN" ] && [ -z "$GH_TOKEN" ]; then
    export GH_TOKEN="$GITHUB_MCP_TOKEN"
elif [ -n "$GITHUB_PERSONAL_ACCESS_TOKEN" ] && [ -z "$GH_TOKEN" ]; then
    export GH_TOKEN="$GITHUB_PERSONAL_ACCESS_TOKEN"
fi
```

**验证**：
```bash
GH_TOKEN="$GITHUB_MCP_TOKEN" gh api user --jq '.login'
# 期望: Buluhanke（exit 0）
# 之前: "no oauth token found" 或 401
```

### 方案 B：给 launchd plist 补 GH_TOKEN（让定时任务也能用）

脚本 fix 后，launchd 任务本身也需要能读到 token（脚本内 export 只影响子进程）。用 PlistBuddy 追加：

```bash
/usr/libexec/PlistBuddy -c "Add :EnvironmentVariables:GH_TOKEN string" \
    ~/Library/LaunchAgents/com.hermes.weekly-backup.plist
/usr/libexec/PlistBuddy -c "Set :EnvironmentVariables:GH_TOKEN $GITHUB_MCP_TOKEN" \
    ~/Library/LaunchAgents/com.hermes.weekly-backup.plist
# reload
launchctl unload ~/Library/LaunchAgents/com.hermes.weekly-backup.plist
launchctl load ~/Library/LaunchAgents/com.hermes.weekly-backup.plist
```

### 方案 C：重新登录 gh（需用户操作，有浏览器依赖）

```bash
gh auth refresh --hostname github.com
# 需用户完成浏览器 Device Flow 授权
```

---

## 决策树

```
env 有 GITHUB_MCP_TOKEN?
  → YES: 脚本加 export GH_TOKEN (方案 A) → 验证 gh api → plist 加 GH_TOKEN (方案 B)
  → NO:  方案 C（需用户授权）
```

## 备份 repo 监控（2026-07-04 新增：git 可看层断了 1 个月才发现）

`hermes-backup-v2` 的 skills 备份层断更 1 个月才发现，因为每次只看 `github-push.log`（加密 `.gpg` 层），没查 `hermes-backup-v2` commits。

**新增必跑项** — 每次检查备份时并行查两个仓库：
```bash
# 加密整盘层（hermes-backup）
gh api repos/Buluhanke/hermes-backup/git/matching-refs/heads/backup- \
  --jq '.[].ref' 2>/dev/null | sort -r | head -1

# git 可看 skills 层（hermes-backup-v2） ← 容易忽略
gh api repos/Buluhanke/hermes-backup-v2/commits \
  --jq '.[0].commit.author.date' 2>/dev/null
# 对比今天日期：> 30 天 → 备份已断
```

## 关联

- `hermes-runtime-fortress` SKILL.md Section 六 — 备份系统监控 SOP
- `launchd-plist-gotchas.md` — plist 字段常见坑
