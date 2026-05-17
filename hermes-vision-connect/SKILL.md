---
name: hermes-vision-connect
description: "Hermes 三层视觉感知连接器 — 截屏->OCR/VLM->SSIM验证完整链路，含smart_click.py三层感知系统。核心文件: smart_click.py（三层感知+两阶段zoom-in）；技术发现: references/smart-click-key-findings-2026-05-17.md"
---

# hermes-vision-connect

## 核心架构

```
smart_click("发送按钮")
    │
    ├─ [L1] Vision OCR (60-240ms) → Apple Vision，中英文字极速识别
    │       找到了 → 中心点坐标
    │
    ├─ [L2] smolvlm2 (5-15s) → 复杂元素兜底，<code>click(x=0.5,y=0.3)</code>格式
    │       找到了 → 归一化转像素坐标
    │
    └─ [L3] SSIM (5ms) → 点击后截图对比
            > 0.98 → 失败重试
            < 0.92 → 成功
            0.92-0.98 → 轻微变化（弹窗）
```

## 关键经验（2026-05-17）

## 核心架构：感知→定位→执行→验证 四层闭环（2026-05-17确认）

用户明确要求按以下路径持续执行：**看见→看清→看懂→动手→精确**，随着画面变化动态调整动手位置。

```
截屏 → OCR快速定位 → VLM语义理解 → 坐标计算 → 拟真执行 → 截图验证 → SSIM判断
   ↑                                                                 ↓
   └──────── 失败则串联历史帧重分析，持续迭代直到成功 ◄────────┘
```

**三层感知优先级**（已实现，按速度排列）：
1. **L1 Vision OCR**（60-240ms）：极速文字定位，模糊匹配容错
2. **L2 smolvlm2 VLM**（2-5s）：语义理解兜底
3. **L3 Gemini Flash**：云端兜底

**迭代精调机制**（关键发现）：
- smart_click 失败后不放弃，串联环形缓冲区最近3帧给VLM分析
- 画面变化时（如弹窗、加载、内容更新）自动重定位目标
- SSIM < 0.96 即认为成功（对人类操作的容忍度）

### smolvlm2 响应格式（实测）
```
# 格式1: <code>click(x=0.495, y=0.378)</code>
# 格式2: 裸坐标 0.495, 0.378（无包裹）
# 格式3: JSON {"x":0.5,"y":0.3}
```
纯JSON格式几乎不出现，优先匹配前两种。

### 图片必须缩小
全分辨率(1920x1080, 4MB)会导致Ollama超时。缩放到800px宽后约700KB，响应时间7-15s。

### OCR识别率低时用smolvlm2兜底
锁屏界面/特殊字体下OCR只识别2-3个文字块，但smolvlm2能完整理解屏幕内容。

## 使用方法

```python
import sys
sys.path.insert(0, '/Users/aimac/.hermes/skills/hermes-vision-connect')
from smart_click import smart_click, ask_screen, vision_ocr_texts

# 三层感知点击
smart_click("Safari图标")

# 直接问屏幕
ask_screen("这个页面的标题是什么？")

# 纯OCR文字定位
texts = vision_ocr_texts()
for text, x, y, w, h in texts:
    print(f"「{text}」@ ({x},{y})")
```

## 已知限制
- OCR对锁屏界面/TUI渲染识别率极低
- smolvlm2 1.8B 准确率约60-70%，复杂界面可能猜错
- CUA/AX-tree 可做100%准确的备选（但需要窗口可见）
