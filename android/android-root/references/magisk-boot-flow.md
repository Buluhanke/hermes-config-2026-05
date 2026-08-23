# boot.img 结构与 Magisk Root 原理

## boot.img 格式

Android boot.img 采用 AOSP bootimg 格式，结构如下：

```
+------------------- 4096 bytes (页大小) -------------------+
|  Header (struct boot_img_hdr)                           |
|  - kernel_size, ramdisk_size, second_size, etc.         |
|  - kernel_addr, ramdisk_addr, etc.                       |
+-----------------------------------------------------------+
|  kernel (内核)                           size = kernel_size |
+-----------------------------------------------------------+
|  ramdisk (cpio 归档)                     size = ramdisk_size |
|  包含 /init, /init.rc, /etc/ 等系统初始化文件               |
+-----------------------------------------------------------+
|  second stage (可选)                    size = second_size  |
+-----------------------------------------------------------+
|  device tree (dtb)                     size = dtb_size    |
+-----------------------------------------------------------+
```

页大小通常为 4096 字节，kernel/ramdisk/second/dtb 均按页对齐。

## Magisk Root 原理

Magisk 不修改 kernel，只修改 ramdisk。

### 原始 ramdisk 结构
```
ramdisk.cpio:
  etc/
  system/
  init
  init.rc
  init.usb.configfs.rc
  ...
```

### Magisk 修补后的 ramdisk
```
ramdisk.cpio:
  overlay/
    sbin/
      su           ← 新增：Magisk su 二进制
      magisk       ← Magisk 守护进程
  etc/
  system/
  init            ← 被替换为 Magisk init
  init.rc
  init.usb.configfs.rc
  ...
```

Magisk init 会：
1. 挂载 overlayfs，将 overlay/sbin/su 叠加到系统 /sbin
2. 启动 magiskd 守护进程
3. 通过 Zygisk 注入到 zygote 进程

## Magisk boot.img 修补流程

```
原始 boot.img
    │
    ▼
magiskboot unpack → kernel / kernel_dtb / ramdisk.cpio / header
    │
    ▼
magiskboot cpio ramdisk.cpio "patch"
    │  读取 boot_patch.sh，注入 overlay/sbin/su 和 Magisk init
    ▼
修补后 ramdisk.cpio
    │
    ▼
magiskboot repack → new-boot.img
    │  保留原 header（大小/地址字段），更新 ramdisk_size/checksum
    ▼
magisk_patched.img ← 刷入 boot 分区
```

## 为什么需要 boot.img 文件

Magisk app 的"选择并修补一个文件"功能：
- 需要用户选择 boot.img 文件（**不是**从设备读取）
- 修补后的文件保存到 `/sdcard/Download/magisk_patched-*.img`

Magisk app 能"直接安装"（不用选文件）的条件：
- 需要设备已 root
- 此时 Magisk 可以直接读取并替换 /dev/block/boot 分区

## 循环依赖问题

```
提取 boot.img ──需要 root──→ 需要 su ──需要 boot.img 修补──┘
```

**解法：永远不从设备提取 boot.img**，只从官方 ROM 包获取。

## 从设备提取 boot.img 的正确方法（假设已有 root）

```bash
# 知道 boot 分区设备号
dd if=/dev/block/sde45 of=/data/local/tmp/boot.img bs=1M count=64
# 或
adb shell "dd if=/dev/block/sde45 of=/sdcard/boot.img bs=1M count=64"
```

**注意：** `adb shell` 的 dd 需要 root 权限。shell 用户的 uid=2000 读写 /dev/block/* 需要 CAP_SYS_ADMIN（实际没有），会报 Permission denied。

## MI8 (dipper) boot 分区信息

| 项目 | 值 |
|------|------|
| 分区设备 | /dev/block/sde45 |
| 符号链接 | /dev/block/bootdevice/by-name/boot → sde45 |
| 分区大小 | 64MB |
| 文件系统 | raw (无文件系统，是 bootimg 格式) |
