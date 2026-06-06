# 云盘选型对比（2026-06 实测）

实测"hermes 完整状态 ~130MB 压缩包 + 增量"在不同云盘上的表现。

## 7 个选项打分

| 选项 | 国内速度 | 增量 | 加密 | 桌面客户端 | 5GB 全量 | 月费/价格 | 适配场景 |
|------|----------|------|------|------------|----------|-----------|----------|
| **坚果云 WebDAV** | ⭐⭐⭐⭐⭐ | ✅ rclone 增量 | ✅ rclone crypt 可选 | ✅ macOS/Win/iOS | ✅ | 免费 1GB/月上传、¥199/年 30GB/月 | **国内首选** |
| iCloud Drive | ⭐⭐⭐⭐⭐ | ✅ | ✅ E2EE | ✅ macOS 原生 | ✅ | 5G 免费 / 2T ¥21/月 | Apple 生态备份 |
| OneDrive | ⭐⭐⭐ | ✅ | ✅ E2EE (个人版) | ✅ | ✅ | 5G 免费 / 1T ¥398/年 | 海外/微软生态 |
| 阿里云盘 | ⭐⭐⭐ | ⚠ 无官方同步 | ❌ | ✅ | ✅ 100G 免费 | 免费 | 凑合 |
| 百度网盘 | ⭐⭐ | ❌ 限速 | ❌ | ✅ | ✅ 大量空间 | 容量大 | 不推荐（限速）|
| GitHub 私有仓 | ⭐⭐ | ✅ | ✅ repo 加密 | ✅ Web | ✅ 无限 | 免费 | 小文件（< 100MB/文件）|
| S3 / R2 / 自建 | ⭐⭐ 慢 | ✅ | ✅ rclone crypt | ❌ | ✅ | $0.015/GB/月 | 海外 / 折腾 |

## 关键决策点

### 1. 国内 vs 海外

- **国内主力** → 坚果云 / 阿里云盘 / iCloud (国区)
- **海外** → iCloud / OneDrive / S3

### 2. WebDAV 是关键

- ✅ 支持 WebDAV = 可用 rclone 增量同步 = 自动备份
- ❌ 不支持 WebDAV = 只能手动上传 = 容易忘

支持的：坚果云、OneDrive(企业版)、S3、iCloud(无官方但可用 bypass 工具)  
不支持 WebDAV：百度网盘、阿里云盘、GitHub

### 3. 月上传流量限制

每周 1 次 × 130MB ≈ 600MB/月 → **免费版够**  
每天 1 次 × 130MB ≈ 4GB/月 → **专业版（30GB）够**

### 4. 加密能力

- ✅ 必须用户端加密（你掌握密钥 = 你掌控数据）
- ⚠ 服务端加密 = 服务商能读（合规但隐私弱）
- ❌ 无加密 = 灾难（API key 直接泄露）

## 推荐组合（2026-06-06 给用户的）

| 优先级 | 方案 | 月成本 | 适用 |
|--------|------|--------|------|
| ⭐⭐⭐⭐⭐ | **坚果云专业版 + GPG 加密** | ¥199/年 | 国内主力 |
| ⭐⭐⭐⭐ | iCloud Drive 2TB + 加密 dmg | ¥21/月 | Apple 生态重度用户 |
| ⭐⭐⭐ | GitHub 私有仓（仅小文件） | 免费 | scripts/skills/cron 等小文件双轨 |
| ⭐⭐ | S3 / R2 + rclone crypt | $1-3/月 | 海外 |

**不推荐**：
- 百度网盘（限速 + 无 WebDAV）
- 阿里云盘（无官方同步客户端 = 不能 rclone）

## 价格明细（2026-06 当时）

### 坚果云
- 免费版：1GB/月上传，3GB/月下载，单文件 500M
- 专业版：¥199/年，30GB/月上传 + 加享 1GB×12月
- 高级专业版：¥299/年，72GB/月上传

### iCloud
- 免费：5GB
- 50GB：¥3/月
- 200GB：¥21/月
- 2TB：¥42/月

### OneDrive
- 免费：5GB
- Microsoft 365 Basic：¥30/月，100GB
- Microsoft 365 Personal：¥398/年，1TB

### 阿里云盘
- 免费 100GB（限制下载速度 + 偶尔限速）

### 百度网盘
- 免费大量（但限速到 100KB/s）

## rclone 集成要点

### 坚果云
```ini
# ~/.config/rclone/rclone.conf
[jianguoyun]
type = webdav
url = https://dav.jianguoyun.com/dav/
vendor = other
user = your@email.com
pass = $(rclone obscure "your-32char-app-password")
```

**拿应用密码**：https://www.jianguoyun.com/d/account#security → 第三方应用管理 → 添加应用密码（32位，只显示一次！）

### iCloud (rclone 1.65+)
```ini
[icloud]
type = iclouddrive
apple_id = your@email.com
```
**注意**：rclone 走 iCloud 是用 Apple ID 密码 + 2FA（首次需要交互）

### OneDrive
```ini
[onedrive]
type = onedrive
# rclone config 会跳 OAuth
```

### S3 / R2
```ini
[s3]
type = s3
provider = Cloudflare
access_key_id = xxx
secret_access_key = xxx
endpoint = https://<accountid>.r2.cloudflarestorage.com
```

## rclone crypt（端到端加密层）

如果云盘本身加密弱，可加 rclone crypt（透明加密 + 解密）：

```ini
[jianguoyun-encrypted]
type = crypt
remote = jianguoyun:hermes-backups-encrypted
password = $(rclone obscure "your-encryption-password")
# 或用 password_file / password2 (二阶段加密)
```

**注意**：rclone crypt **不能 100% 替代 GPG**。GPG 在 backup.sh 里就完成加密 → 上传后文件本身已是密文。rclone crypt 是上传**后**再加密一层（双保险，但通常不需要）。

## 国内坚果云的特殊坑

- 坚果云 WebDAV **单文件限制 500M**（Web 端 500M，WebDAV 端也 500M）
- **频率限制**：免费版每 30 分钟一次，付费版更高
- **小文件 5 万个**限制：解压后 .hermes 有 ~5000 个文件，远低于限制
- **不要用分享链接模式**：分享链接不走 WebDAV，rclone 用不了

## 实测性能（2026-06-06 用户机器）

| 动作 | 耗时 |
|------|------|
| 打包 5.5GB → 129MB | 6-8 秒 |
| GPG 加密 129MB → 114MB | 1-2 秒 |
| split 分卷 | < 1 秒 |
| rclone 上传 114MB (WebDAV 坚果云) | 30-60 秒 |
| 拼分卷 + 解密 | 2-3 秒 |
| tar 解压 | 5-8 秒 |
| **总流程**（上传到坚果云）| **~50-80 秒** |

**结论**：技术上完全可行，成本低（¥199/年），用户体验好（一行命令搞定）。

## 备选：GitHub 私有仓做"双轨"

如果想给小文件（scripts/skills/cron/plugins/config）做版本化同步：

```bash
cd ~/.hermes
git init backup-repo
cat > .gitignore <<EOF
state.db
state.db-shm
state.db-wal
.env
*.bak
.cache
backups
EOF
git add scripts/ skills/ plugins/ cron/ profiles/ config.yaml
git commit -m "Initial commit"
git remote add origin git@github.com:USER/hermes-config-backup.git
git push -u origin main
```

**优势**：
- 变更历史可查（diff 每次 commit）
- 公私钥认证，零密码
- 免费 1GB / 仓库

**劣势**：
- 单文件 100MB 限制（state.db 391M → 必须 git-lfs 或拆分）
- 不适合"全量快照"场景（每次都是 diff commit）
- 国内访问 GitHub 偶尔慢
