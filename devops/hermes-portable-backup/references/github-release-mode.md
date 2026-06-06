# GitHub Release 模式 — Hermes 备份的第三条路

> 2026-06-06 实测沉淀。`hermes-portable-backup` SKILL.md "GitHub Release 模式" 节的详细实战笔记。

## 什么时候用这个模式

| 用户表达 | 推荐方案 |
|---|---|
| "我有 GitHub 仓 / 我习惯 git" | **GitHub Release 模式** |
| "想最简单 / 不想搞 rclone" | hermes_backup_simple.sh(任何网盘) |
| "想完全自动化" | hermes_backup.sh(rclone + 坚果云 WebDAV + launchd) |
| "免费 + 国内 + 自动化" | hermes_backup.sh(坚果云免费版 + 每周一次) |
| **"如果是只有那么大都可以完全走 github"** (2026-06-06 用户原话) | **GitHub 模式直接走, 不要纠结 WebDAV** |

**不要**给已经习惯 GitHub 的人推 rclone 方案——增加学习成本, 违背"轻量模式"原则。

## 为什么不用 `git push` 而用 `gh release create`

`git push` 推大文件 (50MB+) 在 macOS 上会撞:

```
RPC failed; curl 16 Error in the HTTP2 framing layer
fatal: The remote end hung up unexpectedly
```

实测(2026-06-06 Mac mini M4):
- 30MB 文件:失败
- 50MB 文件:失败
- 115MB 文件:失败

**所有可能的 workaround 都试过**:
- `git config http.version HTTP/1.1` ❌
- `git config http.postBuffer 524288000` ❌
- 改 SSH 推(`git@github.com:user/repo.git`)❌(用户 SSH key 没配到 GitHub)
- 改 HTTPS + gh credential helper ❌
- **唯一稳的:绕开 git 协议层, 用 GitHub Release API**

`gh release create` 的 asset 上限是 **2GB/文件**, 对 115MB Hermes 备份绰绰有余。

## 完整工作流

### Step 0:前提条件
```bash
# 1. 装 gh CLI
brew install gh

# 2. 登录(推荐 HTTPS + token 方式)
gh auth login

# 3. 在 GitHub 网页端建一个**私有**仓 hermes-backup(脚本里 --init 也会帮你建)
```

### Step 1:首次初始化
```bash
bash ~/.hermes/scripts/hermes_backup_github.sh --init
```

这一步会:
- 检测/创建 `Buluhanke/hermes-backup` 私有仓
- 探测 `default_branch`(用户老仓可能是 `master`, 不是 `main`)
- 探测远端是否已有 commit(有的话 `--force` 推 README 覆盖)
- 写一个 README 到 main 分支

### Step 2:每周备份
```bash
bash ~/.hermes/scripts/hermes_backup_github.sh
```

内部流程:
1. 调 `hermes_backup_simple.sh` 生成 .gpg
2. `gh release create "backup-$(date +%Y%m%d-%H%M%S)" ./xxx.gpg`
3. 失败重试 3 次(每次 sleep 5 秒)
4. 自动清理 4 份之前的旧 release(`gh release delete`)

### Step 3:换电脑还原
```bash
# 1. 装 hermes-agent 源码
git clone https://github.com/NousResearch/hermes-agent.git ~/.hermes/hermes-agent
cd ~/.hermes/hermes-agent
python3.11 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cd ui-tui && npm install

# 2. 从 GitHub Release 下载加密包
gh release download --repo Buluhanke/hermes-backup --pattern '*.gpg' -D /tmp/dl
LATEST_GPG=$(ls -t /tmp/dl/*.gpg | head -1)

# 3. 解密 + 解压
gpg -d "$LATEST_GPG" > /tmp/hermes.tar.gz
# 输入 GPG 密码
tar --strip-components=1 -xzf /tmp/hermes.tar.gz -C ~/.hermes

# 4. 验证
hermes --version
```

## 5 个实战坑(沉淀在 SKILL.md 坑 5-9)

### 坑 5:gh release 重复上传同名大文件 = 偶发 HTTP/2 EOF
**症状**:`Post "https://uploads.github.com/.../assets": unexpected EOF`
**修法**:每次新时间戳 tag + 3 次重试 + 5 秒 sleep

### 坑 6:函数返回值被 ANSI 染色污染 `$()`
**症状**:`local x=$(my_func)` 拿到带 `\033[32m` 的字符串
**修法**:所有日志 `>&2`, 只有返回值走 stdout

### 坑 7:老仓的 default_branch 不一定是 main
**症状**:`src refspec main does not match any`
**修法**:`gh api repos/<user>/<repo> --jq '.default_branch'` 探测

### 坑 8:老仓里有残留 commit, push README 报非 fast-forward
**症状**:`! [rejected] main -> main (fetch first)`
**修法**:`gh api "repos/<user>/<repo>/commits?per_page=1" --jq 'length'` 探测, 非 0 就 `--force`

### 坑 9:`cp src dst` 报 "identical" 让 set -e 终止
**症状**:`are identical (not copied)` 后脚本挂
**修法**:`cp src dst 2>&1 | grep -v identical || true`

## 坑 11:raw.githubusercontent.com 私有仓 404 缓存(2026-06-06 重磅发现)

**症状**:
```bash
curl -sL https://raw.githubusercontent.com/Buluhanke/hermes-backup/main/hermes_restore_one.sh
# → 404: Not Found
# (即使 gh API 能拿到文件, push 也成功了)
```

**根因**:
- `raw.githubusercontent.com` CDN 不跟 GitHub 主站实时同步
- 私有仓的 raw 路径**首次访问**会返回 `404: Not Found` 文本(被 CDN 缓存为"不存在"状态)
- **持续几小时到几天**才刷新
- 加 cache buster(`?nocache=$(date +%s)`)也救不回来
- 即使加 `--header 'Cache-Control: no-cache'` 也无效

**结论**:`curl raw.githubusercontent.com/<user>/<repo>/<branch>/<file>` **不要用**(针对私有仓 / 刚 commit 的文件)。

**修法 — 用 gh api 替代(永远工作)**:
```bash
# 一行下载任意文件(不依赖 raw CDN 缓存)
gh api repos/<user>/<repo>/contents/<path> --jq .content | base64 -d

# 一行跑(适用于 bootstrap 脚本)
gh api repos/<user>/<repo>/contents/hermes_restore_one.sh --jq .content | base64 -d | bash -s --
```

**新电脑 fallback 三选项**(按可用性从高到低):
```bash
# A: gh api 模式(永远能跑)
gh auth login
gh api repos/Buluhanke/hermes-backup/contents/hermes_restore_one.sh --jq .content | base64 -d | bash

# B: 先 clone 仓(如果方案 A 因为 gh 没登录挂了)
gh repo clone Buluhanke/hermes-backup /tmp/hb
bash /tmp/hb/hermes_restore_one.sh

# C: 等几小时 raw 缓存刷新
curl -sL https://raw.githubusercontent.com/Buluhanke/hermes-backup/main/hermes_restore_one.sh | bash
```

**预防**:写"一键还原"类脚本时**只推 gh api 模式**到 README, **别推 curl raw**。

## 坑 12:Apple git 2.15 + macOS HTTP/2 framing layer(2026-06-06 breakthrough)

**根因**(调试 4 小时后的发现):
- macOS `/usr/local/bin/git` = **Apple 自带 git 2.15.0**(2017 年的版本)
- 这个版本对 HTTP/2 帧协议实现有 bug, **pack-objects 走 HTTP/2 上传大文件必断**
- `GIT_HTTP_VERSION=HTTP/1.1`(env 变量)在 2.15 上**不生效**(2.16+ 才有)
- `git config http.version HTTP/1.1`(config)在 2.15 上**也不生效**(2.17+ 才有)
- 即使所有 workaround 都试了, git push 50MB+ 必撞

**症状识别三件套**(同时出现 = 100% 是这个坑):
1. `curl 16 Error in the HTTP2 framing layer`
2. `fetch-pack: unexpected disconnect while reading sideband packet`
3. `git --version` 输出 2.15.x

**修法**(Hermes 写 GitHub 推送脚本**必须前置**):
```bash
# 在脚本最顶上 set -euo pipefail 之后立刻写
export PATH="/opt/homebrew/bin:$PATH"

# 验证
which git
# 必须输出 /opt/homebrew/bin/git (不是 /usr/local/bin/git)
git --version
# 必须 2.4x / 2.5x
```

**用 `gh` 命令也要确认走 homebrew**:`gh` 也装在 /opt/homebrew/bin/, 同样需要 `export PATH`。

## GitHub git push 拆分 50MB 模式(2026-06-06 跑通, Release 模式补充)

**触发场景**:`gh release create` 也撞 HTTP/2 EOF, 或用户**不用 release**(想用 git branch 形式备份)。

**思路**:
- 115MB 单 .gpg → `split -b 50M` 拆 3 卷(50+50+15.8MB)
- 每卷 50MB < GitHub 100MB 单文件限制
- 用 git push 推到**独立分支** `backup-YYYYMMDD-HHMMSS`
- 用 `export PATH="/opt/homebrew/bin:$PATH"` 切到新 git 绕开 HTTP/2 坑

**核心脚本**:`templates/hermes_backup_github_push.sh`(已交付)

**工作流**:
```bash
# 1. 找最新 .gpg(优先桌面, 备选 staging)
gpg_file=$(ls -t ~/Desktop/hermes-backup-*.gpg 2>/dev/null | head -1)

# 2. 拆 50MB/卷
mkdir -p /tmp/chunks
cd /tmp/chunks
split -b 50M -d -a 3 "$gpg_file" "hermes-${TIMESTAMP}.gpg.part"
# → hermes-20260606-164407.gpg.part000  part001  part002

# 3. 写到 MANIFEST + restore.sh(随包)
cat > MANIFEST.txt <<EOF
时间戳: ...
分卷数: 3
GPG 密码: 你脑子里
拼回: cat hermes-*.gpg.part* > merged.gpg
EOF
cp ~/.hermes/scripts/hermes_restore.sh .

# 4. 推到独立分支(用 homebrew git 2.53)
cd /tmp/push
export PATH="/opt/homebrew/bin:$PATH"
git init && git remote add origin https://github.com/<user>/<repo>.git
git fetch origin main --depth 1
git checkout -b backup-20260606-164407
cp -r /tmp/chunks/* .
git add . && git commit -m "backup: ..."
GIT_HTTP_VERSION=HTTP/1.1 git -c http.postBuffer=104857600 push -u origin backup-20260606-164407

# 5. 清理旧分支(保留 4 个)
```

**vs Release 模式选择**:
| 维度 | git push 拆分 | gh release create |
|------|--------------|-------------------|
| 协议 | git smart HTTP(走 homebrew git 2.53 修) | GitHub upload API |
| 失败率 | 低(拆 50MB 后) | 偶发 HTTP/2 EOF(50MB+) |
| 还原 | `git clone` + `git checkout 分支名` | `gh release download` |
| 速度 | 取决于网络 | 同 |
| 适用 | 喜欢 git branch 形式 | 喜欢 release 形式 |

**结论**:两者互为补充, 都跑也行(双云端)。**默认用 Release**(gh 命令更稳定), **Release 失败 fallback 到 push 拆分**。

## "新电脑一键还原" hermes_restore_one.sh(2026-06-06 新交付)

**场景**:新电脑/重装系统后, 跑这一行就能恢复完整 Hermes。

**核心设计**:**7 步自动 + 1 次密码输入**:
1. 检测环境(brew/python/gpg/node/gh 装了没)
2. 装缺的工具
3. GitHub 认证(`gh auth login` 触发)
4. 找最新 `backup-YYYYMMDD-HHMMSS` 分支
5. 拉分卷 + 拼回 .gpg
6. **要用户输 GPG 密码**
7. 解密 + 解压到 `~/.hermes` + 装 hermes-agent 源码 + venv + npm + 健康检查

**分发渠道**(按优先级, 避免坑 11 的 raw 404):
```bash
# 1. gh api base64 模式(永远能跑, 推 main 分支)
gh auth login
gh api repos/Buluhanke/hermes-backup/contents/hermes_restore_one.sh --jq .content | base64 -d | bash

# 2. 先 clone 仓(gh 没登录时)
gh repo clone Buluhanke/hermes-backup /tmp/hb
bash /tmp/hb/hermes_restore_one.sh

# 3. 等 raw 缓存刷新(几小时后, 私有仓不可靠)
curl -sL https://raw.githubusercontent.com/Buluhanke/hermes-backup/main/hermes_restore_one.sh | bash
```

**预计时间**:20-30 分钟, 中间只需输一次 GPG 密码。

**脚本**:`templates/hermes_restore_one.sh`(已交付, 8.5KB, 完整 7 步逻辑)。

**给 AI 代理的提醒**:这个脚本是**新电脑救星**, **建议用户打印出来贴墙上**(或 `EMERGENCY_RECOVERY.md`)。**不要因为"现在用不到"就跳过**——硬盘坏了什么都来不及。

## 隐私 / 公开仓风险

**2026-06-06 发现**:用户 5/31 前有个 `Buluhanke/hermes-config-2026-05` **公开**仓(5.8MB)。

**风险**:
- 如果里面有任何 `~/.env` 摘要、API key、token = 立刻泄露
- 即使是 skills/scripts 也是私有资产, 公开 = 任何人都能看

**修法**:
```bash
# 1. 立刻查仓里有什么
gh repo view Buluhanke/hermes-config-2026-05

# 2. 如果确定没敏感内容, 改 private
gh repo edit Buluhanke/hermes-config-2026-05 --visibility private

# 3. 如果有敏感内容, 删仓
gh repo delete Buluhanke/hermes-config-2026-05 --yes
```

**AI 代理硬规则**:发现用户有**公开**的备份仓时, **主动提醒**用户检查内容并改 private 或删除。**不要替用户删**——这是用户对自己资产的决定。

## 与其他方案的关系

- **不冲突**:可以同时跑 `hermes_backup.sh`(坚果云)+ `hermes_backup_github.sh`(GitHub)+ `hermes_backup_simple.sh`(手动)
- **互为备份**:3 个云端 = 3 份独立丢失风险
- **GitHub 优势**:版本控制(每次 release 是 immutable 的) + 私有不额外收费 + 多年历史
- **GitHub 劣势**:HTTP/2 偶发错误(已重试机制)+ 公开仓泄露风险 + 国内访问偶尔抽风

## 失败时的 fallback

如果 `gh release create` 3 次都失败(HTTP/2 EOF), 脚本退出。**用户应该**:
1. 打开 GitHub 网页端 → Buluhanke/hermes-backup → Releases → "Draft a new release"
2. 上传 `~/.hermes/.backups/staging/hermes-backup-XXX.gpg`
3. 发布

**AI 代理不要**反复重试或换工具——网络问题反复重试只会浪费 token。
