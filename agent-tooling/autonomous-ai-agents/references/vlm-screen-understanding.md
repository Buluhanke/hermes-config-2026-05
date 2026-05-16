# VLM 屏幕理解 — Ollama + smolvlm2-agentic-gui

> 当 accessibility tree 读不到内容（验证码、canvas、复杂UI）时，用本地VLM看截图判断点击位置。

## 模型选择

**推荐：`ahmadwaqar/smolvlm2-agentic-gui`**
- 专门微调用于 GUI 自动化，直接输出点击坐标
- 2GB 下载，推理约 3-4GB 内存，24GB Mac mini 可用
- 其他备选：`qwen2.5vl:3b`（~2GB）、`llava:7b`（~4GB）

```bash
ollama pull ahmadwaqar/smolvlm2-agentic-gui
```

## 核心工作流

```
截图 → /api/generate + images数组 → 模型返回 click(x, y) → 归一化坐标→实际像素→点击
```

## API 格式（关键）

**不要用 `/api/chat`**，Ollama 的 chat 接口不支持 images 数组格式给这个模型。

**正确方式：**

```python
import requests, base64

with open("/tmp/screen.png", "rb") as f:
    img_b64 = base64.b64encode(f.read()).decode()

payload = {
    "model": "ahmadwaqar/smolvlm2-agentic-gui",
    "prompt": "这是网页截图，告诉我应该点击哪个链接进入搜索页面找纸箱供应商？用中文简短回答，只说点击什么元素。 <image>",
    "images": [img_b64],   # <-- 必须用 images 数组
    "stream": False
}

resp = requests.post("http://127.0.0.1:11434/api/generate", json=payload, timeout=60)
print(resp.json()["response"])
```

**输出示例：**
```
选择搜索页面中的纸箱供应商链接。

<code>
click(x=0.519, y=0.238)
</code>
"
```

## 归一化坐标 → 实际像素

模型输出的是归一化坐标 (0-1)，需转换：

```python
# macOS 获取屏幕分辨率
import subprocess
result = subprocess.run(
    ["bash", "-c", 
     "system_profiler SPDisplaysDataType 2>/dev/null | grep -A1 Resolution | tail -1 | awk '{print $3\"x\"$5}'"],
    capture_output=True, text=True
)
# 返回如 "1920 x 1080 @ 60.00Hz" → 提取 1920 和 1080

width, height = 1920, 1080  # 或从上面获取
x_actual = int(x_norm * width)
y_actual = int(y_norm * height)
```

**Retina 屏幕注意：** macOS 缩放因子 ×2，但 `screencapture` 默认截logical像素，不需要额外乘因子。

## 截图方式

```python
# 方式1：screencapture（推荐，最简单）
subprocess.run(["screencapture", "/tmp/screen.png"])

# 方式2：Chrome截图通过CDP
# browser_navigate 已经正常，但 browser_screenshot MCP连不上时用 screencapture 兜底
```

## 集成到 Perception Bridge 的路径

当前 `HermesPerceptionBridge.perceive()` 优先用 accessibility tree + Baidu OCR。增加 VLM fallback：

```python
def perceive_with_vlm_fallback(self, force_vlm: bool = False) -> list[UIObject]:
    # 1. 先试 AX tree + OCR
    objects = self.perceive(force_ocr=False)
    if not force_vlm and objects:
        return objects
    
    # 2. VLM fallback
    screenshot_path = "/tmp/perception_vlm.png"
    subprocess.run(["screencapture", screenshot_path])
    
    # 调用 smolvlm2-agentic-gui
    response = call_smolvlm(screenshot_path, prompt)
    coords = parse_click_coords(response)  # 解析 click(x, y)
    
    # 3. 转换为 UIObject + 合并到 WorldState
    if coords:
        ui = UIObject(
            id=f"vlm_click_{coords['x']}_{coords['y']}",
            type="vlm_target",
            text=f"点击({coords['x']:.3f}, {coords['y']:.3f})",
            bbox=[int(coords['x']*width), int(coords['y']*height), 10, 10],
            clickable=True,
            source="vlm"
        )
        objects.append(ui)
    return objects
```

## 已知限制

- MiniMax 不支持 `image_url` 格式（报错 `unknown variant 'image_url'`），所以本地VLM是正确路径
- 模型返回的坐标偶尔会有偏差，验证步骤必要
- OCR+AX tree 优先，VLM 作为"什么都读不到"时的兜底，不要每次都调VLM（慢且费内存）
