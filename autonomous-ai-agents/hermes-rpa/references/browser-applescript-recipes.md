# AppleScript 浏览器内容读取食谱

> 当用户日常 Chrome 没有 `--remote-debugging-port` 时，用 AppleScript 读取内容。
> 需要 Chrome 开启：显示 → 开发者 → 允许 Apple 事件中的 JavaScript

## 核心语法速查

### 读取活跃标签页
```applescript
tell application "Google Chrome"
    set tabURL to URL of active tab of window 1
    set tabTitle to title of active tab of window 1
    set pageText to execute active tab of window 1 javascript "document.body.innerText"
end tell
```

### 读取指定窗口/标签页
```applescript
tell application "Google Chrome"
    set tabURL to URL of tab 2 of window 1
    set tabTitle to title of tab 2 of window 1
    set pageText to execute tab 2 of window 1 javascript "document.body.innerText"
end tell
```

### 遍历所有标签页
```applescript
tell application "Google Chrome"
    set tabCount to count of tabs of window 1
    repeat with t from 1 to tabCount
        set tTitle to title of tab t of window 1
        set tURL to URL of tab t of window 1
    end repeat
end tell
```

### 提取指定元素
```applescript
-- 提取页面中所有 .chat-message 元素的文本
execute active tab of window 1 javascript "
    Array.from(document.querySelectorAll('.chat-message'))
        .map(el => el.innerText)
"

-- 提取表格数据
execute active tab of window 1 javascript "
    Array.from(document.querySelectorAll('table tr')).map(row =>
        Array.from(row.querySelectorAll('td, th')).map(cell => cell.innerText)
    )
"

-- 提取页面标题 + meta 描述
execute active tab of window 1 javascript "
    JSON.stringify({
        title: document.title,
        description: document.querySelector('meta[name=description]')?.content,
        ogImage: document.querySelector('meta[property=\\'og:image\\']')?.content
    })
"
```

### 打开新 URL（在当前窗口）
```applescript
tell application "Google Chrome"
    open location "https://example.com"
end tell
```

### 在新标签打开
```applescript
tell application "Google Chrome"
    tell window 1 to make new tab with properties {URL:"https://example.com"}
end tell
```

## 浏览器支持情况

| 浏览器 | AppleScript 支持 | JS 执行 | 说明 |
|--------|-----------------|---------|------|
| Google Chrome | ✅ | ✅ (需设置) | 最完整 |
| Safari | ✅ | ✅ (需开发菜单) | `text of current tab` 可直接读文本 |
| Firefox | ⚠️ 有限 | ❌ | 只能获取 URL/标题，不能执行 JS |
| Edge | ✅ (同 Chromium) | ✅ | 同 Chrome 语法 |
| Arc | ✅ (同 Chromium) | ✅ | 名字是 "Arc" |
| Brave | ✅ (同 Chromium) | ✅ | 名字是 "Brave Browser" |

## 检测运行中的浏览器

```applescript
tell application "System Events"
    set browserList to {}
    set allProcs to every process whose background only is false
    repeat with proc in allProcs
        set pname to name of proc
        if pname contains "Chrome" or pname contains "Safari" or pname contains "Firefox" or pname contains "Edge" or pname contains "Arc" or pname contains "Brave" then
            set end of browserList to pname
        end if
    end repeat
end tell
return browserList
```

## AppleScript 的 `&` 避坑

Hermes terminal tool 将 AppleScript 的 `&`（字符串拼接）误判为 shell 后台指令。
**不要**在内联 AppleScript 中使用 `&`，写成文件再执行：

```bash
# ❌ 失败：内联 & 被拦截
osascript -e 'set x to "hello" & " world"'

# ✅ 成功：写成文件
cat > /tmp/t.applescript <<'EOF'
set x to "hello" & " world"
return x
EOF
osascript /tmp/t.applescript
```

## 常见问题

### Q: 执行 JS 报错 -10006
A: 用户没开启 Chrome 设置：显示 → 开发者 → 允许 Apple 事件中的 JavaScript。
**注意**：即使开启了，从 Hermes terminal 环境调用仍可能失败（osascript 进程可能无正确 tcc 权限链）。

### Q: AppleScript 的 `&` 被 Hermes terminal tool 拦截
A: Hermes terminal tool 将 `&` 误判为 shell 后台指令。两种解决方式：
1. 写成 `.applescript` 文件再用 `osascript 文件路径` 执行
2. 使用 `scripts/exec_applescript.py` 助手（自动写临时文件绕过）

### Q: AppleScript 卡住不返回
A: 加了 `timeout` 参数或用 `with timeout` 块：
```applescript
tell application "Google Chrome"
    with timeout of 15 seconds
        execute active tab of window 1 javascript "..."
    end timeout
end tell
```

### Q: 读不到页面文本（返回空）
A: 可能页面是 canvas/iframe 渲染的。尝试读取根部：
```applescript
execute active tab of window 1 javascript "
    document.documentElement.innerText || 
    document.body?.innerText || 
    '页面无文本内容'
"
```

### Q: 混合 stdout/stderr 输出问题
A: `osascript` 的 `log` 输出走 stderr，`return` 走 stdout。在终端中：
```bash
osascript script.applescript 2>&1  # 合并输出
osascript script.applescript 2>/dev/null  # 只拿 return
```
