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
  - 学法减分
  - 答题
  - 自动化手机App
---

# Android Control — Mac 控制 Android 设备

Mac mini M4 (macOS 26.5) 上通过 scrcpy 投屏控制 Android，支持 USB 有线、无线调试、FIRERPA lamda 远程控制两种方案。覆盖小米手机 MI 8 和华为平板 MRX-W29。

## When to Use

控制/投屏安卓手机、开关无线调试、清理手机存储、侧载 App、装官方 APK、远程控制手机。

---

## 已知设备

| 设备 | 型号 | IP | USB调试端口 | scrcpy命令 | 备注 |
|------|------|-----|------------|-----------|------|
| 小米 MI 8 | dipper | 192.168.8.204 | 5555 | `~/scrcpy-phone` 选1 | Android 10, MIUI 12, FIRERPA lamda✅ |
| 华为平板 MRX-W29 | HWMRX | 动态读取（WiFi 192.168.0.x） | 5555 | `~/scrcpy-phone` 选2 | Android 12 |

> Mac mini M4 有线网段 192.168.8.x，无线网段 192.168.0.x。无线 adb 走 WiFi 段，设备 IP 由 DHCP 分配、重启或换网就会变——**绝不把 IP 写死在脚本或命令里**：USB 还连着时用 `adb -s <USB序列号> shell ip route` 取 `src <IP>`；已无线连接时用 `adb devices -l` 里 model:MRX_W29 那条 `IP:端口`（解析规则见坑点 11）。

### 统一入口脚本 ~/scrcpy-phone

两台设备共用一个交互脚本（选 1=MI8，选 2=MRX-W29）。平板端**动态解析 IP**，不写死：

```bash
ADB=/Users/aimac/.local/bin/adb
find_pad_ip() {
  $ADB devices -l | awk '/model:MRX_W29/ && $1 ~ /:[0-9]+$/ {print $1; exit}'
}
ensure_pad_wireless() {
  IP=$(find_pad_ip)
  [ -n "$IP" ] && return 0
  USB=$($ADB devices -l | awk '/model:MRX_W29/ && $1 !~ /:/ {print $1; exit}')
  [ -z "$USB" ] && return 1
  IP=$($ADB -s "$USB" shell ip route 2>/dev/null | grep -o 'src [0-9.]*' | head -1 | awk '{print $2}')
  [ -z "$IP" ] && return 1
  $ADB -s "$USB" tcpip 5555 >/dev/null 2>&1
  sleep 3
  $ADB connect "$IP:5555" >/dev/null 2>&1
  find_pad_ip
}
```

选 2 时先 `ensure_pad_wireless`，把拿到的 `$IP` 传给 `scrcpy -S -s "$IP" ...`。MI8 同理：IP 变了就 USB 重开 tcpip 后重新 connect。改完用 `bash -n ~/scrcpy-phone` 验证语法。

> 注意：新设备首次都要 USB 连一次执行 `adb -s <id> tcpip 5555`；日常无需重开。

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

**pad 脚本** (`~/.local/bin/pad`)：优先用 `~/scrcpy-phone` 选 2（自动解析 IP）；手写时别写死 IP：
```bash
#!/bin/bash
IP=$(/Users/aimac/.local/bin/adb devices -l | awk '/model:MRX_W29/ && $1 ~ /:[0-9]+$/ {print $1; exit}')
[ -z "$IP" ] && { echo "平板未连接"; exit 1; }
exec scrcpy -S -s "$IP" --always-on-top --window-title "MRX-W29" "$@"
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
   pad      # 华为平板 MRX-W29
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
# adb connect <动态读到的IP>:5555  # 平板（见坑点 11）
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

## 华为平板 MRX-W29 特别说明

| 项目 | 值 |
|------|---|
| 型号 | 华为平板 MRX-W29（`model:MRX_W29` / `device:HWMRX`，Android 12，华为桌面 `com.huawei.android.launcher`） |
| IP | 动态读取，WiFi 段 192.168.0.x（见坑点 11） |
| USB 调试端口 | 5555 |
| 连接命令 | `adb connect <读到的IP>:5555` |
| scrcpy 命令 | `scrcpy -S -s <IP> --always-on-top --window-title "MRX-W29"` |

**USB 无线调试配置步骤（每个设备只需一次）:**
1. USB 有线连接平板
2. `adb devices` 确认识别
3. `adb -s <设备ID> tcpip 5555` 开启 TCP 模式
4. 拔掉 USB 线
5. 从 USB 读 IP 后无线连接：`IP=$(adb -s <设备ID> shell ip route | grep -o 'src [0-9.]*' | head -1 | awk '{print $2}')` → `adb connect "$IP:5555"`（详见坑点 9）

**机型归属**：MRX-W29 是华为机，不是小米平板——MIUI 专属项（「USB 调试（安全设置）」、MIUI 屏幕共享、平板助手限制）都不适用，别按 MIUI 流程排查。

---

## 设备维护（存储清理 / 装 App）

清理和装 App 的完整流程、可删与绝不能删的清单、APK 校验、**升级不丢配置（包名变更判断、adb backup 盲区、用 dex 扫类名定位隐藏迁移入口、离线导出/导入实测流程）**见 `references/device-maintenance.md`。
铁律：清理前先分类并向用户确认范围；账号数据、刷机备份、lamda 运行时一律不动。
升级铁律：包名或大版本变了，**不要**直接搬数据目录或改包名 restore，先扫 dex 找 App 自带的迁移 Activity。

## 熄屏 / 锁屏下操作

用户锁屏后 adb 操作不中断；点亮、判定锁屏态、调 PIN 盘解锁的完整命令见 `references/headless-operation.md`。
铁律：PIN 只在会话内存用，不落盘。

## App 界面自动化（刷课时 / 答题 / 填表）

看页面 → dump 控件拿 bounds → `input tap` 的固定循环、引导页翻页、登录墙处理、输入框与重试次数陷阱、**H5/WebView 页 dump 拿不到控件时的切片 OCR 定位法**、政务业务审核闸门、长时挂机学习的屏幕常亮/轮询/随机人脸抓拍交接、原生考试页答题与看图题交接见 `references/app-ui-automation.md`。
铁律：不主动索要密码；用户主动给出自己设备的凭据并要求代填时照做，密码值不落盘、不复述。

**长任务实时盯屏铁律**：挂机学习/答题这类长时任务，禁止用单个长 `sleep 280` 阻塞完再看——脚本早就跑完却迟迟没发现＝浪费时间，用户明确不满过。正确做法：`terminal(background=True, notify=[完成标志性文字])` 事件驱动，完成瞬间就收到通知；或每 15–30 秒短轮询状态/完成标记文件。检测到终态（提交成功 / 去考试 / 学习完成 / 累积学时已满）当轮立刻推进下一步并向用户汇报，不空转、不中途分神做别的。

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
`adb connect` 和 scrcpy 无线模式要求 Mac 和手机在同一网段。Mac mini M4 有线网卡 192.168.8.x，无线网卡 192.168.0.x；手机/平板走 WiFi 拿到的是 192.168.0.x，无线 adb 必须在该段，不要拿旧的有线段 IP 去 connect。

### 5. MIUI 屏幕共享限制
MIUI 的「屏幕共享」需要对方有小米 App，scrcpy 不依赖 MIUI，可正常使用。

### 6. Android 10 音频不支持
scrcpy 在 Android 10 上不支持音频（需 Android 11+），投屏无声音属正常现象。

### 7. 多设备冲突
USB 和无线同时连接时 `adb devices` 显示两个设备，不带 `-s` 的命令报 `more than one device/emulator`。**优先给每条 adb 命令加 `-s <目标>`，不必拔 USB**——开无线调试时本来就需要 USB 在线读 IP。只有确实要跑不带 `-s` 的批量命令时才 `adb disconnect <USB设备ID>`。

### 9. 华为平板 MRX-W29 无无线调试开关（老版本 Android）

部分华为/旧版 Android 设备系统设置里没有「无线调试」开关，无法直接点开。正确流程：

```bash
# Step 1 — USB 有线连接平板（确保平板已授权 USB 调试）
adb devices -l
# 输出: S8M6R20A27000680 device ... model:MRX_W29

# Step 2 — 通过 USB 开启 TCP 调试模式（无需平板操作）
adb tcpip 5555
# 输出: restarting in TCP mode port: 5555

# Step 2.5 — 从 USB 读当前 IP（DHCP 会变，绝不写死）
IP=$(adb -s S8M6R20A27000680 shell ip route | grep -o 'src [0-9.]*' | head -1 | awk '{print $2}')

# Step 3 — 等待 3 秒后无线连接
sleep 3 && adb connect "$IP:5555"
# 输出: connected to <IP>:5555

# Step 4 — 验证
adb -s "$IP:5555" shell echo "wireless OK"
# 输出: wireless OK ✅
```

**之后 USB 线可拔掉**，无线连接持续有效。设备重启后需重新走 Step 1-3。

### 10. 设备重启后先查连接，不要假设无线失效

重启后**先** `adb devices -l` 看无线是否还在，再决定要不要 USB：设置过 `persist.adb.tcp.port` 的设备重启后无线会自己回来，没设置的才需要 USB 重开。重启后立刻连也可能短暂未就绪，隔几秒重查一次。

**重启后第一次访问内部存储前必须解锁屏幕**：未解锁时 `/storage/emulated/0` 写文件报 `Required key not available`（FBE 密钥未加载），`/sdcard` 的符号链接链也可能暂时指向不存在的目标。先按 `references/headless-operation.md` 用 PIN 解锁，再 `cp`/`mkdir`。这条不是 adb 断连，命令能跑但文件操作失败，容易误判成 root 或目录问题。

### 11. 排查平板无线调试是否开启

平板无线调试已开启但端口不通（`adb connect` 报 `Connection refused`）：
- 平板可能切换了 IP → USB 还连着时用 `adb -s <USB序列号> shell ip route` 直接读当前 IP（输出中 `src <IP>` 即设备地址），免翻手机设置；已无线连接则从 `adb devices -l` 解析：
  ```bash
  /Users/aimac/.local/bin/adb devices -l | awk '/model:MRX_W29/ && $1 ~ /:[0-9]+$/ {print $1; exit}'
  ```
  **解析 `adb devices -l` 必须匹配第一字段 `$1`，不能把 `:端口$` 锚到整行末尾**——`-l` 会在地址后追加 `product:`/`model:`/`transport_id:` 等元数据，行尾根本不是端口。BSD awk 不支持 `{4}` 这类区间量词，用 `+` 或显式重复字符。
- 无线调试端口可能变了 → 去设置 → 开发者选项 → 无线调试查看当前端口
- 平板和 Mac 不在同一网段 → 无线 adb 要同在 192.168.0.x（Mac 的 WiFi 段），USB 调试才是 192.168.8.x；别拿有线段的旧 IP 去 connect

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

### 16. 无线 adb 断了先别重连：USB 还在线就直接走 USB

设备熄屏/休眠后无线 `adb connect` 可能报 `Network is unreachable`，但 `adb devices -l` 里 USB 那条往往仍是 `device`。此时别折腾重连或扫网段，直接给每条命令加 `-s <USB序列号>` 继续操作——无线只是通道，USB 一样能注入输入、截图、dump。任务收尾再视需要恢复无线。

### 17. SmsForwarder v3.5.0 换包名后权限全丢（免 root 修复）
v3.5.0 把包名从 com.idormy.sms.forwarder 改成 cn.ppps.forwarder，Android 运行时权限跟包名走，从旧版迁移后新包名所有权限 granted=false（READ_SMS/RECEIVE_SMS 等还带 AUTO_REVOKED），app 报权限不足——这不是需要 root，重新授权即可。
修复（USB adb，无需 root）：`pm grant cn.ppps.forwarder android.permission.<PERM>`，PERM 遍历 READ_SMS / RECEIVE_SMS / RECEIVE_MMS / RECEIVE_WAP_PUSH / READ_CALL_LOG / READ_PHONE_STATE / READ_PHONE_NUMBERS / READ_CONTACTS / GET_ACCOUNTS / ACCESS_FINE_LOCATION / READ_EXTERNAL_STORAGE 等 app 请求过的全部运行时权限。
通知读取（验证码短信关键）：组件 `cn.ppps.forwarder/.service.NotificationService`，追加到 `settings put secure enabled_notification_listeners`（保留原有条目，冒号拼接，不要覆盖）。
保活：`dumpsys deviceidle whitelist +cn.ppps.forwarder`。
华为自启动：appops 无 AUTO_START 操作，只能在 app 内「开机启动」跳系统设置手动开。
验证：`dumpsys package cn.ppps.forwarder` 的 User 0 runtime permissions 全 granted=true；输出里 User 130 那段 granted=false 是副用户，忽略。

### 18. 坐标点击全落空先查屏幕方向
`input tap` 点首页图标却进资讯、点卡片却跳导航，多半是**横竖屏翻转**导致坐标基准错了，不是控件不可点。同一台设备不同场次会在 `1600x2560`（竖）和 `2560x1600`（横）间切换，视频类页面尤其容易转横屏。每次写死坐标前先用 dump 的 bounds 现取（wrt 当前方向）。同一台设备不同场次会在 `1600x2560` 和 `2560x1600` 间切换，视频类页面尤其容易转横。注意 `wm size` 只报物理尺寸、不随旋转变化，`screencap` PNG 和 dump bounds 才是当前方向——别用 wm size 推断当下是横是竖。`input tap` 点首页图标却进资讯、点卡片却跳导航，都是坐标基准错了而不是控件不可点。

---

## 交管12123 学法减分

申请→审核→30分钟学习→20题考试→人脸认证→失败补考的完整自动化流程、刷题循环、看图题处理、抓拍应对见 `references/xfjf-exam.md`；解锁/等抓拍/等补考开考/等最终认证的事件驱动等待脚本见 `scripts/xfjf_wait.py`（配合 `terminal(background=True, notify=True)` 落地「长任务实时盯屏铁律」）。看图题视觉方案（免费VLM实测+题库API+像素兜底，含reasoning吃token/主题色污染等坑）见 `references/vision-solution-research.md`，秒答脚本 `scripts/xfjf_vision.py`。

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

### 验证 D — 能不能操作这台设备（不投屏，Hermes 终端内可做）

用户问「能不能操作这个平板/手机」时用这条链实测，别只回一句「能」：

```bash
ADB=/Users/aimac/.local/bin/adb
D="-s <当前实际IP>:5555"
$ADB $D shell getprop ro.product.model
$ADB $D shell getprop ro.build.version.release
$ADB $D shell wm size
$ADB $D shell dumpsys battery | grep -i level
$ADB $D shell dumpsys activity activities | grep -E "mResumedActivity|topResumedActivity"
$ADB $D shell input keyevent KEYCODE_WAKEUP
sleep 1
$ADB $D shell dumpsys power | grep -m1 mWakefulness=   # Awake = 输入注入生效
$ADB $D shell screencap -p /sdcard/t.png
$ADB $D pull /sdcard/t.png /Users/aimac/.hermes/cache/scratch/t.png
file /Users/aimac/.hermes/cache/scratch/t.png          # 非空、尺寸与 wm size 一致
$ADB $D shell rm /sdcard/t.png
$ADB $D shell input keyevent KEYCODE_SLEEP             # 还原熄屏
$ADB $D shell dumpsys power | grep -m1 mWakefulness=   # Asleep
```

**验证成功**：读到机型/分辨率/电量，唤醒后 `mWakefulness=Awake`，截图文件非空且尺寸匹配。收尾把屏幕还原到操作前状态；不需要投屏时保持熄屏，符合用户后台无扰偏好。

---

## 快速命令速查

```bash
# 连接 MI 8
adb connect 192.168.8.204:5555 && phone

# 连接平板 MRX-W29（IP 动态读，见坑点 11；或 ~/scrcpy-phone 选 2 自动解析）
IP=$(/Users/aimac/.local/bin/adb devices -l | awk '/model:MRX_W29/ && $1 ~ /:[0-9]+$/ {print $1; exit}')
adb connect "$IP" && scrcpy -S -s "$IP" --always-on-top --window-title "MRX-W29"

# 查看已连接设备
adb devices -l

# 断开设备
adb disconnect 192.168.8.204:5555

# 重启 adb 服务
adb kill-server && adb start-server

# 截图保存到桌面
adb shell screencap /sdcard/screen.png && adb pull /sdcard/screen.png ~/Desktop/
```