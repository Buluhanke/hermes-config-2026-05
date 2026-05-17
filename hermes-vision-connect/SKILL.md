---
name: hermes-vision-connect
description: "Hermes 三层视觉感知连接器 v2 — 截屏→OCR/VLM→SSIM完整链路，新增: Qwen2.5VL本地闭环、smart_click精准点击、SSIM动态阈值、视觉心跳、失败降级策略。核心: smart_click.py + vision_connect.py"
version: 2.0.0
platforms: [macos]
metadata:
  hermes:
    tags: [vision, screen-understanding, free, openrouter, ollama, qwen25vl, ssim, heartbeat]
    category: desktop
---

# hermes-vision-connect v2

**目标**：截屏 → VLM分析 → 返回可执行指令 → 拟真执行 → 验证确认

**免费优先原则**（已验证）：
1. **L1 Apple Vision OCR**（60-240ms）— 极速文字定位，零Token
2. **L2 Qwen2.5-VL:7B + Ollama本地**（CPU模式，~20s/次，零Token）
3. **L3 smolvlm2本地备用**（2GB，轻量但准确度一般）
4. **L4 硅基流动**（国内直连，免费额度）
5. **L5 OpenRouter Gemini Flash**（最后兜底，需API Key）

---

## 新增功能（v2）

### (1) Qwen2.5VL + Ollama 本地免费闭环

**M4 Mac 必须用 CPU 模式**，否则 OOM：
```python
options={"num_gpu": 0}  # 关键参数，不加必OOM
```

**截图必须压缩**（全分辨率导致超时）：
```python
# 缩放到800px宽，约700KB，响应7-15s
from PIL import Image
img.thumbnail((800, 9999), Image.LANCZOS)
```

**推荐优先级**：
| 优先级 | 模型 | 内存 | 速度 | Token | 备注 |
|--------|------|------|------|-------|------|
| ⭐⭐⭐ | qwen2.5vl:7b | ~6GB | ~20s | 0 | 主力，需加 `:7b` 后缀 |
| ⭐⭐ | smolvlm2-agentic-gui | ~2GB | 5-15s | 0 | 备用 |
| ⭐ | Qwen2.5-VL-7B | - | - | 0 | 硅基流动API |

### (2) smart_click 精准点击（两阶段Zoom-In）

**原理**：R-VLM启发，两阶段放大定位，精度提升13%

```
阶段1: VLM全图预测归一化坐标 (nx1, ny1)
         ↓ 截取中心点周围20%区域
阶段2: VLM局部图再次预测 (nx2, ny2)
         ↓ 局部坐标 → 全图坐标
像素坐标: (px, py)
```

**代码位置**：`smart_click.py`（已实现，两阶段Zoom-In）

### (3) SSIM 动态阈值

**固定阈值的局限**：屏幕内容差异大，固定阈值（0.92/0.98）不精准。

**动态阈值策略**：
```
初始基线: ssim_before = baseline(前3帧平均)
当前帧: ssim_current vs ssim_before
变化率: |ssim_current - ssim_before| / ssim_before

动态判断:
  - 变化率 > 5%  → 页面发生显著变化（成功）
  - 变化率 2-5%  → 轻微变化（弹窗/局部刷新，算成功）
  - 变化率 < 2%  → 无变化（失败，需重试）
```

**自适应阈值（基于画面复杂度）**：
```
画面复杂度 = 边缘密度（用Canny边缘检测）
简单画面（低复杂度）: SSIM成功阈值 0.96
复杂画面（高复杂度）: SSIM成功阈值 0.93
```

**实测校准**：
| SSIM | 实际状态 |
|------|---------|
| > 0.98 | 几乎无变化，失败 |
| 0.95-0.98 | 轻微变化，点击可能成功 |
| 0.92-0.95 | 局部变化（弹窗），**实际已成功** |
| < 0.92 | 显著跳转，成功 |

### (4) 视觉心跳机制

**目的**：定期确认视觉系统健康，及时发现模型挂掉/截图黑屏等问题。

**心跳间隔**：默认30秒，可配置

**心跳内容**：
```
1. 截屏测试（确认屏幕可读）
2. OCR响应测试（确认Vision框架可用）
3. Ollama ping（确认模型服务在线）
4. 截图文件大小检测（异常则重试）
```

**心跳状态**：
```python
{
  "status": "healthy" | "degraded" | "failed",
  "ocr_latency_ms": 150,
  "ollama_latency_ms": 20000,
  "screenshot_ok": true,
  "last_heartbeat": "2026-05-17T15:00:00"
}
```

**实现**：独立线程，每30秒执行一次，发现异常自动告警

### (5) 失败降级策略

**三级降级**（每级重试1-2次）：

```
Level 1: smart_click 失败
  → 清理截图缓存，重试（最多2次）
  → 清理 Ollama 模型缓存，重新加载

Level 2: OCR+VLM 均失败
  → 降级到 CDP AX-tree（如果有目标窗口）
  → 用 human-vision-buffer 历史帧分析

Level 3: 所有本地方案失败
  → 降级到硅基流动API（需要API Key）
  → 最后尝试 OpenRouter Gemini Flash

Level 4: 彻底失败
  → 返回结构化失败报告，包含:
    - 失败阶段
    - 尝试的坐标列表
    - 截图证据路径
    - 建议（"目标元素可能不在当前屏幕"）
```

**降级触发条件**：
- L1/Vision OCR: 3次连续失败
- L2/VLM: 2次连续失败（OOM/超时/无响应）
- L3/SSIM验证: 连续3次 SSIM > 0.96（无变化）
- Ollama服务: ping超时 > 5秒

---

## 核心流程

```
用户指令（"帮我点这个按钮"）
    ↓
截屏（mss，~50ms）
    ↓
[L1] Vision OCR（60-240ms）
    找到 → 执行human_click → SSIM验证
    未找到 ↓
[L2] Qwen2.5-VL + Ollama（CPU模式，~20s）
    找到 → 两阶段Zoom-In精确定位 → 执行 → SSIM验证
    Ollama挂了 → smolvlm2备用
    都失败 ↓
[L3] 硅基流动API / OpenRouter
    找到 → 执行 → SSIM验证
    都失败 ↓
[L4] 返回失败报告 + 建议
```

**SSIM验证循环**：
```
点击后立即截屏 → 计算ssim
  ssim < 0.93 → 成功（显著变化）
  ssim 0.93-0.96 → 轻微变化，VLM再确认一次
  ssim > 0.96 → 无变化，尝试重新定位（最多2次）
```

---

## 使用方式

### 直接用 Python（在 execute_code 里）

```python
import sys
sys.path.insert(0, '/Users/aimac/.hermes/skills/hermes-vision-connect')
from vision_connect import VisionConnect

vc = VisionConnect()

# 找元素并点击（带完整降级策略）
result = vc.find_and_click("加入进货单")
print(result)

# 看屏幕问答
answer = vc.ask_screen("当前页面是什么内容？")
print(answer)

# 视觉心跳状态
status = vc.get_heartbeat_status()
print(status)
```

### legacy API（保持兼容）

```python
from smart_click import smart_click, ask_screen

smart_click("登录按钮")
ask_screen("这个页面的标题是什么？")
```

---

## VisionConnect 核心类

### `__init__` 参数

```python
vc = VisionConnect(
    screenshot_dir="/tmp",          # 截图存放目录
    ollama_url="http://127.0.0.1:11434",
    ollama_model="qwen2.5vl:7b",   # 主力视觉模型
    fallback_model="ahmadwaqar/smolvlm2-agentic-gui",
    use_siliconflow=False,          # 启用硅基流动兜底
    siliconflow_api_key=None,
    heartbeat_interval=30,          # 心跳间隔秒，0=禁用
    ssim_threshold=0.93,            # 基础SSIM阈值
    dynamic_ssim=True,              # 启用动态阈值
    max_retries=2,                 # 每层最大重试
    verbose=True
)
```

### 主要方法

| 方法 | 说明 | 返回 |
|------|------|------|
| `find_and_click(desc)` | 找元素并点击 | `{"success": bool, "coords": (x,y), "layer": str, "ssim": float, "retries": int}` |
| `ask_screen(question)` | 看屏幕问答 | `str` |
| `smart_click(desc)` | find_and_click 别名 | 同上 |
| `get_heartbeat_status()` | 获取心跳状态 | `dict` |
| `start_heartbeat()` | 启动心跳线程 | - |
| `stop_heartbeat()` | 停止心跳 | - |
| `compute_ssim(img1, img2)` | 计算两张图SSIM | `float` |

---

## SSIM 动态阈值实现

```python
def compute_dynamic_threshold(img_path: str) -> float:
    """
    基于画面复杂度自适应SSIM阈值
    复杂度越高（边缘多），阈值越低
    """
    import cv2
    img = cv2.imread(img_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Canny边缘检测
    edges = cv2.Canny(gray, 50, 150)
    edge_ratio = edges.sum() / edges.size  # 边缘像素占比
    
    # 边缘少 → 简单画面 → 阈值高
    # 边缘多 → 复杂画面 → 阈值低
    base = 0.93
    complexity_factor = edge_ratio * 0.05  # 最多降低0.05
    return max(0.90, base - complexity_factor)

def ssim_with_baseline(img_current: str, baseline_frames: list) -> dict:
    """
    变化率检测（非单帧对比）
    对比历史帧栈，计算变化率
    """
    import cv2
    from PIL import Image
    
    curr = np.array(Image.open(img_current).convert("RGB"), dtype=np.float64)
    ssims = []
    for bf_path in baseline_frames[-3:]:  # 最近3帧
        baseline = np.array(Image.open(bf_path).convert("RGB"), dtype=np.float64)
        s = _ssim_fast(curr, baseline)
        ssims.append(s)
    
    avg_ssim = np.mean(ssims)
    latest_ssim = ssims[-1]
    
    change_rate = abs(latest_ssim - avg_ssim) / avg_ssim if avg_ssim > 0 else 0
    
    return {
        "ssim": latest_ssim,
        "avg_ssim": avg_ssim,
        "change_rate": change_rate,
        "changed": change_rate > 0.05,  # 5%变化率
        "threshold_applied": 0.05  # 变化率阈值（非SSIM绝对值）
    }
```

---

## 视觉心跳实现

```python
import threading
import time
import subprocess

class VisionHeartbeat:
    def __init__(self, vc, interval=30):
        self.vc = vc
        self.interval = interval
        self.running = False
        self.thread = None
        self.status = {"status": "unknown"}

    def ping(self) -> dict:
        """执行一次心跳检测"""
        import os
        result = {"status": "healthy", "ocr_latency_ms": 0, 
                  "ollama_latency_ms": 0, "screenshot_ok": False}
        
        # 1. 截图测试
        t0 = time.time()
        path = self.vc.capture_screen()
        result["screenshot_ok"] = os.path.exists(path) and os.path.getsize(path) > 10000
        result["screenshot_latency_ms"] = int((time.time() - t0) * 1000)
        
        # 2. OCR测试
        t0 = time.time()
        try:
            texts = self.vc.vision_ocr("")
            result["ocr_latency_ms"] = int((time.time() - t0) * 1000)
            result["ocr_texts_count"] = len(texts)
        except Exception as e:
            result["ocr_latency_ms"] = -1
            result["status"] = "degraded"
        
        # 3. Ollama ping
        t0 = time.time()
        try:
            import requests
            r = requests.get("http://127.0.0.1:11434/api/tags", timeout=5)
            result["ollama_latency_ms"] = int((time.time() - t0) * 1000)
            result["ollama_models"] = r.json().get("models", [])
        except Exception:
            result["ollama_latency_ms"] = -1
            result["status"] = "failed"
        
        result["last_heartbeat"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        self.status = result
        return result

    def _loop(self):
        while self.running:
            self.ping()
            time.sleep(self.interval)

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
```

---

## 失败降级实现

```python
def find_and_click_with_degradation(self, description: str) -> dict:
    """
    带完整降级策略的 find_and_click
    """
    # 记录失败历史
    failures = []
    
    for attempt in range(self.max_retries + 1):
        try:
            # L1: Vision OCR
            x, y = self.ocr_find_coordinates(description)
            if x is not None:
                return self._execute_and_verify(x, y, "ocr", attempt)
            failures.append("L1_OCR")
            
            # L2: Qwen2.5VL
            x, y = self._vlm_locate(description, model=self.ollama_model)
            if x is not None:
                return self._execute_and_verify(x, y, "qwen25vl", attempt)
            failures.append("L2_Qwen25VL")
            
            # L2b: smolvlm2备用
            x, y = self._vlm_locate(description, model=self.fallback_model)
            if x is not None:
                return self._execute_and_verify(x, y, "smolvlm2", attempt)
            failures.append("L2_smolvlm2")
            
            # L3: 硅基流动
            if self.use_siliconflow:
                x, y = self._siliconflow_locate(description)
                if x is not None:
                    return self._execute_and_verify(x, y, "siliconflow", attempt)
                failures.append("L3_SiliconFlow")
            
            # L4: OpenRouter
            x, y = self._openrouter_locate(description)
            if x is not None:
                return self._execute_and_verify(x, y, "openrouter", attempt)
            failures.append("L4_OpenRouter")
            
        except Exception as e:
            failures.append(f"Exception: {e}")
        
        # 重试前清理
        self._cleanup_cache()
        time.sleep(1)
    
    # 彻底失败，返回报告
    return {
        "success": False,
        "coords": None,
        "layer": "exhausted",
        "ssim": None,
        "failures": failures[-5:],  # 最近5次失败
        "suggestion": "目标元素可能不在当前屏幕，请尝试滚动或切换视图"
    }
```

---

## 坐标解析（已验证格式）

smolvlm2 几乎不输出纯JSON，常见格式只有两种：

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

---

## 依赖

- `mss` — 截屏（`pip install mss`）
- `numpy` — 数值计算
- `requests` — HTTP调用
- `Pillow` — 图片处理
- `opencv-python` — SSIM动态阈值（边缘检测）
- `Vision`, `AppKit` — Apple Vision OCR（macOS原生）
- Ollama 本地服务（`brew install ollama`）
- `cliclick` — 拟真点击（`brew install cliclick`）

### ⚠️ Pillow LANCZOS 兼容性坑

**问题**：Pillow 10+ 将 `Image.LANCZOS` 改为 `Image.Resampling.LANCZOS`，旧代码会报 `AttributeError`。

**兼容写法**：
```python
from PIL import Image
try:
    resample = Image.Resampling.LANCZOS
except AttributeError:
    resample = Image.LANCZOS  # Pillow < 10
img.resize((800, 600), resample)
```
`vision_connect.py` 中已内置兼容处理。

---

## 验证方式

```bash
# 测试截屏
python3 -c "
import mss, os
with mss.MSS() as s:
    s.shot(output='/tmp/hermes_screen.png')
print(os.path.exists('/tmp/hermes_screen.png'))

# 测试Ollama Qwen2.5VL
curl -X POST http://127.0.0.1:11434/api/generate -d '{
  \"model\": \"qwen2.5vl:7b\",
  \"prompt\": \"描述这张图片\",
  \"images\": [\"/tmp/hermes_screen.png\"],
  \"stream\": false,
  \"options\": {\"num_gpu\": 0}
}' | jq .response

# 全流程测试
python3 -c "
import sys
sys.path.insert(0, '/Users/aimac/.hermes/skills/hermes-vision-connect')
from vision_connect import VisionConnect
vc = VisionConnect()
print(vc.find_and_click('Safari', max_retries=1))
"
```

---

## 文件结构

```
hermes-vision-connect/
├── SKILL.md              # 本文件
├── smart_click.py        # v1 legacy API（L1 OCR + L2 smolvlm2 + SSIM固定阈值）
├── vision_connect.py     # v2新实现（VisionConnect类 + 心跳 + 降级 + SSIM动态阈值）
└── references/
    ├── ollama-models-status.md           # Ollama模型状态
    ├── vision-qwen25vl-2026-05-17.md    # Qwen2.5VL实测记录
    ├── smart-click-key-findings-2026-05-17.md  # 关键发现
    ├── see-understand-act-workflow.md     # 看见→看懂→动手流程
    ├── screen-understanding-research-2026-05-17.md  # 研究记录
    └── vlm-screen-understanding-2026-05-17.md  # VLM屏幕理解
```
