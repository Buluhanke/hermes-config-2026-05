# 移动端盲区解决方案（2026-05-17）

## 方案对比

| 方案 | 内存占用 | 稳定性 | 前置条件 | 推荐度 |
|------|---------|--------|---------|--------|
| iPhone Mirroring（macOS 15+） | ~0（系统级） | 高 | 需要物理 iPhone 在局域网 | ⭐⭐⭐⭐（有 iPhone 时） |
| Android 模拟器（MuMu/AS） | 4GB+ | 中 | 无 | ⭐⭐⭐（无 iPhone 时） |
| Appium + 真机 | 1GB | 中 | USB 连接或同局域网 | ⭐⭐ |

## iPhone Mirroring（当前系统已预装）

路径：`/System/Applications/iPhone Mirroring.app`
版本要求：macOS 15.1+，iOS 18+（iPhone 和 Mac 须同局域网）

**局限性**：不是纯软件方案，需要一部真实的 iPhone。如果用户没有 iPhone，此方案不可用。

**接入方式**：通过 macOS 的 AXUI 直接读取镜像窗口，Hermes 可以像操作 Mac 软件一样操作手机屏幕。

## Android 模拟器

推荐 MuMu（网易出品，对 M 芯片优化较好）。

内存分配：建议 4GB。
adb 控制：标准 Android 调试桥，Hermes 可通过 `adb shell input` 注入手势和文字。

## 结论

移动端盲区优先级低于桌面端真人化（发呆/过冲/视觉流）。如果用户有 iPhone，iPhone Mirroring 是最省内存的方案。如果没有，先跳过移动端。
