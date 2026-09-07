---
name: macos-troubleshooting
description: macOS排障：Dock图标重复/Launch Services/进程注册。
triggers:
  - "Dock 里出现两个相同图标"
  - "app 在 Dock 里重复"
  - "Hermes desktop 两个图标"
  - "Launch Services 注册异常"
  - "macOS 应用重复出现"
---

# macOS Troubleshooting

诊断 macOS 系统层问题：Dock 异常、Launch Services、进程注册。

## 诊断流程

### 1. 查运行中的进程（最快，最准确）

```bash
# 查名字含 hermes 的进程及路径
osascript -e 'tell application "System Events" to get file of every process whose name contains "Hermes"'

# 查所有非后台进程（显示真实 Dock 项目）
osascript -e 'tell application "System Events" to get name of every process whose background only is false'

# 查所有登录项
osascript -e 'tell application "System Events" to get the name of every login item'
```

**核心原则**：osascript 查出来的是真货。Dock 显示的可能残留，Activity Monitor 显示的更实时。

### 2. 查 Bundle Identifier（判断是否同一 app）

```bash
mdimport -r /path/to/App.app 2>/dev/null
codesign -d -i com.example.app 2>/dev/null
plutil -p "/path/to/App.app/Contents/Info.plist" | grep -E "CFBundleIdentifier|LSUIElement"
```

### 3. 查 Launch Services 注册

```bash
/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister -f /path/to/app.app
```

### 4. 查 Dock 持久化条目

```bash
defaults read com.apple.dock.plist persistent-apps 2>/dev/null | grep -A5 "hermes\|Hermes"
```

### 5. 重建 Launch Services 缓存

```bash
/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister -f /Applications/MyApp.app
killall Dock
```

## 常见模式

### 两个完全相同的 Dock 图标
通常是 Launch Services 缓存了旧的 bundle 注册。修复：
1. `lsregister -f` 强制刷新 app 的 plist 注册
2. `killall Dock`
3. 重启 app 验证

### Hermes Helper (Renderer) 单独占 Dock 位
Hermes 基于 Electron，其 Helper app 的 `Info.plist` 已有 `LSUIElement=true`，但 Launch Services 缓存了旧数据。`lsregister -f` 可解决。

### app 已删但 Dock 还有残影
Dock plist 残留条目，删除之：
```bash
# 备份
cp ~/Library/Preferences/com.apple.dock.plist ~/Library/Preferences/com.apple.dock.plist.bak
# 删除 Hermes 条目（需要 plist 操作）
plutil -p ~/Library/Preferences/com.apple.dock.plist | grep -B2 -A2 "Hermes"
```

## 工具链

| 工具 | 用途 |
|------|------|
| `osascript` | 查进程、Dock 项、登录项 |
| `lsregister` | 强制刷新 Launch Services 注册 |
| `mdfind` | 按 bundle identifier 或名字找 app |
| `plutil` | 读写 plist（Info.plist / Dock plist） |
| `codesign` | 查 app 签名和 bundle ID |

## 禁止

- 不要用 `open -n` 测试是否有第二个实例——macOS 有 singleton 锁机制，同一 app 多次 open 只会激活已运行的实例，不会新建
- 不要猜测进程数——用 osascript 实时查，不要用 `pgrep` 的静态结果
