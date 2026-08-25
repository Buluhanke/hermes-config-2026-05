---
name: macos-network-sharing
description: "macOS SMB共享 smbd自启445端口排查。Use when Mac之间SMB文件共享不通"
triggers:
  - "Finder 网络/侧边栏找不到 Mac"
  - "局域网发现不了"
  - "smb 无法连接"
  - "文件共享开启失败"
  - "Bonjour 不广播"
  - "com.apple.smbd Disabled"
  - "failed to bind to port 445"
  - "smbd not advertising"
  - "_smb._tcp.local no results"
---

# macOS 网络共享（SMB/Bonjour）故障诊断

## 核心架构（三层都必须通）

```
Layer 1: SMB TCP 端口    → lsof -i :445  必须有 smbd 监听
Layer 2: Bonjour UDP    → lsof -iUDP:5353 必须有 mDNSResponder
Layer 3: mDNS 多播路由   → ARP 表有设备 + 224.0.0.251 存在
```

## 快速诊断（按顺序）

### 1. SMB 端口状态
```bash
sudo lsof -nP -iTCP:445 -sTCP:LISTEN
ps aux | grep -i smb | grep -v grep
# launchd 自身占 445 → smbd 未启动
# smbd 进程存在但不监听 → 查看日志
log show --predicate 'process == "smbd"' --last 10s
```

### 2. Bonjour 广告验证
```bash
# 必须在 Mac mini 本机运行，看是否收到自己的广告
dns-sd -B _smb._tcp local.
# 期望看到: Add 3 1 local. _smb._tcp. "Aimac的Mac mini"
```

### 3. ARP 表连通性
```bash
arp -a | grep -v incomplete
# 看同网段设备是否在 en1 上出现
# 224.0.0.251 是 Bonjour 多播地址，必须存在
```

### 4. 关键 plist 检查
```bash
cat /System/Library/LaunchDaemons/com.apple.smbd.plist
# <Disabled>true</Disabled> → 需要用 launchctl load -wF 启用
```

## 常见故障与修复

### 故障 A：smbd Disabled 导致开机不自启
**表现**：`launchd` 占着端口 445 但 smbd 进程不存在，`lsof -i :445` 只有 launchd
**修复**：
```bash
sudo launchctl bootout system/com.apple.smbd
sudo launchctl bootstrap system /System/Library/LaunchDaemons/com.apple.smbd.plist
sudo launchctl start com.apple.smbd
```

### 故障 B：端口 445 被旧 smbd 占用（failed to bind）
**表现**：`log show` 里有 "failed to bind to port 445"，新进程起不来
**原因**：旧 smbd 进程未正确退出
**修复**：
```bash
sudo killall smbd   # 强制终止所有 smbd
sleep 2
sudo launchctl start com.apple.smbd
```

### 故障 C：smbd 进程在跑但不监听端口
**表现**：ps 里有 smbd 但 `lsof -i :445` 无输出
**修复**：
```bash
sudo launchctl bootout system/com.apple.smbd
sleep 2
sudo launchctl bootstrap system /System/Library/LaunchDaemons/com.apple.smbd.plist
sleep 1
sudo launchctl start com.apple.smbd
sleep 3
# 验证
ps aux | grep -i smb | grep -v grep
sudo lsof -nP -iTCP:445 -sTCP:LISTEN
```

### 故障 D：SMB 直连 IP 能通但 Finder 看不到名字
**表现**：`smb://192.168.0.77` 能连，但 Finder 侧边栏没有
**原因**：Bonjour 没有正确广播。可能原因：
- 第三方防火墙（Little Snitch / 薄冰）阻止 UDP 5353
- 路由器 AP 隔离
- 跨网段（设备不在同一 Wi-Fi SSID 或有线/无线走了不同路由器）

**排查步骤**：
1. 确认两台设备在同一个 /24 或 /23 网段：`arp -a` 对比
2. 确认同一 Wi-Fi SSID
3. 检查第三方防火墙：`ps aux | grep -iE "snitch|glasswire"`
4. 关闭 macOS 防火墙：`sudo defaults write /Library/Preferences/com.apple.alf globalstate -int 0`
5. Bonjour 广告验证：`dns-sd -B _smb._tcp local.`（本机必须有 Add 记录）

### 故障 E：Wi-Fi 和有线不在同一网段
**表现**：`ifconfig` 显示 en0（有线）inactive，Wi-Fi IP 段与路由器 LAN 口段不匹配
**说明**：Mac mini 有线和无线可能接了不同路由器，或路由器做了 AP 隔离
**处理**：确认所有设备在同一个 LAN（同一路由器或同一网段交换机下）

## SMB 服务完整重启流程
```bash
# 1. 完全停止
sudo launchctl bootout system/com.apple.smbd 2>/dev/null
sudo killall smbd 2>/dev/null
sleep 2

# 2. 确认端口释放
sudo lsof -i :445  # 应该只有 launchd 或无输出

# 3. 启动
sudo launchctl bootstrap system /System/Library/LaunchDaemons/com.apple.smbd.plist 2>&1
sudo launchctl start com.apple.smbd
sleep 3

# 4. 验证
ps aux | grep -i smb | grep -v grep
sudo lsof -nP -iTCP:445 -sTCP:LISTEN
dns-sd -B _smb._tcp local.  # 确认广告出现
```

## 验证清单（发给用户）

- [ ] SMB 直连 IP：`smb://192.168.0.77` 能打开吗？
- [ ] Finder → Go → Connect to Server → `smb://AimacdeMac-mini.local` 能找到吗？
- [ ] 其他 Mac 和 Mac mini 在同一个 Wi-Fi SSID 吗？
- [ ] 其他 Mac 是用无线还是接了有线？

## 关键日志命令
```bash
# SMB + mDNSResponder 综合日志
log show --predicate 'process == "smbd" OR process == "mDNSResponder"' --last 20s

# 过滤关键事件
log show --predicate 'process == "smbd"' --last 10s | grep -iE "advertis|bonjour|register|bind|port|success"
```
