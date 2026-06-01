# AI 网站登录访问模式（2026-06-01 实测）

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
| B. 启动 chrome-debug Chrome 并登录 | ✅ profile级 | ⭐⭐ | 手动启动一次 | 长期有效，需终端命令 |
| C. cookie 导出扩展 | ✅ 可导入 | ⭐⭐ | 安装扩展+导出 | 需手动操作，cookie 格式转换 |
| D. Keychain 解锁 + browsercookie | ✅ profile级 | ⭐⭐⭐ | Keychain 解锁 | 复杂，易超时 |

## 推荐路径：chrome-debug Chrome

```bash
# 启动带调试端口的 Chrome（一次性，用户操作）
open -a "Google Chrome" --args \
  --user-data-dir="$HOME/.hermes/chrome-debug" \
  --remote-debugging-port=9333 \
  --no-first-run \
  --no-default-browser-check

# 验证端口
curl -s http://127.0.0.1:9333/json | python3 -c "import json,sys; [print(t['title'], t['url']) for t in json.load(sys.stdin)]"
```

启动后：
1. 用这个 Chrome 手动登录各个 AI 网站
2. 登录完成后，Hermes 用 `dom-js-inject` 连接 9333 端口
3. 后续 automation 直接复用登录态

## 各 AI 网站登录要求

| 网站 | 最低登录要求 | 登录方式 |
|------|-------------|---------|
| 豆包 | 抖音账号或手机号 | 扫码/短信 |
| ChatGLM | 手机号注册 | 短信验证码 |
| DeepSeek | 手机号注册 | 短信验证码 |
| Gemini | Google 账号 | 谷歌登录 |
| ChatGPT | OpenAI 账号 | 邮箱/谷歌/GitHub |
| Grok | X/Twitter 账号 | 推特登录 |

## 快速测试：验证登录态是否可用

```python
# 用 dom-js-inject 提取页面内容
from dom_tools import dom_snapshot

result = dom_snapshot()  # 当前活动 tab
# 检查是否显示"登录"按钮或用户头像
```

## 已知限制

- browser 工具临时实例的 cookies 在 gateway 重启后清空
- chrome-debug Chrome 的 profile 持久化，但需手动启动
- 豆包访客模式直接拒绝对话，不会显示输入框
- computer_use 方案依赖用户可见窗口，不适合后台运行
