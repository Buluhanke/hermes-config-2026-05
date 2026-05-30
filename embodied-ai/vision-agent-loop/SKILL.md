---
name: vision-agent-loop
description: 视觉Agent闭环 — 截图→VLM推理→解析action→执行，完整的桌面自动化循环。用于Hermes的screen-based agent能力。
trigger: 需要感知屏幕内容、做视觉决策、执行桌面操作时加载此技能
created: 2026-06-01
tags: [vision, agent-loop, desktop-automation, computer-use, screen-perception]
---

# 视觉Agent闭环 (Vision Agent Loop)

完整流程：截图 → VLM推理 → 解析action → 执行 → 验证

## 核心架构

```
screencapture → [smolvlm2 / Gemini] → action解析 → [computer_use/playwright] → 执行验证
```

**M4 Mac最优方案**：smolvlm2-agentic-gui（本地，7s/步，1.85GB）

## 执行流程

### 1. 截图（screencapture）
```bash
screencapture -x /tmp/agent_screen.png
# 可选：压缩到合适大小（sips -z 800 800）
```

### 2. VLM推理

**⚠️ 必须用 `/api/chat`，不能用 `/api/generate`（screen-watcher-vision skill 实测验证）**：
- `/api/generate`：1920x1080 截图需 41.6s，容易触发 120s 超时
- `/api/chat`：相同截图只需 31.7s，快 24%，响应格式更干净
- payload 格式差异：`prompt:` → `messages:[{role:'user',content:,images:}]`
- response 格式差异：`data['response']` → `data['message']['content']`

#### 本地Ollama（smolvlm2）✅ 主方案
```python
import base64, json, urllib.request

with open('/tmp/agent_screen.png', 'rb') as f:
    img = base64.b64encode(f.read()).decode()

payload = {
    'model': 'ahmadwaqar/smolvlm2-agentic-gui:latest',
    'messages': [{'role': 'user', 'content': '网页截图。描述：1)页面标题 2)主要元素 3)功能', 'images': [img]}],
    'stream': False,
    'options': {'temperature': 0.1}
}
req = urllib.request.Request(
    'http://localhost:11434/api/chat',  # ⚠️ 用 /api/chat，不用 /api/generate
    data=json.dumps(payload).encode(),
    headers={'Content-Type': 'application/json'},
    method='POST'
)
with urllib.request.urlopen(req, timeout=60) as r:
    response = json.loads(r.read())['message']['content']
```

**响应时间**：6-11秒（Mac本地，取决于截图复杂度）

#### 其他VLM备选
| 模型 | 响应 | 状态 | 备注 |
|------|------|------|------|
| smolvlm2-agentic-gui | 6-11s | ✅ **主方案** | GUI专用，1.85GB，M4 24GB最优 |
| qwen3-vl:2b | 60s+ 超时 | ❌ 不适合实时 | 已安装但太慢，仅适合离线OCR |
| qwen3-vl:8b | ~15s 估计 | ⚠️ 未实测 | 需 github 恢复后 pull |
| richardyoung/smolvlm2-2.2b-instruct | 未测 | ⚠️ 备选 | 通用 SmolVLM2，非GUI专用 |
| moondream:1.8b-v2-q4_K_M | 未测 | ⚠️ 备选 | 通用视觉，约1GB |
| Gemini 1.5-flash | DNS不通 | ❌ 网络问题 | 本地网络限制 |
| GLM 4V | 429额度耗尽 | ❌ | API额度问题 |

### 3. Action解析
VLM输出格式（smolvlm2示例）：
```json
{"action": "done", "reasoning": "页面标题为Example Domain"}
{"action": "scroll(direction='up', amount=10)", "reasoning": "..."}
```

**解析逻辑**：
- 匹配 `action: "click\|scroll\|type\|..."` 
- 提取参数：`direction`, `amount`, `text`, `coordinate`
- 异常处理：超时、N/A输出、模型幻觉

### 4. 执行层

#### computer_use（推荐）
```python
computer_use(action='click', element=N)  # SOM索引定位
computer_use(action='scroll', direction='up', amount=3)
computer_use(action='type', text='...')
```

#### Playwright + JS打标签（高精度场景）
```python
JS_EXTRACT_DOM = '''
() => {
    let elements = document.querySelectorAll('a, button, input, textarea, select, [role="button"], [tabindex="0"]');
    let interactables = [];
    elements.forEach(el => {
        const rect = el.getBoundingClientRect();
        if (rect.width === 0 || rect.height === 0) return;
        const uniqueId = idCounter++;
        el.setAttribute('data-hermes-id', uniqueId);
        interactables.push({
            id: uniqueId,
            tag: el.tagName.toLowerCase(),
            type: el.type || '',
            text: (el.innerText || el.value || el.placeholder || '').trim().substring(0, 60)
        });
    });
    return interactables;
}
'''
# 用 [data-hermes-id='X'] 精准定位执行
await page.locator('[data-hermes-id="12"]').fill('张三')
```

### 5. 验证循环
执行后重新截图 → VLM判断结果 → 继续或完成

## 已知问题与解决

### smolvlm2中文识别弱
- 表现：百度页面识别为"天气"，中文语境理解差
- 解决：用英文prompt，或用 qwen3-vl:8b（更好的中文）

### GLM 429额度耗尽
- 错误：`"余额不足或无可用资源包，请充值"`
- 解决：需充值或换用其他API key

### Gemini DNS不通
- `generativelanguage.googleapis.com` ping 100%丢包
- 原因：本地网络限制（非工具问题）
- 解决：用本地VLM替代

### qwen3-vl:2b超时
- 原因：模型太大（1.9GB），Mac GPU解码慢
- 解决：用 smolvlm2-agentic-gui（更快）

## 完整脚本模板

```python
#!/usr/bin/env python3
"""Vision Agent Loop 完整模板"""
import subprocess, time, base64, json, urllib.request

def screenshot(path, compress=False):
    subprocess.run(['screencapture', '-x', path], capture_output=True)
    if compress:
        subprocess.run(['sips', '-z', '800', '800', path, '--out', path], capture_output=True)

def call_vlm(prompt, img_path, timeout=60):
    with open(img_path, 'rb') as f:
        img = base64.b64encode(f.read()).decode()
    payload = {
        'model': VLM_MODEL,
        'messages': [{'role': 'user', 'content': prompt, 'images': [img]}],
        'stream': False,
        'options': {'temperature': 0.1}
    }
    req = urllib.request.Request(
        'http://localhost:11434/api/chat',  # ⚠️ 必须用 /api/chat，不用 /api/generate
        data=json.dumps(payload).encode(),
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=timeout) as r:
        res = json.loads(r.read())
    return time.time() - t0, res.get('message', {}).get('content', '')

# 主循环
url = 'https://example.com'
subprocess.run(['osascript', '-e', f'tell application "Google Chrome" to set URL of active tab of window 1 to "{url}"'], capture_output=True)
time.sleep(1.5)

screenshot('/tmp/agent_screen.png', compress=True)
t, response = call_vlm('ahmadwaqar/smolvlm2-agentic-gui:latest',
    '描述网页标题和主要元素',
    '/tmp/agent_screen.png')
print(f'VLM耗时: {t:.1f}s')
print(f'输出: {response[:300]}')
```

## 适用场景
- 屏幕感知（看见网页/桌面内容）
- 视觉决策（识别按钮、输入框、菜单）
- 自动化操作（点击、填表、滚动）
- 多轮交互（搜索→点击→填表→提交）

## 不适用场景
- 验证码识别（1688滑块等自研CAPTCHA无解）
- 需要精确坐标的复杂桌面操作（用Playwright DOM方案）
- 网络依赖的在线VLM（本地网络限制时）