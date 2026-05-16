# 1688 扫码登录自动化流程

## 问题背景

`browser_navigate` 打开的是独立浏览器实例（无登录态），跳转到 open.1688.com 会重定向到淘宝登录页。

## 解决流程

1. `browser_navigate` 打开目标页（如 open.1688.com/support/register.htm）
2. 页面显示淘宝登录页 → 包含"密码登录"和"短信登录"两个tab
3. 点击"短信登录"（或类似tab）切换到扫码登录方式 → 显示二维码
4. **用户手动扫码**（AI 无法代操作）
5. 登录成功后，AI 继续自动化操作

## 关键命令

```python
# browser_navigate 打开页面
browser_navigate("https://open.1688.com/support/register.htm")

# 查看页面结构，找到登录tab
browser_snapshot()

# 点击"短信登录" tab 显示二维码（ref来自snapshot输出）
browser_click(ref="e8")  # "短信登录" tab

# 等待用户扫码后继续...
# 确认登录成功
browser_snapshot()
```

## 页面元素参考（open.1688.com 登录页）

| 元素 | ref | 说明 |
|------|-----|------|
| 密码登录 tab | e7 | link |
| 短信登录 tab | e8 | link（点击后显示二维码） |
| 账号输入框 | e13 | textbox |
| 密码输入框 | e14 | textbox |
| 登录按钮 | e12 | button |
| 忘记密码 | e9 | link |
| 免费注册 | e11 | link |

## 登录成功后

登录成功后页面 URL 会从 `login.taobao.com` 跳转到目标页（如 open.1688.com），此时 `browser_snapshot()` 会显示入驻页面内容，包含"采购服务商→立即入驻"等按钮。

## 当前状态（2026-05-10）

用户已扫码登录，但点击"立即入驻"按钮的精确定位尚未完成。
