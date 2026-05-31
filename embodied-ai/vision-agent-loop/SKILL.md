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
screencapture → [qwen3-vl:2b / future CUA model] → action解析 → [computer_use/playwright/RPA] → 执行验证
```

**M4 Mac当前方案**：qwen3-vl:2b（本地，7-47s/步，1.76GB，scene classification 优先）

**参考框架**：GUI Agents 三代架构演进（详见 references/fara1.5-and-three-generations.md）
- Gen 1: Selector-Action (RPA) — 30-40% 维护 = selector 修复
- Gen 2: Vision+LLM (Set-of-Marks) — **Hermes 当前位置**，open-loop，无验证
- Gen 3: VLA Unified Model — 目标方向，closed-loop (perception→reason→action→verify)

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

#### 本地Ollama（qwen3-vl:2b）✅ 当前主方案
```python
import base64, json, urllib.request

with open('/tmp/agent_screen.png', 'rb') as f:
    img = base64.b64encode(f.read()).decode()

payload = {
    'model': 'qwen3-vl:2b',
    'messages': [{'role': 'user', 'content': 'Classify this screenshot: browser, desktop, or other?', 'images': [img]}],
    'stream': False,
    'options': {'temperature': 0.0}
}
req = urllib.request.Request(
    'http://localhost:11434/api/chat',
    data=json.dumps(payload).encode(),
    headers={'Content-Type': 'application/json'},
    method='POST'
)
with urllib.request.urlopen(req, timeout=60) as r:
    response = json.loads(r.read())['message']['content']
```

**响应时间**：6.9-47s（scene classification ~7s，full screenshot analysis 19-47s，取决于复杂度）

**⚠️ 注意**：smolvlm2-agentic-gui 已于 2026-06-02 从 Ollama registry 下线（pull 返回 404），qwen3-vl:2b 已接管全部视觉任务。

#### 其他VLM备选
| 模型 | 响应 | 状态 | 备注 |
|------|------|------|------|
| qwen3-vl:2b | 7-47s | ✅ **当前主方案** | 1.76GB，scene classification 7s，截图分析 19-47s |
| qwen3-vl:8b | ~15s 估计 | ⚠️ 未实测 | 需 github 恢复后 pull，6.1GB |
| Fara1.5-4B (Microsoft) | 未测 | ⚠️ 待评估 | 2026-05-21发布，Online-Mind2Web 57%，Qwen3.5基座 |
| richardyoung/smolvlm2-2.2b-instruct | 未测 | ⚠️ 备选 | 通用 SmolVLM2，非GUI专用 |
| moondream:1.8b-v2-q4_K_M | 未测 | ⚠️ 备选 | 通用视觉，约1GB |
| Mano-P 4B (Mininglamp) | ~80 tok/s M5 | ⚠️ Cider SDK | Think-Act-Verify闭环，Apache-2.0，需github恢复 |
| smolvlm2-agentic-gui | 6-11s (历史) | ❌ 已从registry下线 | 2026-06-02 404，非可用模型 |
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

### qwen3-vl:2b 响应时间波动
- 原因：模型 1.76GB，Mac GPU 解码速度受截图尺寸/复杂度影响
- scene classification（400-800px 缩略图）：6.9-7s ✅ 适合实时
- full screenshot analysis（1920x1080）：19-47s，高分辨率场景触发超时
- 解决：缩小输入截图尺寸（sips -z 800 800），或用 `/api/chat` 替代 `/api/generate`（快 ~24%）
- 注意：smolvlm2-agentic-gui 已从 Ollama registry 下线，qwen3-vl:2b 为当前唯一可用本地视觉模型

### smolvlm2中文识别弱（已下线，历史记录）
- smolvlm2-agentic-gui 已在 2026-06-02 从 Ollama registry 删除，pull 返回 404
- qwen3-vl:2b 中文理解能力强于 smolvlm2

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
t, response = call_vlm('qwen3-vl:2b',
    'Describe the web page and its main elements.',
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

---

## 架构演进参考

### 三代桌面自动化框架（详见 references/fara1.5-and-three-generations.md）

| 世代 | 架构 | 代表 | 特征 |
|------|------|------|------|
| Gen 1 | Selector-Action | RPA (UiPath等) | 30-40%维护=selector修复，UI变化即断链 |
| Gen 2 | Vision+LLM (open-loop) | Set-of-Marks, **Hermes当前** | 截图→坐标，无验证，无错误恢复 |
| Gen 3 | VLA Unified Model (closed-loop) | Mano-P 4B, Fara1.5 | 统一感知-推理-动作-验证闭环 |

### Fara1.5 (Microsoft, May 2026)
- Qwen3.5 基座，4B/9B/27B 三尺寸
- **Observe-Think-Act 循环**，每次输入最近 3 张截图 + 历史对话
- Context management meta-actions: memorize/ask_user/verify
- Online-Mind2Web 63% (9B), 72% (27B) — 超越 GPT-5.4 CUA 和 Gemini 2.5
- FaraGen1.5: Copilot CLI 自动生成沙盒站点训练数据

### 对 Hermes 的实践意义
- DRY_RUN=False 切换 = Gen 2 → Gen 3 架构跨越
- 当前 vision-agent-loop 缺少：verify 闭环、多帧上下文、context management actions
- SafeGround + Fara1.5 insights 提供 Gen 3 过渡路径