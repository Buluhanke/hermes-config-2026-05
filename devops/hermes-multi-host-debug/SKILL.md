---
name: hermes-multi-host-debug
description: Multi-host Hermes diagnostics — confirm which machine is which, SSH troubleshooting, data migration, and process health checks
triggers:
  - "Hermes崩了吗"
  - "检查Hermes"
  - "SSH连不上"
  - any IP/hostname like 192.168.0.x, Mac-Pro, aimac
version: 1.0.0
---

# hermes-multi-host-debug

## 关键陷阱：主机身份确认

**不要假设本机 IP。** macOS `hostname` + `ipconfig getifaddr en0` 显示的是本机真实 IP，不是用户心里的"本机"。

诊断流程：
1. 先跑 `hostname` + `ipconfig getifaddr en0`（或 en1）确认本机 IP
2. 如果用户说的 IP 和本机不同 → 用户在说另一台机器，需要 SSH
3. 如果 SSH 失败，先 `nc -zv -w 5 <host> 22` 确认端口可达
4. 端口可达但 SSH 失败 = auth 问题，不是 Hermes 问题

## SSH auth 失败排查
```bash
ssh -vvv -o ConnectTimeout=8 -o StrictHostKeyChecking=no user@host
```
看 `debug1: Next authentication method:` 段落：
- publickey only → 无密钥，尝试 `ssh -o PreferredAuthentications=password`
- keyboard-interactive → 服务器支持但失败，可能需要交互式密码输入

## 本机 Hermes 存活检查（不需要 SSH）
```bash
ps aux | grep -E 'hermes|gateway' | grep -v grep
curl -s --connect-timeout 5 http://127.0.0.1:9119/api/health
```
返回 `Unauthorized` = 服务正常，不是崩了。

## launchd 进程检查
```bash
launchctl list | grep -i hermes
```

## 已知主机档案
| 主机 | IP | 用户 | SSH密码 | 备注 |
|------|-----|------|---------|------|
| aimac (Mac mini) | 192.168.0.4 | aimac | — | **本机**（主力），Hermes 完整运行 |
| Mac-Pro | 192.168.0.2 | mac | 3308 | **已停用**，数据已全部迁移到 192.168.0.4 |

## Hermes 数据迁移（192.168.0.2 → 当前机器）

当需要将 Mac Pro 的 Hermes 数据拷贝到本机时：

```bash
# SSH 认证
sshpass -p '3308' ssh -o PreferredAuthentications=password mac@192.168.0.2 "command"

# Rsync 全部数据（排除模型配置和通讯渠道）
sshpass -p '3308' rsync -avz --progress \
  --exclude='config.yaml' \
  --exclude='config.yaml*' \
  --exclude='auth.json' \
  --exclude='auth.json.backup*' \
  --exclude='auth.lock' \
  --exclude='.env' \
  --exclude='.env.example' \
  --exclude='channel_directory.json' \
  --exclude='gateway_state.json' \
  --exclude='gateway.lock' \
  --exclude='gateway.pid' \
  --exclude='interrupt_debug.log' \
  --exclude='processes.json' \
  --exclude='response_store.db' \
  --exclude='.restart_last_processed.json' \
  mac@192.168.0.2:~/.hermes/ ~/.hermes/
```

### 迁移后 Venv 修复
```bash
cd ~/.hermes/hermes-agent/venv/bin
# 1. 修复 python 软链
rm python3.11 && ln -s /Users/aimac/.local/bin/python3.11 python3.11
rm python python3 && ln -s python3.11 python && ln -s python3.11 python3
# 2. 修复所有 shebang 路径
sed -i '' 's|/Users/mac/|/Users/aimac/|g' *
# 3. 修复 activate 脚本
sed -i '' 's|VIRTUAL_ENV=/Users/mac/|VIRTUAL_ENV=/Users/aimac/|g' activate
# 4. 重装包
./python3 -m pip install -e ~/.hermes/hermes-agent
# 5. 验证
hermes --version
```

## Pitfalls
- 用户说"本机"时必须立即用 `hostname` 验证，不能凭记忆
- Hermes Dashboard 在 :9119，返回 Unauthorized 就是好的
- `gateway run --replace` 是正常启动方式，不是崩溃
- 192.168.0.2 的 SSH 用户是 `mac`，密码 `3308`，非默认 `aimac` 用户
