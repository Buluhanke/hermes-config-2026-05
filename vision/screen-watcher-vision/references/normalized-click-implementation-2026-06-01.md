# Normalized Click 实现文档（2026-06-01）

## Qwen3-VL 坐标约定 — 官方验证

**结论**：Qwen3-VL 使用 **normalized 0-1000 相对坐标**，像素映射公式 `x_px = int(coord_x / 1000 * screen_w)`。

### 验证来源

QwenLM/Qwen3-VL cookbooks/2d_grounding.ipynb 官方 notebook 中的 `plot_points()` 和 `plot_points_json()` 函数：

```python
# plot_points_json — 官方标准用法
x, y = int(point_2d[0] / 1000 * width), int(point_2d[1] / 1000 * height)

# plot_bounding_boxes — bbox 坐标
abs_x1 = int(bounding_box["bbox_2d"][0] / 1000 * width)
abs_y1 = int(bounding_box["bbox_2d"][1] / 1000 * height)
```

notebook 注释也明确说明：
> "Coordinate System: Qwen3-VL's default coordinate system has been changed from the absolute coordinates used in Qwen2.5-VL to **relative coordinates ranging from 0 to 1000**."

### ⚠️ 修订历史

- 早期错误记录（来源 DeepWiki）：除数用 **999**（`round(x/999*w)`） 
- 2026-06-01 官方 notebook 验证：除数用 **1000**（`int(x/1000*w)`）
- 坐标范围：0-999 共 1000 个整数点，但转换公式用 `1000` 做除数

## normalized_click 实现

文件：`~/.hermes/autonomous-ai-agents/hermes-rpa/scripts/hermes_desktop_rpa.py`

### 函数

```python
def get_screen_size():
    """获取当前屏幕分辨率（主显示器）"""
    # system_profiler → JSON 解析 → 正则提取 "1920 x 1080 @ 60.00Hz"
    # 降级：Quartz.CGDisplayBounds (pyobjc-framework-Quartz)
    # 最终降级：1920x1080 默认值

def normalized_click(nx, ny, screen_w=None, screen_h=None):
    """
    从 Qwen3-VL 归一化坐标 (0-1000) 转换为像素坐标并点击。
    转换：x_px = round(nx / 1000 * screen_w), y_px = round(ny / 1000 * screen_h)
    """
    if screen_w is None or screen_h is None:
        size = get_screen_size()  # 自动检测
        screen_w, screen_h = size["width"], size["height"]
    x = round(nx / 1000 * screen_w)
    y = round(ny / 1000 * screen_h)
    return click(x, y)
```

### CLI 用法

```bash
# 归一化坐标 (500,500) → 屏幕中心 (960,540) on 1920×1080
python3 hermes_desktop_rpa.py nclick 500,500

# 返回:
# {"x": 960, "y": 540, "success": true, "error": null}
```

### 屏幕尺寸检测

优先级：
1. `system_profiler SPDisplaysDataType -json` → 解析 `_spdisplays_resolution` 正则
2. `Quartz.CGDisplayBounds` (pyobjc)
3. 默认值 1920×1080

备份文件：`hermes_desktop_rpa.py.bak.20260601_0525`
