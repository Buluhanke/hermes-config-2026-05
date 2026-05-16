---
name: hermes-vision-connect
description: "串联截屏→VLM分析→拟真执行的免费视觉闭环。优先用本地Ollama(Qwen2.5-VL)，兜底用OpenRouter(Gemini Flash)。"
version: 1.0.0
platforms: [macos]
metadata:
  hermes:
    tags: [vision, screen-understanding, free, openrouter, ollama]
    category: desktop
---

# hermes-vision-connect

**目标**：截屏 → VLM分析 → 返回可执行指令 → 拟真执行

**免费优先原则**：
1. 优先本地Ollama + Qwen2.5-VL（零Token消耗）
2. 兜底OpenRouter + Gemini Flash（$0.001/M视觉Token）

## 核心流程

```
用户指令（"帮我点这个按钮"）
    ↓
截屏（mss，~50ms）
    ↓
VLM分析（Ollama或OpenRouter）
    ↓
返回坐标+动作描述
    ↓
human-rpa执行（贝塞尔曲线+随机抖动）
    ↓
截图确认（SSIM，验证是否成功）
```

## 使用方式

### 直接用Python（在execute_code里）

```python
import sys
sys.path.insert(0, '/Users/aimac/.hermes/hermes-agent/venv/lib/python3.13/site-packages')

from vision_connect import find_and_click, ask_screen

# 找元素并点击
result = find_and_click("加入进货单")
print(result)

# 问屏幕一个问题
answer = ask_screen("当前页面是什么内容？")
print(answer)
```

### 在Hermes对话里

```
用户：帮我点"登录"按钮
→ 截图 → 发给Qwen2.5-VL → 返回坐标(x,y) → human_click(x,y) → 截图确认
```

## find_and_click 实现逻辑

```python
def find_and_click(description: str, retry: int = 2):
    """
    1. 截屏保存 /tmp/hermes_screen.png
    2. 优先发 Ollama Qwen2.5-VL（http://127.0.0.1:11434）
    3. 如果 Ollama 挂了，fallback 到 OpenRouter Gemini Flash
    4. 解析返回的坐标和动作
    5. 用 human_click 执行
    6. 再截一张屏，用 SSIM 确认是否跳转
    """
```

## 关键坑点（2026-05-16实测）

### M4 24GB 模型优先级

qwen2.5vl:7b 在 M4 24GB 上会 OOM 加载失败。必须先用 smolvlm2：

```python
models_to_try = [
    ("ahmadwaqar/smolvlm2-agentic-gui:latest", 60),  # 先试这个，2GB
    ("qwen2.5vl:7b", 90),  # 只有 smolvlm2 挂了才试这个
]
```

### mss 新版 API

```python
# ❌ 旧版（mss < 10.0）：已deprecated，运行时警告
with mss.mss() as s:
    s.shot(output=path, monitor=1)

# ✅ 新版（mss >= 10.0）
with mss.MSS() as s:
    s.shot(output=path)
```

### SSIM 阈值实测校准

| SSIM | 实际状态 |
|------|---------|
| 0.962 | 轻微变化，**点击实际已成功**（坐标正确），但验证偏严格 |
| > 0.98 | 几乎无变化，失败 |
| < 0.92 | 显著跳转，成功 |

0.962 处于不确定区间，说明 SSIM 阈值需要调整或与 VLM 确认结合使用。

## 依赖

- mss（截屏）：`pip install mss`
- pyautogui（备选）：`pip install pyautogui`
- human-rpa（已装在 ~/.hermes/plugins/human-rpa/）
- Ollama Qwen2.5-VL（已有）

## 验证方式

```bash
# 测试截屏
python3 -c "
import mss
import os
with mss.mss() as s:
    s.shot(output='/tmp/hermes_screen.png')
print(os.path.exists('/tmp/hermes_screen.png'))
"

# 测试VLM
curl -X POST http://127.0.0.1:11434/api/generate -d '{
  "model": "qwen2.5vl:7b",
  "prompt": "描述这张图片的内容",
  "images": ["/tmp/hermes_screen.png"]
}' | head -50
```

## API设计

### ask_screen（看图问答）
输入：问题字符串
输出：VLM的回答（文字）

### find_and_click（找元素并点击）
输入：元素描述（"搜索按钮"、"加入进货单"）
输出：{"success": bool, "coords": (x,y), "ssim_after": float, "retry_count": int}

### capture_verify（截图+SSIM验证）
输入：点击前截图路径，预期变化描述
输出：{"changed": bool, "ssim": float}