# CDP/DOM访问限制与替代方案（2026-06-02完整诊断）

## 核心问题分类

| 问题 | 原因 | 解决方案 |
|------|------|---------|
| CDP WebSocket HTTP 500 | Shadow DOM + 懒加载 | screencapture截图（唯一解） |
| browser工具无登录态 | 临时Chrome profile | CDP 9222直连用户Chrome |
| computer_use capture 0x0 | 活动标签是about:blank | 切换到目标标签后再capture |
| Page.captureScreenshot 0字节 | Chrome GPU合成层 | screencapture -x绕过 |
| MiniMax 2.7/3无法读图 | 纯文字模型，无多模态 | 需切到Claude/Gemini等 |

## Shadow DOM站点清单（2026-06-02实测）

以下站点的CDP `Runtime.evaluate`返回HTTP 500或空text nodes，DOM查询完全失效：
- chat.deepseek.com（DeepSeek）
- chatglm.cn（ChatGLM）
- doubao.com（豆包）
- grok.com（Grok部分功能）

Gemini可读（`gemini.google.com`）。

## 可行方案（按场景）

### 场景1：注入问题到AI站点（无回复需求）
✅ **CDP直接注入** — 向已登录站点的输入框写内容并发送
- 用CDP `Runtime.evaluate`向输入框注入文字
- 成功率取决于登录态和站点结构

### 场景2：读取AI回复内容
⚠️ **screencapture + 视觉模型**（当前模型不支持图片输入，需切模型）
1. `screencapture -x /tmp/ai_site.png`
2. 用Claude/Gemini等视觉模型分析截图

### 场景3：信息检索类查询
✅ **Bing搜索** — Python urllib + 正则提取，无需登录态
```python
import urllib.request, urllib.parse, re
query = "2025 AI大模型进展"
url = f"https://www.bing.com/search?q={urllib.parse.quote(query)}"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req, timeout=10) as resp:
    content = resp.read().decode('utf-8', errors='ignore')
# 提取搜索结果
results = re.findall(r'<li[^>]*class="[^\"]*b_algo[^\"]*"[^>]*>(.*?)</li>', content, re.DOTALL)
```

## 不要做的事（已验证无效）

- ❌ 对Shadow DOM站点用CDP `Runtime.evaluate` — HTTP 500
- ❌ 等`browser_snapshot`期待Shadow DOM内容出现 — 动态内容查不到
- ❌ 依赖`Page.captureScreenshot` — Chrome GPU返回0字节
- ❌ 用当前MiniMax模型分析截图 — 不支持图片输入