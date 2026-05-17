# Smart Click 三层感知系统 — 关键技术发现

## smolvlm2 输出格式（最重要）

smolvlm2 **几乎不输出纯JSON**，常见格式只有两种：

```
格式1: <code>包裹（最可靠）
click(x=0.495, y=0.378)

格式2: 裸坐标（最常见）
0.495, 0.378
x=0.495 y=0.378
click at 0.495, 0.378
```

**解析策略**：用正则取最后两个小数（避免被其他数字干扰）：
```python
coords = re.findall(r'0\.\d+', response)
x, y = float(coords[-2]), float(coords[-1])
```

## CUA 后台截图（重大突破）

```python
# 方法1: mcp_cua_screenshot（推荐，不抢焦点）
mcp_cua_screenshot(window_id=N)

# 方法2: screencapture命令
screencapture -l <window_id> -d /tmp/out.png
```

注意: `screencapture -x` 会抢焦点，`-l -d` 组合不抢。

## 图片大小限制

- 全分辨率(1920x1080, 4MB) → Ollama 超时
- 缩放到800px宽(~700KB) → 响应7-15s
- 缩放算法: PIL LANCZOS, `Image.thumbnail((800, 9999))`

## R-VLM 两阶段 Zoom-In

来自论文: "Refining Visual Grounding with Semantic Focus" (KAIST + AWS AI Labs)

阶段1: smolvlm2全图预测归一化坐标
阶段2: 放大该区域，再次预测
精度提升: 13%

## 坐标系统

统一用归一化(0-1)：Smol2Operator验证此策略最优，避免分辨率绑定
像素转换: pixel_x = x * screen_width, pixel_y = y * screen_height
当前屏幕: 1920x1080

## 响应时间

- L1 Apple Vision OCR: 0.5-0.6s
- L2 smolvlm2 (800px): 7-15s
- L3 SSIM验证: 5ms
- 总计 smart_click: 8-20s

## CUA get_window_state 超时问题

调用 mcp_cua_get_window_state 超时120s
原因: AX-tree遍历大窗口（如Chrome）耗时过长
解决方案: 用smolvlm2 VLM代替AX-tree获取元素位置

## 文件位置

- 核心代码: /tmp/smart_click.py (~380行)
- 技能部署: /Users/aimac/.hermes/skills/hermes-vision-connect/smart_click.py
- 截图缓存: /Users/aimac/.hermes/image_cache/img_*.png
