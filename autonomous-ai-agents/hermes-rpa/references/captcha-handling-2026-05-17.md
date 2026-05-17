# 验证码处理完整指南 — 2026-05-17

> **现状**：hermes-rpa 对验证码处理是 100% 空白。已有 `captcha-slider-2026-05-13.md` 只有滑块轨迹模拟（overshoot+回退），无打码平台集成，无点选/拼图策略，无自训练方向。
>
> **目标**：补全三种主流验证码的完整处理框架（滑块/点选/拼图），打码平台集成（CapSolver为主），自训练模型路线图。

---

## 一、验证码分类与策略选择

| 类型 | 子类 | 特征 | Hermes 处理策略 |
|------|------|------|----------------|
| **滑块类** | 拖动滑块到缺口 | 滑块+缺口背景图 | 轨迹模拟（已有）+ 打码平台（缺口定位） |
| **点选类** | 文字点选/图标点选 | 文字指令+"点击图中X" | VLM 理解 + 点击坐标 |
| **拼图类** | 滑块拼图/旋转拼图 | 碎片打乱，需还原 | 模板匹配 + 轨迹模拟 |
| **行为类** | reCAPTCHA v3 / Turnstile | 无可见UI，行为分析 | 指纹硬化 + 浏览器环境伪装 |
| **混合类** | 滑块+点选组合 | 先滑后点 | 分阶段处理 |

### 决策树

```
检测到验证码
    │
    ├─ 有滑动轨道 → 滑块类
    │       ├─ 背景图完整（缺口需识别）→ CapSolver 缺口定位
    │       └─ 背景图已处理 → 用已有轨迹模拟代码
    │
    ├─ 有文字指令+"点击图中X" → 点选类
    │       ├─ 图标少(<5个) → smolvlm2 本地识别
    │       └─ 场景复杂 → CapSolver
    │
    ├─ 有碎片拼图 → 拼图类
    │       └─ 模板匹配 + 旋转校正
    │
    └─ 无可见UI（后台评估）→ reCAPTCHA v3 / Turnstile
            └─ 指纹硬化（Patchright/反指纹配置）
```

---

## 二、滑块验证码处理

### 2.1 已有能力（captcha-slider-2026-05-13.md）

```python
# ~/Vision_Lab/captcha_slider.py — 轨迹模拟核心
def human_drag(start_x, start_y, end_x, end_y, 回退校准=True):
    # 人类拖拽物理特征：起点犹豫 → 快速初期 → 减速接近 → overshoot → 回退微调
    time.sleep(random.uniform(0.05, 0.15))  # 起点犹豫
    path = _humanoid_path(start_x, start_y, end_x, end_y, roughness=0.8)
    # ... 变速移动 + overshoot回退
```

### 2.2 缺口识别（打码平台）

**CapSolver API** — 滑动验证码核心是找到缺口位置（通常缺口距离为目标 x 偏移量）：

```python
import requests, json, base64

CAPSOLVER_API_KEY = "YOUR_KEY"  # 从 capsolver.com 注册获取

def solve_slider_captcha(slider_image_b64: str, background_image_b64: str) -> int:
    """
    返回缺口左侧边缘的 x 坐标（像素）
    """
    payload = {
        "clientKey": CAPSOLVER_API_KEY,
        "task": {
            "type": "Slide",  # CapSolver 任务类型
            "images": [slider_image_b64, background_image_b64],  # 滑块图 + 背景图
            "method": "common"  # 通用滑动（自动检测）
        }
    }
    resp = requests.post("https://api.capsolver.com/createTask", json=payload, timeout=30)
    result = resp.json()  # {"taskId": "..."}
    
    # 轮询结果（通常5-15秒）
    for _ in range(20):
        time.sleep(1)
        r = requests.post("https://api.capsolver.com/getTaskResult",
                          json={"clientKey": CAPSOLVER_API_KEY, "taskId": result["taskId"]})
        data = r.json()
        if data["status"] == "ready":
            return data["solution"]["point"]["x"]  # 缺口 x 坐标
    raise RuntimeError("CapSolver 超时无返回")
```

### 2.3 完整滑块解题闭环

```python
def solve_slider_with_hermes(slider_elem_ref, bg_elem_ref):
    """
    1. 截图滑块图 + 背景图
    2. 发 CapSolver 求缺口 x
    3. 用人类轨迹拖动到目标位置
    """
    # Step 1: 截图（通过 CDP 或 hermes_desktop_rpa）
    slider_bytes = cdp_screenshot(slider_elem_ref)
    bg_bytes = cdp_screenshot(bg_elem_ref)
    slider_b64 = base64.b64encode(slider_bytes).decode()
    bg_b64 = base64.b64encode(bg_bytes).decode()
    
    # Step 2: CapSolver 找缺口
   缺口_x = solve_slider_captcha(slider_b64, bg_b64)
    
    # Step 3: 获取滑块当前位置（起始 x）
    slider_x = get_slider_current_x()  # 需要定位滑块元素
    
    # Step 4: 人类轨迹拖动
    human_drag(slider_x, slider_y, 缺口_x, slider_y)
```

---

## 三、点选验证码处理

### 3.1 文字点选（"点击图中所有的XX"）

**本地方案 — smolvlm2**（免费，2GB）：

```python
def solve_click_captcha_local(captcha_image_b64: str, instruction: str) -> list[tuple[int, int]]:
    """
    用 smolvlm2 理解点选验证码，返回点击坐标列表
    instruction: "点击图中所有的公交车" / "点击所有的红绿灯"
    """
    payload = {
        "model": "ahmadwaqar/smolvlm2-agentic-gui",
        "prompt": f"""这是一个点选验证码。按照指令点击图中对应物体。
指令: {instruction}
请用中文简短回答你点击的位置，格式: click(x=0.XXX, y=0.XXX)
如果有多个目标，按顺序回答每个的坐标。
<image>",
        "images": [captcha_image_b64],
        "stream": False
    }
    resp = requests.post("http://localhost:11434/api/generate", json=payload, timeout=60)
    response_text = resp.json().get("response", "")
    
    # 解析所有 click(x=0.XXX, y=0.XXX) 坐标
    coords = []
    for m in re.finditer(r'click\s*\(\s*x\s*=\s*([\d.]+)\s*,\s*y\s*=\s*([\d.]+)\s*\)', response_text):
        norm_x, norm_y = float(m.group(1)), float(m.group(2))
        screen_x = int(norm_x * screen_width)
        screen_y = int(norm_y * screen_height)
        coords.append((screen_x, screen_y))
    return coords
```

**CapSolver 方案**（付费，更准，成功率更高）：

```python
def solve_click_captcha_capsolver(captcha_image_b64: str, instruction: str) -> list[tuple[int, int]]:
    """
    CapSolver text click 任务
    instruction: "点击图中的公交车"
    """
    payload = {
        "clientKey": CAPSOLVER_API_KEY,
        "task": {
            "type": "Custom",
            "image": captcha_image_b64,
            "instructions": instruction,
            "module": "clickCaptcha"  # 点选模块
        }
    }
    resp = requests.post("https://api.capsolver.com/createTask", json=payload)
    task_id = resp.json()["taskId"]
    
    # 轮询
    for _ in range(30):
        time.sleep(1)
        r = requests.post("https://api.capsolver.com/getTaskResult",
                          json={"clientKey": CAPSOLVER_API_KEY, "taskId": task_id})
        data = r.json()
        if data["status"] == "ready":
            return [(p["x"], p["y"]) for p in data["solution"]["click"]]
    raise RuntimeError("CapSolver 点选超时")
```

### 3.2 图标点选（无文字，仅图标）

```python
def solve_icon_click_captcha(captcha_image_b64: str) -> list[tuple[int, int]]:
    """
    无文字指令的点选验证码 — smolvlm2 零样本理解
    指令可由模型自己推断（如：点击所有方形图标）
    """
    payload = {
        "model": "ahmadwaqar/smolvlm2-agentic-gui",
        "prompt": """这是一个图标点选验证码。图中有多个图标，
请找出所有属于同一类别的图标（形状/颜色/类型相同的），并点击它们。
按顺序给出每个点击位置，格式: click(x=0.XXX, y=0.XXX)
<image>",
        "images": [captcha_image_b64],
        "stream": False
    }
    # ... 解析同上
```

---

## 四、拼图验证码处理

### 4.1 滑块拼图（碎片在轨道上滑动还原）

```python
def solve_jigsaw_slider_captcha():
    """
    典型拼图验证码流程：
    1. 识别拼图碎片位置（x_offset）
    2. 识别拼图目标位置（template matching）
    3. 计算滑动距离
    4. 用人类轨迹滑动
    """
    # 截图拼图区域
    puzzle_img = capture_puzzle_region()
    
    # 方法A: CapSolver
    # payload = {"type": "Jigsaw", "images": [base64.b64encode(puzzle_img).decode()]}
    
    # 方法B: OpenCV 模板匹配（自训练方向第一步）
    import cv2, numpy as np
    puzzle = cv2.imdecode(np.frombuffer(puzzle_img, np.uint8), cv2.IMREAD_COLOR)
    
    # 提取滑块（通常在图片左/右边缘）
    slider = puzzle[:, :50, :]  # 左边50px通常含滑块
    
    # 找缺口位置（背景图边缘缺口特征）
    # ... 模板匹配逻辑
    
    # 计算滑动距离后，用 human_drag 执行
```

### 4.2 旋转拼图（将碎片旋转到正确角度）

```python
def solve_rotation_captcha(piece_image_b64: str) -> float:
    """
    返回需要旋转的角度（度）
    CapSolver rotation 任务类型
    """
    payload = {
        "clientKey": CAPSOLVER_API_KEY,
        "task": {
            "type": "Rotate",
            "image": piece_image_b64,
            "module": "rotateCaptcha"
        }
    }
    # ... 轮询获取角度
    # 返回如 47.3（度）
```

---

## 五、打码平台集成

### 5.1 CapSolver（首选）

**官网**：https://www.capsolver.com

**注册步骤**：
1. 访问 capsolver.com 注册（支持 Google/微信登录）
2. 充值（支持支付宝，最低 $2 起）
3. 获取 API Key（在 Dashboard → API Key）

**价格参考**：
| 任务类型 | 单价 | 备注 |
|---------|------|------|
| 滑动验证码 | $0.5-2 / 1000次 | 按缺口难度分 |
| 点选验证码 | $1-3 / 1000次 | 按图标数量分 |
| reCAPTCHA v2 | $2-5 / 1000次 |  |
| reCAPTCHA v3 | $1-2 / 1000次 |  |
| hCaptcha | $2-5 / 1000次 |  |

**Python SDK**：
```python
# 不需要额外安装库，直接 requests 调用上方 API 即可
# 如需 SDK: pip install capsolver（官方有但非必须）
```

**自用封装**：
```python
class CaptchaSolver:
    """统一入口，按验证码类型自动路由"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    def solve(self, captcha_type: str, **kwargs) -> dict:
        if captcha_type == "slider":
            return self._solve_slider(kwargs["slider_b64"], kwargs["bg_b64"])
        elif captcha_type == "click":
            return self._solve_click(kwargs["image_b64"], kwargs["instruction"])
        elif captcha_type == "jigsaw":
            return self._solve_jigsaw(kwargs["image_b64"])
        elif captcha_type == "rotate":
            return self._solve_rotate(kwargs["image_b64"])
        elif captcha_type == "recaptcha_v2":
            return self._solve_recaptcha_v2(kwargs["site_url"], kwargs["site_key"])
        elif captcha_type == "recaptcha_v3":
            return self._solve_recaptcha_v3(kwargs["site_url"], kwargs["site_key"])
        elif captcha_type == "turnstile":
            return self._solve_turnstile(kwargs["site_url"], kwargs["site_key"])
        else:
            raise ValueError(f"不支持的类型: {captcha_type}")
    
    def _solve_slider(self, slider_b64, bg_b64):
        # 见上方 2.2 完整实现
        pass
```

### 5.2 Anti-Captcha（备选）

**官网**：https://anti-captcha.com

**特点**：
- 纯人工打码，成功率 99%
- 价格比 CapSolver 贵 2-3 倍
- 适合高价值目标（如金融操作）

### 5.3 2Captcha（备选）

**官网**：https://2captcha.com

**特点**：
- 老牌服务商
- API 简单
- 速度较慢（人工队列）

### 5.4 免费自处理优先级

| 验证码类型 | 免费自处理 | 何时用打码平台 |
|------------|------------|----------------|
| 滑块（缺口可识别）| smolvlm2 定位缺口 | 复杂背景、缺口不明显 |
| 文字点选（简单图标）| smolvlm2 本地 | 图标数量多、遮挡严重 |
| 旋转拼图 | — | 始终付费更稳 |
| reCAPTCHA v3 | Patchright 指纹硬化 | 评分低时降级 |
| Turnstile | Patchright 指纹硬化 | 始终付费更稳 |

---

## 六、自训练模型方向

### 6.1 训练目标

| 模型 | 输入 | 输出 | 训练集来源 |
|------|------|------|-----------|
| **滑块缺口检测** | 背景图 | 缺口边界框(x1,y1,x2,y2) | 自己采集 + 合成 |
| **图标分类** | 图标截图 | 类别ID / 热度图 | 公开数据集 + 自己标注 |
| **拼图位置预测** | 拼图碎片 | 目标位置(x,y) | 合成数据 |

### 6.2 数据采集策略

**滑块验证码数据**：
```python
def collect_slider_training_data(n_samples=1000):
    """
    从真实网站采集滑块验证码截图对（背景图 + 缺口位置标注）
    """
    import os, json
    os.makedirs(f"/Users/aimac/Vision_Lab/captcha_data/slider", exist_ok=True)
    
    # 目标网站列表（1688/淘宝/京东等）
    targets = ["1688", "taobao", "jd", "baidu"]
    
    for site in targets:
        for i in range(n_samples // len(targets)):
            # 触发验证码（刷新页面/多次请求）
            trigger_captcha(site)
            time.sleep(random.uniform(2, 5))
            
            # 截图
            bg_path = f"slider/{site}_{i}_bg.png"
            slider_path = f"slider/{site}_{i}_slider.png"
            screencapture(bg_path)
            screencapture(slider_path)
            
            # 人工标注缺口位置（用 labelImg 工具）
            # 导出 VOC/COCO 格式
```

### 6.3 模型选型

**缺口检测（Object Detection）**：
```bash
# YOLOv8（小模型，适合 Mac 训练）
pip install ultralytics

# 训练
from ultralytics import YOLO
model = YOLO('yolov8n.pt')  # nano 最小最快
results = model.train(
    data='captcha_slider.yaml',
    epochs=50,
    imgsz=320,
    device='mps'  # Mac M系列GPU加速
)
```

**captcha_slider.yaml**：
```yaml
path: /Users/aimac/Vision_Lab/captcha_data/slider
train: images/train
val: images/val
names: ['gap']  # 缺口

# 数据示例：
# images/train/1688_0_bg.png  →  labels/train/1688_0_bg.txt (格式: class x_center y_center width height，归一化)
```

**图标分类（Image Classification）**：
```bash
# ResNet / EfficientNet（PyTorch）
# or MobileNetV4（移动端优先，速度快）
```

### 6.4 自训练 vs 打码平台对比

| 维度 | 自训练模型 | 打码平台 |
|------|-----------|---------|
| 初始成本 | 高（标注数据 + 训练时间） | 低（注册即用） |
| 边际成本 | ≈0（本地推理） | 按次计费 |
| 适用量级 | >1000次/天 | <1000次/天 |
| 维护成本 | 高（需持续采集新样本） | 低（平台维护模型） |
| 速度 | 快（本地 GPU/MPS） | 5-15秒/次 |
| 准确率 | 可达 90%+ | 60-80%（AI）/ 99%（人工） |

**结论**：
- 日均 <500次：直接用 CapSolver，更划算
- 日均 >2000次：自训练模型，3个月内回本
- 高价值操作（金融/账号）：人工打码（Anti-Captcha）

### 6.5 渐进路线图

```
Phase 1（0-1月）: 打码平台托底
  └─ CapSolver 注册充值，接入 API
  
Phase 2（1-3月）: 滑块专项自训练
  └─ 采集 1688/淘宝/京东 滑块数据 2000+ 组
  └─ YOLOv8 训练缺口检测模型
  └─ 本地推理，CapSolver 兜底失败case
  
Phase 3（3-6月）: 点选/拼图扩展
  └─ 扩展数据采集到点选验证码
  └─ smolvlm2 微调（可选，2GB VRAM可跑）
  
Phase 4（6月+）: 全自研替代
  └─ 自建模型仓库
  └─ 持续学习新验证码变种
```

---

## 七、hermes-rpa 集成点

### 7.1 新增 triggers（在 SKILL.md 中）

```yaml
triggers:
  # 新增验证码相关
  - 验证码 / 滑块 / 拼图 / 点选 / captcha
  - 帮我过验证码 / 解验证码 / captcha
  - 打码 / 识别缺口 / 缺口检测
```

### 7.2 新增 scripts

```
scripts/
  ├─ captcha_solver.py        # CaptchaSolver 统一入口类
  ├─ captcha_slider.py        # 滑块轨迹模拟（已有，补全）
  └─ captcha_ocr_fallback.py  # 无打码平台时的 OCR 降级
```

### 7.3 perception/.actions 扩展

```python
# perception/actions/captcha.py（新文件）
class CaptchaAction:
    def detect_captcha_type(self, page_state) -> str:
        """根据页面特征判断验证码类型"""
        
    def solve_slider(self, slider_elem, bg_elem) -> bool:
        """滑块验证码解题"""
        
    def solve_click(self, captcha_img, instruction) -> list[tuple]:
        """点选验证码解题"""
        
    def solve_jigsaw(self, puzzle_elem) -> bool:
        """拼图验证码解题"""
```

### 7.4 世界状态扩展

```python
# 在 WorldState 中新增 captcha 上下文
@dataclass
class CaptchaContext:
    type: str                    # "slider" | "click" | "jigsaw" | "rotate"
    challenge_id: str            # 验证码 session id
    attempts: int = 0            # 本次尝试次数
    last_error: str = ""         # 上次错误原因
    solved: bool = False
```

---

## 八、实战注意事项

### 8.1 1688 验证码特殊性

- 阿里巴巴自研验证码系统，非标准 reCAPTCHA
- 滑块验证码缺口识别难度高（背景图高模糊+高噪声）
- **扫码登录（手机阿里 APP）比账号密码+滑块更稳定**
- 如遇 1688 滑块验证码：优先扫码，次选 CapSolver，轨迹模拟是辅助

### 8.2 降级策略

```
尝试 CapSolver
  ├─ 成功 → 返回坐标
  ├─ 失败（超时/余额不足）→ smolvlm2 本地兜底
  └─ 兜底也失败 → 人工介入提示用户
```

### 8.3 速率控制

- CapSolver 有 QPS 限制（根据套餐）
- 本地请求加 `time.sleep(random.uniform(1, 3))`
- 连续失败 3 次后切换策略

---

## 九、参考文献

- `references/captcha-slider-2026-05-13.md` — 滑块轨迹模拟（overshoot+回退）
- `references/2026-05-17-deep-evolution-research.md` — 验证码对抗行业格局
- `references/perception-kernel-modules-2026-05-14.md` — 感知核心理念（可复用架构）
- CapSolver API Docs: https://www.capsolver.com/docs/api
- Anti-Captcha API Docs: https://anti-captcha.com/apiready
- YOLOv8 Training: https://docs.ultralytics.com/modes/train/