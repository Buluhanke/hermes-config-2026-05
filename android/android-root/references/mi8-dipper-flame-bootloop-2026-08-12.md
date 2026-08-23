# MI8 dipper — FLAMEINGlobal bootloop 救砖实录 (2026-08-12)

## 事件

用户提供的 boot.img（来源: magisk_patched，从某个 MI8 ROM 修补）：
- 文件: `doc_4199a7ab40c9_boot.img`，49MB
- 刷入结果: `fastboot flash boot` ✅ 成功（大小合适）
- 启动结果: ❌ 仍卡 logo，boot 版本不匹配

关键教训：**大小匹配 ≠ 版本匹配**。即使 boot.img 能刷进分区，kernel/基带/ramdisk 版本不匹配仍会 bootloop。

## 诊断流程（每次刷 boot.img 前必做）

```bash
# 1. 确认 boot 分区大小
fastboot getvar partition-size:boot

# 2. 确认 boot.img 大小 ≤ boot 分区
ls -lh boot.img

# 3. 用 fastboot boot 测试（不写分区！）
fastboot boot boot.img
# 成功 → 屏幕亮起 Android
# 失败 → 报 Bad Buffer Size / 其他错误，说明版本不匹配

# 4. 版本核对（刷入后能进系统）
adb shell getprop ro.build.version.security_patch  # 安全补丁日期
adb shell getprop ro.build.display.id            # MIUI 版本
```

## boot.img 来源风险分级

| 来源 | 风险 | 说明 |
|------|------|------|
| 设备当前系统提取 | ✅ 最低 | 100% 匹配，需要 root（循环依赖） |
| 同版本 Fastboot ROM 解压 | ✅ 低 | 分区大小经过裁剪，版本一致 |
| 同版本 OTA payload.bin 提取 | ⚠️ 中 | boot.img 可能比设备 boot 分区大 |
| 其他 MI8 变体ROM 的 boot.img | ❌ 高 | Pro/标准版/屏下指纹版 boot.img 不通用 |
| 第三方修改版 | ❌ 极高 | kernel/基带可能不匹配 |

## OTA boot.img 为什么常常比 boot 分区大

MIUI OTA 包假设的目标分区可能比设备实际分区大：
- 同一型号不同市场版本（Global/China）boot 分区不同
- 同一型号硬件版本迭代，boot 分区大小改变
- OTA 包设计时考虑了未来分区调整

**永远用 Fastboot ROM 包的 boot.img，不是 OTA 包的。**

## MI8 dipper FLAMEINGlobal 实测数据

```
用户 ROM:     V816.0.2.0.UGUINXM (MIUI 14, Android 14) — FLAMEINGlobal
OTA boot.img: 96MB  → boot 分区 64MB，溢出
magisk_patched: 49MB → 大小合适，但版本不匹配，仍 bootloop
正确解法:     下载 V12.0.3.0.QEAMIXM Fastboot ROM，取其 boot.img
```

## Xiaomi CDN 访问状态 (2026-08-12)

```
bigota.d.miui.com        → 403 Forbidden ❌
cdn.developer.xiaomi.com → 超时 ❌
bula.d.miui.com          → 超时 ❌
gh-proxy.com 镜像        → 403 ❌
```

**解法：用户手动从浏览器下载，或用 FIRERPA 控制手机浏览器下载。**
