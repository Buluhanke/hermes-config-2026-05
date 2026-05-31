# GUI 坐标校准研究（2026-06-01 方向D发现）

## 为什么要做坐标校准？

当前 `auto_execute` 处于 DRY_RUN=True 安全模式。切换为 False 前需要：
1. 理解 qwen3-vl:2b 的坐标输出格式
2. 理解坐标系与像素坐标的映射关系
3. 验证点击精度

## 核心论文

### POINTS-GUI-G-8B（arXiv 2602.06391, Feb 2026）
- **ScreenSpot-v2 95.7%** — 当前 SOTA
- 三个成功因素：统一数据集 + 视觉编码器微调 + RL with Verifiable Rewards
- RL 适合 GUI grounding：奖励可验证、精度高
- Repo/模型信息待追踪（百度/腾讯团队）

### RULER tokens + I-MRoPE（arXiv 2510.03230, Oct 2025, ServiceNow/Mila）
- 显式位置标记（RULER tokens）替代隐式坐标生成
  - 类似网格参考点，模型只需"调整"而非"生成"坐标
- I-MRoPE：解决宽度和高度维度不对称
- 最大改进在高分辨率界面（与 Mac 大屏场景吻合）

### DRS-GUI（CVPR 2026）
- Dynamic Region Search：免训练的 GUI grounding
- 对任意模型（含 qwen3-vl:2b）可提升 ScreenSpot-Pro 14%
- 思路：搜索→定位→确认 而非 一步到位

### Qwen3-VL 坐标约定（GitHub Issue #1560）
- **关键事实**：Qwen3-VL 输出 [x, y] 在 **1000×1000 相对坐标 canvas** 上
- 不是像素绝对坐标！不是百分比！是 0-1000 范围的相对值
- 像素映射公式：
  ```python
  x_px = x / 1000 * screen_width
  y_px = y / 1000 * screen_height
  ```
- 例：Qwen3-VL 输出 [450, 320] → 屏幕 2560×1600 → 像素 (1152, 512)

## 对 DRY_RUN=False 切换的意义

1. **当前缺陷**：hermes_desktop_rpa.py 的 `click(x, y)` 接受**像素坐标**
2. **需要修复**：auto_execute 中需添加 1000→像素 的映射层
3. **精度验证**：映射后误差 ≤5px 即合格

## next step 建议

1. 编写 `/tmp/test_coordinate_mapping.py`：用 qwen3-vl:2b 识别已知UI元素，对比输出坐标与期望坐标
2. 验证 1000→像素 映射精度
3. 如精度达标，在 auto_execute 中集成映射层
4. 最后切换 DRY_RUN=False
