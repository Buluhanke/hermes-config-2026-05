# MI8 dipper Root 实测记录 — 2026-08-12

## 设备信息
- 机型：小米 MI8 (dipper)
- ROM：V12.0.3.0.QEAMIXM (MIUI 12, Android 10)
- Bootloader：已解锁
- Magisk：v30.7 APK 已装，root 未激活

## boot.img 来源
用户提供的 boot.img (51MB, PATCH_LEVEL=2019-08) → **与设备 ROM V12.0.3.0.QEAMIXM (2021-12) 不匹配，导致原版 boot.img 也 bootloop**

**教训：boot.img 必须与当前 ROM 版本完全匹配，不能混用不同版本/不同来源的 boot.img。**

## magiskboot 纯 CLI 修补流程（成功，但 bootloop）

```bash
# 1. 从 Magisk APK 提取 magiskboot（静态 ELF）
python3 -c "
import zipfile
with zipfile.ZipFile('/tmp/magisk_fromphone.apk') as z:
    with open('/tmp/magiskboot_arm64', 'wb') as f:
        f.write(z.read('lib/arm64-v8a/libmagiskboot.so'))
"
# 注意：文件名是 .so，实际是静态链接可执行文件，push 后 chmod +x 直接运行

# 2. Push 到手机
adb push /tmp/magiskboot_arm64 /data/local/tmp/magiskboot
adb shell "chmod 755 /data/local/tmp/magiskboot"

# 3. 解包 boot.img
adb shell "cd /data/local/tmp && ./magiskboot unpack boot.img"

# 4. 修补 ramdisk
adb shell "cd /data/local/tmp && ./magiskboot cpio ramdisk.cpio patch"

# 5. 重新打包
adb shell "cd /data/local/tmp && ./magiskboot repack boot.img new-boot.img"

# 6. Pull 回 Mac
adb pull /data/local/tmp/new-boot.img /tmp/new-boot.img

# 7. 刷入
fastboot flash boot /tmp/new-boot.img
fastboot reboot
```

**结果：bootloop ❌** — AVB 签名失效

## AVB 签名陷阱

```
原始 boot.img:        AVB1_SIGNED, checksum=b5beb1b2...
修补后 new-boot.img:  AVB1_SIGNED, checksum=8714264e...  ← checksum 变了，签名失效
```

MIUI 开启了 verified boot，签名失效直接 bootloop。

**正确方法：用 Magisk app UI「选择并修补一个文件」，app 内部处理 AVB 重签名。**

## 救砖

原版 boot.img 也 bootloop（版本不匹配）时：

```bash
# 同时按住 音量下+电源键 10秒 进入 fastboot
~/adb-tools/platform-tools/fastboot boot /tmp/boot.img  # 先从 RAM 启动测试
# 如果卡 logo → boot.img 版本不对，需要找到正确版本
```

## fastboot 工具路径

Mac 上没有 Android SDK 的 fastboot，用这个独立工具：
```
~/adb-tools/platform-tools/fastboot
```
