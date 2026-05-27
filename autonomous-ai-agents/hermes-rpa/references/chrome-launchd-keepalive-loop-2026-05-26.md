# Chrome launchd KeepAlive 循环问题（2026-05-26）

## 问题现象

Mac 重启后，Google Chrome 被拉起多个窗口，强制关闭后自动重新启动，无限循环。

## 根因

plist 配置了 `KeepAlive: true`：

```xml
~/Library/LaunchAgents/com.aimac.hermes-chrome-debug.plist
<key>RunAtLoad</key>
<true/>
<key>KeepAlive</key>
<true/>
```

launchd 守护进程会在 Chrome 退出后自动重新启动它（无论是程序崩溃、手动退出、还是被 kill）。

## 解决方案

将 `KeepAlive` 改为 `false`，Chrome 启动后不再自动拉起：

```bash
# 1. 卸载当前 plist
launchctl unload ~/Library/LaunchAgents/com.aimac.hermes-chrome-debug.plist

# 2. 编辑 plist，将 KeepAlive 改为 false
# <key>KeepAlive</key>
# <false/>

# 3. 重新加载
launchctl load ~/Library/LaunchAgents/com.aimac.hermes-chrome-debug.plist
```

## 影响

| 功能 | 影响 |
|------|------|
| MCP 浏览器自动化工具 | 需要时手动打开 Chrome |
| 日常 Chrome 使用 | 不受影响 |
| cua-driver 桌面控制 | 完全不受影响 |
| 其他 Hermes 功能 | 不受影响 |

## 注意

- `RunAtLoad: true` 保留 → Mac 启动时仍会自动打开 Chrome
- 只有手动关闭 Chrome 时不会自动拉起（因为 KeepAlive: false）
- 想用 MCP 工具时手动打开 Chrome 即可

## 相关文件

- plist 路径：`~/Library/LaunchAgents/com.aimac.hermes-chrome-debug.plist`
- Chrome 调试数据：`~/.hermes/chrome-debug/`（4.7GB，大部分是 Chrome On-Device ML 模型，无法清理）