# AI聊天网站可访问性（2026-06-01）

## 状态总览

| 网站 | URL | 登录态 | AI对话 | 备注 |
|------|-----|--------|--------|------|
| 豆包 | doubao.com | ❌ 显示登录按钮 | ❌ 无回复 | 需手机号登录 |
| ChatGLM | chatglm.cn | ❌ 显示登录按钮 | ❌ 无回复 | 需账号登录 |
| DeepSeek | chat.deepseek.com | ❌ 需要登录 | ❌ | 需手机号 |
| ChatGPT | chat.openai.com | ❌ 429限速 | ❌ | 账号被限制 |
| Gemini | gemini.google.com | ❌ 需Google账号 | ❌ | 未登录 |
| Grok | grok.com | ⚠️ 页面空 | ⚠️ | 状态不明 |

## 技术原因

Playwright启动的是干净Chrome实例，没有用户Chrome的cookies和session。

AI网站检测到无头/无cookie浏览器：
- 禁用AI对话功能
- 弹出登录验证
- 返回429或空白页面

## 替代方案

### Bing搜索（✅可用）
```python
import urllib.request, urllib.parse, re

query = "2025 AI大模型 技术进展"
url = f"https://www.bing.com/search?q={urllib.parse.quote(query)}&mkt=zh-cn"
req = urllib.request.Request(url, headers={
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15'
})
with urllib.request.urlopen(req, timeout=10) as resp:
    content = resp.read().decode('utf-8', errors='ignore')
results = re.findall(r'<li[^>]*class="[^"]*b_algo[^"]*"[^>]*>(.*?)</li>', content, re.DOTALL)
```

### 用户配合模式
用户能看到Playwright浏览器窗口，直接口头告诉AI回复内容。

### Cookies导入（理论可行）
从用户Chrome导出cookies.json → 导入Playwright context。需要：
1. Chrome DevTools Protocol (CDP)
2. Chrome安全存储解密（macOS Keychain）
3. 第三方工具如 browsercookie（当前超时）

## 结论

AI知识获取现阶段依赖：
1. Bing搜索（信息类查询）
2. 用户口头转述（AI对话内容）
3. 长期：解决cookies导入问题
