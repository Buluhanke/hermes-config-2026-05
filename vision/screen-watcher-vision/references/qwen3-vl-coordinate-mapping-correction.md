# Qwen3-VL 坐标映射修正

**发现日期**：2026-06-01（凌晨巡检方向D）
**来源**：QwenLM/Qwen3-VL DeepWiki → cookbooks/mobile_agent.ipynb 第50行
**访问方式**：browser_navigate https://deepwiki.com/QwenLM/Qwen3-VL/5.2-spatial-understanding-and-2d-grounding

## 旧记录（错误）

之前 idle_learning 和 screen-watcher-vision 技能记录为：
```
Qwen3-VL 坐标约定：[x, y] on 1000×1000 相对坐标 canvas
像素映射：x_px = x/1000 × W, y_px = y/1000 × H
```

## 实际（正确）

**Qwen3-VL 使用 normalized 0-999 scale**（非 0-1000）。

公式来源（mobile_agent.ipynb 第48-50行，从 DeepWiki 的 Rescaling Implementation 章节提取）：
```python
def rescale_coordinates(point, width, height):
    point = [round(point[0]/999*width), round(point[1]/999*height)]
    return point
```

### 关键细节

- **除数用 999 不是 1000**：坐标范围 0-999 共 1000 个整数点，0-based indexing 导致最大索引为 999
- **Bounding box 格式**：`bbox_2d: [x1, y1, x2, y2]`，点击点取中心 `(x1+x2)/2, (y1+y2)/2`
- **Mobile Agent 动作**：click, type, scroll, swipe — 全部坐标均为 0-999 归一化值
- **输出格式**：`<tool_call>{"name": "mobile_use", "arguments": {"action": "click", "coordinate": [x, y]}}</tool_call>`

## 对 handler 的影响

auto_execute 坐标映射链需实现：
```python
def qwen_coord_to_pixel(point_norm, screen_width, screen_height):
    """Qwen3-VL 归一化坐标 → 屏幕像素坐标"""
    x_px = round(point_norm[0] / 999 * screen_width)
    y_px = round(point_norm[1] / 999 * screen_height)
    return (x_px, y_px)
```

## ⚠️ 待验证

- 上述公式来自 QwenLM/Qwen3-VL 的 Transformers 版（HuggingFace 推理路径）
- **Ollama 版 qwen3-vl:2b 是否沿用同一坐标约定待实测验证**
- Ollama 的 GGUF 量化可能有独立的后处理逻辑
- 验证方法：给 qwen3-vl:2b 传入屏幕截图 + "Click on the browser address bar" prompt，检查返回坐标是否在 0-999 范围内
