---
name: bitwarden-cli
description: "Bitwarden CLI password manager — install, login, unlock, query."
triggers:
  - bitwarden
  - 密码管理
  - vault
  - 密码填充
  - bw cli
  - bitwarden cli
version: 1.0.0
category: productivity
author: Hermes Agent
created: 2026-08-10
tags:
  - bitwarden
  - password-manager
  - cli
  - secrets
---

# Bitwarden CLI Skill

集中管理 Bitwarden vault 的命令行技能。覆盖安装、登录、解锁、查询、密码生成、常见坑点及验证。

---

## 1. 安装

### 方式一：Homebrew（推荐 macOS）

```bash
brew install bitwarden-cli
```

### 方式二：npm

```bash
npm install -g @bitwarden/cli
```

### 验证安装

```bash
bw --version
```

---

## 2. 登录

> Bitwarden 自托管用户需指定 `--host`。

```bash
# 官方云 vault
bw login

# 自托管实例（如 Bitwarden RS、Nightly）
BW_HOST=https://vault.example.com bw login
```

**交互流程：**

1. 输入 email，回车
2. 输入 master password，回车
3. 若开启两步登录（2FA），CLI 会输出 `Two-step token:` 提示，输入 6 位验证码后回车
4. 登录成功后会显示 session key（或提示已写入 config）

> **注意：** headless 环境下可使用 `BW_PASSWORD` 和 `BW_EMAIL` 环境变量（不推荐生产环境）：
> ```bash
> export BW_EMAIL="your@email.com"
> export BW_PASSWORD="your_master_password"
> bw login --passwordenv
> ```

---

## 3. 解锁（Unlock）

登录后 vault 内容是加密状态，需要先解锁获取 session key。

```bash
bw unlock
```

**交互流程：**

1. 输入 master password，回车
2. 输出一个 `BW_SESSION` 值（约 100+ 字符的 base64 字符串）

### 导出 session 环境变量

```bash
export BW_SESSION="your_BW_SESSION_here"
```

> **坑点：** session 有超时（默认 30 天，可自定义），超时后需重新 `bw unlock`。  
> **建议：** 将 session key 写入配置文件或 keychain，避免每次手动 export：
> ```bash
> # macOS keychain 示例
> security add-generic-password -a "bitwarden" -s "BW_SESSION" -w "$(bw unlock --raw)"
> # 读取
> export BW_SESSION=$(security find-generic-password -a "bitwarden" -s "BW_SESSION" -w)
> ```

---

## 4. 常用命令

> 以下所有命令均依赖 `BW_SESSION` 环境变量（除非注明 `--session`）。

### 列出所有 items

```bash
bw list items
```

带格式输出（JSON 过滤）：

```bash
# 只看 name 和 id
bw list items | jq '.[] | {name, id}'

# 按文件夹分组
bw list items --folderid <folder-uuid>
```

### 搜索 item

```bash
# 搜索名称包含 "github" 的条目
bw list items --search github
```

### 获取单个 item 详情

```bash
# 获取完整 JSON
bw get item <item-id-or-name>

# 只取 password 字段（不在日志中暴露）
bw get password "<item-name>"

# 只取 username
bw get username "<item-name>"

# 只取 TOTP（两步验证码）
bw get totp "<item-name>"
```

### 密码生成

```bash
# 生成 20 位强密码（默认）
bw generate

# 自定义：16 位，包含数字和符号
bw generate -l 16 -n -s

# 参数说明：
#   -l, --length      密码长度（默认 20）
#   -u, --uppercase   包含大写字母（默认开启）
#   -l, --lowercase   包含小写字母（默认开启）
#   -n, --number      包含数字（默认开启）
#   -s, --special     包含特殊字符（默认关闭）
#   -p, --passphrase  生成密码短语（而非随机密码）
```

### 创建 / 编辑 item

```bash
# 创建 login item
bw create item item '{"name":"GitHub","login":{"username":"user@example.com","password":"secret123"}}'

# 编辑现有 item
bw edit item <item-id> '{"login":{"password":"newpassword456"}}'
```

### 附件操作

```bash
# 下载附件
bw get attachment <attachment-id> --itemid <item-id> --output /path/to/file

# 上传附件
bw create attachment --file /path/to/file --itemid <item-id>
```

### 导出 vault

```bash
# JSON 格式（可重新导入）
bw export --format json

# CSV 格式（与 1Password 兼容）
bw export --format csv

# 加密 JSON（需要密码）
bw export --format json --encrypt
```

### 发送密码到剪贴板（安全）

```bash
# 复制密码到剪贴板（macOS，自动清除）
echo $(bw get password "<item-name>") | pbcopy
# 30 秒后清除剪贴板
sleep 30 && pbcopy </dev/null

# 更安全的方式：用 security clip（macOS）
bw get password "<item-name>" | security clip
```

---

## 5. 与 1Password 对比

| 维度 | Bitwarden CLI | 1Password CLI (`op`) |
|------|--------------|---------------------|
| **安装** | `brew install bitwarden-cli` | `brew install 1password-cli` |
| **登录方式** | `bw login`（交互式） | `op signin`（需记住 account shorthand） |
| **解锁** | `bw unlock` 单独步骤 | `op unlock` 或集成在 signin |
| **Session 管理** | `BW_SESSION` 环境变量，需手动 export | `OP_SESSION` 自动写入 `~/.op/config` |
| **密码生成** | `bw generate` | `op create item` 内联生成 |
| **查询语法** | `--search`、`jq` 过滤 | `op item get <name>`（更直观） |
| **团队/家庭共享** |Organizations 原生支持 | Teams/Business 账户 |
| **自托管** | ✅ 支持（Bitwarden RS/Vaultwarden） | ❌ 仅官方云 |
| **开源** | ✅ GPL-3.0 | ❌ 闭源 |
| **成本** | 免费（个人/家庭）；服务端自托管免费 | 个人免费；CLI 全功能需付费订阅 |
| **自动化友好度** | 高（标准 CLI，JSON 输出） | 高（结构化 JSON，文档清晰） |

**选 Bitwarden 的理由：** 自托管免费、开源、自托管实例（Vaultwarden）资源占用极低。
**选 1Password 的理由：** UX 更流畅、session 管理更优雅、不需要自己维护服务器。

---

## 6. 坑点清单

### ⚠️ Session 超时
- `bw unlock` 的 session 有 TTL，默认 30 天（可服务端配置）。
- 超时后 `bw list items` 返回 `Expired session` 错误。
- **修复：** 重新 `bw unlock` 并 export 新 session。

### ⚠️ 两步登录（2FA）手动输入
- `bw login` 在 2FA 启用时需要手动输入验证码。
- **方案：** headless/CI 场景下可生成 [device attachment](https://bitwarden.com/help/authenticator-keys/#device-key) 或使用 `BW_PASSWORD` 环境变量 + `--passwordenv`。

### ⚠️ CLI 无 GUI 自动填充
- Bitwarden CLI 本身不提供浏览器自动填充。
- **方案：** 配合浏览器扩展（Bitwarden Browser Extension）使用；或使用 `bw` 将密码 pipe 到剪贴板后手动粘贴。

### ⚠️ 密码含有特殊字符导致 shell 转义问题
- 某些特殊字符（`$`、`\`、反引号）在 shell 中需要转义。
- **方案：** 用单引号包裹，或 `--response` 输出 JSON 避免转义。

### ⚠️ `bw generate` 默认不含特殊字符
- 默认生成的密码不含 `!@#$%` 等符号，长度仅 20 且有数字。
- **方案：** 显式加 `-s` 参数：`bw generate -l 32 -s`

### ⚠️ 自解压 session key 暴露
- `bw unlock --raw` 直接输出明文 session key。
- **不要** 将其写入公开的 shell 历史或日志文件。

### ⚠️ 登录状态与 vault 服务地址耦合
- `BW_HOST` 决定连接哪个 Bitwarden 实例。切换账号/服务端时需重新 `bw login`。

---

## 7. 验证步骤

### 验证 1：CLI 可执行

```bash
bw --version
# 期望：输出类似 "2024.x.x"
```

### 验证 2：已登录 + 已解锁

```bash
echo $BW_SESSION
# 期望：非空字符串（约 100+ 字符）

bw unlock --check
# 期望：无报错或返回 session 状态 JSON
```

### 验证 3：能列出 vault 内容

```bash
bw list items
# 期望：JSON 数组，包含你的所有登录项

# 更友好的检查：
bw list items | jq 'length'
# 期望：返回 item 总数（大于 0 表示 vault 正常）
```

### 验证 4：能获取指定密码

```bash
# 用你知道密码的 item name 替换 "TestItem"
bw get password "TestItem"
# 期望：输出对应密码（无报错）

# 检查 TOTP
bw get totp "TestItem"
# 期望：输出 6 位 TOTP 码（若开启 2FA）
```

### 验证 5：密码生成功能

```bash
bw generate -l 32 -s
# 期望：输出一个 32 位含特殊字符的强密码
```

### 验证 6：搜索功能

```bash
bw list items --search github | jq '.[0].name'
# 期望：输出匹配条目的名称
```

---

## 8. 快速参考（TL;DR）

```bash
# 安装
brew install bitwarden-cli

# 登录
bw login

# 解锁并保存 session
bw unlock
export BW_SESSION="$(bw unlock --raw)"

# 日常使用
bw list items                           # 列出所有
bw get password "GitHub"                 # 获取密码
bw generate -l 24 -s                    # 生成强密码
bw list items --search "aws"             # 搜索
bw create item item '{"name":"NewSite"}' # 创建条目
bw export --format json                  # 导出 vault
```
