---
name: android-control
description: 手机控制投屏装App清存储 scrcpy/adb/lamda。Use when 控制安卓手机或清理手机
version: 1.1.0
author: Hermes Agent
license: MIT
tags: [android, scrcpy, adb, miui, remote-control, lamda, phone-maintenance]
metadata:
  hermes:
    tags: [android, adb, scrcpy, phone-maintenance]
    related_skills: [hermes-humanlike-ops]
required_commands: [adb, scrcpy]
setup_status: user-required
triggers:
  - android
  - 手机控制
  - scrcpy
  - adb
  - MIUI
  - 远程控制手机
  - 刷课时
  - 答题
  - 自动化手机App
---

# Android Control — Mac 控制 Android 设备

Mac mini M4 (macOS 26.5) 上通过 scrcpy 投屏控制 Android，支持 USB 有线、无线调试、FIRERPA lamda 远程控制两种方案。覆盖小米手机 MI 8 和小米平板 MRX-W29。

## When to Use

控制/投屏安卓手机、开关无线调试、清理手机存储、侧载 App、装官方 APK、远程控制手机。

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
# 注意：tcpip 打印 "restarting in TCP mode port: 5555" ≠ 端口已监听，
# 第一次 connect 可能超时，等 2-3 秒重试一次即可
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

## 设备维护（存储清理 / 装 App）

清理和装 App 的完整流程、可删与绝不能删的清单、APK 校验、**升级不丢配置（包名变更判断、adb backup 盲区、用 dex 扫类名定位隐藏迁移入口、离线导出/导入实测流程）**见 `references/device-maintenance.md`。
铁律：清理前先分类并向用户确认范围；账号数据、刷机备份、lamda 运行时一律不动。
升级铁律：包名或大版本变了，**不要**直接搬数据目录或改包名 restore，先扫 dex 找 App 自带的迁移 Activity。

## 熄屏 / 锁屏下操作

用户锁屏后 adb 操作不中断；点亮、判定锁屏态、调 PIN 盘解锁的完整命令见 `references/headless-operation.md`。
铁律：PIN 只在会话内存用，不落盘。

## App 界面自动化（刷课时 / 答题 / 填表）

看页面 → dump 控件拿 bounds → `input tap` 的固定循环、引导页翻页、登录墙处理、输入框与重试次数陷阱见 `references/app-ui-automation.md`。
铁律：不主动索要密码；用户主动给出自己设备的凭据并要求代填时照做，密码值不落盘、不复述。

## 坑点汇总

### 1. ~/scrcpy-phone 选1报 "Could not find ADB device 192.168.8.204:5555"
MI8 无线调试未开启。需要 USB 连一次执行 `adb -s <设备ID> tcpip 5555` 后才能无线连接。
首次连接 USB 时手机会弹出「允许 USB 调试」，必须点「允许」才能继续，否则 `adb devices` 显示 `unauthorized`。

**排查顺序：**
1. 下拉通知栏 → 点击 USB 通知 → 确认是「文件传输(MTP)」或「PTP」，不是「仅充电」
2. 开发者选项 → USB 调试已开启
3. 小米额外：开发者选项 → 「USB 调试（安全设置）」已开启
4. 重新插拔 USB 线，等待授权弹窗 → 点「允许」

**持续 unauthorized（重插 USB、重启 adb 都不弹窗或点了「允许」仍不行）：**
Mac 侧 ADB RSA 公钥与手机记录不一致（旧 key 残留、对话框曾被误拒绝）时，删掉密钥强制重新生成并触发全新授权弹窗：
```bash
rm -f ~/.android/adbkey ~/.android/adbkey.pub
adb kill-server && adb start-server
adb devices -l   # 手机上此时弹出「是否允许 USB 调试」→ 点「允许」（勾选「一律允许」）
```
删 key 后 adb 下次连接自动生成新 keypair，手机把它当新电脑重新询问，这是唯一能绕开"记住的拒绝状态"的办法。

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

### 9. 华为平板 MRX-W29 无无线调试开关（老版本 Android）

部分华为/旧版 Android 设备系统设置里没有「无线调试」开关，无法直接点开。正确流程：

```bash
# Step 1 — USB 有线连接平板（确保平板已授权 USB 调试）
adb devices -l
# 输出: S8M6R20A27000680 device ... model:MRX_W29

# Step 2 — 通过 USB 开启 TCP 调试模式（无需平板操作）
adb tcpip 5555
# 输出: restarting in TCP mode port: 5555

# Step 3 — 等待 3 秒后无线连接
sleep 3 && adb connect 192.168.8.248:5555
# 输出: connected to 192.168.8.248:5555

# Step 4 — 验证
adb -s 192.168.8.248:5555 shell echo "wireless OK"
# 输出: wireless OK ✅
```

**之后 USB 线可拔掉**，无线连接持续有效。设备重启后需重新走 Step 1-3。

### 10. 设备重启后先查连接，不要假设无线失效

重启后**先** `adb devices -l` 看无线是否还在，再决定要不要 USB：设置过 `persist.adb.tcp.port` 的设备重启后无线会自己回来，没设置的才需要 USB 重开。重启后立刻连也可能短暂未就绪，隔几秒重查一次。

**重启后第一次访问内部存储前必须解锁屏幕**：未解锁时 `/storage/emulated/0` 写文件报 `Required key not available`（FBE 密钥未加载），`/sdcard` 的符号链接链也可能暂时指向不存在的目标。先按 `references/headless-operation.md` 用 PIN 解锁，再 `cp`/`mkdir`。这条不是 adb 断连，命令能跑但文件操作失败，容易误判成 root 或目录问题。

### 11. 排查平板无线调试是否开启

平板无线调试已开启但端口不通（`adb connect` 报 `Connection refused`）：
- 平板可能切换了 IP → USB 还连着时用 `adb shell ip route` 直接读当前 IP（输出中 `src <IP>` 即设备地址），免翻手机设置；USB 已拔则去设置 → 关于手机 → 状态信息 → IP 地址
- 无线调试端口可能变了 → 去设置 → 开发者选项 → 无线调试查看当前端口
- 平板和 Mac 不在同一网段 → 确认都在 192.168.8.x

### 12. Hermes 终端里 adb 不在 PATH
Hermes 的 shell 找不到 `adb`，但符号链接 `~/.local/bin/adb` 已存在 → 所有 adb 命令用全路径 `/Users/aimac/.local/bin/adb`，或在命令前 `export PATH="/Users/aimac/.local/bin:$PATH"`。scrcpy 自己硬编码该路径（见坑点2），不受影响。

### 13. 清理把账号或刷机备份删掉
按 `references/device-maintenance.md` 的三类清单执行。聊天软件的媒体缓存可再生可删，但账号目录、`MicroMsg`、刷机镜像、`/data/local/tmp/server` 删了会导致重新登录或设备变砖。

### 14. `magisk --stop` 会摧毁 root，直到重启
`magisk --stop` 不是"重启守护进程"——它移除**所有** Magisk 更改：`su` 二进制消失、magiskd 进程消失、magisk 挂载消失，之后 `su` 全路径都报 `inaccessible or not found`，只能重启设备让 init 重新注入才能恢复。
想让 DenyList 或新配置生效时，正确做法是 `am force-stop <pkg>` 后重新拉起 App，或直接重启设备；**绝不在没有明确目的时执行 `magisk --stop`**，尤其不要在一条组合命令里顺手带上它——它会静默生效，而同一行后面的 `su` 调用才报错，容易被误判成"命令没生效"。

### 15. 根检测 App 闪退 ≠ 包坏了
银行/政务 App 在 root 设备上由加固库在 `JNI_OnLoad` 主动 `abort`。诊断顺序与 Zygisk DenyList 修复步骤见 `references/device-maintenance.md` 的"Root 设备上的 App 闪退"。
**不要**因为日志里出现 `ClassNotFoundException` 或 ABI 字样就去换 arm64 包——官方各渠道 MD5 相同时根本没有第二个包。

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