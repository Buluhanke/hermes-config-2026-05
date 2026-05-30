# AI网站登录与自动化 — 踩坑记录

## 问题背景

用户要求在本地Chrome(日常用)上自动化操作6个AI网站：
- https://gemini.google.com/app
- https://www.doubao.com/chat
- https://chatglm.cn/main/alltoolsdetail
- https://chat.deepseek.com/
- https://chatgpt.com/
- https://grok.com/z

## browser工具的局限

browser工具(MCP chrome bridge)连接的是Hermes专用Chrome实例：
```
--user-data-dir=/Users/aimac/.hermes/chrome-debug
```
这个profile没有登录任何AI网站，而用户日常Chrome是：
```
~/Library/Application Support/Google/Chrome/Default
```

两个profile完全隔离，cookies不共享。

## 各网站验证状态

| 网站 | browser工具Chrome | 原因 |
|------|------------------|------|
| 豆包 | ✅ 可用 | 不需要登录 |
| Gemini | ❌ Cloudflare/验证 | 需要Google账号 |
| ChatGLM | ❌ 滑动验证 | 反爬拦截 |
| DeepSeek | ❌ 需要手机号 | 账号体系 |
| ChatGPT | ❌ Cloudflare | 严格反爬 |
| Grok | ❌ Cloudflare | 严格反爬 |

## 解决方案

### 方案A：browser工具Chrome登录（部分可行）
- 对不需要登录的网站（豆包）直接可用
- 被Cloudflare/滑动验证挡的网站无效
- IP被识别为数据中心/bot流量

### 方案B：AppleScript操作用户日常Chrome
- 可以操作用户真实登录状态的Chrome
- 需要账号信息（手机号/邮箱）才能完成登录
- 操作速度慢，需要窗口可见

### 方案C：复制Cookies（理论上可行）
把用户日常Chrome的Cookies复制到hermes chrome-debug profile。
实现难度高，涉及SQLite解析、Cookie加密问题。

## 结论

AI网站自动化受限于：
1. Cloudflare等反爬机制
2. browser工具Chrome profile与用户日常Chrome隔离
3. 账号体系（手机号/邮箱）需要用户配合提供

对于真人化AI Agent目标，更可行的路径是：
- 无账号网站：browser工具直接操作
- 有账号网站：用户先在日常Chrome登录，用AppleScript操作用户日常Chrome
