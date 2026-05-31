# ScreenParser YOLO M4 部署实测（2026-06-01）

## 模型信息

- **模型**: docling-project/ScreenParser — YOLO11-Large fine-tuned on ScreenParse v2
- **文件**: best.pt (146.2 MB)
- **License**: Apache 2.0
- **发布**: IBM Research - ETH Zurich
- **Paper**: arXiv 2602.14276 (ICML 2026)
- **55 UI 元素类**: Table, Column/Browser, Button, Utility Button, App Icon, Navigation Bar, Status Bar, Search Field, Toolbar, Tooltip, Video, Tab Bar, Side Bar, Slider, Picker, ContextMenu, DockMenu, EditMenu, Image, Scroll, Switch, File Icon, Chart, Window, Screen, List, List Item, PopUp Menu, Steppers, Toggles, Text Input, Rating Indicator, Checkbox, Radiobox, Select, Avatar, Badge, Alert, Progress bar, Bottom navigation, Breadcrumb, Page control, Link, Menu, Pagination, Tab, Search Bar, Date-Time picker, Calendar, Text, Heading, Code snippet, Carousel, Notification, Logo

## 部署步骤

### 1. 下载模型权重

```python
from huggingface_hub import hf_hub_download
# 首次下载（~13.8s, 146.2 MB）
path = hf_hub_download(repo_id='docling-project/ScreenParser', filename='best.pt')
print(path)  # ~/.cache/huggingface/hub/models--docling-project--ScreenParser/snapshots/.../best.pt
# 后续加载从缓存读（实测 0.7s）
```

### 2. 加载模型

```python
from ultralytics import YOLO

# ⚠️ 必须用本地路径！HF短名不工作！
model = YOLO('/path/to/best.pt')  # 加载 ~0.1s

# CPU推理（MPS反而更慢，不要用）
model.to('cpu')

# 快速场景分类（320px）
results = model('/path/to/screenshot.png', imgsz=320, verbose=False)
```

### 3. 推理性能实测（M4 24GB, ultralytics 8.4.57）

| 分辨率 | CPU 推理时间 | MPS 推理时间 |
|--------|-------------|-------------|
| 320px  | **93ms**    | N/A         |
| 640px  | **126ms**   | 2,949ms     |
| 1280px | **378ms**   | N/A         |

**结论**: CPU 比 MPS 快 7-31x。YOLO11 MPS backend 未优化。

### 4. 结果分析

```python
from collections import Counter

r = results[0]
boxes = r.boxes

# 按类别统计
cls_counts = Counter(int(b.cls) for b in boxes)
for cls_id, count in cls_counts.most_common(10):
    print(f'{model.names[cls_id]}: {count}')

# 高置信度检测（>0.5）
high_conf = [b for b in boxes if float(b.conf[0]) > 0.5]

# 判断桌面活跃度
if len(boxes) > 5:
    scene = 'active_desktop'  # 活跃桌面：有多个UI元素
elif len(boxes) <= 1:
    scene = 'idle_lockscreen'  # 空闲/锁屏：几乎没有UI元素
else:
    scene = 'ambiguous'
```

## 集成到 screen_watcher handler（方案）

在 handler 启动时加载 YOLO 模型一次（~0.1s），每帧 scene classification 从 qwen3-vl:2b（~7s）切到 ScreenParser（~93ms）：

```python
# 伪代码
class FastClassifier:
    def __init__(self):
        self.model = YOLO(best_pt_path).to('cpu')
    
    def classify(self, screenshot_path):
        results = self.model(screenshot_path, imgsz=320, verbose=False)
        boxes = results[0].boxes
        if len(boxes) > 5:
            return 'active'
        elif len(boxes) <= 1:
            return 'idle'
        else:
            return 'uncertain'  # 需要进一步用 VLM 分析
```

## 已知坑

1. **HF短名不工作**: `ultralytics.YOLO('docling-project/ScreenParser')` 报 `FileNotFoundError: 'docling-project/ScreenParser' does not exist`。必须用本地路径。
2. **MPS更慢**: 别用 `model.to('mps')`，CPU 反而更快。
3. **暗屏/锁屏**: 检测到 ~1 个 "Image" 元素（低置信度 0.32-0.87），无法区分具体 UI。需要结合 VLM 做二次分析。
4. **首次加载缓存**: hf_hub_download 下载到 `~/.cache/huggingface/hub/`，后续加载直接从缓存读取（0.1s）。

## 双层分类器架构（2026-06-01 实测提案）

替代单一 VLM 场景分类（qwen3-vl:2b ~3s）的最佳实践：

```
Layer 1: ScreenParser YOLO (93ms @ 320px)
  ├── >5 UI 元素 → active (browser/app/chat)
  ├── 2-5 元素 → uncertain（需升级）
  └── 0-1 元素 → idle/lockscreen → 直接跳过

Layer 2: qwen3-vl:2b (~3s, 仅 Layer 1 uncertain 时调用)
  ├── browser → 精确分类
  ├── wechat/chat → 精确分类
  └── other → 静默跳过
```

**收益**: idle 场景从 ~8s full cycle 降至 ~93ms。活跃场景不受影响（VLM 仍精确分析）。
**限制**: ScreenParser 训练于 rendered web screenshots，原生桌面应用（微信/钉钉等）识别准确率待验证。
