# macOS 动态壁纸 / WallpaperExtension CPU 问题

## 2026-06-01 发现

**进程**：
- `WallpaperAerialsExtension.appex` — Apple TV Aerial 航拍视频动态壁纸
  - CPU时间：66分45秒（持续运行）
- `WallpaperImageExtension.appex` — 静态壁纸扩展，CPU时间短（正常）
- `WallpaperAgent` — 系统壁纸管理进程

**路径**：
```
/System/Library/ExtensionKit/Extensions/WallpaperAerialsExtension.appex/Contents/MacOS/WallpaperAerialsExtension
/System/Library/ExtensionKit/Extensions/WallpaperImageExtension.appex/Contents/MacOS/WallpaperImageExtension
```

## 症状
- CPU 占用异常高（单核持续跑）
- 内存占用不大但 CPU 时间累积快
- 系统每次唤醒（wake from sleep）会重启扩展

## 临时解决方法
```bash
# 杀掉进程（系统会重启）
kill $(pgrep -f WallpaperAerialsExtension)
```

## 永久解决方法
**系统设置 → 壁纸 → 把"航拍视频"换成任意静态壁纸**

这是 macOS Sonoma+ 内置功能，不是第三方 App，关掉后不影响其他功能。

## 相关命令
```bash
# 查看当前壁纸扩展进程
ps aux | grep -E "WallpaperAerials|WallpaperImage|WallpaperAgent" | grep -v grep

# 查看系统壁纸配置
open x-apple.systempreferences:com.apple.DesktopSettings
```

## session_search 关联
2026-06-01 发现：昨晚（2026-05-31）的对话里有讨论过动态壁纸，但 session_search 搜"动态壁纸 壁纸"返回0结果，FTS 索引可能有关键词匹配问题。详见 proactive-self-evolution skill 的 Pitfall 章节。
