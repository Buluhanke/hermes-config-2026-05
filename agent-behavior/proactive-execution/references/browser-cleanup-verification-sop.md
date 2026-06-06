# 浏览器清理验证 SOP（2026-06-04 实测）

## 核心原则

**没有验证步骤的清理流程等于没清理。**

每次浏览器操作后，必须验证窗口关闭，不能假设"关了"。

## 标准流程

### Step 1: 清理

```bash
osascript -e 'tell application "Google Chrome" to close every window'
```

### Step 2: 立即验证（不能跳过）

```bash
count=$(osascript -e 'tell application "System Events" to tell process "Google Chrome" to get count of windows')
if [ "$count" -ne 0 ]; then
    # 还有残留，重试
    osascript -e 'tell application "Google Chrome" to close every window'
    sleep 1
    count=$(osascript -e 'tell application "System Events" to tell process "Google Chrome" to get count of windows')
fi
# 期望: count = 0
```

### Step 3: 确认

期望输出: `count = 0`

不等于 0 → 再跑一次 osascript close every window，或用 `mcp_chrome_chrome_close_tabs`

## 为什么 osascript 清理后还要验证

`osascript close every window` 在某些情况下会静默失败（特别是 debug 模式的 Chrome）：
- Chrome 的"全部关闭"命令可能只关了一个窗口，而不是所有窗口
- macOS Ventura+ 的多窗口管理有时会保留一个"空"窗口
- 验证 `count of windows` 返回 0 才算真正干净

## 备选工具

如果 osascript 不稳定，用 MCP chrome：
```bash
mcp_chrome_chrome_close_tabs
```
（会自动关闭标签页和丢弃 Playwright 引用，最彻底）

## 反面教材（2026-06-04 真实事件）

1. 上一轮已加"用完即关"规则
2. 本轮：`computer_use capture` → `mcp_chrome get_windows_and_tabs` → `osascript close every window`
3. **但没验证窗口数**
4. 几分钟后用户反馈"屏幕全是浏览器"
5. 修复：补上 `count of windows` 验证步骤

**教训**：写规则时只写 "how to clean"，没写 "how to verify clean"。

---

更新来源：proactive-execution skill → 规则12（2026-06-04）