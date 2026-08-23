---
name: android-root
description: Android root — Magisk boot.img 修补工作流，bootloader解锁设备。
tags: [android, root, magisk, boot-img]
triggers:
  - root手机
  - Magisk boot.img
  - boot.img root
  - su二进制
---

# Android Root — Magisk boot.img 修补工作流

不刷机保留数据的前提下给 Android 设备 root。核心：boot.img 包含 kernel+ramdisk，Magisk 在 ramdisk 注入 su 守护进程。修补 boot.img → 刷入 boot 分区 → su 激活。

---

## 必要条件

| 条件 | 要求 |
|------|------|
| Bootloader | 必须已解锁（`fastboot oem unlock`） |
| Magisk APK | v25+ 已安装 |
| boot.img | 与当前 ROM 版本匹配的未修补 boot 镜像 |
| 工具 | fastboot + Python 3 + magiskboot |

**没有 boot.img = 整个流程卡死。** boot.img 只能从官方 ROM 包获取（从设备提取需要 root，循环依赖）。

---

### boot.img 两个来源

#### 来源 1 — 官方 ROM 包（推荐）

下载设备对应 ROM 的 Fastboot 包，解压提取 `boot.img`。

**MI8 (dipper) 示例：**
```
版本: V12.0.3.0.QEAMIXM (Android 10)
CDN: https://bigota.d.miui.com/V12.0.3.0.QEAMIXM/dipper_global_images_V12.0.3.0.QEAMIXM_20211213.0000.00_10.0_global_911d49e79e.tgz
大小: ~2.4GB
解压: tar -xzf xxx.tgz → images/boot.img
```

国内 CDN 403 时换源：
- `https://xiaomiadvices.com` 页面
- `https://xmfirmwareupdater.com/miui/dipper/`
- 手机浏览器直连（手机网络可能通）

#### 来源 2 — MIUI OTA `.zip` 压缩包（内含 payload.bin）

MIUI 官方下载的完整包常是 `.zip` 内含 `payload.bin`（4GB+），没有单独的 `boot.img`。需从 payload.bin 抠出 boot 分区：

### payload-dumper 提取法（推荐）

```bash
# 安装（必须用 /usr/local/bin/python3，Python 3.14）
# 系统默认 python3 (3.11) 无 payload_dumper
/usr/local/bin/python3 -m pip install --index-url https://pypi.tuna.tsinghua.edu.cn/simple payload-dumper
```

```python
#!/usr/local/bin/python3
import zipfile, os
from payload_dumper.dumper import Dumper

zip_path = '/path/to/miui_xxx.zip'
out_dir = '/tmp/miui_boot'
os.makedirs(out_dir, exist_ok=True)

with zipfile.ZipFile(zip_path, 'r') as z:
    with z.open('payload.bin') as f:
        d = Dumper(f, out_dir, images='boot')
        d.run()        # 注意：是 run() 不是 dump()

# 产物: /tmp/miui_boot/boot.img
```

**⚠️ 关键坑 — boot 分区大小验证（必须步骤）：**
```bash
# Step 1: 查设备 boot 分区大小
fastboot getvar partition-size:boot
# 返回 0x4000000 = 64MB

# Step 2: 查 boot.img 文件大小
ls -lh boot.img
# 如果 boot.img > boot 分区，fastboot flash 和 fastboot boot 都会失败

# Step 3: 验证 boot.img 格式（不解压）
file boot.img
# 必须返回: "Android bootimg, kernel ..."

# Step 4: 用 fastboot boot 先测试（不写分区）
fastboot boot boot.img
# 成功则显示 "BOOTING"，失败则报 "Invalid Boot image Header"
# 即使 boot.img 大小合适，如果版本不匹配也会失败
```

**常见失败模式：**
- `FAILED (remote: 'Error flashing partition : Volume Full')` → boot.img > boot 分区
- `FAILED (remote: 'Invalid Boot image Header: Bad Buffer Size')` → boot.img 版本与设备不匹配（即使大小合适）
- `fastboot flash` 成功但仍 bootloop → **大小匹配 ≠ 版本匹配**，必须用 `fastboot boot` 先测试
- OTA 包 boot.img 可能是给更大分区设计的全局镜像，必须和目标设备分区匹配

**查设备版本（不解压）：**
```python
import zipfile
with zipfile.ZipFile('xxx.zip') as z:
    print(z.read('META-INF/com/android/metadata').decode())
```

**payload.bin 结构：** `CrAU` 魔数 → DeltaArchiveManifest protobuf → 各分区 operations（REPLACE/BZ/XZ/ZERO）

**适用场景：** MIUI 完整包（文件名含 `OS*UGUINXM` / `fastboot_*`），而非 TWRP 卡刷包（`.zip` 内直接含 `boot.img`）

### 来源 2 — LineageOS/TWRP（最后手段）

⚠️ **版本兼容性风险：** LineageOS boot.img 基于 LineageOS kernel，**不兼容 MIUI**，WiFi/基带/指纹可能失效。只作为无官方镜像时的备选。

```
LineageOS: https://download.lineage.microg.org/dipper/
TWRP: https://dl.twrp.me/dipper/
```

---

## Step-by-Step 流程

### Step 1 — 获取 boot.img

```bash
# 直接下载（CDN 可能 403）
curl -L "https://bigota.d.miui.com/V12.0.3.0.QEAMIXM/..." -o rom.tgz

# 解压提取 boot.img
tar -xzf rom.tgz
ls images/boot.img
```

**绕过 CDN 403：** 用 FIRERPA 控制手机浏览器下载：
```python
from lamda.client import Device
d = Device('192.168.0.44', 65000)
d.start_activity(
    action='android.intent.action.VIEW',
    data='https://bigota.d.miui.com/V12.0.3.0.QEAMIXM/...',
    package='com.android.browser'
)
```

### Step 2 — Magisk 修补 boot.img（纯 CLI，无需 Magisk app UI）

**新方法（推荐）：** 从 Magisk APK 提取 magiskboot，直接在手机上用命令行修补，无需打开 Magisk app。

```python
# Step 2a — 从 APK 提取所有必要二进制
import zipfile
with zipfile.ZipFile('Magisk-v30.7.apk') as z:
    files = {
        'lib/arm64-v8a/libmagiskboot.so':  'magiskboot',     # 静态 ELF → chmod +x 直接运行
        'lib/arm64-v8a/libmagisk.so':      'magisk',          # 动态 ELF
        'lib/arm64-v8a/libmagiskinit.so':  'magiskinit',      # 静态 ELF
        'lib/arm64-v8a/libinit-ld.so':     'init-ld.so',
        'assets/stub.apk':                 'stub.apk',
    }
    for src, name in files.items():
        with open(f'/tmp/{name}', 'wb') as f:
            f.write(z.read(src))
```

```bash
# Step 2b — Push 到手机
for f in magiskboot magisk magiskinit stub.apk; do
    adb push $f /data/local/tmp/$f
done
adb shell "chmod 755 /data/local/tmp/magiskboot /data/local/tmp/magisk"

# Step 2c — 在手机上解包 boot.img（假设 boot.img 已在 /data/local/tmp/）
adb shell "cd /data/local/tmp && ./magiskboot unpack boot.img"

# Step 2d — 修补 ramdisk
adb shell "cd /data/local/tmp && ./magiskboot cpio ramdisk.cpio patch"

# Step 2e — 重新打包
adb shell "cd /data/local/tmp && ./magiskboot repack boot.img new-boot.img"
```

**magiskboot.so 实为静态 ELF：** 文件名是 `.so` 但实际是静态链接可执行文件，push 到手机 `chmod +x` 后直接运行，无需任何动态库。

**旧方法（Magisk app UI）：**
1. 打开 Magisk → 安装 → 选择「选择并修补一个文件」
2. 选 boot.img → 自动修补 → 输出 `magisk_patched-*.img`
3. `adb pull /sdcard/Download/magisk_patched-*.img`

### Step 3 — 刷入 boot.img（不动 userdata）

```bash
# 进 Fastboot
adb reboot bootloader

# 刷入（只写 boot，不动 userdata）
fastboot flash boot magisk_patched.img
fastboot reboot
```

### Step 4 — 验证（两步验证）

```bash
# 验证 1: magiskd 进程存在
adb shell "ps -A | grep magiskd"
# 应显示: root 671 ... S magiskd

# 验证 2: su 可用（必须！magiskd 在 ≠ su 生效）
adb shell "su -c id"
# 输出 uid=0(root) 即 root 激活成功
# 若报 Permission denied → SELinux 策略问题，见下方「SELinux 拦截 su」坑点
```

---

## FIRERPA lamda Python API（实测可用）

连接：
```python
from lamda.client import Device
d = Device('192.168.0.44', 65000)
```

**启动命令（v10.4 专用）：**
```bash
# lamda v10.4 是 Python 模块，不是独立二进制
# server 文件在 /data/local/tmp/server/
adb shell "cd /data/local/tmp && LD_LIBRARY_PATH=/data/local/tmp/server/lib nohup /data/local/tmp/server/bin/python3.12 -m lamda --launch > /data/local/tmp/lamda.log 2>&1 &"
sleep 3
# 验证 HTTP 端口
adb shell "curl -s --connect-timeout 3 http://localhost:65000"
# 若返回空（exit 0）= 服务在跑
```

**Mac 直连 MI8 需 adb forward：**
```bash
adb forward tcp:65000 tcp:65000
python3.14 -c "
from lamda.client import Device
d = Device('127.0.0.1', 65000)
print(d.device_info())
"
```

**`failed (file broken)` 初始化失败 → 排查顺序：**
1. 旧版残留文件干扰 → `rm -rf /data/local/tmp/server && tar -xzf lamda-server-v10.4.tar.gz`
2. 权限不足（shell 用户）→ tar chown 报错可忽略，关键文件已解压
3. 服务挂了 → 看日志 `adb shell "cat /data/local/tmp/lamda.log"`
4. **"file broken" 且 su -c 提权后仍失败 → 根本原因：tar 包内文件是 root:root，.pyc 是 0600，shell 用户读不了**
   - **正确解法：安装 APK**（APK 安装时自动设正确权限）：
     ```bash
     pm install -r /data/local/tmp/server/lib/python3.12/site-packages/lamda/ime.apk
     ```
     若报 `INSTALL_FAILED_USER_RESTRICTED` → 手机上需手动点"允许"安装
   - **不要**手动 tar 解压后 chown — `.pyc` 文件是 0600 root:root，即使 `chown shell:shell` 后 shell 用户仍无读权限
   - APK 安装完成后用 su 提权启动：
     ```bash
     su -c 'LD_LIBRARY_PATH=/data/local/tmp/server/lib PYTHONPATH=/data/local/tmp/server/lib/python3.12 nohup /data/local/tmp/server/bin/python3.12 -m lamda --launch > /data/local/tmp/lamda_root.log 2>&1 &'
     ```
   - **重要：** v10.4 的 tarball 里**没有 `lamda` 二进制**，只有 Python 模块 + server/bin 工具链。启动入口是 `python3.12 -m lamda --launch`，不是 `server/bin/lamda`。

**注意：** v10.4 的 tarball 里**没有 `lamda` 二进制**，只有 Python 模块 + server/bin 工具链。不要找 `server/bin/lamda`。

**已知坑 — lamda 服务重启后失效：**
lamda 进程在设备重启后会消失，需要重新部署：
```bash
# python 路径是 /data/local/tmp/server/bin/python3.12，不是 /system/bin/python3
adb shell "LD_LIBRARY_PATH=/data/local/tmp/server/lib nohup /data/local/tmp/server/bin/python3.12 -u -m lamda --launch > /data/local/tmp/lamda.log 2>&1 &"
sleep 5
curl http://localhost:65000/status  # 返回 404 是正常的，lamda 在跑
```

**UI 操作：**

| 操作 | 代码 |
|------|------|
| 启动 App | `app = d.get_application_by_name('Magisk'); app.start()` |
| 截图 | `raw = d.take_screenshot(60); open('screen.png','wb').write(raw.getvalue())` |
| UI 布局 XML | `xml_data = d.dump_window_hierarchy(); ET.parse(BytesIO(xml_data.read()))` |
| 按键 | `d.press_keycode(code)` — code 是整数如 3=Home |
| 执行 shell 脚本 | `d.execute_script('ls /sdcard/Download/')` |
| 列出已安装 App | `d.enumerate_installed_apps()` |
| 搜索文件 | `d.execute_script('find / -name "magisk_patched*" 2>/dev/null')` |

**已知问题：**
- `start_activity` 在部分设备无效，换 `d.get_application_by_name('AppName').start()`
- FIRERPA `d.touch(x,y)` 参数格式不匹配，用 `adb shell "input tap X Y"` 代替

---

## MI8 (dipper) 参数

| 项目 | 值 |
|------|-----|
| 代号 | dipper（标准版）/ **flame（屏幕指纹版）** / ursa（UD版） |
| ROM | **V12.0.3.0.QEAMIXM (MIUI 12, Android 10)** ← 当前设备 |
| Bootloader | unlock=unlocked ✅ |
| ro.debuggable | 0（官方ROM，adb root无效）|
| **Boot分区** | **64MB (0x4000000)** ⚠️ |
| Boot分区路径 | /dev/block/bootdevice/by-name/boot |
| Magisk | v30.7 APK 已装，su 未激活 ❌ |
| FIRERPA | ✅ 192.168.0.44:65000 |
| 当前版本 | QEAMIXM（全球版），**不能用 QEACNXM（中国版）boot.img** ⚠️ |

**⚠️ MI8 Boot 分区只有 64MB。** 从最新 MIUI 14 OTA 包抠出的 boot.img 是 96MB，塞不进去。必须用对应版本的官方线刷包（Fastboot ROM）里的 boot.img。

**⚠️ 设备代号必须核实！** 用户说"标准版"可能是 flame（屏幕指纹版）。用 `fastboot getvar product` 确认。

---

## AVB 签名陷阱（重要）

**magiskboot repack 会破坏 AVB 签名。**

```
原始 boot.img:        AVB1_SIGNED, checksum=b5beb1b2...
修补后 new-boot.img:  AVB1_SIGNED, checksum=8714264e...  ← checksum不同，签名已失效
```

MIUI 开启了 verified boot（AVB），签名失效的 boot.img 会导致 bootloop。

**解法：**
1. **推荐** — 用 Magisk app 的「选择并修补一个文件」（app 内部处理 AVB 重签名）
2. **备选** — 修补 boot.img 后擦除 vbmeta 分区解除 AVB 校验：
   ```bash
   # 正确大小的 vbmeta 镜像（131072 字节）
   python3 -c "open('/tmp/vbmeta.img','wb').write(b'\\x00'*131072)"
   fastboot erase vbmeta
   fastboot flash vbmeta /tmp/vbmeta.img
   ```
3. **备选** — 用 `fastboot boot` 而非 `fastboot flash`（从 RAM 启动，不写分区，绕过签名验证）

### boot.img 版本匹配验证（本 session 新增 2026-08-12）

**即使 boot.img 大小合适，版本不匹配也会 bootloop。** 必须和当前系统版本完全一致。

**从用户提供的 dipper boot.img 提取版本信息：**
```python
import struct, os

boots = [
    '/tmp/miui_boot/boot.img',                              # OTA payload-extract, 96MB, 不匹配
    '/Users/aimac/.hermes/cache/documents/doc_4199a7ab40c9_boot.img',  # 用户发, 49MB, bootloop
    '/Users/aimac/.hermes/cache/documents/doc_a2aa901b9420_dipper.img', # 用户发, 57MB, bootloop
    '/Users/aimac/.hermes/cache/documents/doc_08c042a62206_dipper.img', # 用户发, 57MB, bootloop
]

for path in boots:
    try:
        with open(path,'rb') as f:
            f.read(8)  # magic
            kernel = struct.unpack('<I', f.read(4))[0]
            ramdisk = struct.unpack('<I', f.read(4))[0]
            f.read(8)  # addrs
            page = struct.unpack('<I', f.read(4))[0]
            os_ver = struct.unpack('<I', f.read(4))[0]
            os_patch = struct.unpack('<I', f.read(4))[0]
            h_major = struct.unpack('<H', f.read(2))[0]
            h_minor = struct.unpack('<H', f.read(2))[0]
            name = f.read(16).rstrip(b'\x00').decode('utf-8', errors='ignore')
            cmdline = f.read(512).rstrip(b'\x00').decode('utf-8', errors='ignore')
        size = os.path.getsize(path)
        print(f'{os.path.basename(path)}:')
        print(f'  size={size/1024/1024:.1f}MB kernel={kernel/1024:.0f}KB ramdisk={ramdisk/1024:.0f}KB page={page}')
        print(f'  os={os_ver>>4}.{os_ver&0xF} patch=0x{os_patch:08x} name={repr(name)}')
        print(f'  cmdline={cmdline[:100]}')
    except Exception as e:
        print(f'{path}: ERROR {e}')
```

**当前设备版本（从 payload_properties.txt）：**
- post-build: `Redmi/flame/flame:14/UKQ1.240523.001/V816.0.2.0.UGUINXM:user/release-keys`
- post-sdk-level: 34 (Android 14)
- post-security-patch: 2024-12-01
- **设备代号: flame（不是 dipper）** ⚠️

**boot.img 代号不匹配后果：**
- `dipper` boot.img → `flame` 设备：100% bootloop（基带/gpu 固件不兼容）
- `flame` boot.img → `dipper` 设备：100% bootloop
- 必须用 `fastboot getvar product` 确认设备真实代号，再用对应代号 ROM 的 boot.img

**设备代号速查：**
- MI 8 标准版 = dipper
- MI 8 屏幕指纹版 = **flame** ← 当前设备是这个
- MI 8 UD = ursa

**教训（2026-08-12）：**
- 用户说"MI 8 标准版"，但实际设备是 flame（屏幕指纹版）
- 错误代号导致找了 dipper 的 boot.img，全部 bootloop
- 同一批用户发的 dipper.img（57MB）刷了 3 次都 bootloop，不是大小问题，是代号问题

## 坑点

| 坑 | 原因 | 解法 |
|-----|------|------|
| `adb root` 无效 | `ro.debuggable=0`，官方ROM设计限制 | 只走 boot.img 路线 |
| boot.img 提取需 root | 循环依赖 | 从官方 ROM 包获取，不从设备提取 |
| 小米 CDN 全部 403 | 地域限制 | 用户手动下载或 FIRERPA 控制手机浏览器 |
| TWRP 官网链接返回 HTML | JS 重定向，curl 只拿中转页 | 换 `androidfilehost.com` 或 github releases |
| Magisk "安装" 按钮无效 | boot.img 未修补时 APK 装了个寂寞 | 先获取 boot.img 再点 |
| shelldo `python3` 调用 `import ctypes` 失败 | Python 3.12 找不到 ffi.so | 用纯 Python 标准库，不依赖 ctypes |
| magiskboot 文件名是 `.so` | 历史遗留命名，实际是静态 ELF | 直接 chmod +x 当可执行文件用 |
| FIRERPA `d.touch(x,y)` 参数格式错误 | API 定义与实际不符 | 用 `adb shell "input tap X Y"` |
| **boot.img > boot 分区** | OTA 包 boot.img 通常比设备 boot 分区大 | 用 `fastboot getvar partition-size:boot` 确认；必须找对应版本的 Fastboot ROM 包 boot.img |
| **`fastboot boot` 成功但 `fastboot flash` 后仍 bootloop** | boot.img 修补失败（Magisk 日志显示 "Failed to patch"） | 检查 Magisk install 日志 `cat /sdcard/Download/magisk_install_log_*.log`，确认 ramdisk 修补是否成功 |
| **Magisk daemon 运行正常（`magiskd` 在），但 `su` 报 Permission denied** | SELinux 策略阻止 shell 用户切换到 magisk_exec 上下文 | ① 手机上 Magisk App → 右上角⚙️ → 超级用户访问权限 = "应用和 ADB"；② 检查超级用户列表里是否有 shell 用户并已授权；③ 若仍失败，需重新修补 boot.img 时注入正确的 SELinux 策略，或在 Magisk app 里执行"修复 SELinux" |
| **Magisk App UI 一直崩（start timeout），但 magiskd 在跑** | Magisk daemon（magiskd）运行正常，但 App UI 的 Provider 被 zygisk 模块卡住无法 attach | 禁用 zygisk 模块：创建 `/data/adb/modules/<模块名>/disable/` 目录（必须是**目录**不是空文件），然后重启。禁用后 Magisk App 和其他 App 通常都能恢复正常 |
| **禁用模块后 Magisk App 仍然崩** | 系统刚经历过 lamda 等模块导致的崩溃，Magisk App 数据可能损坏 | `adb shell "pm clear com.topjohnwu.magisk"` 清除 App 数据，重启后重新打开 Magisk App |
| **Magisk App 启动 → SuRequestActivity → start timeout → killed** | Magisk 的 Provider 被 zygisk 模块的 SELinux 策略拦截，无法在规定时间内 attach | 禁用所有 zygisk 模块（创建 disable/ 目录），重启让新状态生效。用 `adb shell "su -c 'ls /data/adb/modules/<name>/disable'"` 验证 disable 目录是否存在 |
| **Magisk "安装"完成后 Downloads 里找不到 magisk_patched 文件** | Magisk 的 `cp` 命令报 `can't preserve ownership`，文件未复制到 /sdcard/Download | patched 文件实际在 `/data/user_de/0/com.topjohnwu.magisk/install/magisk_patched-xxx.img`，或直接用 `adb pull /data/local/tmp/new-boot.img` 拉取 |
| **lamda 进程消失** | 设备重启后 lamda 服务未自动启动 | 重新部署：`. /data/local/tmp/server/bin/launch.sh &`（用 python3.12 路径） |
| **`fastboot flash` 成功但仍 bootloop** | **大小匹配 ≠ 版本匹配** | 每次刷入前必须先用 `fastboot boot` 测试，能进系统后核对 `getprop ro.build.display.id` |
| `Dumper` 对象无 `dump()` 方法 | payload_dumper API 写的是 `run()` 不是 `dump()` | 见上方 payload-dumper 提取示例 |

---

## 参考文件

`references/magisk-boot-flow.md` — boot.img 结构 + Magisk 注入原理 + 完整 CLI 工作流（2026-08-12 MI8 dipper 实测）

`references/mi8-dipper-root-2026-08-12.md` — AVB 签名陷阱教训 + magiskboot 纯 CLI 修补流程 + 救砖方法

`references/mi8-qeacnxm-root-2026-08-13.md` — QEACNXM ZIP → Magisk App 修补 → 刷入流程（2026-08-13）

`references/mi8-dipper-flame-bootloop-2026-08-12.md` — magisk_patched boot.img 大小合适但代号不匹配导致 bootloop（2026-08-12 实测）

`references/mi8-dipper-vs-flame-bootloop-2026-08-12.md` — dipper vs flame 代号不匹配教训，设备代号必须用 `fastboot getvar product` 核实

`references/mi8-qeamixm-root-2026-08-13.md` — QEAMIXM 全球版 Magisk root 流程、copy bug 解析、纯 CLI magiskboot 修补步骤
