---
name: macos-file-sharing
description: Fix Finder Network not showing Mac (SMB/Bonjour discovery).
triggers:
  - "Mac 在网络中看不见"
  - "Finder 访达网络找不到电脑"
  - "SMB 连接失败"
  - "can't connect to Mac from network"
  - "Bonjour _smb._tcp not appearing"
---

# macOS File Sharing Diagnostics

## Quick Diagnosis Tree

```
用户报告: 局域网中其他 Mac 看不到这台电脑 (Finder Network)
│
├─ SMB 服务是否监听?
│  └─ lsof -i :445 → 端口被 launchd 或 smbd 持有
│
├─ Bonjour 广告是否发出?
│  └─ dns-sd -B _smb._tcp local. (后台) → 应看到 Add 条目
│
├─ smbd 进程是否存在?
│  └─ ps aux | grep -i smb | grep -v grep
│
└─ launchd plist 状态
    └─ sudo launchctl list | grep -i smb
       → "- 0" = 未激活 / Disabled
```

## Common Root Causes

### 1. smbd.plist Disabled (boot 时未启动)
**症状**: smbd 进程不存在，端口 445 被 launchd 持有（socket activation），dns-sd -B 无输出

**诊断**:
```bash
sudo launchctl list | grep -i smb
# 输出: "- 0  com.apple.smbd" → Disabled 状态
cat /System/Library/LaunchDaemons/com.apple.smbd.plist | grep Disabled
# 输出: <key>Disabled</key><true/>
```

**修复**:
```bash
# 清理 launchd 状态
sudo launchctl bootout system/com.apple.smbd
sleep 2

# 重新加载 plist
sudo launchctl bootstrap system /System/Library/LaunchDaemons/com.apple.smbd.plist
sleep 2
sudo launchctl start com.apple.smbd
sleep 3

# 验证
ps aux | grep -i smb | grep -v grep
lsof -i :445  # smbd 应出现在这里
```

### 2. 端口 445 被旧 smbd 占用 (bind 失败)
**症状**: smbd: failed to bind to port 445 in log; 新 smbd 进程启动后立即退出

**诊断**:
```bash
log show --predicate 'process == "smbd"' --last 30s | grep "bind"
lsof -i :445
```

**修复**: killall smbd 后重启:
```bash
sudo killall smbd
sleep 2
sudo launchctl start com.apple.smbd
```

### 3. Bonjour 广告未注册 (smbd 运行但网络发现不到)
**症状**: smbd 进程在跑，端口监听中，但 dns-sd -B _smb._tcp local. 无输出

**诊断**:
```bash
# 方法1: 实时抓 Bonjour 查询
dns-sd -B _smb._tcp local. &
sleep 3; kill %1

# 方法2: 查看 smbd 日志
log show --predicate 'process == "smbd"' --last 20s | grep -iE "advertis|bonjour|register"
```

**修复**: 重启 smbd 触发 Bonjour 重新注册:
```bash
sudo launchctl kickstart -kp system/com.apple.smbd
# 或
sudo killall -HUP smbd; sleep 2; sudo launchctl start com.apple.smbd
```

### 4. mDNSResponder 未正常广播
**症状**: dns-sd 能 Browse 但从其他设备看不到

**诊断**:
```bash
ps aux | grep -i "mDNSResponder" | grep -v grep
# 两个进程: _mdnsresponder + mDNSResponderHelper

# 测试本机 mDNS
dns-sd -B _device-info._tcp local.
```

**修复** (不打断现有连接):
```bash
sudo killall -INFO mDNSResponder  # 触发状态 dump
# 或
sudo launchctl kickstart -kp system/com.apple.mDNSResponder
```

## Verification Checklist

完成修复后，依次验证:

```bash
# 1. smbd 进程存活
ps aux | grep -i smb | grep -v grep

# 2. 端口监听
lsof -i :445 + lsof -i :139 | grep LISTEN

# 3. Bonjour 广告 (两个接口 ifindex 1 + 15 正常)
dns-sd -B _smb._tcp local. &
sleep 3; kill %1
# 期望: Add  3  1  local.  _smb._tcp.  Aimac的Mac mini

# 4. 从同局域网其他 Mac 验证
smbutil //AimacdeMac-mini.local
# 或 Finder → 网络 应看到 Aimac的Mac mini
```

## Key Log Locations

```bash
# SMB 日志
log show --predicate 'process == "smbd"' --last 30s

# mDNSResponder 日志
log show --predicate 'process == "mDNSResponder"' --last 10s

# 系统日志
cat /var/log/system.log | tail -20
```

## Gotchas

- launchctl load -w 切换 Disabled 状态，但 System/Library 下 plist 可能因 SIP 或挂载只读失败
- launchctl bootout 会彻底清理 launchd 内存状态，比 stop/start 更干净
- killall -HUP smbd 发送 SIGHUP，不是所有进程都按预期处理；用 killall smbd 更可靠
- macOS 使用 launchd socket activation 预占端口 445，所以 lsof 显示 launchd 持有端口是正常的
