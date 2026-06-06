---
name: hermes-portable-backup
description: |
  把 Hermes 完整状态（state.db、skills、scripts、config、memory、cron、plugins、.env 等）加密备份到云端（坚果云 WebDAV / rclone crypt），换新电脑后下载+解密即可完整恢复。覆盖"换电脑=零损失"这个 class 的工作流——3 步核心（哪些必须备份/怎么加密+分卷/怎么恢复）、5 个产品对比（坚果云 / iCloud / OneDrive / TeraBox / 123/阿里/百度网盘）、4 个实战坑（macOS tar --transform 不支持、set -e + 函数捕获、SQLite WAL 残骸、Keychain 存密码）、1 个 30 分钟"硬盘全坏"灾难恢复 SOP。

  触发词：
  - "换电脑" / "换台电脑" / "新电脑" / "云端同步" / "异地备份"
  - "备份 Hermes" / "hermes 备份" / "全部数据同步上去" / "下载回来跟当下一模一样"
  - "云盘选哪个" / "坚果云" / "iCloud" / "阿里云盘" / "OneDrive" / "百度网盘" / "TeraBox" / "123 云盘" / "免费云盘" / "其他云盘"
  - "加密备份" / "GPG 对称加密" / "rclone crypt" / "WebDAV"
  - "hermes_backup" / "hermes_restore" / "hermes_setup_jianguoyun"
  - "GitHub 备份" / "gh release" / "github 仓备份" / "git 仓同步"
  - "硬盘坏了" / "硬盘坏了怎么办" / "电脑坏了" / "重装系统" / "新电脑怎么恢复" / "灾难恢复" / "disaster recovery"

  不要用于：
  - 单文件备份/恢复（用 git 或 tar 临时打）
  - hermes-agent 源码本身（用 git clone + pip install）
  - venv/node_modules 等可重建缓存（不要备份）
version: 2026-06-06.4
---

## 轻量模式（2026-06-06 新增 — 用户明确表达"想要简单"）

**触发信号**：用户问"能直接打个压缩包上传到 X 云盘吗" / "不想折腾 rclone" / "给我个最简单的方案"。

**当主备份方案（rclone + WebDAV + 100M 分卷 + 远端自动保留）对用户来说**太重**时，**退一步用轻量模式**：

- ✅ 跳过 rclone / WebDAV / 32 位应用密码这一整套
- ✅ 跑一个命令 → 输出一个 115MB 的 .gpg 文件到桌面
- ✅ 用户**手动**拖到任何云盘（阿里云盘 / 百度网盘 / iCloud Drive / OneDrive 都行，不依赖 WebDAV）
- ❌ 代价：每周 2 分钟手动拖一下；不会自动

**实现**：`templates/hermes_backup_simple.sh`（不是分卷，是一个完整 .gpg 文件输出到指定目录）
- `--set-password`：首次设 GPG 密码到 Keychain
- `--output ~/Desktop/`：输出到桌面（默认）
- `--dry-run`：看会备份什么
- `--no-encrypt`：不加密（**不推荐**，除非用户信得过网盘）

**和主方案对比**：

| 维度 | 轻量模式 | 主方案（rclone） |
|------|----------|------------------|
| 操作步骤 | 1 步：拖文件 | 5 步：rclone config + app 密码 + 写 plist |
| 依赖 | 浏览器/客户端 | rclone、Keychain、WebDAV |
| 自动化 | ❌ 手动 | ✅ launchd 自动 |
| 文件大小 | 单文件 115MB | 100M 分卷 × 2 |
| 适合谁 | 个人、轻度、不想折腾 | 重度、运维控、长期维护 |
| 适用云盘 | **任何**（阿里/百度/iCloud/OneDrive） | 仅 WebDAV（坚果云） |

**用户偏好硬规则**（2026-06-06 拍板）：
- 用户问"哪个云盘" → **先推 WebDAV 方案（坚果云）**作为首选，给"零成本 + 国内 + 自动化"
- 用户拒绝 / 说"想简单" / "不想搞 rclone" → **立刻退到轻量模式**，不重述 rclone 优势
- 不要再问"要不要 / 想不想自动化"——**用户没问就是接受手动**
- **永远不要说"我推荐 X"**之后用户说"想简单"还坚持 X——直接切方案
- **"如果是只有那么大都可以完全走 github"**（2026-06-06 用户原话）→ **立刻停掉坚果云 / rclone 配置**，全切到 GitHub 模式。115MB 在 GitHub Release 单文件 2GB 限制内、git push 拆分 50MB × 3 卷、gh CLI 已登录用户零成本。**不要再纠结 WebDAV 1GB 月流量**——用户问"X 能不能干"已经暗示他想要 X

**KEEP_COUNT 选型**（2026-06-06 用户实际选）：
- 用户场景：坚果云免费版 + 每周备份 + 想要最简
- **KEEP_COUNT = 4**（不是默认的 7）：~516MB 远端 < 1GB 免费容量
- 备份频率：每周 1 次（launchd Weekday=0 周日 03:00），~130MB × 4 = ~520MB/月 流量
- 如果用户**升级坚果云专业版（¥199/年）**：KEEP_COUNT 可改 7 / 10，频率可改 daily

## 轻量模式的还原（不同云盘的差异）

无论用户上传到哪个网盘，**还原流程都一样**——网盘只负责"存放 + 下载"，不参与加密/分卷逻辑：

```bash
# 1. 从网盘下载 hermes-backup-XXX.gpg 到新电脑
# 2. 解密
gpg -d hermes-backup-XXX.gpg > /tmp/hermes.tar.gz
# 3. 解压
tar --strip-components=1 -xzf /tmp/hermes.tar.gz -C ~/.hermes
# 4. git clone hermes-agent + 重建 venv（见 disaster-recovery-sop.md）
```

**省事之处**：不需要在新电脑配 rclone / WebDAV / 拉分卷拼卷。

# Hermes Portable Backup — 换电脑=零损失

把 ~/.hermes 完整状态加密同步到云端，新电脑下载+解密即可恢复——这是 class-level 工作流，不是某个 session 的一次性方案。

## 为什么是 class

Hermes 的"价值" = `state.db` (12万条消息历史) + skills (189MB 已固化知识) + config.yaml (你的偏好) + memory_store.db (长期记忆) + .env (API key) + cron 任务 + 自定义脚本。换电脑就完蛋了，不是某个文件可以丢。`hermes-agent/` 本来就是 git 仓库（origin = NousResearch/hermes-agent），换电脑 `git clone` + `pip install` 重建 venv 就行，**不用备份**。

## 设计原则（2026-06-06 用户拍板）

**核心原则 1：一键恢复 = 设计目标，不是事后补丁**
- 用户原话（2026-06-06）："对的就应该有个索引，比如我新电脑安装好了 hermes 配好模型，直接告诉它一个索引它就能去完成"
- **含义**：任何"备份/恢复"方案必须以"**用户从新机器上跑一行命令就能完成**"为**验收标准**
- 验收清单：
  1. 恢复命令**必须**能贴到任何 macOS 终端直接跑（不需要预先装 rclone / gh / python）
  2. 命令**必须**自带环境检测 + 装缺的工具（不依赖用户已经装过什么）
  3. 命令**必须**指向**单一入口**（不是 5 步教程，是 1 行）
  4. 命令**必须**能离线写在纸上/记在脑子里（不需要"先打开网页看 README"）
- ❌ 反例：`curl -L https://github.com/.../raw/.../restore.sh | bash`（raw 缓存 5+ 分钟可能 404，2026-06-06 实测）
- ✅ 正例：`gh api repos/<user>/<repo>/contents/<file> --jq .content | base64 -d | bash`（API 无缓存，永远能拿到）

**核心原则 2：真实验证 > 报告成功**
- 用户说"我保持怀疑的态度" → 立刻**实地打开 .gpg 解出来**，列 sessions/messages/skills/scripts 实际数字
- **不允许**用"看 log 报成功" / "看 title 报成功" 打发用户的疑问
- 详细规则见 `verification-before-reporting` skill

**核心原则 3：删/清理前/后给对账表**
- 用户对"删/清理" scope 极度敏感
- 任何 `rm -rf` 前**必给**对账表（删了什么+什么没动）
- **不要**主动列 11+12 行大表（用户会以为是扩大战果）
- 详细规则见 `hermes-memory-hygiene` skill 的"破坏性操作"段

**核心原则 4：替用户跑"删"类命令会被 Hermes 安全闸拦**
- 详见坑 4.6
- AI 代理**写自包含脚本**让用户自己跑，不替用户 rephrase "删" 类命令

## 核心 3 步工作流

### Step 1：数据分级（什么必备份 / 什么不备份 / 什么加密）

| 类别 | 处理 | 理由 |
|------|------|------|
| state.db (391M) | ✅ 备份 | 12万条消息历史，**丢了 = 你和 Hermes 的全部对话记忆没了** |
| skills/ (189M) | ✅ 备份 | 你自己写/改的技能，git 里没有 |
| config.yaml (16K) | ✅ 备份 | 你的所有偏好和皮肤 |
| .env (4K) | ✅ **加密** | 30 个 API key，**绝对不能明文上云** |
| memory_store.db (4M) | ✅ 备份 | 长期记忆 |
| cron/jobs.json (3K) | ✅ 备份 | 你的定时任务 |
| profiles/ (9M) | ✅ 备份 | 你 profile 下的设置 |
| plugins/ (1M) | ✅ 备份 | 你的插件 |
| scripts/ (1M) | ✅ 备份 | 你自己的脚本 |
| lsp/ (99M) | ❌ 不备份 | 装回来成本低 |
| bin/ (10M) | ❌ 不备份 | 装回来成本低 |
| hermes-agent/ (4.3G 含 venv) | ❌ 不备份 | `git clone + pip install` 重建 |
| logs/ (24M) | ⚠️ 可选 | 历史日志，重建无意义 |
| screenshots/ (5M) | ❌ 不备份 | 临时截图 |
| cache/ / .cache/ | ❌ 不备份 | 缓存 |
| mcp-chrome-extension/ (37M) | ❌ 不备份 | 重新装 |

**判定原则**：
- 丢了 = 痛苦 → 备份
- 丢了 = 重装 5 分钟 → 不备份
- 含 API key / token / cookie → 必加密

### Step 2：打包 + 加密 + 分卷

**核心范式**（macOS + Linux 通用）：

```bash
# 1. SQLite 先做 WAL checkpoint, 防止 .db + .db-wal 拆分导致还原时损坏
python3 -c "
import sqlite3
for db in ['state.db', 'memory_store.db']:
    c = sqlite3.connect(db)
    c.execute('PRAGMA wal_checkpoint(TRUNCATE)')
"

# 2. 打包(BSD tar 不支持 --transform, 用相对路径 + 还原时 --strip-components)
tar \
    --exclude=.hermes/hermes-agent \
    --exclude=.hermes/lsp \
    --exclude=.hermes/bin \
    --exclude=.hermes/cache \
    --exclude=.hermes/.cache \
    --exclude=.hermes/screenshots \
    --exclude=.hermes/mcp-chrome-extension \
    --exclude=.hermes/.backups \
    --exclude=.hermes/logs \
    --exclude=.hermes/.git \
    --exclude=.hermes/skills/.git \
    --exclude=.hermes/skills/.hub \
    --exclude=.hermes/skills/.curator_backups \
    --exclude=.hermes/models_dev_cache.json \
    -czf hermes-$(date +%Y%m%d-%H%M%S).tar.gz \
    .hermes

# 3. GPG 对称加密 (AES-256, 几乎不增加体积)
gpg --batch --yes --pinentry-mode loopback --passphrase "$PW" \
    --cipher-algo AES256 --compress-algo none \
    --symmetric --output hermes.tar.gz.gpg \
    hermes.tar.gz

# 4. 分卷 100M (坚果云 WebDAV 单文件 500M 限制, 留 5x 余量)
split -b 100M -d -a 3 hermes.tar.gz.gpg hermes.tar.gz.gpg.part
```

**实测体积**（2026-06-06 Mac mini M4 24GB 上 ~5.5GB 原始 .hermes）：
- 压缩后：~129MB（gzip 对 SQLite 几乎无效，但其他能压 90%）
- GPG 加密后：~114MB（不增体积）
- 分卷：100M + 14M

### Step 3：上传 + 验证 + 还原

```bash
# 1. 上传(用 rclone 增量同步, 实际只传 diff)
rclone copy /path/to/encrypted/ jianguoyun:hermes-backups/ \
    --transfers 2 --checkers 4 --progress

# 2. 换电脑后还原
mkdir -p ~/.hermes
rclone copy jianguoyun:hermes-backups/ /tmp/hermes-restore/
cat /tmp/hermes-restore/hermes-*.tar.gz.gpg.part* | \
    gpg --batch --passphrase "$PW" --decrypt > hermes.tar.gz
tar --strip-components=1 -xzf hermes.tar.gz -C ~/.hermes
chmod 700 ~/.hermes
chmod 600 ~/.hermes/.env

# 3. 重建 hermes-agent
git clone https://github.com/NousResearch/hermes-agent.git ~/.hermes/hermes-agent
cd ~/.hermes/hermes-agent
python3.11 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cd ui-tui && npm install
```

## 4 个必须知道的坑（实战沉淀）

### 坑 1：macOS BSD tar 不支持 `--transform`

**症状**：`tar: Option --transform is not supported`
**原因**：macOS 默认 `tar` 是 BSD 版（libarchive），不是 GNU tar
**后果**：用 `s|^\.hermes|hermes-home|` 想改路径前缀会失败
**修法**：
- ❌ 不要用 `--transform`
- ✅ 用相对路径打包（`tar -czf out.tar.gz .hermes`），包内路径是 `.hermes/...`
- ✅ 还原时 `tar --strip-components=1` 去掉 `.hermes/` 这一层

### 坑 2：`set -euo pipefail` + bash 函数捕获的 stdout 污染

**症状**：`local x=$(my_func)` 拿到一堆乱七八糟的输出，路径错了下游都失败
**原因**：`my_func` 里 `log "..."` 默认走 stdout，`echo "$out"` 也走 stdout，`$()` 一并捕了
**修法**：
- ✅ 函数里所有日志 `>&2` 走 stderr：`log "..." >&2`
- ✅ 只有**真正要返回的值**走 stdout：`echo "$out"`
- 详见 `references/set-e-pipefail-pitfalls.md`

**配套坑**：`{ ... } > file` group command 里如果用 `sort | head -50`，head 提前关 pipe → sort 收到 SIGPIPE → 在 `set -euo pipefail` 下整 group 失败 → 整脚本 exit。**修法**：先把数据写到 tmp file，再 `sort tmp | head -50`。

### 坑 3：SQLite 的 WAL 残骸（不打包 .db-wal 会丢新数据）

**症状**：备份的 state.db 还原后读不到最近的对话
**原因**：SQLite WAL 模式下，新写入先到 .db-wal 文件，定期 checkpoint 才合并回 .db。**如果只备份 .db 不备份 .db-wal，最近几分钟的写入会丢**
**修法**：
- ✅ 备份前先 `PRAGMA wal_checkpoint(TRUNCATE)` 把 WAL 合并回 .db
- ✅ 然后**只打包 .db**，不打包 .db-wal（避免半写状态）
- 完整代码见 `templates/wal-checkpoint.py`

### 坑 4：GPG 密码管理（不写在脚本里、也不每次问）

**症状**：把 GPG 密码 `echo "xxx"` 写在 backup.sh 里 → 密码泄露到 git/云/聊天记录
**修法**：
- ✅ 第一次跑 `hermes_backup.sh --keychain-set` 写入 macOS Keychain
- ✅ 之后 `security find-generic-password -s com.hermes.backup.gpg -a hermes-archive -w` 取密码
- ✅ 脚本只在用户没设过 Keychain 时才报错"先跑 --keychain-set"
- 完整代码在 `templates/gpg-keychain-helper.sh`

**配套**：写**第二个脚本**（如 `hermes_backup_simple.sh`）要拿**同一个密码**时，做**双 keychain 兜底**：
```bash
# 优先找新脚本的 keychain, 找不到就用老脚本的(兼容历史)
pw=$(security find-generic-password -s "com.hermes.backup.simple" -a "hermes-simple" -w 2>/dev/null) || \
pw=$(security find-generic-password -s "com.hermes.backup.gpg" -a "hermes-archive" -w 2>/dev/null)
```
否则用户换脚本时 Keychain 找不到密码会误以为没设。

### 坑 4.5：state.db 预存 corruption（integrity_check 报错但不是脚本问题）

**症状**：跑 `PRAGMA integrity_check` 报 `*** in database main *** Tree X page Y...` 各种 invalid page
**原因**：SQLite WAL 文件没合并，page pointer 错乱（不一定真损坏，**先看 sessions/messages 数量对不对**）
**修法**：
- ✅ 备份脚本**不要**因为 integrity_check 报错就退出
- ✅ 用 try/except 包住 checkpoint，失败只 warn 不 fatal
- ✅ 备份脚本**容忍** state.db 预存 corruption，照常打包（备份的目的就是保住当前快照）
- 还原后**用户手动** `sqlite3 state.db ".recover"` 或 `VACUUM INTO` 修复，或接受现状

**为什么不能自动修**：自动修复 SQLite 是高风险操作（`recover` 会丢损坏 page 的数据），**让用户自己决定**。

### 坑 4.6：AI 代理替用户跑 `rm -rf ~/.hermes/.backups/...` 会被 Hermes 安全闸拦

**症状**：`Command Approval Required` / `BLOCKED: User denied this command`
**原因**：Hermes 安全闸 v2（2026-06-06 验证）对"删 staging/backup 内容"的命令也敏感
**修法**：
- ❌ AI 代理**不要 rephrase** 同一目标（"清理 staging" → "删除旧的 .gpg" → ...）闸门会持续拦
- ❌ AI 代理**不要**说"用户说 yes"绕过——闸门是硬规则
- ✅ AI 代理**写一个**自包含的验证脚本（如 `verify_backup.sh`），让用户**自己复制粘贴跑**
- ✅ 验证脚本里**只删**自己创建的临时文件（如 `/tmp/hermes-roundtrip`），不碰 ~/.hermes
- 详见 `references/disaster-recovery-sop.md` 末尾"给 AI 代理的提醒"

## 5 步真实验证（"新电脑"模拟）

光打包不验证就是空炮。**必须**做 5 步：

```bash
# 1. 备份原 .hermes
mv ~/.hermes ~/.hermes.original.bak

# 2. 模拟新电脑(空目录)
mkdir ~/.hermes

# 3. 跑完整 backup → 拿到加密分卷
hermes_backup.sh  # 默认上传, 或 --no-upload

# 4. 用分卷 + 密码 还原到 空 .hermes
expect -c "
spawn hermes_restore.sh /tmp/hermes-backup/hermes-*.gpg.part000
expect \"确认拼接并解密?\" { send \"yes\r\" }
expect \"GPG 密码:\" { send \"$PW\r\" }
expect \"继续?\" { send \"yes\r\" }
expect eof
"

# 5. 关键文件 diff 对比
diff -q ~/.hermes.original.bak/config.yaml ~/.hermes/config.yaml
diff -q ~/.hermes.original.bak/.env ~/.hermes/.env
ls ~/.hermes/skills/ | wc -l   # 应等于原始
python3 -c "import sqlite3; c=sqlite3.connect('~/.hermes/state.db'); print(c.execute('SELECT COUNT(*) FROM sessions').fetchone()[0])"
# 应 = 原始 sessions 数

# 6. 还原原 .hermes(测试用, 不留测试环境)
rm -rf ~/.hermes
mv ~/.hermes.original.bak ~/.hermes
```

**实测（2026-06-06）**：第一次跑下来 4770 个文件、config.yaml 完全一致、68 个 skills 完整、state.db 391M 还原后 sessions 2166 / messages 123126 全部。

## 存储选型

### 1 个原则：**WebDAV 决定能不能自动化**

"换电脑一键拉回来" = 零手动操作 = 必须支持 rclone = **必须支持 WebDAV（或 S3 兼容 API）**。

| 选项 | 5GB 全量 | 增量 | 加密 | 国内速度 | WebDAV / rclone | 价格 | 适用 |
|------|----------|------|------|----------|-----------------|------|------|
| **坚果云 WebDAV** | ✅ | ✅ | ✅ GPG + 可选 rclone crypt | ⭐⭐⭐⭐⭐ 快 | ✅ 原生 WebDAV | 免费 1GB/月、专业 ¥199/年 30GB/月 | **首选**（国内唯一免费 + WebDAV）|
| iCloud Drive | ✅ | ✅ | ✅ E2EE | ⭐⭐⭐⭐⭐ | ⚠ rclone 1.65+ 走 iclouddrive | 5G 免费 / 2T ¥21/月 | Apple 生态 |
| OneDrive | ✅ | ✅ | ✅ E2EE (个人版) | ⭐⭐⭐ 中 | ✅ rclone onedrive | 5G 免费 / 1T ¥398/年 | 海外 |
| **TeraBox** | ✅ 1TB 免费 | ❌ 手动 | 必须 GPG(隐私条款允许扫描) | ⭐⭐⭐ 需代理 | ❌ 无 | 免费 | **异地兜底**(每月手动) |
| **123 云盘** | ✅ 2TB | ❌ 手动 | ❌ | ⭐⭐⭐ | ❌ 无 | 免费 | 不推荐(纯文档可) |
| **阿里云盘** | ✅ 100G | ❌ | ❌ | ⭐⭐⭐ | ❌ 无 | 免费 | 不推荐 |
| **百度网盘** | ⚠ 限速 | ❌ | ❌ | ⭐⭐ | ❌ 无 | 免费 | **最不推荐**（限速+风控） |
| **GitHub 私有仓 + Release** | ✅ 无限 | ✅ | ✅ GPG + 仓私有 | ⭐⭐ | ⚠ git 不是 WebDAV | 免费 | 用户已有 GitHub 习惯时首选（详见下方 GitHub Release 模式节） |
| **GitHub 公开仓** | ✅ 无限 | ✅ | ❌ **公开 = API key 裸奔** | ⭐⭐ | ⚠ | 免费 | **绝对不推荐** |
| S3 / R2 | ✅ 10G 免费 | ✅ | ✅ rclone crypt | ⭐⭐ 慢 | ✅ S3 | $0.015/GB/月 | 海外/折腾 |

**详细对比（含 4 个国内免费盘的 WebDAV 缺失原因）**见 `references/free-cloud-alternatives.md`。

**核心结论**：国内"免费 + WebDAV + 能用"**只有坚果云**。其他免费盘（TeraBox/123/阿里/百度）容量大、速度快，但**没 WebDAV = 不能 rclone 自动化 = 必须手动上传 = 容易忘**。

**我的推荐（用户实际场景，2026-06-06）**：
- 主力（自动化）：**坚果云免费版**（每周 1 份 ~130MB = ~520MB/月 < 1GB 免费额度），或专业版 ¥199/年 30GB/月
- 兜底（异地）：**TeraBox 1TB**，每月手动上传一次（详见 `references/free-cloud-alternatives.md`）
- 双轨（小文件版本化）：**GitHub 私有仓**放 scripts/skills/cron
- **不推荐自建 S3 / R2**：国内速度慢 + 配置复杂
- **绝对不推荐百度网盘**：限速 100KB/s + 账号风控 + 无 WebDAV

## GitHub Release 模式（git push 失败时的替代）

**触发场景**：
- 用户已经有 GitHub 仓 / 习惯用 GitHub 备份
- rclone / 坚果云 / 阿里云盘**都不想用**
- 想要"git 仓 + 加密包"的版本控制感

**为什么不用 `git push` 而用 `gh release create`**：
- `git push` 推 50MB+ 单文件会撞 `RPC failed; curl 16 Error in the HTTP2 framing layer`（**macOS 上很常见**，2026-06-06 实测 30MB 都失败）
- 即使启用 `git config http.version HTTP/1.1` 也救不回来
- Git LFS 要重新配 + LFS 配额 1GB 免费不够
- **`gh release create` + release asset 上限 2GB/文件**，绕开 git 协议层

**核心流程**：
```bash
# 1. 探测 gh 登录 + 仓存不存在, 不存在就 --private 创建
gh api user --jq '.login'                          # 拿用户名
gh api repos/<user>/<repo> --jq '.name'            # 探仓(用 api 不用 gh repo view,更稳)
gh repo create <repo> --private                    # 创建私有仓

# 2. 探测 default_branch(用户老仓可能是 master 不是 main)
gh api repos/<user>/<repo> --jq '.default_branch'

# 3. 跑 hermes_backup_simple.sh 生成 .gpg, 推 release
gh release create "backup-$(date +%Y%m%d-%H%M%S)" \
    --repo <user>/<repo> \
    --title "Backup YYYYMMDD-HHMMSS" \
    --notes "GPG encrypted Hermes backup" \
    ./hermes-backup-XXX.gpg
```

**实测（2026-06-06）**：115MB .gpg 第一次 release 上传成功；后续重复上传同名 115MB 文件偶发 HTTP/2 EOF；小文件稳定。

**5 个新坑**（写 hermes_backup_github.sh 踩出来的）：

### 坑 5：gh release 重复上传同名大文件 = 偶发 HTTP/2 EOF
**症状**：`Post "https://uploads.github.com/.../assets": unexpected EOF`
**原因**：GitHub upload API 对大文件 (50MB+) 的 HTTP/2 帧传输有偶发问题
**修法**：
- 每次备份用**新时间戳**的 tag（如 `backup-20260606-152308`），永远不重名
- 失败重试 3 次（每次 sleep 5 秒），3 次都失败就让用户去网页端手动 upload

### 坑 6：gh 函数返回值被 ANSI 染色后被 `$()` 污染
**症状**：`local x=$(my_func)` 拿到带 `\033[32m` 的字符串
**原因**：`my_func` 里 `green "..."` 走 stdout，`echo "$path"` 也走 stdout，`$()` 一并捕
**修法**：所有日志 `>&2`，只有返回值走 stdout（与坑 2 同源）

### 坑 7：老 GitHub 仓的 default_branch 不一定是 main
**症状**：`git push -u origin main` 失败 `src refspec main does not match any`
**原因**：用户 2024 年前创建的仓默认分支是 `master`
**修法**：用 `gh api repos/<user>/<repo> --jq '.default_branch'` 探

### 坑 8：老 GitHub 仓里残留几个空 commit, 推 README 报非 fast-forward
**症状**：`! [rejected] main -> main (fetch first)`
**原因**：旧 backup 仓里残留 `test` / `remove test` 这种占位 commit
**修法**：用 `gh api "repos/<user>/<repo>/commits?per_page=1" --jq 'length'` 探测，非 0 就 `git push --force`

### 坑 9：函数返回值 vs 日志输出混着, cp 报"identical" 让 set -e 终止
**症状**：`cp src dst` 报 `are identical (not copied)` 返回非 0, `set -e` 让脚本挂
**原因**：cp 报 identical 本身不是错误(同一个文件)，但 bash 严格模式认为失败
**修法**：`cp src dst 2>&1 | grep -v identical || true`，或先 `[ -f dst ] && skip`

### 坑 10：macOS Apple 自带 git 2.15 太老,git push 大文件必撞 HTTP/2 EOF
**症状**：`error: RPC failed; curl 16 Error in the HTTP2 framing layer`（即使 `git config http.version HTTP/1.1` 也救不回来）
**根因**（2026-06-06 调试 breakthrough）：
- macOS `/usr/local/bin/git` = **Apple 自带 git 2.15.0**（2017 年的版本）
- 这个版本对 HTTP/2 帧协议的实现有 bug，**pack-objects 走 HTTP/2 上传大文件必断**
- `GIT_HTTP_VERSION=HTTP/1.1` 在 2.15 上**不生效**（env 变量是 git 2.16+ 才有）
- `git config http.version HTTP/1.1` 在 2.15 上**也不生效**（这个 config 是 git 2.17+ 才有）
**修法**（**Hermes 写 GitHub 推送脚本必须前置**）：
```bash
# 在脚本最顶上 set -euo pipefail 之后立刻写
export PATH="/opt/homebrew/bin:$PATH"
# 然后所有 git/curl/gh 命令都用 homebrew 版本（git 2.53+）
```
**验证**：`which git` 必须是 `/opt/homebrew/bin/git`（不是 `/usr/local/bin/git`），`git --version` 必须是 2.4x / 2.5x。
**症状发现技巧**：看到 `curl 16 Error in the HTTP2 framing layer` + `fetch-pack: unexpected disconnect` + git 版本 2.15 三个同时出现 = **100% 是这个坑**，不是网络。
**`hermes_backup_github_push.sh` / `hermes_backup_github.sh` 已应用此修复**（脚本头加 `export PATH="/opt/homebrew/bin:$PATH"`）。

### 坑 10.5：`gh release upload` 上传 116MB 单文件也偶发 HTTP/2 EOF（坑 5 的扩展）
**症状**：115MB / 116MB 单文件 `gh release upload` 也报 `unexpected EOF`
**根因**：坑 5 说 30MB/50MB 失败，**实际上 116MB 也失败**（2026-06-06 实测），GitHub upload API 对大文件 HTTP/2 帧传输就是不稳
**修法**：
- ✅ 不要依赖 `gh release upload` 上传 100MB+ 文件
- ✅ 改用 **`git push` 拆分 50MB × 3 卷推独立分支**（这是 2026-06-06 跑通的方案）
- ✅ Release 模式留作 **< 50MB 的小备份**（如纯配置 / 纯脚本）

### 坑 11：GitHub 私有仓 `raw.githubusercontent.com` 缓存延迟 5+ 分钟（**新电脑恢复关键坑**）
**症状**：新电脑跑 `curl -sL https://raw.githubusercontent.com/<user>/<repo>/main/hermes_restore_one.sh | bash` 报 **404 Not Found**
**根因**（2026-06-06 实测）：
- 私有仓文件推到 main 后，**raw CDN 有 5-10 分钟缓存**（偶尔更长，老的"不存在"状态会黏住）
- 同一个文件**第一次推完后立刻 curl 经常 404**
- API (`gh api .../contents/<file>`) **不受这个缓存影响**（返回的 `.content` 是 base64 编码的文件本体）
**修法**（**Hermes 一键恢复索引命令必须用这个**）：
```bash
# ❌ 不要用(会 404)
curl -sL https://raw.githubusercontent.com/<user>/<repo>/main/hermes_restore_one.sh | bash

# ✅ 用 gh API(无缓存,永远能拿到)
gh api repos/<user>/<repo>/contents/hermes_restore_one.sh --jq .content | base64 -d | bash

# ✅ 备选 1:先 clone 仓再跑脚本(最稳)
gh repo clone <user>/<repo> /tmp/hb
bash /tmp/hb/hermes_restore_one.sh

# ✅ 备选 2:gh API 落到文件看一眼再跑(能 cat 验证)
gh api repos/<user>/<repo>/contents/hermes_restore_one.sh --jq .content | base64 -d > /tmp/r.sh
cat /tmp/r.sh | head -3    # 验证内容对
bash /tmp/r.sh
```
**症状发现技巧**：`gh api` 拿到 `download_url` 是 raw 路径，**但 raw 路径 404** = 100% 是这个缓存坑。直接换 gh API 就行。
**对新电脑用户的影响**：恢复命令必须发 **3 个备选**（gh API 一行 / gh clone / curl 等缓存刷新），不能只发 curl 一种。

### 坑 12：`expect` 启动 `hermes_restore.sh` 捕获不到 `read -rs` 输入（交互式密码）
**症状**：`expect -c "spawn hermes_restore.sh; expect \"GPG 密码:\" { send \"$PW\\r\" }"` 拿不到正确密码，**GPG 解密失败**
**根因**（2026-06-06 实测）：
- `read -rs` 读 stdin 走的是 **TTY**（不是 stdin pipe）
- `expect` 启动的子进程 stdin 被 expect 重定向到 pseudo-terminal，**`read -rs` 读不到 expect send 的字符串**
- GPG 拿到空密码 → 失败
**修法**：
- ❌ `expect` **不能**可靠喂 `read -rs` 的密码
- ✅ 改用 **`HERMES_BACKUP_PASSPHRASE` 环境变量**（`hermes_restore.sh` 优先 env 取，env 没值才 read）
- ✅ 或者在 restore.sh 加 `--password "$PW"` CLI 参数
- ✅ 或者**让人手输**（但破坏自动化）
**结论**：任何"自动跑 hermes_restore" 的脚本，**不要用 expect**。要么 env 传密码，要么改成非交互。

### 坑 13：launchd plist 的 `<string>` 里 `&` 必须 escape 成 `&amp;`（XML）
**症状**：`plutil -lint ~/Library/LaunchAgents/xxx.plist` 报 `Encountered unknown ampersand-escape sequence at line 33`
**根因**：macOS launchd plist 是 XML 格式，`2>&1` 里的 `&` 是 XML 保留字符，**必须写成 `&amp;`**；`>>` 是 `&gt;&gt;`（虽然实测 `>>` 不报错但 `&` 必报）
**修法**：
```xml
<!-- ❌ 错 -->
<string>/path/to/script.sh >> /var/log/x.log 2>&1</string>
<!-- ✅ 对 -->
<string>/path/to/script.sh &gt;&gt; /var/log/x.log 2&gt;&amp;1</string>
```
**症状发现技巧**：`launchctl load` 没报错（用了缓存的旧 plist），但 `plutil -lint` 报错 → **plist 没真的更新**。每次改 plist **先 `plutil -lint` 再 `unload` + `load`**，否则你以为加载了其实跑的是旧版。
**配套坑**：`launchctl list | grep <label>` 看到 PID ≠ 你期望的 → plist 没真的更新。**先 unload 再 load**。

**KEEP 策略**：每次备份一个新 release，KEEP_RELEASES=4（旧的 `gh release delete` 自动清，参见 `templates/hermes_backup_github.sh`）。

**已知 public 仓隐私风险**：
- 用户 5/31 前有个 `Buluhanke/hermes-config-2026-05` 公开仓（5.8MB）
- **如果 .env 在里面 = 30 个 API key 公开 = 立刻删仓**
- 处理：`gh repo delete <user>/<public-backup-repo> --yes`
- 详见下方 **"GitHub 公开仓隐私风险"独立警示段**

## ⚠️ GitHub 公开仓隐私风险（独立警示）

**核心规则**：**任何含 ~/.hermes 内容的 GitHub 仓都必须是 PRIVATE**。公开 = API key / cookie / 凭据裸奔。

**自检三步**（新用户 / 老用户都跑一次）：
```bash
# 1. 列出自己所有仓, 找出公开的
gh api user/repos?per_page=100 --jq '.[] | select(.private == false) | "\(.full_name)  \(.size)KB  updated=\(.updated_at[:10])  desc=\(.description // \"\")"'

# 2. 看公开仓里有什么文件(可能含 .env / config.yaml)
gh api repos/<user>/<public-repo>/contents/ --jq '.[].name'

# 3. 如果有敏感文件:
#    a) 立刻删仓: gh repo delete <user>/<public-repo> --yes
#    b) 改私有:   gh repo edit <user>/<public-repo> --visibility private --accept-visibility-change-consequences
#    c) 删敏感文件 + 改私有（保守做法）:  gh repo edit ... && git filter-repo ...
```

**如果 `gh repo delete` 报 `403 Must have admin rights / delete_repo scope`**：
```bash
# 原因: gh 的 token 缺 delete_repo scope
# 解决 A: 刷新 token (需要浏览器交互, CLI 跑会超时挂起)
gh auth refresh -h github.com -s delete_repo

# 解决 B: 手动网页删 (5 秒, 永远不超时)
#   1. 打开 https://github.com/<user>/<public-repo>/settings
#   2. 滚到 Danger Zone
#   3. 点 Delete this repository
#   4. 输入 <user>/<public-repo> 确认
```

**用户案例（2026-06-06 Buluhanke）**：
- 4 个 hermes 仓，3 个私有（hermes-backup / hermes-backup-v2 / hermes2026-05），**1 个公开**（hermes-config-2026-05，5.8MB）
- 仓内实际只有 `.gitignore` + `.install_method` + `.update_check` + 空 `skills`，**没 .env**，隐私上没风险
- 但**仍然删**——公开仓原则上一律删，谨慎为先
- 删时 `gh token` 缺 `delete_repo` scope → 让用户**手动网页删**

**预防**：写 backup 脚本时**强制** `--private`：
```bash
gh repo create "$GITHUB_REPO" --private  # 永远不要省略 --private
```

## GitHub Release 模式：gh auth 已就绪的预设

**用户已有 GitHub 习惯时的快速通道**（2026-06-06 Buluhanke 实测）：
- 用户 `gh auth status` 显示 `Logged in to github.com account Buluhanke (keyring)` —— **`gh` 走 macOS Keychain，不用每次输密码**
- 跑 `gh auth refresh -h github.com -s delete_repo` 想加权限时，**会卡住等浏览器**（Hermes 在 headless/CLI 跑不开浏览器，60s 超时挂起）
- **结论**：CLI 模式下能用的权限 = `gh auth login` 时勾的 scope；想加权限只能重新走 OAuth 流程或在网页设置
- **写脚本时**不要假设有 `delete_repo` / `admin:org` 这种破坏性 scope

**默认有权限的 gh 命令**（标准 token scope）：
- `gh release create / upload / delete` — OK
- `gh repo view / edit` — OK（edit 公开→私有 OK）
- `gh api user/repos / repos/.../commits / repos/.../releases` — OK
- ❌ `gh repo delete` — **需要 delete_repo scope（默认没有）**

## 自动化（launchd 每周一次）

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key><string>ai.hermes.weekly-backup</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>/Users/aimac/.hermes/scripts/hermes_backup.sh</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Weekday</key><integer>0</integer>  <!-- 周日 -->
        <key>Hour</key><integer>3</integer>     <!-- 凌晨 3 点 -->
        <key>Minute</key><integer>0</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>/Users/aimac/.hermes/.backups/backup.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/aimac/.hermes/.backups/backup.log</string>
</dict>
</plist>
```

部署：`cp backup.plist ~/Library/LaunchAgents/ && launchctl load ~/Library/LaunchAgents/ai.hermes.weekly-backup.plist`

**关键**：plist 的 `StandardOutPath` **必须**指向 .backups/backup.log，**不要**让脚本自己用 `tee` 双写到同一文件（会双倍行）。详见 `macos-process-lifecycle/references/launchd-bash-logging-pitfall.md`。

**plutil -lint 是 plist 修改后的必经步骤**（详见坑 13）：改了 plist 一定要先 `plutil -lint ~/Library/LaunchAgents/xxx.plist` 看 OK 不 OK，然后 `launchctl unload` + `load`。`launchctl load` 对有语法错误的 plist 不报错（用缓存的旧 plist），会让"以为加载了新版本"但其实跑的是旧版。

**`PATH` 环境变量必须包含 `/opt/homebrew/bin` 在最前**（详见坑 10）：
```xml
<key>EnvironmentVariables</key>
<dict>
    <key>PATH</key>
    <string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin</string>
</dict>
```
不写就用 Apple git 2.15，推送必失败。

## 灾难恢复：硬盘彻底坏了

**完整 30 分钟 SOP**（从零到 Hermes 跑起来）见 `references/disaster-recovery-sop.md`。

**核心 8 步**：
1. 新电脑装 macOS + brew + `python@3.11 node gpg rclone git`
2. 创建同用户名 `aimac`（否则路径全错）
3. `git clone` hermes-agent + 重建 venv（`python3.11 -m venv venv + pip install -r requirements.txt`）
4. 配 rclone + 拉坚果云加密分卷（`rclone copy jianguoyun:hermes-backups/ /tmp/`)
5. 跑 `hermes_restore.sh`（交互式 — 问 GPG 密码）
6. 验证 6 个关键数字（state.db size / sessions / messages / skills 数 / .env 变量数 / hermes-agent commit）
7. 重设 Keychain + 挂回 launchd 周备份
8. 立即手动跑一次 `hermes_backup.sh`（双保险）

**4 件保险 checklist**（GPG 密码进 1Password、`.env` 单独加密、加密 U 盘、TeraBox 异地兜底 + 告诉一个你信任的人）。

**最坏情况**（坚果云丢 + 密码丢）：完全无解 — AES-256 暴力破解到宇宙毁灭。

**给 AI 代理的提醒**：恢复 SOP 涉及大量不可逆操作（`rm -rf ~/.hermes`、覆盖）。**让用户亲自跑**，不要替用户跑。AI 可以解释、写脚本、引导，但**不能"看 log 报成功"就完事**（详见 `verification-before-reporting`）。

## 配套脚本

| 脚本 | 路径 | 用途 |
|------|------|------|
| `hermes_backup.sh` | `~/.hermes/scripts/` | 主备份脚本(SQLite checkpoint + tar + GPG + split + rclone) |
| `hermes_backup_simple.sh` | `~/.hermes/scripts/` | **极简版**(无 rclone/分卷,单 .gpg 文件输出,本地拖到任何云盘) |
| `hermes_backup_github.sh` | `~/.hermes/scripts/` | **GitHub Release 模式**(绕开 git push 大文件 HTTP/2 错误,gh release create 上传 .gpg 作 release asset) |
| `hermes_backup_github_push.sh` | `~/.hermes/scripts/` | **GitHub git push 拆分 50MB 模式**(Release 失败时 fallback,把 .gpg 拆 50MB × 3 卷推到独立分支 `backup-YYYYMMDD-HHMMSS`)。**2026-06-06 实测唯一稳的 GitHub 大文件方案** |
| `hermes_restore.sh` | `~/.hermes/scripts/` | 还原脚本(拼分卷 + GPG 解密 + tar 解压 + 权限 + 健康检查) |
| `hermes_restore_one.sh` | `~/.hermes/scripts/` | **新电脑一键还原脚本**(7 步自动:环境检测 → 装工具 → GitHub 登录 → 拉分卷 → 拼回 → GPG 解密 → 解压 → 装 hermes-agent + venv) |
| `hermes_setup_jianguoyun.sh` | `~/.hermes/scripts/` | 一次性配置 rclone + 坚果云 WebDAV |
| `verify_hermes_backup.py` | `skills/.../scripts/` | 验证加密包完整性的 Python 工具(5 步检查) |

源码见 `templates/` 和 `scripts/` 目录。

**2026-06-06 真实生产脚本位置**：`~/.hermes/scripts/hermes_backup_github_push.sh`（**当前主用**）和 `~/.hermes/scripts/hermes_restore_one.sh`（**新电脑恢复主用**）。`templates/` 里的版本是**模板**（剥离了用户特定路径），生产时要把 `gpg` 命令里的 GPG 密码和 GitHub 账号对应起来。

## KEEP_COUNT 选型参考

| 版本 | KEEP_COUNT | 远端体积 | 月上传流量 | 适用 |
|------|------------|----------|------------|------|
| 免费版（推荐起步） | 4 | ~516MB | ~520MB/月 | 坚果云免费 1GB/月上传 |
| 专业版 | 7 | ~903MB | ~520MB/月 | 坚果云专业 30GB/月上传 |
| 频繁改 state.db | 14 | ~1.8GB | ~1GB/月 | 重度使用 + 愿意花钱 |

**计算公式**：`月上传 = 129MB × 备份频率/月`；`远端体积 = 129MB × KEEP_COUNT`。
**免费版硬约束**：1GB 月上传 ≤ 4 次/周 = 每周 1 次。**专业版可放开到每天 1 次**。

## 相关 skills & references

**子 reference（这个 skill 自己的）**：
- `references/macos-bsd-tar-pitfalls.md` — macOS BSD tar 的 7 个坑（vs GNU tar）
- `references/cloud-storage-comparison.md` — 7 个云盘选项打分 + rclone 集成要点 + 实测性能
- `references/set-e-pipefail-pitfalls.md` — bash 严格模式的 4 个坑（函数捕获 / SIGPIPE / 未定义数组 / `(( ))` 算术）
- `references/free-cloud-alternatives.md` — **国内/外免费云盘对比 + "WebDAV 是自动化的门"原则**
- `references/disaster-recovery-sop.md` — **硬盘全坏 30 分钟恢复 SOP**
- `references/github-release-mode.md` — **GitHub Release 模式实战**（2026-06-06 新增，详见"GitHub Release 模式"节）
- `references/github-curl-vs-gh-api.md` — **私有仓文件获取：`curl raw` 缓存坑 vs `gh api` 稳态**（2026-06-06 新增，"一键恢复"命令的 3 层 fallback 设计）
- `references/post-restore-cron-verify.md` — **恢复后 cron jobs 静默丢失**（2026-06-06 新增，恢复后必须验证 jobs.json 中 job 数量）

**相关 skills**：
- `hermes-multi-host-debug` — 同一局域网两台 Mac 之间的数据迁移（**不是云端/新机器场景**）
- `verification-before-reporting` — 备份/还原后必须做"实地比对验证"而不是看 title 报成功
- `script-provider-independence` — 任何定时脚本不绑死 provider/model（备份脚本用 rclone 走 WebDAV，不绑模型）
- `proactive-execution` — "推荐清单=执行令"，不重新问"要不要继续"
- `macos-process-lifecycle` — 30 分钟空闲自动杀 / 资源调度（备份脚本不该常驻）
- `devops/mac-resource-cleanup` — 清理 .hermes 前的对账表（备份脚本的 staging 目录该清）

## Pitfall

- ❌ 不要备份 `hermes-agent/` 整目录（git 仓库 + 4.3GB，换电脑 `git clone + pip install` 5 分钟搞定）
- ❌ 不要把 GPG 密码明文写在 backup.sh（→ Keychain 存）
- ❌ 不要用 `tar --transform`（macOS BSD 不支持，详见坑 1）
- ❌ 不要相信"看 title 报成功"——必须 `diff` + `wc -l` + sqlite 实际查询
- ❌ 不要用"自动同步"型工具直接同步 ~/.hermes（sqlite + .env + .lock 经常半写状态，必须打包+检查点）
- ❌ 不要忘了在还原脚本里 `chmod 600 ~/.hermes/.env`（API key 暴露风险）
- ❌ 不要在 SQLite WAL 模式下只备份 .db（丢最近写入，详见坑 3）
- ❌ 不要在 launchd plist + tee -a 双写同一 log（双倍行，详见 macos-process-lifecycle 的 launchd-bash-logging-pitfall）
- ❌ 不要从坚果云"分享链接"模式备份（不走 WebDAV，rclone 用不了）
- ❌ 不要用 `git push` 推 .gpg 大文件（HTTP/2 EOF 必撞），改用 `gh release create`（详见坑 5）
- ❌ 不要在 `gh repo view` 不可靠时信它的输出，用 `gh api repos/<user>/<repo>` 更稳（详见坑 7）
- ❌ 不要在用户面前 `rm -rf ~/.hermes` —— 恢复 SOP 涉及不可逆操作，**让用户亲自跑**（见 disaster-recovery-sop.md 末尾"给 AI 代理的提醒"）
- ❌ 不要替用户跑 `rm -rf ~/.hermes/.backups/staging/...` 之类的"清理"操作——Hermes 安全闸 v2 会拦（详见坑 4.6），**写自包含脚本让用户自己跑**
- ❌ **不要只验证文件存在就认为恢复完整** — cron jobs 可能在 config.yaml 迁移或 jobs.json 覆盖中被静默丢弃。恢复后必须检查 `~/.hermes/cron/jobs.json` 中 job 数量（详见 `references/post-restore-cron-verify.md`）
- ✅ 第一次跑前**先备份原 .hermes 到 .bak**（任何"切换动作"前的标准保险）
- ✅ 验证用 5 步流程（不是看 exit code，是 diff + wc + sqlite 查询）
- ✅ 还原后**重新跑 `--keychain-set`** 把 GPG 密码写到新电脑的 Keychain
- ✅ 把"3 步核心"固化为 skill 而不是 session-specific 脚本（下次同样问题 0 思考）

## 用户偏好（这个 skill 服务的用户，2026-06-06 已确认）

执行恢复 SOP 时**必须遵守**（用户曾在多次"删/清理"类操作中拍板）：

1. **真实验证 > 报告成功** —— "看 title 报成功" = 空炮，必须 `diff` + `wc -l` + sqlite 实际查询 + 6 个关键数字对得上
2. **推荐清单 = 执行令** —— 列完就执行，不重新问"要不要继续"；不打断确认
3. **删/清理前/后给对账表** —— 列出"删了什么+什么没动"两栏，1-2 句确认即可，**不要列 11+12 行大表**
4. **删完只清用户明确说的 1 个目标** —— 后续"还能清哪些"等用户主动问，**不主动列大单子**
5. **破坏性操作必须用户授权** —— 涉及 `rm -rf` / 覆盖现有数据，让用户亲自跑
6. **不替用户跑"删"类命令** —— Hermes 安全闸 v2 会拦（BLOCKED），且即使绕开也违反用户"亲手确认"原则
7. **表达风格** —— "我换个思路试试" / "这条路走不通" / 像有经验的工程师说话，**不要机械列 1./2./3.**
8. **遇到困难不甩锅** —— 说我做过的尝试 + 观察到的事实 + 打算怎么试，不要"出错了"直接停
9. **用户说"我保持怀疑的态度"** —— 立刻做**实地验证**，不靠"我看了 manifest/看 log 报成功"。**用户问"115MB 就是 hermes 的全部吗"** 5 次 → 每次都要给更深的证据（解开 .gpg → 看 sessions/messages 数量 → 看 skills 数 → 看 scripts 数 → 看 .env 变量数）。**不要用"理论上"** 打发——用"我跑了一下 → 看到 X"
