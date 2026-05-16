# Perception Kernel — Architecture Reference

> Hermes 本地感知内核：浏览器快照 → 标准化 → 世界状态 → 查询 → 动作 → 验证 → 策略学习

## 模块结构

```
perception/
├── bridge.py                      # 浏览器快照 → 感知 → 动作 → 验证（主入口）
├── schema/ui_object.py            # NormalizedUIObject / UIObject 数据模型
├── normalizers/
│   ├── ax.py                     # Chrome AX Tree → NormalizedUIObject
│   ├── ocr.py                    # Baidu OCR → NormalizedUIObject
│   └── yolo.py                   # YOLO → NormalizedUIObject
├── fusion/merger.py               # IoU 融合（多源去重）
├── resolution/entity_resolution.py  # text_similarity / bbox_iou 消重
├── world/state.py                 # WorldState 世界状态管理
├── query/engine.py               # find_by_text / find_clickable / find_inputs
├── actions/click.py              # click(text) 原语
├── verification/verifier.py      # URL 变化 / 元素消失 / hash 验证
├── diff/world_diff.py            # WorldDiff 结构变化检测
├── transform/coordinate.py        # viewport ↔ screen ↔ retina 坐标转换
├── drivers/mouse_driver.py       # PyAutoGUI / CDP 双驱动抽象
├── runtime/loop.py              # observe → act → verify → update 闭环
└── explorer/
    ├── site_explorer.py         # 全站探索循环（UCB1 策略）
    ├── sitemap/site_map.py        # 页面地图
    └── strategy/action_strategy.py  # UCB1 动作策略
```

## 核心接口（真实方法签名）

### WorldState（perception/world/state.py）
```python
class WorldState:
    ui_objects: list[UIObject]
    url: str
    page_title: str
    screenshot_hash: str
    timestamp: float

    def update(self, objects: list[UIObject]) -> None
    def snapshot(self) -> list[UIObject]  # 返回 ui_objects 副本
    def get_page_hash(self) -> str
    @classmethod
    def from_dict(cls, data: dict) -> WorldState
    def to_dict(self) -> dict
```

### QueryEngine（perception/query/engine.py）
```python
class QueryEngine:
    def __init__(self, objects: list[UIObject])
    def find_by_text(self, text: str, types: list[str] | None = None) -> list[UIObject]
    def find_by_type(self, *types: str) -> list[UIObject]
    def find_clickable(self, text: str | None = None) -> list[UIObject]
    def find_inputs(self) -> list[UIObject]
    def find_nearest(self, x: int, y: int, types: list[str] | None = None, max_count: int = 5) -> list[tuple[UIObject, float]]
    def query(self, text: str | None = None, types: list[str] | None = None,
              clickable: bool | None = None, enabled: bool | None = None,
              visible: bool | None = None) -> list[UIObject]
```

### Verifier（perception/verification/verifier.py）
```python
class Verifier:
    def __init__(self, bridge: HermesPerceptionBridge)
    def verify(self, action: str, target: UIObject | str) -> ActionResult
    @staticmethod
    def url_change(old_url: str, new_url: str) -> ActionResult
    @staticmethod
    def url_no_change(old_url: str, new_url: str) -> ActionResult
    @staticmethod
    def element_gone(target: UIObject, world_state: WorldState) -> ActionResult
    @staticmethod
    def page_clicked(action: ActionResult, new_state: WorldState) -> ActionResult
    def verify_multiple(self, *checks: Callable[[], ActionResult]) -> ActionResult
```

### HermesPerceptionBridge（perception/bridge.py）
```python
class HermesPerceptionBridge:
    def __init__(self, cdp_url: str = "http://127.0.0.1:9333", use_ocr: bool = True, use_transform: bool = True)
    def browser_snapshot(self) -> dict | None  # {ax_tree, url, title, viewport, content_hash, timestamp}
    def browser_navigate(self, url: str) -> bool
    def perceive(self, force_ocr: bool = False) -> list[UIObject]  # 快照 → normalize → merge → WorldState
    def find(self, text: str) -> list[UIObject]
    def find_clickable(self, text: str | None = None) -> list[UIObject]
    def click(self, target: str | UIObject, verify: bool = True) -> bool
    def type_text(self, target: str | UIObject, text: str, enter: bool = False) -> bool
    def run_once(self, target_text: str, action: str = "click") -> bool
    def interactive(self, max_count: int = 20)
    world_state: WorldState  # 当前世界状态（可直接访问）
    query_engine: QueryEngine
```

### UIObject（perception/schema/ui_object.py）
```python
class UIObject:
    id: str
    type: str          # button / input / text / image / card / link
    text: str
    bbox: list[int]    # [x, y, w, h]（viewport 坐标）
    clickable: bool
    enabled: bool
    visible: bool
    confidence: float
    source: str        # ax / ocr / yolo / dom / vision
    raw: dict           # 原始数据（AX node / OCR result / etc）

class NormalizedUIObject(UIObject):
    @classmethod
    def from_ax(cls, node: dict) -> NormalizedUIObject
    @classmethod
    def from_ocr(cls, word: dict) -> NormalizedUIObject
    def to_ui(self) -> UIObject
```

## SiteExplorer 全站探索器

```python
from perception.explorer import SiteExplorer, ExplorerConfig

config = ExplorerConfig(
    start_url="https://example.com",
    exploration_rate=0.2,
    save_interval=20,
    save_path="~/.hermes/explorer_data.json",
)
explorer = SiteExplorer(bridge=bridge, config=config)
explorer.run(max_iterations=100)   # 启动
explorer.save()                    # 手动保存
explorer.stop()                    # 停止
```

策略核心：**UCB1 算法** — 每 (page_url, action_name, target_text) 独立统计成功率，平衡探索和利用。

## 关键设计决策

1. **screen coordinate 而非 viewport** — Mac Retina 缩放因子 ×2，AX tree 报告的是 logical pixel
2. **WorldState 单一实例** — 通过 `get_world_state()` 访问，不可变快照适合调试
3. **Bridge 是协调层** — 不自己执行，用 QueryEngine + ClickAction + Verifier 组合
4. **策略持久化** — ActionStrategy/SiteMap 均可序列化，加载后继续学习
