---
name: android-remote-control
description: Mac scrcpy无线控制Android手机。触发：手机投屏/远程控制安卓/scrcpy/Android。
---

# Android Remote Control (Mac → Android)

用 scrcpy 在 Mac 上无线投屏和控制 Android 设备。

## 快速启动

**有线连接（首次或无线连不上时）：**
```bash
phone
```

**无线调试已配置（推荐日常使用）：**
手机 IP `192.168.8.204`，端口 `5555`。每次使用：
```bash
adb connect 192.168.8.204:5555
phone
```

**设置无线调试（只需一次，USB 插着时做）：**
```bash
adb tcpip 5555
# 手机进入开发者选项，确认 USB 调试已开
# 然后拔掉 USB 线
adb connect 192.168.8.204:5555
```

**无线 scrcpy（含 IP 指定）：**
```bash
scrcpy -m 1024 -b 15M --max-fps=30 --always-on-top -s 192.168.8.204:5555
```

## 已知环境

| 设备 | 型号 | IP | 端口 | 控制命令 |
|------|------|-----|------|---------|
| 小米 MI 8 | dipper | 192.168.8.204 | 5555 | `phone` |
| 华为平板 MRX-W29 | HWMRX | 192.168.8.248 | 5555 | `pad` |

> 注意：Intel Mac IP 曾被误报为 192.168.8.156，实际是 192.168.8.123（有双网卡：192.168.8.123 和 192.168.0.16）。

## phone 脚本内容

```bash
#!/bin/bash
scrcpy -m 1024 -b 15M --max-fps=30 --always-on-top
```

## pad 脚本内容

```bash
#!/bin/bash
exec scrcpy -s 192.168.8.248:5555 --always-on-top --window-title "MRX-W29" "$@"
```

## 常用 scrcpy 参数
| 参数 | 作用 |
|------|------|
| `-m 1024` | 分辨率上限 |
| `-b 15M` | 视频码率 |
| `--max-fps=30` | 帧率限制 |
| `--turn-screen-off` | 关闭手机屏幕 |
| `--always-on-top` | 窗口置顶 |

## 重要限制
- Hermes终端里无法运行scrcpy（无图形显示上下文），必须在Mac的Terminal.app中执行
- Android 10不支持音频（需Android 11+）
- scrcpy启动时需要设置 `export ADB=/path/to/adb`，PATH不足以自动发现

## 无线调试配置（已设置）

**小米 MI 8** — IP `192.168.8.204`，端口 `5555`。
**华为平板 MRX-W29** — IP `192.168.8.248`，端口 `5555`。

**设置步骤（每个设备只需执行一次）：**
1. USB 有线连接设备
2. `adb -s <设备ID> tcpip 5555` — 重启 adb 监听 TCP 模式
3. 拔掉 USB 线
4. `adb connect 192.168.8.xxx:5555` — 无线连接

**日常使用：**
```bash
adb connect 192.168.8.204:5555
phone
# 或直接指定 IP：
scrcpy -m 1024 -b 15M --max-fps=30 --always-on-top -s 192.168.8.204:5555
```

## MI 8 系统版本记录

| 项目 | 版本 |
|------|------|
| 型号 | Xiaomi MI 8 (dipper) |
| MIUI 版本 | V12.0.3.0.QEAMIXM（国际版最新稳定版） |
| Android | 10.0 |
| 安全性补丁 | 2020-09-01 |
| 官方最高支持 | Android 10，MIUI 12（已停止维护） |

> MI 8 官方最高仅支持 Android 10，无线调试通过 `adb tcpip 5555` USB先行开启后使用。

## 常见问题

### scrcpy 找不到 adb
scrcpy 硬编码在 `~/.local/bin/adb` 找 adb，PATH 有没有都不行。
```bash
adb kill-server && sleep 2 && adb start-server && adb devices -l
```
正常输出示例：
```
d0b859af               device product:dipper model:MI_8 device:dipper transport_id:1
## MI 8 系统版本记录

| 项目 | 版本 |
|------|------|
| 型号 | Xiaomi MI 8 (dipper) |
| MIUI 版本 | V12.0.3.0.QEAMIXM（国际版最新稳定版） |
| Android | 10.0 |
| 安全性补丁 | 2020-09-01 |
| 官方最高支持 | Android 10，MIUI 12（已停止维护） |

> MI 8 官方最高仅支持 Android 10，无线调试通过 `adb tcpip 5555` USB先行开启后使用。

## 常见问题

### scrcpy 找不到 adb
scrcpy 硬编码在 `~/.local/bin/adb` 找 adb，PATH 有没有都不行。
**修复（M4 Mac mini）：做软链接**
```bash
ln -sf ~/adb-tools/platform-tools/adb ~/.local/bin/adb
```

### scrcpy 报 "At most one device selector option may be passed"
同时传了 `-s`（指定设备）和 `--tcpip`（TCP/IP 模式），二选一，不能共存。无线已连接时只留 `-s` 即可。
```bash
# 错误 ❌
scrcpy -s 192.168.8.248:5555 --tcpip=192.168.8.248:5555

# 正确 ✅
scrcpy -s 192.168.8.248:5555
```

### Android 设备完全检测不到（adb devices 为空）
可能原因及排查顺序：
1. **手机 USB 模式是「仅充电」** — 下拉通知栏 → 点击 USB 通知 → 改成「文件传输(MTP)」或「PTP」。「仅充电」不暴露 USB 数据接口，adb 根本看不见设备。
2. **USB 调试未开启** — 开发者选项 → USB 调试 → 开启
3. **Xiaomi 额外安全设置** — 开发者选项 → 「USB 调试（安全设置）」需要开启，否则无法注入输入事件
4. **授权弹窗未点** — 首次连接会弹出「允许USB调试」，需点「允许」

### Intel Mac 下载了 Apple Silicon 版本
scrcpy 有两个 macOS 二进制：
- `scrcpy-macos-aarch64-*.tar.gz` — Apple Silicon (M1/M2/M3/M4)
- `scrcpy-macos-x86_64-*.tar.gz` — Intel

用错版本会立刻报 `exec: No such file or directory`。

### 远程给另一台 Mac 装 scrcpy 时 scp 超时
内网传大文件（9MB+）容易超时。改让那台 Mac 自己从 GitHub 下载：
```bash
ssh user@target-mac "cd /tmp && \
  curl -L 'https://github.com/Genymobile/scrcpy/releases/download/v3.3.4/scrcpy-macos-x86_64-v3.3.4.tar.gz' -o scrcpy.tar.gz && \
  tar -xzf scrcpy.tar.gz && \
  cp scrcpy-macos-x86_64-v3.3.4/scrcpy ~/.local/bin/ && \
  cp scrcpy-macos-x86_64-v3.3.4/scrcpy-server ~/.local/bin/ && \
  chmod +x ~/.local/bin/scrcpy ~/.local/bin/scrcpy-server && \
  rm -rf /tmp/scrcpy*"
```

## 远程方案（互联网/非局域网）
| 方案 | 免费额度 | iOS控制Android |
|------|---------|--------------|
| AirDroid+AirMirror | 200MB/月 | ✅ |
| scrcpy-mobile | 免费 | ✅ |
| Iperius Remote | 有免费 | ✅ |

## MI 8 Root 状态（2026-08-05 实测）

**Magisk Manager v29.0 已安装，Root 激活流程进行中。**

| 检查项 | 结果 |
|--------|------|
| `adb root` | `adbd cannot run as root in production builds` |
| `su` 命令 | 不存在（Magisk su 未注入 boot） |
| `/data/local/test` 写权限 | Permission denied |
| BootLoader | 已解锁（用户确认） |
| Magisk Manager | ✅ v29.0 已安装 |
| Root 状态 | APP装好，boot未修补，su未生效 |

**Root 激活步骤（BL 已解锁）：**
1. Magisk APP → 「安装」 → 「直接安装（推荐）」最简单，或选「选择并修补文件」
2. 「直接安装」自动完成无需电脑；「修补文件」需提取 boot.img 配合 ROM
3. 重启后 `su` 生效，`setprop persist.adb.tcp.port 5555` 可设置

**Magisk APK adb 安装正确流程（SELinux 限制）：**
```bash
# GitHub 国内慢，改从手机 curl 下载（手机能访问 github.com）
adb shell "curl -L -o /sdcard/Download/magisk.apk 'https://github.com/topjohnwu/Magisk/releases/download/v29.0/Magisk-v29.0.apk'"

# system_server 无法读 sdcard，必须先 cp 到 /data/local/tmp/
adb shell "cat /sdcard/Download/magisk.apk > /data/local/tmp/magisk.apk"

# 从 tmp 安装才成功
adb shell "pm install /data/local/tmp/magisk.apk"

# 启动 Magisk
adb shell "monkey -p com.topjohnwu.magisk -c android.intent.category.LAUNCHER 1"
```

## 持久化无线调试

- **有 root**：`setprop persist.adb.tcp.port 5555`，真正持久化，重启不丢
- **无 root**：`adb tcpip 5555` 在**锁屏待机/休眠时不丢**，只有**关机重启**才失效
- **Android 10** 无 root 无法脚本自动持久化，必须每次重启后 USB 开一次

### 日常连接流程（无 root）
```bash
# 重启后：USB 连上 → 开无线 → 拔线
adb tcpip 5555 && sleep 2 && adb connect 192.168.8.204:5555

# 日常使用（手机未重启）：直接连
adb connect 192.168.8.204:5555
phone
```

### 多设备冲突问题
USB 和无线同时连接时 `adb devices` 显示两个设备，部分命令报 `more than one device/emulator`。
```bash
# 只保留无线，断开 USB
adb disconnect d0b859af
adb devices -l  # 确认只剩无线 IP
```

## References
