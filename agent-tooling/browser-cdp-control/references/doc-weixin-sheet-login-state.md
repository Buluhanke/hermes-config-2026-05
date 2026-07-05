# 企业微信文档 — doc.weixin.qq.com/sheet 已知模式（2026-07-06 实测）

## 登录态判断

主页面标题"企业微信文档" + 登录对话框可见 ≠ 已登录。

**判断方法**：Runtime.evaluate 查 iframe 结构：

```javascript
JSON.stringify({
  iframes: Array.from(document.querySelectorAll('iframe')).map(f => ({
    src: f.src,
    id: f.id,
    name: f.name,
    visible: f.offsetParent !== null
  }))
})
```

**未登录特征**：
- 有 `login_frame` iframe，src 含 `WeworkLogin.html`
- iframe 内嵌 `login.weixin.qq.com` 或 `login.work.weixin.qq.com` 登录页
- 主页面 body 有 `#loginContainer` / `.login-dialog` 元素

**已登录特征**：
- 无 login_frame iframe
- 主页面直接加载文档内容（canvas 渲染表格）

## 编辑前置条件

未登录 → 用户必须先在 iframe 登录界面扫码或输入账号。
登录成功后 iframe 消失，文档 canvas 加载完毕才能 CDP 自动化。

## CDP 操作限制

- 内容在 canvas 渲染 → 标准 DOM query 返回 0
- 可操作：formula bar (`#alloy-simple-text-editor`)、cell 地址框 (`input.bar-label`)、sheet tab 切换
- 不可操作：canvas 内部渲染、鼠标选择高亮

## 与 chrome-profile-mirror 的关系

Hermes 的 `chrome-profile-mirror` 是独立的 Chrome 实例（`--user-data-dir=~/.hermes/chrome-profile-mirror`）。
用户自己的 Chrome（PID 722）在 `~/Library/Application Support/Google/Chrome/Default`。

**两者 CDP 9222 端口隔离**：
- `chrome-profile-mirror` 的 9222 → 无用户登录态
- 用户主 Chrome 的 9222 → 有完整登录态

若要操作用户主 Chrome 的已登录标签页，用 `browser_cdp` + `target_id` 直连，不需要也没法合并 profile。
