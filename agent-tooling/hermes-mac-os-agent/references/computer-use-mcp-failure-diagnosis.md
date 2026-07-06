# computer_use MCP 故障诊断（2026-07-09 实测）

## 症状
- `computer_use` tool（`mode=som/vision/ax`）返回 `0x0`，`elements: []`
- `list_apps` 返回空
- 但 `hermes computer-use doctor` 显示全部 ✅

## 根因
cua-driver MCP server 进程活着，但 Hermes → cua-driver 的 MCP 通道路由不通。

## 诊断 SOP

```bash
# Step 1: 验证 TCC 权限（应该全绿）
hermes computer-use doctor

# Step 2: 验证 cua-driver 进程
ps -p $(lsof -ti:9321 2>/dev/null) -o pid,stat,command 2>/dev/null
# 期望看到: pid XXXX Ss /Applications/CuaDriver.app/Contents/MacOS/cua-driver mcp

# Step 3: 用 osascript 读浏览器状态（fallback）
osascript -e '
tell application "Google Chrome"
    set tabTitle to title of active tab of front window
    set tabURL to URL of active tab of front window
    return "Title: " & tabTitle & "
URL: " & tabURL
end tell
'

# Step 4: 用 screencapture 截屏（fallback）
screencapture -x -R 0,30,1920,995 /tmp/chrome_screen.png
# 然后 vision_analyze /tmp/chrome_screen.png（如果 vision provider 可用）
```

## Fallback 工具链

当 `computer_use` MCP 不通时：

| 工具 | 用途 | 限制 |
|---|---|---|
| `osascript` | 读 Chrome URL / title / window bounds | 只读界面信息，读不到网页 DOM |
| `screencapture` | 截图 | ✅ 可用 |
| `vision_analyze` | 看图理解 | ⚠️ 可能因 provider 配置报错 |
| `cliclick` | 按坐标点击 | ✅ 可用（`cliclick c:100,200`）|

## vision_analyze 常见报错

```
Gemini HTTP 400 (INVALID_ARGUMENT): * GenerateContentRequest.model: unexpected model name format
```

**根因**: `auxiliary.vision` 的 `model` 字段格式不对（通常是空字符串或包含 provider 前缀）

**检查**:
```bash
grep -A5 "auxiliary\|vision" ~/.hermes/config.yaml
```

**修法**: 设置正确的 model 名（如 `gemini-2.0-flash`）或清空让 provider 自动选择。

## 相关文件
- `references/vision-fallback-integration.md` — vision provider 二级降级方案
- `references/cua-driver-daemon-mcp-lifecycle.md` — cua-driver 生命周期
