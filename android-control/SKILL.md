---
name: android-control
description: Android投屏与控制 — scrcpy/adb有线无线 + FIRERPA lamda远程 + 小米平板MRX-W29。触发：android、手机控制、scrcpy、adb、MIUI、远程控制手机。
tags: [android, scrcpy, adb, miui, remote-control, lamda]
required_commands: [adb, scrcpy]
setup_status: user-required
triggers:
  - android
  - 手机控制
  - scrcpy
  - adb
  - MIUI
  - 远程控制手机
---

# Android Control — Mac 控制 Android 设备

Mac mini M4 (macOS 26.5) 上通过 scrcpy 投屏控制 Android，支持 USB 有线、无线调试、FIRERPA lamda 远程控制两种方案。覆盖小米手机 MI 8 和小米平板 MRX-W29。

---

## 已知设备

| 设备 | 型号 | IP | USB调试端口 | scrcpy命令 | 备注 |
|------|------|-----|------------|-----------|------|
| 小米 MI 8 | dipper | 192.168.8.204 | 5555 | `~/scrcpy-phone` 选1 | Android 10, MIUI 12, FIRERPA lamda✅ |
| 华为平板 MRX-W29 | HWMRX | 192.168.8.248 | 5555 | `~/scrcpy-phone` 选2 | Android 12 |

> Mac mini M4 有线网段 192.168.8.x，无线网段 192.168.0.x。注意不要混用网段。

### 统一入口脚本 ~/scrcpy-phone

两台设备共用一个交互脚本，支持选设备：

```bash
#!/bin/bash
echo "请选择要控制的设备："
echo "  1) 小米 MI8         (192.168.8.204:5555)"
echo "  2) 华为平板 MRX-W29 (192.168.8.248:5555)"
printf "输入 1 或 2: "
read choice

case "$choice" in
  1)
    exec scrcpy -m 1024 -b 15M --max-fps=30 --always-on-top -s 192.168.8.204:5555 --window-title "MI8" "$@"
    ;;
  2)
    exec scrcpy -s 192.168.8.248:5555 --always-on-top --window-title "MRX-W29" "$@"
    ;;
  *)
    echo "无效输入"
    exit 1
    ;;
esac
```

> 注意：MI8 需要先用 USB 连一次执行 `adb -s <id> tcpip 5555` 开启无线调试；MRX-W29 同理。日常使用无需重开。

---

## 方案 A — scrcpy 投屏控制

scrcpy 在 Mac 上实时显示并控制 Android 屏幕，支持 USB 和无线两种连接方式。

### 安装 scrcpy

```bash
brew install scrcpy
```

> Apple Silicon Mac (M1/M2/M3/M4) 安装 `scrcpy-macos-aarch64`，Intel Mac 安装 `scrcpy-macos-x86_64`。用错版本会报 `exec: No such file or directory`。

### 快速启动脚本

**phone 脚本** (`~/.local/bin/phone`):
```bash
#!/bin/bash
scrcpy -m 1024 -b 15M --max-fps=30 --always-on-top "$@"
```

**pad 脚本** (`~/.local/bin/pad`):
```bash
#!/bin/bash
exec scrcpy -s 192.168.8.248:5555 --always-on-top --window-title "MRX-W29" "$@"
```

```bash
chmod +x ~/.local/bin/phone ~/.local/bin/pad
```

### USB 连接（首次）

1. **手机开启 USB 调试**
   - 设置 → 关于手机 → 连续点击「MIUI 版本」7 次 → 开发者选项
   - 开发者选项 → 开启「USB 调试」
   - 小米额外：开发者选项 → 「USB 调试（安全设置）」也需开启，否则无法注入输入事件

2. **USB 连接 Mac**，手机弹出「允许 USB 调试」→ 点「允许」

3. **确认连接**
   ```bash
   adb devices -l
   ```
   输出示例：
   ```
   d0b859af               device product:dipper model:MI_8 device:dipper transport_id:1
   ```

4. **启动 scrcpy**
   ```bash
   phone    # 小米 MI 8
   pad      # 小米平板 MRX-W29
   ```

### 无线连接（日常使用）

**首次设置（需要 USB 插着做一次）:**
```bash
# 开启设备的 TCP/IP 调试模式
adb tcpip 5555
# 拔掉 USB 线
adb connect 192.168.8.204:5555   # MI 8
# adb connect 192.168.8.248:5555  # 平板
```

**日常使用（设备未重启时）:**
```bash
adb connect 192.168.8.204:5555
phone
```

**无线 scrcpy 常用参数:**
```bash
scrcpy -s 192.168.8.204:5555 \
  -m 1024 \          # 分辨率上限（省资源）
  -b 15M \           # 视频码率
  --max-fps=30 \     # 帧率限制
  --always-on-top \  # 窗口置顶
  --turn-screen-off  # 关闭手机屏幕但保持控制
```

**关闭设备屏幕但保持控制:**
```bash
scrcpy -s 192.168.8.204:5555 --turn-screen-off
# 或
scrcpy -s 192.168.8.204:5555 -S   # -S 效果同 --turn-screen-off
```

> ⚠️ Hermes 终端无图形上下文，scrcpy 必须在 Mac 的 Terminal.app / iTerm2 中执行，不能在 Hermes 工具里运行。

---

## 方案 B — FIRERPA lamda 远程控制（无需在同一局域网）

FIRERPA lamda 通过云端中继实现远程控制 Android 设备，无需公网 IP 或同一局域网，支持无 Root 使用 Shizuku。

### 安装 lamda 客户端

```bash
pip3 install -U lamda
```

### 服务端部署（安卓手机）

**方式一：Shizuku（无需 Root，推荐）**
1. 手机安装 Shizuku（通过 Play Store 或 APKMirror）
2. 开发者选项 → 开启 USB 调试
3. 用 adb 授权 Shizuku：
   ```bash
   adb shell sh /storage/emulated/0/Android/data/moe.shizuku.privileged.api/start.sh
   ```
4. 启动 Shizuku App，按提示完成授权

**方式二：Root 设备**
直接在设备上安装 lamda 服务端 APK，授予 Root 权限即可。

### 文档参考

- FIRERPA Device Farm: https://device-farm.com/docs/zh/quick-start
- lamda GitHub: https://github.com/firerapA/lamda

### Python 脚本连接控制

```python
import lamda

# 连接到远程设备
client = lamda.Client()
device = client.connect(
    host="<device-host-or-ip>",   # 设备地址
    port=5555,
    use_shizuku=True              # 使用 Shizuku 模式
)

# 控制设备
device.shell("input tap 500 500")  # 点击屏幕坐标
device.shell("input swipe 300 500 600 500 300")  # 滑动
device.screenshot()               # 截图
```

### lamda 常用操作

| 操作 | 代码 |
|------|------|
| 点击 | `device.shell("input tap X Y")` |
| 滑动 | `device.shell("input swipe x1 y1 x2 y2 duration")` |
| 输入文本 | `device.shell("input text 'hello'")` |
| 截图 | `device.screenshot()` |
| 安装 APK | `device.install("app.apk")` |
| 拉取文件 | `device.pull("/sdcard/screenshot.png", "local.png")` |

---

## 小米平板 MRX-W29 特别说明

| 项目 | 值 |
|------|---|
| 型号 | Xiaomi Pad (MRX-W29) |
| IP | 192.168.8.248 |
| USB 调试端口 | 5555 |
| 连接命令 | `adb connect 192.168.8.248:5555` |
| scrcpy 命令 | `scrcpy -s 192.168.8.248:5555 --always-on-top --window-title "MRX-W29"` |

**USB 无线调试配置步骤（每个设备只需一次）:**
1. USB 有线连接平板
2. `adb devices` 确认识别
3. `adb -s <设备ID> tcpip 5555` 开启 TCP 模式
4. 拔掉 USB 线
5. `adb connect 192.168.8.248:5555` 无线连接

**MIUI 屏幕共享限制：**
- MIUI 的「屏幕共享」功能需要对方安装小米会议/小米通话 App，和 scrcpy 是不同机制
- scrcpy 直接读取 framebuffer，不依赖 MIUI 屏幕共享，可正常使用
- 部分 MIUI 平板有「平板助手」限制后台进程，可能影响长时间投屏

---

## 坑点汇总

### 1. ~/scrcpy-phone 选1报 "Could not find ADB device 192.168.8.204:5555"
MI8 无线调试未开启。需要 USB 连一次执行 `adb -s <设备ID> tcpip 5555` 后才能无线连接。
首次连接 USB 时手机会弹出「允许 USB 调试」，必须点「允许」才能继续，否则 `adb devices` 显示 `unauthorized`。

**排查顺序：**
1. 下拉通知栏 → 点击 USB 通知 → 确认是「文件传输(MTP)」或「PTP」，不是「仅充电」
2. 开发者选项 → USB 调试已开启
3. 小米额外：开发者选项 → 「USB 调试（安全设置）」已开启
4. 重新插拔 USB 线，等待授权弹窗 → 点「允许」

### 2. scrcpy 找不到 adb
scrcpy 硬编码在 `~/.local/bin/adb` 找 adb，PATH 有没有都不行。

**修复（M4 Mac mini）:**
```bash
ln -sf ~/adb-tools/platform-tools/adb ~/.local/bin/adb
```

**验证 adb 正常:**
```bash
adb kill-server && sleep 2 && adb start-server && adb devices -l
```
正常输出示例：
```
d0b859af               device product:dipper model:MI_8 device:dipper transport_id:1
```

### 3. "At most one device selector option may be passed"
同时传了 `-s`（指定设备）和 `--tcpip`（TCP/IP 模式），二选一，不能共存。
```bash
# 错误 ❌
scrcpy -s 192.168.8.248:5555 --tcpip=192.168.8.248:5555

# 正确 ✅
scrcpy -s 192.168.8.248:5555
```

### 4. 无线调试需要同一局域网
`adb connect` 和 scrcpy 无线模式要求 Mac 和手机在同一网段。Mac mini M4 有线网卡 192.168.8.x，无线网卡 192.168.0.x，确保手机和 Mac 在同一网段。

### 5. MIUI 屏幕共享限制
MIUI 的「屏幕共享」需要对方有小米 App，scrcpy 不依赖 MIUI，可正常使用。

### 6. Android 10 音频不支持
scrcpy 在 Android 10 上不支持音频（需 Android 11+），投屏无声音属正常现象。

### 7. 多设备冲突
USB 和无线同时连接时 `adb devices` 显示两个设备，部分命令报 `more than one device/emulator`。
```bash
# 只保留无线，断开 USB
adb disconnect <USB设备ID>
adb devices -l  # 确认只剩无线 IP
```

### 8. 设备重启后无线调试失效
无 Root 时 `adb tcpip 5555` 在锁屏待机/休眠时不丢，只有关机重启才失效。日常使用只需每次重启后 USB 开一次。

---

## 验证步骤

### 验证 A — scrcpy 能显示手机画面

```bash
# 1. 确认设备已连接
adb devices -l
# 输出类似：d0b859af ... product:dipper model:MI_8

# 2. 启动 scrcpy
phone
# 或
scrcpy -s 192.168.8.204:5555 --always-on-top
```

**验证成功：** Mac 窗口显示手机画面，鼠标点击/键盘输入可控制手机。

### 验证 B — lamda 能连接

```bash
# 1. 确认 Shizuku 在手机上运行
adb shell "dumpsys activity services | grep shizuku"

# 2. 测试 lamda 连接
python3 -c "
import lamda
client = lamda.Client()
d = client.connect(host='192.168.8.204', port=5555, use_shizuku=True)
print('连接成功:', d.device_info())
d.shell('echo hello')
"
```

**验证成功：** 输出设备信息，`echo hello` 返回 `hello`。

### 验证 C — 无线调试持久化（有 root）

```bash
# 有 root 设备设置持久化
adb shell su -c "setprop persist.adb.tcp.port 5555"

# 重启验证
adb reboot
adb connect 192.168.8.204:5555
adb shell echo "无线调试持久化成功"
```

---

## 快速命令速查

```bash
# 连接 MI 8
adb connect 192.168.8.204:5555 && phone

# 连接平板 MRX-W29
adb connect 192.168.8.248:5555 && pad

# 查看已连接设备
adb devices -l

# 断开设备
adb disconnect 192.168.8.204:5555

# 重启 adb 服务
adb kill-server && adb start-server

# 截图保存到桌面
adb shell screencap /sdcard/screen.png && adb pull /sdcard/screen.png ~/Desktop/
```