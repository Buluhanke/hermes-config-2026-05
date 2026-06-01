# AI网站访问状态参考（2026-06实测）

## 免登录站点（可直连）
- **Gemini** (gemini.google.com) ✅ 免登录，多模态强，可上传文件，首选
- **豆包** (doubao.com) ✅ 免登录，字节跳动，响应快

## 需注册站点
- **ChatGLM** ❌ 需手机号注册
- **DeepSeek** ❌ 需手机号
- **ChatGPT** ❌ 需OpenAI账号
- **Grok** ❌ 需X/Twitter账号

## 核心问题：browser工具Chrome没有登录态

### 问题根因
- browser工具Chrome = agent-browser独立临时实例（`/var/folders/.../agent-browser-chrome-XXX/`）
- 用户Chrome = 日常Chrome（`~/Library/Application Support/Google/Chrome/Default/`）
- 两者cookies/状态不共享

### 解决方案：用 computer_use 控制用户真实Chrome

```
1. computer_use(action="capture", app="Chrome", mode="ax")
   → 读取用户Chrome的AX Tree（纯文本，不需要vision模型）
   
2. 判断用户Chrome里是否有已登录的AI网站标签页

3. computer_use(action="click", element=N) 操作用户Chrome
```

### 为什么不用截图
- AI网站都是结构化网页
- AX Tree文本提取 + Playwright语义定位比截图快10倍、Token消耗低
- 只有Canvas验证码才需要截图

## browser_navigate 适用场景
- 用户Chrome没有目标AI网站 → 用browser_navigate开新页面
- 新页面是独立Chromium实例，没有用户登录态
- 对于免登录站点（Gemini、豆包）可以直接使用