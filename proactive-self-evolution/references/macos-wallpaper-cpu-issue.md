# macOS 动态壁纸 / WallpaperExtension CPU 问题

## 2026-06-02 实测永久解决方案

**根因**：macOS 把动态壁纸（Sequoia Sunrise.mov）注册在 `com.apple.wallpaper` plist 的 `SystemWallpaperURL`。`WallpaperAerialsExtension` 进程是跟随这个设置的系统扩展，`kill` 后会自动重启。

**临时解决**（进程会重启）：
```bash
kill $(pgrep -f WallpaperAerialsExtension)
```

**永久解决**（一劳永逸，改 plist）：
```bash
defaults write com.apple.wallpaper SystemWallpaperURL -string "file:///System/Library/Desktop%20Pictures/Mac%20Blue.heic"
killall WallpaperAgent wallpaperexportd
kill $(pgrep -i WallpaperAerial)
```

验证：`ps aux | grep -i Aerials | grep -v grep` 应返回空，且 CPU 降到 0%。

**可用静态壁纸路径**：
- `/System/Library/Desktop Pictures/Mac Blue.heic`
- `/System/Library/Desktop Pictures/iMac Blue.heic`
- `/System/Library/Desktop Pictures/Sonoma.heic`

## 进程说明

| 进程 | 说明 | CPU |
|------|------|-----|
| `WallpaperAerialsExtension.appex` | 航拍视频壁纸驱动 | 6-13%（持续） |
| `WallpaperImageExtension.appex` | 静态壁纸扩展 | <1%（正常） |
| `WallpaperAgent` | 系统壁纸管理 | <1%（正常） |
| `wallpaperexportd` | 壁纸资源导出（root） | <1%（正常） |

## session_search 关联

FTS5 AND 查询要求所有词都命中。搜"动态壁纸 屏幕"返回0，搜"壁纸"能找到。重要结论必须写进 memory，不能依赖跨会话搜索。
