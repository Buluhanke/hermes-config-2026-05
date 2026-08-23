# MI8 QEAMIXM Root — 2026-08-13

## 当前设备状态

- 型号：MI 8 (dipper)
- ROM：V12.0.3.0.QEAMIXM（全球稳定版，Android 10）
- Bootloader：已解锁 ✅
- Magisk：v30.7 APK 已装，su 未激活 ❌
- boot 分区：64MB

## boot.img 版本问题

手机里曾有旧 boot.img（/sdcard/Download/boot.img，49MB），是从中国版 QEACNXM 残留的。

桌面 `miui_MI8_V12.0.3.0.QEACNXM_56da60431d_10.0.zip` 是中国版，和手机当前 QEAMIXM 全球版**不能混用**。

正确版本：
- QEAMIXM = 全球版（MI8 Global）
- QEACNXM = 中国版（MI8 大陆）

## Magisk "安装"后找不到 magisk_patched 文件

**症状：** Magisk app 显示"安装成功"，但 /sdcard/Download/ 里没有 magisk_patched-*.img。

**根因：** Magisk 修补完成后执行 `cp` 复制文件时报错：
```
cp: can't preserve ownership of 'busybox': Operation not permitted
cp: can't preserve ownership of 'init-ld': Operation not permitted
...
```
shell 用户（uid=2000）没有 CAP_CHOWN 权限，`chown` 操作被 SELinux 拒绝，导致文件根本没复制到 /sdcard/Download/。

**Magisk install 日志位置：** `/sdcard/Download/magisk_install_log_*.log`

**实际 patched 文件位置：** 
- `/data/user_de/0/com.topjohnwu.magisk/install/magisk_patched-xxx.img`（需要 root 访问）
- `/data/local/tmp/new-boot.img`（如果是在 app 里选"修补 boot.img"后生成的）

**解法：** 
1. 用 lamda 搜索文件：`d.execute_script('find / -name "magisk_patched*" 2>/dev/null')`
2. 或直接用 `adb pull /data/local/tmp/new-boot.img` 拉取（如果文件在那里）
3. 最佳方案：用 magiskboot 纯 CLI 修补，不依赖 Magisk app UI

## magiskboot 纯 CLI 修补流程（推荐）

不需要 Magisk app，不需要 root，直接在已解锁 bootloader 的设备上操作：

```bash
# 1. 把 boot.img 和 magiskboot push 到手机
adb push boot.img /data/local/tmp/boot.img
adb push magiskboot /data/local/tmp/magiskboot
adb shell "chmod 755 /data/local/tmp/magiskboot"

# 2. 解包
adb shell "cd /data/local/tmp && ./magiskboot unpack boot.img"
# 产物：kernel, kernel_dtb, ramdisk.cpio, header

# 3. 修补 ramdisk
adb shell "cd /data/local/tmp && ./magiskboot cpio ramdisk.cpio patch"

# 4. 重新打包
adb shell "cd /data/local/tmp && ./magiskboot repack boot.img new-boot.img"

# 5. 拉回 Mac
adb pull /data/local/tmp/new-boot.img ~/Desktop/magisk_patched.img

# 6. 刷入
adb reboot bootloader
fastboot flash boot ~/Desktop/magisk_patched.img
fastboot reboot
```

## Magisk 日志分析

日志关键字段：
- `Stock boot image detected` = 正常检测到原版 boot.img
- `Failed to patch` = **ramdisk 修补失败**，new-boot.img 不能使用
- `Repack to boot image` = 打包成功

即使打包成功，也要用 `fastboot boot` 先测试，不能直接 `fastboot flash`。

## lamda 服务重启后失效

设备重启后 lamda 进程消失，需重新部署：

```bash
# python 路径必须是 /data/local/tmp/server/bin/python3.12
adb shell "LD_LIBRARY_PATH=/data/local/tmp/server/lib nohup /data/local/tmp/server/bin/python3.12 -u -m lamda --launch > /data/local/tmp/lamda.log 2>&1 &"
sleep 5
```

验证：`curl http://localhost:65000/status` 返回 404 是正常的（lamda 不走 REST）。

## 快速检查命令

```bash
# 设备当前版本
adb shell getprop ro.build.version.incremental
# V12.0.3.0.QEAMIXM

# 设备代号
adb shell getprop ro.product.device

# boot 分区大小
fastboot getvar partition-size:boot
# 0x4000000 = 64MB

# boot.img 快速验证（不解包）
python3 -c "
import struct
with open('boot.img','rb') as f:
    magic = f.read(8)
    ks = struct.unpack('<I',f.read(4))[0]
    rs = struct.unpack('<I',f.read(4))[0]
    page = struct.unpack('<I',f.read(4))[0]
print('magic:', magic, 'kernel:', ks, 'ramdisk:', rs, 'page:', page)
"
```
