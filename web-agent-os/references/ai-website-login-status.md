# AI 网站登录访问模式（2026-06-01 实测）

## 关键发现：用户真实Chrome (端口9222) 已可直接访问

用户Chrome启动时加 `--remote-debugging-port=9222` 参数后，Hermes 可通过CDP WebSocket直接连接，**读取已登录的AI网站会话**。

```python
# 验证命令（已成功执行）
curl http://127.0.0.1:9222/json/version
# 返回: Chrome/148.0.0.0

# CDP WebSocket 直连示例
ws = websocket.create_connection("ws://127.0.0.1:9222/devtools/page/<tab_id>", timeout=10)
# DOM.getDocument → 成功返回根节点
# Page.getLayoutMetrics → clientWidth=1200, clientHeight=864
```

## 端口分工

| 端口 | Chrome实例 | 登录态 | 用途 |
|------|-----------|--------|------|
| 9222 | 用户真实Chrome | ✅ 已登录 | 读AI网站内容/对话 |
| 9333 | chrome-debug独立profile | ❌ 需重新登录 | dom_tools专用 |

**最佳实践：优先用 9222 读取用户已登录内容。**

## browser 工具的 Chrome 实例架构

```
browser_navigate/click/type
    ↓
Hermes Agent 管理 Playwright 临时 Chromium
    ↓
临时 profile（/var/folders/.../agent-browser-chrome-XXX/）
    ↓
每次启动全新，cookies 不持久化
```

**结论**：browser 工具控制的是**全新临时实例**，无任何登录态。

## 解决方案对比

| 方案 | 登录态持久 | 实施难度 | 用户操作 | 备注 |
|------|-----------|---------|---------|------|
| A. 在 browser 工具里登录 | ❌ session级 | ⭐ | 登录一次 | 最简，每次 gateway 重启后需重登 |
| B. chrome-debug Chrome (9333) | ✅ profile级 | ⭐⭐ | 手动启动一次 | 长期有效，需终端命令 |
| C. 用户Chrome + CDP 9222 | ✅ profile级 | ⭐ | 用户正常启动 | **推荐，零配置** |
| D. cookie 导出扩展 | ✅ 可导入 | ⭐⭐ | 安装扩展+导出 | 需手动操作，cookie 格式转换 |

## 快速测试：验证登录态是否可用

```python
# 用 CDP 直连用户Chrome 9222
import websocket, json

def get_tabs(port=9222):
    import urllib.request
    with urllib.request.urlopen(f"http://127.0.0.1:{port}/json", timeout=5) as r:
        return json.loads(r.read())

tabs = get_tabs()
for t in tabs:
    print(t.get('title', '无标题'), '|', t.get('url', ''))
```

## 各 AI 网站登录要求

| 网站 | 最低登录要求 | 登录方式 |
|------|-------------|---------|
| 豆包 | 抖音账号或手机号 | 扫码/短信 |
| ChatGLM | 手机号注册 | 短信验证码 |
| DeepSeek | 手机号注册 | 短信验证码 |
| Gemini | Google 账号 | 谷歌登录 |
| ChatGPT | OpenAI 账号 | 邮箱/谷歌/GitHub |
| Grok | X/Twitter 账号 | 推特登录 |

## 已知限制

- browser 工具临时实例的 cookies 在 gateway 重启后清空
- chrome-debug Chrome 的 profile 持久化，但需手动启动
- 豆包访客模式直接拒绝对话，不会显示输入框
- computer_use 方案依赖用户可见窗口，不适合后台运行
- 用户Chrome端口9222需要用户在启动Chrome时加参数（或者用户已手动加了这个参数）