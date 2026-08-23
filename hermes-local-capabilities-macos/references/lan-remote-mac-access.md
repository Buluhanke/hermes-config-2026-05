# LAN Mac 远程操作 — Screen Sharing + SSH

## 快速连接命令

```bash
# Screen Sharing（VNC）
open "vnc://192.168.8.236"

# SSH（需要密码）
sshpass -p '3308' ssh kk@192.168.8.236 "hostname && sw_vers"

# SSH 端口检测
nc -z -w 2 192.168.8.236 22 && echo "SSH OPEN" || echo "SSH CLOSED"
```

## 已确认的设备

| 名称 | IP | 用户 | 密码 | 系统 | SSH | VNC | AirPlay |
|------|-----|------|------|------|-----|-----|---------|
| MacBook Air K | 192.168.8.236 | kk | 3308 | macOS 26.5.2 | ✅ | ✅(5900) | ✅(5000) |
| Mac mini Aimac | 192.168.8.155 | aimac | — | macOS 26.5.2 | ✅ | ✅(5900) | — |

## 常见故障

### 1. SSH Operation timed out / Connection refused
**症状**: ping 通但 SSH 连不上

可能原因：
- 远程 Mac 进入休眠（延迟会飙升到 2.5s+）
- SSH 服务响应极慢

解决：先用 Screen Sharing (`vnc://IP`) 连上去唤醒 Mac，或让用户手动在远程 Mac 上操作

### 2. Screen Sharing 弹出"辅助功能访问"授权弹窗
**症状**: `universalAccessAuthWarn` 窗口出现

**这是本机（操作者的 Mac）弹的，不是远程 Mac 弹的。**

Screen Sharing 需要本机的屏幕录制权限。在弹窗上点击「允许」即可。不要尝试远程点击这个弹窗。

```
app: universalAccessAuthWarn
window: 辅助功能访问
```

### 3. `computer_use` 报错: `session '...' has ended`
**症状**: 所有 computer_use 调用失败，返回 `session has ended`

cua-driver session 挂了。修复：

```bash
# 杀重启 cua-driver
kill -9 $(pgrep -f cua-driver)
sleep 1
/Applications/CuaDriver.app/Contents/MacOS/cua-driver serve --socket /tmp/cua.sock &
sleep 3
# 验证
computer_use(action="capture")  # 应恢复正常
```

### 4. SSH 密码错误 (`Too many authentication failures`)
**症状**: `Permission denied, please try again`

macOS 的 SSH 默认先走密钥认证（如果存在），走完所有密钥才到密码。如果用户目录有多个 `.ssh/key` 会被全部试一遍然后失败。

解决：显式指定认证方式
```bash
sshpass -p 'PASSWORD' ssh -o PreferredAuthentications=password kk@IP
```

### 5. 远程 Mac 休眠/屏幕锁定
SSH 仍可连（如果开了远程登录），但 VNC 连接会黑屏或需要重新认证。

唤醒：Screen Sharing 连上去，用户在远程 Mac 前手动解锁一次。

## SSH 到远程 Mac 后的常用检查

```bash
# Hermes 进程状态
ps aux | grep -i hermes | grep -v grep

# Hermes 配置
ls ~/.hermes/
cat ~/.hermes/config.yaml | head -50

# 磁盘空间
df -h

# 内存
free -h  # 或 vm_stat on macOS

# 最新日志
tail -50 ~/.hermes/logs/hermes.log
```

## 开启远程登录（SSH）和屏幕共享

如果远程 Mac 的 SSH 未开，让用户去：
- **系统设置 → 通用 → 共享 → 远程登录** → 打开
- **系统设置 → 通用 → 共享 → 屏幕共享** → 打开

VNC 端口 (5900) 依赖屏幕共享开启。
