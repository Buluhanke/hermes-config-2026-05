# Perception Kernel — 扩展模块（2026-05-14）

## 新增模块总览

```
perception/
├── transform/coordinate.py    # 坐标系转换（Mac Retina 生死线）
├── diff/world_diff.py          # 世界状态对比
├── resolution/entity_resolution.py  # 实体消歧
└── drivers/mouse_driver.py    # 鼠标驱动抽象
```

---

## 1. Coordinate Transform（坐标系转换）

**问题**：Mac Retina 屏幕的 viewport 坐标和 screen 坐标不一致，比例因子 `devicePixelRatio=2`。

- viewport: `(0, 0, 1280, 720)` — 浏览器内部
- screen: `(0, 0, 2560, 1440)` — 实际像素

AX Tree 给出的是 viewport 坐标，直接用 `pyautogui.click(x, y)` 会点偏。

**API**:

```python
from perception.transform import CoordinateTransformer, get_transformer

t = CoordinateTransformer().detect()
screen_x, screen_y = t.to_screen(viewport_x, viewport_y)
screen_bbox = t.to_screen_bbox([x1, y1, x2, y2])
cx, cy = t.screen_center(bbox)
```

**数据来源**：
- Chrome CDP `Browser.getWindowBounds` → 窗口位置/尺寸
- CDP JS `window.devicePixelRatio` → 缩放比例

---

## 2. World Diff（世界状态对比）

**目的**：让 Agent 理解"操作后世界发生了什么"。

```python
from perception.diff import compute_world_diff, verify_by_diff

diff = compute_world_diff(old_state, new_state)
# diff.new_elements     — 新出现的元素
# diff.removed_elements — 消失的元素
# diff.changed_elements — 位置/属性变化的元素

# 验证操作是否达成目标
result = verify_by_diff(old_state, new_state,
    expected_new=["商品列表"],
    expected_removed=["搜索框"])
```

**核心算法**：用 `type|text[:20]` 作为元素签名，匹配跨状态的同一元素，而非依赖不稳定 id。

---

## 3. Entity Resolution（实体消歧）

**问题**：AX、OCR、YOLO 三个感知源可能检测到同一个按钮，产生重复 UIObject。

**融合条件**（第一版规则，不上 AI）：
- `bbox IoU > 0.7` **且** `text_similarity > 0.8` → 同一实体

```python
from perception.resolution import text_similarity, bbox_iou, EntityResolver

sim = text_similarity("登录", "登录按钮")  # 0.85
iou = bbox_iou([0,0,100,100], [50,50,150,150])  # 0.33

resolver = EntityResolver(iou_threshold=0.7, text_sim_threshold=0.8)
unique_objs = resolver.resolve(candidates)
```

**优先级**：`ax > dom > yolo > ocr > vision`

---

## 4. Mouse Driver（鼠标驱动抽象）

**目的**：未来支持多平台（Browser CDP / macOS AX / Android adb / VNC），不绑定 pyautogui。

```python
from perception.drivers import get_mouse_driver

driver = get_mouse_driver("pyautogui")  # 当前
driver = get_mouse_driver("cdp")         # 未来扩展
driver.click(x, y)
driver.move_to(x, y, duration=0.2)
driver.double_click(x, y)
driver.scroll(x, y, 0, -3)
```

**已实现**：
- `PyAutoGUIDriver` — screen 坐标系，带 FAILSAFE
- `CDPDriver` — Chrome DevTools Protocol `Input.dispatchMouseEvent`

---

## 下一步：Reality Test 优先级

1. **先接 `normalize_ax()`** — AX 是主骨架，最稳定
2. **验证坐标转换** — 用真实页面确认 screen 坐标点击命中
3. **跑通 click → verify 闭环** — 第一个端到端测试
4. **测试页面**：Google 登录页 / GitHub 登录页（AX 完整 + UI 规范）
