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
1. 优先本地Ollama + smolvlm2-agentic-gui（零Token，2GB，M4 24GB实测可用）
2. 兜底硅基流动 + Qwen2.5-VL（国内直连，有免费额度）
3. 兜底 Cloudflare Workers AI（10k神经元/天免费）
4. 最后才考虑 OpenRouter（需API Key，不是真免费）

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

### smolvlm2 响应格式（实测）

smolvlm2 返回的内容包含 `<code>` 标签包裹的 action 指令，例如：

```
The image shows a web page with various links...
<code>
scroll(direction='up', amount=10)
</code>
```

找坐标时，VLM 可能说"未找到"但同时返回 action 指令（如 scroll）。需要：
1. 优先解析坐标格式 `(x, y)` / `坐标(x, y)`
2. 如果没有坐标但有 action 指令，先执行 action 再重试找坐标
3. 不要把 `<code>` 里的内容当作最终回答

**完整解析优先级**：
1. 找 `(数字, 数字)` 格式 → 返回坐标
2. 次找 `坐标：数字,数字` / `x=数字 y=数字`
3. 只有 `<code>` 标签 → 元素不在当前屏，先执行 action 再重试
4. "未找到" 不一定是失败，可能是元素真不在当前屏幕

### SSIM 阈值实测校准

| SSIM | 实际状态 |
|------|---------|
| 0.962 | 轻微变化，**点击实际已成功**（坐标正确），但验证偏严格 |
| > 0.98 | 几乎无变化，失败 |
| < 0.92 | 显著跳转，成功 |

0.962 处于不确定区间，说明 SSIM 阈值需要调整或与 VLM 确认结合使用。建议：
- 阈值放宽到 < 0.96 即认为成功（对人类操作的容忍度）
- 或者用 VLM 再确认一次（"页面上是否出现了 X？"）

### smolvlm2 vs qwen2.5vl 选择策略

| 模型 | 内存 | 速度 | 准确度 | 推荐度 |
|------|------|------|--------|--------|
| **qwen2.5vl:7b** | ~6GB | 加载后1-2s | **高** | ⭐⭐⭐⭐⭐ 主力 |
| smolvlm2-agentic-gui | ~2GB | 2-5s | 中（1.8B太小） | ⭐⭐ 仅备用 |

Ollama 命令（注意后缀）：
```bash
ollama run qwen2.5vl:7b                    # 正确，要加 :7b
ollama run ahmadwaqar/smolvlm2-agentic-gui  # GUI专用微调版
```

**注意**：qwen2.5vl 模型名在 Ollama 里必须带 `:7b` 后缀，否则报 "model not found"。

### CogAgent-9B 评估（2026-05-16）

智谱 CogAgent-9B 是全球最强的开源屏幕理解 Agent，但 BF16 需要 ≥29GB 显存，Mac M4 24GB 跑不了。

**当前真人化最佳路径**：qwen2.5vl:7b + Hermes CDP 控制，不需要 CogAgent。

### smolvlm2 响应格式（实测）

官方安装脚本在 M4 上超时，需要手动下载：

```bash
# 1. 下载（手动curl，不走脚本）
cd /tmp/cua-install
curl -L -o cua-driver.tar.gz "https://github.com/trycua/cua/releases/download/cua-driver-v0.1.9/cua-driver-0.1.9-darwin-arm64.tar.gz"

# 2. 解压
tar -xzf cua-driver.tar.gz

# 3. 修复启动脚本（tar解压出来的wrapper路径不对）
cat > /usr/local/bin/cua-driver << 'EOF'
#!/bin/sh
exec "/Applications/CuaDriver.app/Contents/MacOS/cua-driver" "$@"
EOF
chmod +x /usr/local/bin/cua-driver

# 4. 移动到 Applications
cp -r CuaDriver.app /Applications/

# 5. 启动 MCP 模式
cua-driver mcp &
```

### human-rpa 插件（已安装）

位置：`~/.hermes/plugins/human-rpa/__init__.py`

提供的函数（可直接导入使用）：
- `human_mouse_move(x, y, roughness)` — 贝塞尔曲线移动
- `human_click(x, y, hold_ms, jitter_px)` — 移动→悬停→抖动→点击
- `human_drag(start_x, start_y, end_x, end_y, 回退校准)` — 滑动条专用
- `human_type(text, base_delay)` — 异步打字（80-300ms随机间隔）
- `human_scroll(pixels, steps)` — 分段滚轮

依赖 `cliclick`（已安装：`brew install cliclick`）

## L3 免费视觉API备选

OpenRouter 的 Gemini Flash 不是真免费（需要API Key）。以下是真免费选项：

### 硅基流动 SiliconFlow（推荐，国内直连）

- 注册：siliconflow.cn
- 模型：Qwen/Qwen2.5-VL-7B-Instruct（视觉，支持看图问答）
- 地址：`https://api.siliconflow.cn/v1/chat/completions`
- API格式：OpenAI兼容，零配置切换
- 配置示例：
  ```yaml
  auxiliary:
    vision:
      provider: siliconflow
      model: Qwen/Qwen2.5-VL-7B-Instruct
      base_url: https://api.siliconflow.cn/v1
      api_key: YOUR_SILICONFLOW_KEY
  ```

### Cloudflare Workers AI（10k神经元/天免费）

- 模型：`@cf/qwen/qwen2.5-vl-7b-instruct`
- 地址：`https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/ai/run/@cf/qwen/qwen2.5-vl-7b-instruct`
- 需要 Cloudflare 账号（免费注册）

### 最终优先级（2026-05-16实测）

| 优先级 | 模型 | 类型 | Token费用 | 备注 |
|--------|------|------|---------|------|
| 1 | smolvlm2-agentic-gui | 本地Ollama | 0 | ✅ M4 24GB实测可用 |
| 2 | Qwen2.5-VL | 硅基流动 | 免费 | ✅ 国内直连，推荐 |
| 3 | qwen2.5-vl-7b | Cloudflare | 免费10k/天 | 需CF账号 |
| 4 | Gemini Flash | OpenRouter | $0.001/M | ❌ 需API Key |

## 依赖

- mss（截屏）：`pip install mss`
- pyautogui（备选）：`pip install pyautogui`
- human-rpa（已装在 ~/.hermes/plugins/human-rpa/）
- Ollama 本地模型（已有 smolvlm2 运行）

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