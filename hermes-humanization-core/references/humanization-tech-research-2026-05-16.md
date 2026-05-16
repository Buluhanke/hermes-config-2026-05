# 真人化技术调研：2026-05-16 全球最新方案

> 来源：Web研究（browser-use、human_mouse、DMTG、SenseVoice、Qwen3-VL等）

## 屏幕感知：最新方案对比

| 方案 | 类型 | 费用 | 本地 | 推荐度 |
|------|------|------|------|--------|
| browser-use + qwen-vl | 本地Ollama | 免费 | ✅ | ⭐⭐⭐⭐ |
| Qwen3-VL（最新） | 云端API | 按量 | ❌ | ⭐⭐⭐⭐ |
| OmniParser | 本地 | 免费 | ✅ | ⭐⭐⭐ |
| Claude Computer Use | 云端 | 付费贵 | ❌ | ⭐⭐ |

**结论**：browser-use + qwen2.5-vl（Ollama本地）是零成本方案。Qwen3-VL支持像素级定位（bounding box/points）。

## 鼠标轨迹真人化：最新开源库

| 库 | 技术 | 开源 | 推荐度 |
|------|------|------|--------|
| **sarperavci/human_mouse** | Bezier曲线+样条插值 | ✅ | ⭐⭐⭐⭐⭐ |
| DMTG | 扩散模型轨迹生成 | ✅ | ⭐⭐⭐⭐ |
| Ghost Cursor (Puppeteer) | 过冲+自矫正 | ✅ | ⭐⭐⭐⭐ |

**human_mouse 安装**：
```bash
pip install human-mouse
```

**核心用法**：
```python
import human_mouse
human_mouse.move_and_click(x, y)  # 自动走贝塞尔曲线
```

**结论**：human_mouse 是目前最接近真人轨迹的开源方案，优于当前 Hermes 内置的贝塞尔实现。

## 行为节奏真人化：量化方案

真人操作的核心特征：
- 鼠标移动：加速-减速曲线（非匀速）
- 点击延迟：200-800ms 随机
- 打字节奏：非线性（不等概率修正）
- 滚动：分批而非一键到底

**action_rhythm.py 建议实现**：
```python
import random, time

def random_delay(min_ms=200, max_ms=800):
    time.sleep(random.uniform(min_ms/1000, max_ms/1000))

def human_scroll_action():
    for _ in range(random.randint(2, 3)):
        pyautogui.scroll(-3)
        random_delay(100, 300)
```

## ASR语音输入：零成本方案

| 方案 | 类型 | 费用 | 本地 | 中文 |
|------|------|------|------|------|
| **SenseVoice** | 阿里开源 | 免费 | ✅ | ✅⭐ |
| Whisper (OpenAI) | 本地模型 | 免费 | ✅ | ✅ |
| MiniMax ASR | 云端API | 按量 | ❌ | ✅ |

**SenseVoice 优势**：阿里开源，支持中文，免费本地，性能对标Whisper large-v3。

**部署命令**：
```bash
# 推荐用 faster-whisper（已安装）
# SenseVoice 需要额外模型下载，国内镜像：
HF_ENDPOINT=https://hf-mirror.com python -c "from faster_whisper import WhisperModel; ..."
```

## 验证码体系：本地 vs API

| 场景 | 推荐方案 | 成本 |
|------|---------|------|
| 简单滑块 | human_mouse轨迹 + Baidu OCR | 免费 |
| 复杂拼图 | 超级鹰API | ¥0.001/次 |
| 点选验证码 | 超级鹰API | ¥0.001/次 |
| 简单图形 | OmniParser本地 | 免费 |

**本地方案（滑块）**：
```python
from humanization_core import capture_screen, ask_vlm
import pyautogui, re

img_path = capture_screen()
vlm_response = ask_vlm(img_path, "找到滑块缺口的x坐标，回复纯数字")
x = int(re.search(r'\d+', vlm_response).group())
human_mouse.move_and_click(start_x, start_y)
```

## 当前最大卡点（2026-05-16更新）

| 卡点 | 严重度 | 根因 |
|------|--------|------|
| 屏幕全域感知 | 🔴致命 | 每次一帧，无法连续视觉流 |
| 验证码对抗 | 🔴致命 | 1688登录是第一道门槛 |
| ASR语音输入 | 🟡重要 | 只有TTS没有语音输入 |
| 移动端盲区 | 🔴致命 | 100%无法操作手机 |
| 行为节奏 | 🟡重要 | 瞬时操作=机器人特征明显 |

## 落地优先级

1. **立即**：集成 human_mouse（Bezier轨迹）→ 突破鼠标指纹检测
2. **立即**：部署 SenseVoice ASR → 补全语音闭环
3. **1周内**：browser-use + qwen2.5vl → 屏幕感知升级
4. **持续**：action_rhythm.py → 行为节奏拟真
