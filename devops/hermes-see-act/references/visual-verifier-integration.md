# Element Spotting 视觉副驾 — 集成细节

> 来源: 2026-06-29 `visual_verifier.py` + `hermes_native_eyes.py` 集成 session
> 落点: `~/.hermes/scripts/visual_verifier.py` + `~/.hermes/scripts/hermes_native_eyes.py::visual_verify_hook`

## 为什么需要这一层 (而不是直接用 VLM)

cua-driver AX 树是 "稳" 的基石, 但有盲区:
- **canvas / WebGL / 视频游戏**: 没有 a11y label, AX 拿不到
- **自定义绘制控件**: 第三方框架 (UE / Unity / Electron 自绘) 可能不暴露 AX role
- **真要确认操作生效**: AX 拿到 "提交" 按钮并 click, 但**没说点完后是否真的进了下一页** (网络慢 / JS 报错 / 后端 500)

Element Spotting 在**关键操作节点** (提交/确认/状态切换) 给 AX 加一层 "视觉双保险":
- 本地像素 diff → 页面变了没
- PIL 颜色 spot → 找 canvas 控件 (定位 + 命中)
- macOS Vision OCR → 看屏幕上的字 (出现/消失)

**完全本地, 零网络零 LLM 调用**, 延迟 < 500ms。

## 5 个核心 API (`visual_verifier.py`)

```python
from visual_verifier import (
    frame_fingerprint,        # 64x64 灰度 md5 前 12 位, 缓存去重
    diff_frames,              # 两帧像素差异度 0.0~1.0, >0.005 视为有变化
    spot_by_color,            # 找截图里指定 RGB 颜色块的 bbox
    spot_by_text_heuristic,   # macOS Vision OCR 找关键词
    verify_after_click,       # 点击前后对比 + 期望校验 (text/color/diff_min)
    verify_state,             # 综合状态校验 (text/color/no_text 多维 score)
)
```

### 调用代价 (实测)
- `frame_fingerprint`: ~50ms
- `diff_frames`: ~100ms (128x128 灰度对比)
- `spot_by_color`: ~20ms
- `spot_by_text_heuristic`: ~400ms (Swift 子进程调 Vision)
- `verify_after_click` 完整链路: ~400ms
- `verify_state` 3 项校验: ~450ms

### 决策表 (什么时候用什么)

| 场景 | API | 期望 |
|---|---|---|
| AX 读到按钮, 想确认点完后页面变了 | `diff_frames(before, after)` | diff > 0.005 |
| 想确认 "Success" / "已提交" 出现在屏幕上 | `spot_by_text_heuristic(after, ["Success"])` | found=True |
| 想确认红框 / 警告标志出现了 | `spot_by_color(after, (255,0,0), tolerance=25)` | area_pct > 0.001 |
| 想确认 "Error" / "Failed" 没出现 | `verify_state` + `type=no_text` | passed=True |
| canvas 按钮 (AX 读不到) 定位 | `spot_by_color(canvas_img, button_color)` | bbox 中心点 → click(cx, cy) |
| 关键节点一键校验 (出现 + 没出现 + 颜色) | `verify_state(image, [check1, check2, ...])` | score=1.0 |

## 与 mac_vision_fallback 的分工 (避免每次都炸 LLM)

```
关键操作节点 (AX 点击/输入/提交后)
    │
    ├─→ local verifier 路径 (visual_verifier)
    │   ├─ 像素 diff (页面变没变)
    │   ├─ 颜色 spot (canvas 控件)
    │   ├─ Vision OCR (本地, Swift 子进程)
    │   └─ 综合 state 校验
    │   ✅ 优先, 零网络, 400ms 内
    │
    └─→ VLM 兜底路径 (mac_vision_fallback) — 只在 verifier 不够时
        ├─ 一级: vision_with_cache → Gemini (走 agent 主链, 有缓存)
        ├─ 二级: _nv_vision_direct → NVIDIA Nemotron-VL 12B
        └─ 语义理解 / 罕见图标 / OCR 也不认识时
        ⚠ 慢 (2-9s) + 贵 + 偶尔幻觉, 只在 verifier 真不行时才用
```

**铁律**:
- 任何 0 网络能搞定的视觉验证 → 走 visual_verifier, **不调 VLM**
- 视觉副驾是 "关键节点" 工具, 不是 "每步都跑" 的监控 (后者走 screen_watch_daemon)
- VLM 调用前先 grep `~/.hermes/scripts/visual_verifier.py`, 看是否已经覆盖

## 已知坑

1. **OCR 需要 Vision TCC 授权** (首次跑会弹 macOS 权限框)
2. **OCR 0 结果 ≠ bug**: 屏幕纯图片 / 视频 / 加密界面合法返回 0
3. **color spot tolerance < 10 miss 率高**: 抗锯齿 + macOS 色彩管理让小 tolerance 找不到
4. **diff 别对比 macOS 状态栏**: 时钟一直在变, diff 虚高 (>5%)
5. **Swift 子进程超时 15s**: 大图 / 高分辨率可能超时, 考虑先 thumbnail

## hermes_native_eyes 集成点

`build_frame()` 现在支持 `screenshot_path` / `prev_screenshot_path` / `visual_expected` 参数, 传截图自动挂 `visual_verify` 字段:

```python
from hermes_native_eyes import build_frame

frame = build_frame(
    front_app="Safari", window_title="Checkout",
    ax_walk_result=elements,           # cua-driver get_window_state → elements[]
    ocr_result=ocr,                    # 可选, Vision OCR 结果
    prev_ax=prev_elements,             # 可选, 用于 frame_diff
    screenshot_path="/tmp/after.png",  # ← 关键
    prev_screenshot_path="/tmp/before.png",
    visual_expected={"text": ["Success", "已提交"]},
)
# frame["visual_verify"]["expected_met"] → True/False
# frame["visual_verify"]["details"]["ocr"]["hits"] → 命中坐标
```

返回字段 (视觉副驾启用时):
```json
{
  "visual_verify": {
    "enabled": true,
    "mode": "diff",           // "diff" | "state" | "fingerprint_only"
    "before_fp": "abc123",
    "after_fp": "def456",
    "page_changed": true,
    "expected_met": true,
    "details": {
      "diff": 0.042,
      "ocr": {"found": true, "hits": [...], "matched": [...]}
    },
    "latency_ms": 400
  }
}
```

## 未来扩展 (不写代码占位)

- **区域级 verifier**: 只截 ROI 区域做 diff/OCR, 避免全图对比的噪声 (状态栏/壁纸变化)
- **shape spot**: 找特定形状 (圆形进度条 / 三角形警告) — 需要 OpenCV, 暂不引入
- **跨帧追踪**: 不是 2 帧 diff, 而是 N 帧序列判定 "动画进行中" / "加载完成"
- **置信度校准**: OCR conf 0.5 和 conf 0.95 应该区别对待, 当前一视同仁

> 这些都是"将来"事项, 现在的 verifier 已经覆盖 95% 用例, 别过早优化。