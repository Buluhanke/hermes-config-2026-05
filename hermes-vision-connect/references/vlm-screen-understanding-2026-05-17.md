# VLM 屏幕语义理解 — 2026-05-17 实测记录

## 核心成果：看见→看懂→找元素→动手 完整闭环跑通

```
截图(screencapture) → 压缩(sips) → Qwen2.5VL(CPU模式) → 坐标映射 → CUA点击 → 结果验证
```

## Qwen2.5VL CPU 模式（关键突破）

qwen2.5vl:7b 在 M4 24GB 上直接加载会 OOM，必须加 `num_gpu: 0` 强制 CPU 模式：

```python
payload = {
    "model": "qwen2.5vl:7b",
    "prompt": "描述这张图片的内容，用中文回答",
    "images": [img_b64],
    "stream": False,
    "options": {"num_gpu": 0}  # 关键：强制CPU模式避免OOM
}
resp = requests.post('http://localhost:11434/api/generate', json=payload, timeout=180)
```

实测结果：
- 推理时间：15-20秒（CPU模式，慢但能用）
- 识别准确率：高，能准确描述"Mac桌面、终端窗口、右下角Chrome图标"
- 无需 GPU，M4 Mac mini 可用

## 截图压缩 pipeline

全屏截图（1920×1080，约3MB）直接发 Ollama 会 OOM。用 sips 压缩到 800×600：

```bash
screencapture -x /tmp/hermes_screen.png
sips -z 600 800 -s formatOptions 40 /tmp/hermes_screen.png --out /tmp/hermes_screen_small.jpg
```

注意：sips 的 `--out` 参数如果用 `.jpg` 后缀会警告，但实际生成成功。

## 坐标映射（缩图→实际屏幕）

VLM 返回的坐标是相对于缩图的（800×600空间），需要映射回实际屏幕（1920×1080）：

```python
x_screen = int(x_small * 1920 / 800)
y_screen = int(y_small * 1080 / 600)
```

## 完整闭环脚本

已写入：`~/.hermes/scripts/hermes_vision.py`

调用示例：
```bash
python3 ~/.hermes/scripts/hermes_vision.py "桌面上打开了哪些应用？"
python3 ~/.hermes/scripts/hermes_vision.py --goal "打开Chrome浏览器"
python3 ~/.hermes/scripts/hermes_vision.py --find "点击Chrome"
```

## Dock 点击问题与 osascript 兜底

**问题**：CUA overlay 窗口会干扰 Dock 区域点击路由。

**解法**：用 osascript 激活应用，不依赖 Dock 点击：

```python
# 激活 Chrome
subprocess.run(["osascript", "-e", 'tell application "Google Chrome" to activate'])

# 打开新窗口+跳转URL
subprocess.run([
    "osascript", "-e", 'tell application "Google Chrome" to make new window',
    "-e", 'tell application "Google Chrome" to open location "https://www.baidu.com"'
])
```

## 已验证的 VLM 理解能力

| 问题 | VLM 回答 | 用时 |
|------|---------|------|
| 桌面上打开了哪些应用？ | 桌面上打开了一个终端窗口 | 15.9s |
| 左上角和右下角有什么内容？ | 左上角显示天气信息，右下角显示了文件夹和文件图标 | 16.7s |
| 桌面上有哪些可交互元素？ | Chrome图标位于屏幕右下角，靠近桌面底部工具栏中 | 17.7s |
| 打开Chrome浏览器的最佳方式？ | 点击右下角Chrome图标（圆形，彩色C字母） | 19.9s |

## 下一步优化方向

1. 减少推理延迟：当前 15-20s，考虑 qwen2.5vl:3b 或 smolvlm2+ qwen2.5vl 分级
2. 精确坐标获取：VLM 给出区域后，用 AXUI 获取精确边界
3. 端到端打通：hermes_vision.py 输出直接对接到 CUA 点击
