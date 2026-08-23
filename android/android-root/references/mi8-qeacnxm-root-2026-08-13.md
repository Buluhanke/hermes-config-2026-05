# MI8 QEACNXM → QEAMIXM Root Session Log (2026-08-13)

## 设备信息
- 型号: Xiaomi MI 8 (dipper 代号存疑，实际可能是 flame)
- 目标版本: V12.0.3.0.QEAMIXM (MIUI 12, Android 10)
- 已知问题: boot 分区 64MB，大版本 boot.img 96MB 塞不进去

## 流程（本次成功路径）

### Step 1 — 找到匹配的 boot.img
用户桌面有 `miui_MI8_V12.0.3.0.QEACNXM_56da60431d_10.0.zip`（2.1GB）。

```bash
cd /tmp && unzip -o ~/Desktop/miui_MI8_V12.0.3.0.QEACNXM_56da60431d_10.0.zip "*.img"
# 提取出 boot.img (43MB)，大小合适
```

### Step 2 — 推送 boot.img 到手机
手机已开机（无 root），通过 adb push 到 /sdcard/Download/：

```bash
adb push /tmp/boot.img /sdcard/Download/boot.img
```

### Step 3 — Magisk App 修补
手机打开 Magisk App → 安装 → 选择「选择并修补一个文件」→ 选 /sdcard/Download/boot.img

输出: `/sdcard/Download/magisk_patched-30700_PzpGb.img` (44MB)

### Step 4 — 拉回修补镜像
```bash
adb pull /sdcard/Download/magisk_patched-30700_PzpGb.img /tmp/boot_magisk.img
```

### Step 5 — 刷入
```bash
adb reboot bootloader
fastboot flash boot /tmp/boot_magisk.img
fastboot reboot
```

## 结果
✅ boot 刷入成功，手机正常进系统
✅ magiskd 进程运行中 (PID 671)
✅ /sbin/su 存在 → magisk 符号链接
❌ `adb shell "su -c id"` → Permission denied

## SELinux 问题诊断

### 现象
```
shell 用户: uid=2000(shell) gid=2000(shell) context=u:r:shell:s0
magiskd 进程: root, 正常运行
su 调用: Permission denied (exit code 13)
setenforce 0: Permission denied (shell 用户权限不足)
magiskpolicy --live: open '/sys/fs/selinux/policy': Permission denied
```

### 根因
Magisk App 修补 boot.img 时，SELinux 策略未正确注入，导致 shell (u:r:shell:s0) 无法切换到 magisk_exec 上下文执行 su。

### 解决方向（未完成）
1. 手机上 Magisk App → ⚙️ → 超级用户访问权限 = "应用和 ADB"
2. 超级用户列表里检查 shell 用户是否授权
3. 若仍失败，需用 magiskboot 纯 CLI 重新修补 boot.img（完整注入 SELinux 策略）

## 关键教训
- 从用户桌面 ZIP 直接提取 boot.img → 修补 → 刷入，这条路径可行
- Magisk App 修补成功 ≠ SELinux 策略完整
- `magiskd running ≠ su works`，需单独验证
