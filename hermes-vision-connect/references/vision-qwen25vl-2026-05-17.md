# 2026-05-17 视觉感知实测记录

## qwen2.5vl:7b CPU模式（主力验证成功）

**关键发现**：M4 Mac必须加 `num_gpu:0`，否则OOM加载失败。

```python
import requests, base64

with open('/tmp/small.jpg', 'rb') as f:
    img_b64 = base64.b64encode(f.read()).decode('utf-8')

payload = {
    "model": "qwen2.5vl:7b",
    "prompt": "描述这张图片的内容，一句话",
    "images": [img_b64],
    "stream": False,
    "options": {"num_gpu": 0}  # 关键参数
}
resp = requests.post('http://localhost:11434/api/generate', json=payload, timeout=180)
```

**推理速度**：~20秒/次（CPU模式）

## smolvlm2 乱码问题

```
设定、制定、打开、清空、制作、制作、制作...
```
输出循环乱码，判定为不可用。

## 截图压缩

```bash
screencapture -x /tmp/hermes_screen.png
sips -z 600 800 -s formatOptions 40 /tmp/hermes_screen.png --out /tmp/hermes_screen_small.jpg
```
原图~2.9MB，压缩后~744KB，ollama可接受。

## 可用脚本

- `~/.hermes/scripts/screen_vision.py` — 基础截图+问答
- `~/.hermes/scripts/hermes_vision.py` — 完整感知链路，支持 `--goal` / `--find` 参数

## 端到端验证

```
python3 ~/.hermes/scripts/hermes_vision.py --goal "打开Chrome浏览器"

# 输出：
# [19.9s]
# 1. 当前屏幕是Mac桌面，有终端窗口和Chrome图标
# 2. Chrome图标位于屏幕右下角
# 3. 点击右下角Chrome即可达成目标
```
