# 企业微信文档登录态判断（2026-07-07 更新）

## 核心发现：两个 Chrome 实例同时存在 CDP 9222

**本次教训**：用户说"我登录好了"，但 CDP 一直显示登录页。根因是架构认知错误：

```
终端 curl http://127.0.0.1:9222/json/list  → 用户主 Chrome（已登录，PID 722）
Hermes browser_navigate / browser_cdp       → chrome-profile-mirror（独立进程，无登录态）
computer_use (app='Chrome')                 → 0x0（capture 失败，display 虚拟化）
```

关键：`hermes computer-use doctor` 显示权限全绿（Accessibility ✅, Screen Recording ✅），但 `computer_use` 返回 0x0。`computer_use` 的 display capture 在这个 Mac mini 上无法捕获前台窗口。

**教训**：`curl` 能连 9222 ≠ Hermes 工具能操作同一个 Chrome。必须先确认 browser 工具连的是哪个 Chrome 实例。

## 判断 SOP

### 步骤 1：确认当前 CDP 连接的是哪个 Chrome
```bash
curl -s http://127.0.0.1:9222/json/list | python3 -c "
import sys,json
tabs = json.load(sys.stdin)
for t in tabs:
    if t.get('type') == 'page':
        print('Tab:', t['title'][:40], '|', t['url'][:60], '| attached:', t.get('attached'))
"
```
- 如果页面内容是文档但 CDP 显示登录 iframe → 两个 Chrome 实例
- 如果两者一致 → 同一实例，可以继续

### 步骤 2：判断用户是否真的已登录（唯一可信方法）
**不要**只看 `document.title`。

```javascript
// 查 loginContainer 可见性
(function(){
    var lc = document.getElementById('loginContainer');
    if (!lc) return 'no loginContainer';
    return 'loginVisible: ' + getComputedStyle(lc).display + ',' + getComputedStyle(lc).visibility;
})()
```
- 返回 `block,visible` → 未登录或登录态过期
- 返回 `none,hidden` → 已登录

### 步骤 3：已登录但 CDP 仍显示登录页 → 隔离了，不要 reload

**绝对禁止**：
- ❌ Page.reload（会丢失用户在浏览器里已完成的登录状态）
- ❌ 问"要不要刷新"

**正确做法**：
1. 先问用户："你现在屏幕上是登录页还是文档内容？"
2. 用户说"是文档内容"但 CDP 仍显示登录页 → 换个 session 重试（`browser_navigate` 会创建新 CDP session）
3. 新 session 仍是隔离的 → 告知用户 limitation，建议用方案 B（给操作步骤用户自己执行）

## computer_use 捕获前台窗口失败的 workaround

`computer_use` 返回 0x0 时的替代方案：

1. **查 cua-driver 日志**：`log show --predicate 'subsystem == "com.trycua.driver"' --last 5m`
2. **尝试 `app='screen'` 捕获全屏**（同样 0x0 时说明 display session 问题）
3. **降级到 CDP**：`curl http://127.0.0.1:9222/json/list` 找目标 tab，用 `browser_cdp` + `target_id` 操作
4. **如果 CDP 也是 mirror profile** → 告知用户两条路径都隔离，需要装 CORS 代理扩展

## 架构图

```
用户主 Chrome (PID 722)
  └── ~/Library/Application Support/Google/Chrome/Default
       └── 开了 9222 端口 ← curl 终端能连
            └── tab: 企业微信文档（已登录，cookie: sheet_location 存在）

Hermes chrome-profile-mirror (独立进程)
  └── ~/.hermes/chrome-profile-mirror
       └── 独立 Chrome 实例
            └── tab: 企业微信文档（login_frame iframe 可见，未登录）

browser_navigate / browser_cdp → chrome-profile-mirror → 看到登录页
curl http://127.0.0.1:9222/json/list → 用户主 Chrome → 看到真实内容
computer_use → display capture → 0x0（display 虚拟化问题）
```

## 触发词

"我登录好了" / "已经登录" / "不要无头浏览器" → 先确认操作的是哪个 Chrome 实例，再行动。
