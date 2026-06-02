# Chrome GPU合成层截屏限制（2026-06-01实测，2026-06-02修正）

## 问题描述
Chrome运行在GPU合成层，`CGWindowListCreateImage`（底层调用）有时截不到Chrome网页内容。

## 现象
- `computer_use capture app=Chrome` → bounds全[0,0,0,0]，窗口无法捕获
- CDP `Page.captureScreenshot` → 对所有标签页返回空（GPU加速的页面）
- `screencapture -x` → **✅ 成功**（347KB PNG，内容完整可见）

## 根因
- `computer_use`的AX窗口捕获失败是因为Chrome窗口**活动标签是`about:blank`**
- CDP截屏失败是Chrome GPU合成层问题（已知）
- `screencapture -x` 是macOS命令行工具，走系统底层截屏，**可以绕过Chrome GPU合成层**

## 当前可用方案

| 能力 | 状态 | 工具 | 备注 |
|------|------|------|------|
| 读取网页DOM | ✅ | browser_snapshot (8ms, AX Tree) | 动态内容（AI回复）读不到 |
| 点击网页元素 | ✅ | browser_click (ref索引) | 需要活动标签 |
| 输入文本 | ✅ | browser_type | 需要活动标签 |
| 截取Chrome内容 | ⚠️ | `screencapture -x` | ✅ 绕过GPU合成层，活动标签才能截到内容 |
| Vision OCR文字识别 | ✅ | ocr.py detect | 60ms，PaddleOCR高精度中文 |
| AI知识采集 | ⚠️ | `screencapture -x` + Vision OCR + MiniMax API | 需要解决登录态 |

## 关键发现（2026-06-02）
1. **活动标签机制**：Chrome一次只有一个标签是活动的，其他标签在后台，内容不渲染
2. **切换标签后截屏**：切到AI站点标签后，`screencapture -x` 能完整捕获页面内容
3. **computer_use失败原因**：捕获的是`about:blank`活动标签，所有元素bounds为[0,0,0,0]
4. **登录态仍是障碍**：即使截屏成功，AI站点需要登录才能对话（cookies缺失）

## 验证命令
```bash
# 测试screencapture是否能截到Chrome（活动标签内容）
screencapture -x /tmp/test.png && ls -la /tmp/test.png

# 检查Chrome当前活动标签URL
curl -s http://localhost:9333/json | python3 -c "import json,sys; [print(t['url']) for t in json.load(sys.stdin) if t.get('type')=='page']"

# 切换到指定标签（激活它）
python3 -c "
import asyncio, websockets, json
async def activate(tab_id):
    ws_url = f'ws://localhost:9333/devtools/page/{tab_id}'
    async with websockets.connect(ws_url, ping_interval=None) as ws:
        await ws.send(json.dumps({'id':1,'method':'Page.bringToFront'}))
asyncio.run(activate('TAB_ID_HERE'))
"
```