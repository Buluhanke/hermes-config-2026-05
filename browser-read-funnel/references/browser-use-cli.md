# browser-use CLI — 参考文档

> browser-use CLI 是 SOTA 浏览器 Agent 工具，109K GitHub stars。
> 与 browser-read-funnel 的关系：browser-use = **主动操作层**（点击/填表/导航），
> 其他层 = **被动读取层**（抓内容）。两者互补。

## 验证状态（2026-08-17 实测）

```bash
browser-use doctor
# ✅ chrome running, daemon alive, 1 connection
# 连接的是用户已有的 Chrome via CDP (chrome://inspect)
```

## 安装

```bash
# 已安装（uv tool）
uv tool install browser-use

# 独立安装 Chromium（如需要）
browser-use install

# 验证
browser-use doctor
```

## Chrome 端配置（只需做一次）

1. 打开 Chrome → `chrome://inspect/#remote-debugging`
2. 勾 **"Allow remote debugging for this browser instance"**
3. Chrome 144+ 首次连接会弹授权框 → 点 Allow

## 核心命令

```bash
# 查看当前页面状态
browser-use state

# 打开 URL（新标签）
browser-use open https://example.com

# 截图
browser-use screenshot output.png

# 点击坐标
browser-use click 5

# 输入文字
browser-use type "Hello"

# 在 heredoc 里用 Python 接口（推荐）
browser-use <<'PY'
new_tab("https://example.com")
wait_for_load()
print(page_info())
PY
```

## Python 接口（heredoc 方式）

```bash
browser-use <<'PY'
# 打开新标签
new_tab("https://github.com/browser-use/browser-use")
wait_for_load()

# 获取页面信息
info = page_info()
print(info['url'])
print(info['title'])

# 点击元素（需要先用 capture_screenshot 确认坐标）
# click_at_xy(x, y)

# 提取页面文字
js("document.body.innerText")

# 关闭标签
close_tab()
PY
```

## 已知限制

- Google.com 被墙（CDN 限流），用 GitHub 测试
- GitHub search 有 rate limit（429 Too Many Requests），加 `?q=...` 参数可能触发
- 需要 `chrome://inspect` 开启 remote debugging 才能连接用户 Chrome

## 与 cua-driver 的区别

| | browser-use CLI | cua-driver (computer_use) |
|---|---|---|
| 控制范围 | 浏览器 Tab | 全桌面窗口 |
| 连接方式 | CDP (chrome://inspect) | AX tree (macOS) |
| 适合场景 | 网页操作、表单填写、数据提取 | 跨应用操作、桌面自动化 |
| 登录态 | 继承用户 Chrome 的 Cookie | 同上 |
