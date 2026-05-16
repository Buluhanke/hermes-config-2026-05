# macOS Accessibility API — 失败记录

> aimac (Mac mini 192.168.0.4) 2026-05 实测：所有 AXUIElement 路线全部失败。

## 失败方法汇总

| 方法 | 错误 | 原因 |
|------|------|------|
| `from ApplicationServices import AXUIElementCreateApplication` | `ModuleNotFoundError` | Python 3.14 + pyobjc 12.1 下路径不存在 |
| `from Quartz import AXUIElementCreateApplication` | `ImportError: cannot import name 'AXUIElementCreateApplication'` | Quartz 模块不导出此符号 |
| `AppKit.AXIsProcessTrusted()` | `AttributeError` | pyobjc 懒加载未加载此符号 |
| `CGWindowListCopyWindowInfo` (Quartz) | 返回 26 个窗口，但只有 Window Server/Cloudflare WARP 等系统进程 | SIP / 沙箱保护，第三方 App 窗口信息被剥离 |
| `python3 -c "import ApplicationServices"` | `ModuleNotFoundError` | 同上 |

## 唯一可用路线

**AppleScript** — macOS 读/控桌面的唯一可行路径。

```bash
# 读 Safari URL/标题
cat > /tmp/safari_url.scpt << 'EOF'
tell application "Safari"
    set urlText to URL of front document
    set titleText to name of front document
    return "URL: " & urlText & " | Title: " & titleText
end tell
EOF
osascript /tmp/safari_url.scpt
```

## 结论

macOS 的隐私保护（SIP + App Sandbox）使得 pyobjc/AXUIElement 读取第三方 App 控件树在本机上不可行。所有读/控 macOS 桌面应用的场景必须走 AppleScript 路线。
