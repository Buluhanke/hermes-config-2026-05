# MIUI OTA payload.bin → boot.img 提取（2026-08-12 实测）

## 背景

MIUI 完整包（Fastboot 格式）通常是 `.zip` 内含 `payload.bin`（4GB+），没有单独的 `boot.img`。

实测文件：`miui_FLAMEINGlobal_OS1.0.2.0.UGUINXM_f6015ae108_14.0 (1).zip`（4.15GB）

## payload.bin 结构

```
magic: b"CrAU" (Chrome AU = Google Android OTA payload)
├── DeltaArchiveManifest (protobuf)
│   └── partitions[] — boot, system, vendor, ...
└── data blocks (REPLACE/XZ/BZ/ZERO operations)
```

## 提取流程

### Step 1 — 安装 payload-dumper

```bash
/usr/local/bin/python3 -m pip install --index-url https://pypi.tuna.tsinghua.edu.cn/simple payload-dumper
```

**坑：** 必须用 `/usr/local/bin/python3`（Python 3.14），系统 `python3`（3.11）没有这个包。

### Step 2 — 提取 boot 分区

```python
#!/usr/local/bin/python3
import zipfile, os
from payload_dumper.dumper import Dumper

zip_path = '/Users/aimac/Desktop/miui_FLAMEINGlobal_OS1.0.2.0.UGUINXM_f6015ae108_14.0 (1).zip'
out_dir = '/tmp/miui_boot'
os.makedirs(out_dir, exist_ok=True)

with zipfile.ZipFile(zip_path, 'r') as z:
    with z.open('payload.bin') as f:
        d = Dumper(f, out_dir, images='boot')
        d.run()
# 输出: /tmp/miui_boot/boot.img (96MB)
```

### Step 3 — 验证

```bash
file /tmp/miui_boot/boot.img
# 输出: Android bootimg, kernel (0x...), ramdisk (0x...)  ← 成功

python3 -c "
import struct
with open('/tmp/miui_boot/boot.img','rb') as f:
    magic = f.read(8)
    print('Magic:', magic)  # b'ANDROID!'
"
```

## 关键 API 发现

| 错误用法 | 正确用法 |
|---------|---------|
| `python3 -m payload_dumper` | `from payload_dumper.dumper import Dumper` |
| `d.dump()` | `d.run()` |
| `payloadfile='xxx.zip'` | `payloadfile=open('payload.bin','rb')`（file object）|

## 查设备版本（不解压 payload.bin）

```python
import zipfile
with zipfile.ZipFile('xxx.zip') as z:
    meta = z.read('META-INF/com/android/metadata').decode()
    print(meta)
```

输出示例：
```
pre-device=flame        ← 设备代号（flame = MI8）
post-build=Redmi/flame/flame:14/UKQ1.240523.001/V816.0.2.0.UGUINXM:user/release-keys
post-sdk-level=34       ← Android 14
post-security-patch-level=2024-12-01
post-timestamp=1734348095
```

## 实测结果

| 项目 | 值 |
|------|------|
| 设备 | flame (MI8) ✅ |
| ROM | V816.0.2.0.UGUINXM (MIUI 14, Android 14) |
| 安全补丁 | 2024-12-01 |
| boot.img 大小 | 96MB |
| Magic | `ANDROID!` ✅ |

## 桌面目录卡死 workaround

`find / ls mdfind glob` 全部对 Desktop 超时（文件太多或 iCloud/网络盘卡住）：

```bash
# 直接 stat 目标文件
stat "/Users/aimac/Desktop/miui_FLAMEINGlobal_OS1.0.2.0.UGUINXM_f6015ae108_14.0 (1).zip"
# 或 cd + ls（带文件名过滤）
cd /Users/aimac/Desktop && ls *f6015*
```
