# Qwen3-VL 坐标约定：/1000 官方确认

**日期**：2026-06-01
**来源**：QwenLM/Qwen3-VL cookbooks/2d_grounding.ipynb（官方 notebook）

## 核心结论

Qwen3-VL 坐标转换公式使用 **除数 1000**，不是 999。

## 验证过程

1. `browser_navigate` 访问 QwenLM/Qwen3-VL cookbooks/ 目录
2. 确认 `2d_grounding.ipynb` notebook 存在
3. browser_console 提取完整 notebook JSON（含代码 cell）
4. 找到 `plot_points_json()` 函数：`int(point_2d[0] / 1000 * width)`
5. 找到 notebook 注释："relative coordinates ranging from 0 to 1000"

## 修订原因

早期 idle_learning 记录引用 DeepWiki（社区 wiki 可能过期或不准确），而非 Qwen 官方仓库。官方 notebook 是第一手来源。

## 坐标示例

| Qwen3-VL 归一化 | 像素 (1920×1080) |
|----------------|------------------|
| (500, 500)     | (960, 540)       |
| (100, 900)     | (192, 972)       |
| (0, 0)         | (0, 0)           |
| (999, 999)     | (1918, 1079)     |
