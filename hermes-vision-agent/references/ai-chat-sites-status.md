# AI聊天网站可访问性（2026-06-01初建，2026-06-02更新）

## 状态总览

| 网站 | URL | 登录态 | AI对话 | 截屏可见 | 备注 |
|------|-----|--------|--------|---------|------|
| 豆包 | doubao.com | ❌ 显示登录按钮 | ❌ 无回复 | ✅ 可见 | 需手机号登录 |
| ChatGLM | chatglm.cn | ❌ 显示登录按钮 | ❌ 无回复 | ✅ 可见 | 需账号登录 |
| DeepSeek | chat.deepseek.com | ❌ 需要登录 | ❌ | ✅ 可见 | 需手机号 |
| ChatGPT | chat.openai.com | ❌ 429限速 | ❌ | ✅ 可见 | 账号被限制 |
| Gemini | gemini.google.com | ❌ 需Google账号 | ❌ | ✅ 可见 | 未登录 |
| Grok | grok.com | ⚠️ 页面空 | ⚠️ | ⚠️ | 状态不明 |

## 技术原因

**登录态问题**：Playwright启动的是干净Chrome实例，没有用户Chrome的cookies和session。
AI网站检测到无头/无cookie浏览器 → 禁用AI对话功能 → 弹出登录验证。

**截屏问题（已解决）**：
- 之前认为screencapture对Chrome无效 → **2026-06-02实测 `screencapture -x` ✅ 成功**
- `computer_use capture app=Chrome` 返回0x0是活动标签问题，不是Chrome GPU问题
- 切换到AI站点标签后，screencapture能完整捕获登录页面内容

**登录态仍是核心障碍**：即使截屏成功，AI对话功能需要账号登录，cookies缺失导致无法真正采集知识。

## 截屏验证结果（2026-06-02实测）

```
screencapture -x /tmp/ai_screenshots/chrome_full.png
-rw-r-----@ 1 aimac wheel 346977 Jun  2 15:55 /tmp/ai_screenshots/chrome_full.png
```

Vision OCR分析截图确认：7个AI站点标签可见，活动标签是`about:blank`。

## 替代方案

### 方案1：screencapture + Vision OCR（推荐用于免费方案）
```bash
# 1. 切换到目标AI站点标签（激活）
python3 -c "
import asyncio, websockets, json
async def activate(tab_id):
    ws_url = f'ws://localhost:9333/devtools/page/{tab_id}'
    async with websockets.connect(ws_url, ping_interval=None) as ws:
        await ws.send(json.dumps({'id':1,'method':'Page.bringToFront'}))
asyncio.run(activate('TAB_ID'))
"

# 2. 截屏
screencapture -x /tmp/ai_site.png

# 3. Vision OCR读取
~/.hermes/hermes-agent/venv/bin/python3 ~/.hermes/skills/vision/hermes-ocr/scripts/ocr.py read /tmp/ai_site.png
```

### 方案2：Bing搜索（信息类查询）
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

### 方案3：用户配合模式
用户能看到Playwright浏览器窗口，直接口头告诉AI回复内容。

### 方案4：Cookies导入（理论可行，未验证）
从用户Chrome导出cookies.json → 导入Playwright context。需要：
1. Chrome DevTools Protocol (CDP)
2. Chrome安全存储解密（macOS Keychain）
3. 第三方工具如 browsercookie

## 结论

AI知识采集现阶段可行路径：
1. **screencapture + Vision OCR** — 切到标签 → 截屏 → OCR读文字
2. **Bing搜索** — 信息类查询
3. **用户口头转述** — AI对话内容
4. **长期**：解决cookies导入问题

不要做的事：
- 不要反复等 `browser_snapshot` 期待AI回复出现 — 动态内容查不到
- 不要依赖CDP `Page.captureScreenshot` — Chrome GPU合成层返回空