---
name: android-lamda
description: "FIRERPA lamda安装排障 Android远程控制接口。Use when lamda装不上连不上报错的排查"
tags: [android, lamda, firerpa, remote-control]
triggers:
  - lamda
  - FIRERPA
  - firerpa
  - Android黑屏
  - 虚拟显示
  - 手机远程控制
  - file broken
---

# FIRERPA lamda — Android 远程控制

FIRERPA lamda v10.4: https://github.com/firerpa/lamda。核心能力：WebRTC 远程桌面、UI 自动化（含虚拟屏）、内置 Frida/MCP。

## 唯一正确的安装方式：Magisk 模块（两种入口）

**❌ 不要用 tar.gz 包直接解压** —— `.pyc` 是 root 权限存的，非 root 读不了，报 `CRITICAL failed (file broken)`。

**✅ 正确：Magisk 模块包**
Releases: https://github.com/firerpa/lamda/releases/tag/v10.4

| 资产名 | 大小 | 用途 |
|--------|------|------|
| lamda-magisk-module.zip | 437.9 MB | ✅ 装这个 |
| lamda-server-arm64-v8a.tar.gz | 196.1 MB | ❌ tar 有权限问题 |
| lamda-client-py-10.4.tar.gz | 68.4 KB | pip 客户端包 |

### 安装步骤（方式一：Magisk App 图形界面）

1. 下载 `lamda-magisk-module.zip` 到手机 `/sdcard/Download/`
2. Magisk App → 模块（底部 Tab）→ 从本地安装 → 选 zip → 刷入 → 重启

### 安装步骤（方式二：命令行（推荐，更可靠））

```bash
# 手机端用 Magisk CLI 直接安装（无需图形界面）
su -c 'magisk --install-module /sdcard/Download/lamda-magisk-module.zip'
# 输出 "Please reboot your device" 后手动重启
adb reboot
```

方式二成功率更高，Magisk App UI 安装在 MIUI 上经常报 "No boot image found"。

### 安装后验证

```bash
# 重启后等待约 25 秒（service.sh 有 sleep 25）
adb connect <当前IP>:5555

# 检查模块是否在正确路径
adb shell "su -c 'ls /data/adb/modules/lamda/'"

# 检查端口监听（65000 = 0x15B3）
adb shell "cat /proc/net/tcp | grep ' 0A '"   # 找 0x15B3
```

### 服务启动逻辑

模块安装后，Magisk 在 boot 时执行 `/data/adb/modules/lamda/service.sh`：

```sh
sleep 25   # 等待系统完全启动
export ca_store_remount=true
sh /data/adb/modules/lamda/server/bin/launch.sh --port=65000
```

**注意**：service.sh 里有 `sleep 25`，所以重启后约 25 秒服务才就绪。

## 验证

```bash
# 检查进程
adb -s 192.168.0.44:5555 shell "ps -A | grep lamda"
# 测试端口
curl -s --connect-timeout 3 http://192.168.0.44:65000
# Python 客户端
pip3 install lamda
python3 -c "
from lamda.client import Device
d = Device('192.168.0.44', 65000)
print(d.take_screenshot(60))
"
```

## 故障排除

### 服务未启动（端口 65000 不通）
service.sh 有 `sleep 25`，等待 25 秒再试。若仍然无响应，手动启动：
```bash
adb shell "su -c 'sh /data/adb/modules/lamda/server/bin/launch.sh --port=65000 &'"
```

### "failed (file broken"
tar.gz 包的 `.pyc` 是 root 权限，非 root 读不了。**解法：** 用 Magisk 模块安装。

### "INSTALL_FAILED_USER_RESTRICTED"
MIUI 阻止侧载。**解法：** 开启「允许安装未知来源应用」。

### curl 下载超时
**解法：** 用 `https://gh-proxy.com/` 镜像。

### Magisk App 安装报 "No boot image found"
MIUI system-as-root 设备上 Magisk App UI 无法直接装模块 zip。**解法：** 用命令行安装：
```bash
su -c 'magisk --install-module /sdcard/Download/lamda-magisk-module.zip'
```

### 重启后 adb 连不上
手机重启后 WiFi IP 会变。先用 USB 连接，再切 TCP 模式：
```bash
adb usb
adb devices -l   # 找 transport_id
adb -s <serial> tcpip 5555
adb connect <新IP>:5555
```

### adb shell 权限变非 root（shell 用户，不是 root）
Magisk su 仍然有效，用 `su -c` 提权：
```bash
adb shell "su -c 'ls /data/adb/modules/lamda/'"
```

## Python 客户端 API

```bash
pip3 install lamda
python3 -c "
from lamda.client import Device
d = Device('192.168.8.204', 65000)
print(d.device_info())          # 设备信息
raw = d.take_screenshot(60)     # 截图
print(len(raw.getvalue()), 'bytes')
"
```

| 操作 | 方法 |
|------|------|
| 截图 | `d.screenshot()` 或 `d.take_screenshot(timeout)` |
| 点击 | `d.click(x, y)` |
| 滑动 | `d.swipe(x1, y1, x2, y2)` 或 `d.swipe_points([(x,y)...])` |
| 长按 | `d.long_click(x, y)` |
| 文本输入 | `d.input_text('hello')` |
| 按键 | `d.press_keycode(3)` HOME / `d.press_keycode(4)` BACK / `d.press_keycode(26)` 电源 |
| 电源熄屏 | `d.sleep()` |
| 唤醒 | `d.wake_up()` |
| OCR | `d.ocr()` |
| 虚拟显示 | `d.create_virtual_display(w, h, dpi)` — **仅 Android 11+（SDK 30+）** |
| 设备信息 | `d.device_info()` |
| 当前应用 | `d.current_application()` |
| 锁屏状态 | `d.is_screen_locked()` |
| 屏幕状态 | `d.is_screen_on()` |

> ⚠️ **Android 10 (SDK 29) 不支持虚拟显示**。`create_virtual_display` 会报 `CompatibilityException: Virtual display feature requires Android 11+`。MI 8 (dipper) 出厂 Android 9，升级到 10，无法使用虚拟显示。

## 设备 IP（重启后会变！）

**小米 MI 8 (dipper)：** 重启后 IP 从 `192.168.0.44` 变为 `192.168.8.204`，ADB 端口 `5555`。

重新连接流程：
```bash
adb usb                              # 先切回 USB
adb devices -l                       # 找 transport_id (如 d0b859af)
adb -s <serial> tcpip 5555           # 开启无线调试
adb connect 192.168.8.204:5555       # 用新 IP 连接
```

## adb shell 权限说明

`adb shell` 默认是用户 `shell`（uid 2000），不是 root。Magisk su 仍然有效：
```bash
adb shell "id"                    # uid=2000(shell)
adb shell "su -c id"             # uid=0(root) — 用 su -c 提权
```

## 已知限制

- **Android 10 虚拟显示不可用** — `create_virtual_display` 需要 Android 11+
- **MIUI 阻止侧载** — 报 `INSTALL_FAILED_USER_RESTRICTED`，需开启「允许安装未知来源应用」
- **Magisk App UI 安装模块失败** — MIUI system-as-root 上报 "No boot image found"，用 `magisk --install-module` 命令行安装
- **curl 下载超时** — 用 `https://gh-proxy.com/` 镜像
- **tar.gz 包有权限问题** — `.pyc` 是 root 权限存的，非 root 读不了报 `failed (file broken)`，只用 Magisk 模块安装
