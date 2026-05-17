---
name: hermes-fast-ocr-ssim
des
version: 1.0.0cription: Hermes 快眼(Apple Vision OCR) + 视觉心跳(SSIM) — 分层感知体系，60-240ms文字定位，5ms点击验证
---

# Hermes 快眼 + 视觉心跳

## 能力概述
- **快眼 (FastOCR)**：Apple Vision 框架，240ms 全屏 / 60ms 局部区域，中英混合，零 GPU 消耗
- **视觉心跳 (SSIM)**：点击前后像素对比，5ms/次，判断点击是否生效

## 依赖
```bash
pip install pyobjc-framework-Vision pyobjc-framework-Quartz opencv-python
# opencv 已内置于 venv
```

## 截图工具函数
```python
import Quartz
import Foundation

def screenshot(path="/tmp/hermes_shot.png", region=None):
    """截取屏幕。region=None 则全屏，(x,y,w,h) 则局部区域"""
    if region:
        x, y, w, h = region
    else:
        x, y, w, h = 0, 0, 1920, 1080
    
    img = Quartz.CGWindowListCreateImage(
        Quartz.CGRectMake(x, y, w, h),
        Quartz.kCGWindowListOptionOnScreenOnly,
        Quartz.kCGNullWindowID,
        Quartz.kCGWindowImageDefault
    )
    dest = Quartz.CGImageDestinationCreateWithURL(
        Foundation.NSURL.fileURLWithPath_(path),
        "public.png", 1, None
    )
    Quartz.CGImageDestinationAddImage(dest, img, None)
    Quartz.CGImageDestinationFinalize(dest)
    return path
```

## 快眼 OCR
```python
import Vision

def fast_ocr(target_text, image_path, confidence=0.5, languages=["zh-Hans", "en-US"]):
    """
    Apple Vision 极速 OCR
    返回: (x, y) 屏幕坐标 或 None
    耗时: 全屏240ms / 局部60ms (M4实测)
    """
    screen_width = 1920
    screen_height = 1080
    
    url = Foundation.NSURL.fileURLWithPath_(image_path)
    handler = Vision.VNImageRequestHandler.alloc().initWithURL_options_(url, None)
    req = Vision.VNRecognizeTextRequest.alloc().init()
    req.setRecognitionLevel_(1)  # 1=Fast, 0=Accurate
    req.setRecognitionLanguages_(languages)
    handler.performRequests_error_([req], None)
    
    for obs in req.results():
        if obs.confidence() < confidence:
            continue
        text = obs.topCandidates_(1)[0].string()
        if target_text in text:
            bbox = obs.boundingBox()
            # Vision 归一化坐标 -> 屏幕坐标 (左下角原点转换)
            cx = (bbox.origin.x + bbox.size.width / 2) * screen_width
            cy = (1 - bbox.origin.y - bbox.size.height / 2) * screen_height
            return int(cx), int(cy)
    return None
```

## 视觉心跳 (SSIM)
```python
import cv2
import numpy as np

def compute_ssim(imgA, imgB):
    """简化SSIM，5ms/次(1920x1080)"""
    if imgA.shape != imgB.shape:
        return 0.0
    A, B = imgA.astype(np.float64), imgB.astype(np.float64)
    muA, muB = A.mean(), B.mean()
    sigmaA2, sigmaB2 = A.var(), B.var()
    sigmaAB = ((A - muA) * (B - muB)).mean()
    C1, C2 = 6.5025, 58.5225
    num = (2*muA*muB + C1) * (2*sigmaAB + C2)
    den = (muA**2 + muB**2 + C1) * (sigmaA2 + sigmaB2 + C2)
    return float(num / den)

def visual_heartbeat(before_path, after_path, threshold_high=0.98, threshold_low=0.92):
    """
    点击前后截图对比，返回: 'success'(跳转) / 'failed'(无变化) / 'uncertain'(轻微变化)
    - SSIM > 0.98: 画面几乎没变 -> failed
    - SSIM < 0.92: 显著跳转 -> success  
    - 0.92-0.98: 轻微变化，可能是弹窗或局部刷新 -> uncertain
    """
    before = cv2.imread(before_path, cv2.IMREAD_GRAYSCALE)
    after = cv2.imread(after_path, cv2.IMREAD_GRAYSCALE)
    if before is None or after is None:
        return 'error'
    
    score = compute_ssim(before, after)
    if score > threshold_high:
        return 'failed'
    elif score < threshold_low:
        return 'success'
    else:
        return 'uncertain'
```

## 智能点击 (OCR优先 + VLM兜底 + SSIM心跳)
```python
def smart_click(target_desc, use_vlm_fallback=True, region=None):
    """
    三层感知点击:
    1. 局部截图 -> Vision OCR (60-240ms)
    2. 找不到 -> VLM 视觉 (1-2s)  
    3. 点击后 -> SSIM 心跳 (5ms) 验证
    
    target_desc: 目标文字或图标描述
    region: (x,y,w,h) 可选，限制扫描区域加速
    """
    import os, time
    # human_click 从 humanization_engine 引入，不在此文件导入避免循环依赖
    
    # 截图
    before_path = "/tmp/hermes_click_before.png"
    after_path = "/tmp/hermes_click_after.png"
    screenshot(before_path, region)
    
    # 第一层: OCR
    pos = fast_ocr(target_desc, before_path)
    
    if pos:
        human_click(pos[0], pos[1])  # 用 humanization_engine 的拟真点击，不上高级模型
        time.sleep(0.5)
        screenshot(after_path, region)
        hb = visual_heartbeat(before_path, after_path)
        return {'method': 'ocr', 'pos': pos, 'heartbeat': hb}
    
    # 第二层: VLM (由调用方实现)
    if use_vlm_fallback:
        # vlm_pos = vlm_locate(target_desc)  # 外部VLM能力
        # human_click(vlm_pos)  # VLM返回坐标后也走拟真点击
        pass
    
    return None
```

## 性能基准 (M4 24GB)
| 操作 | 耗时 | 备注 |
|------|------|------|
| 截图(全屏) | 87ms | CGWindowListCreateImage |
| 截图(局部) | 20-40ms | 区域越小越快 |
| Vision OCR全屏 | 233ms | Fast级别，92文本块 |
| Vision OCR局部 | 60ms | 180px高度区域，3-4x加速 |
| SSIM对比 | 5ms | 1920x1080灰度 |

> ⚠️ 用户文档常引用"20~50ms"，该数字仅指 Vision 框架识别耗时（不含截图）。全链路（截图+OCR）实际 100-300ms，局部区域可压到 60-80ms。

## 关键坑

### execute_code 沙箱没有 pyobjc

`execute_code` 使用的 venv 没有 pyobjc 模块。**必须用 subprocess 调用系统 Python 或 venv Python：**

```python
import subprocess
venv_python = "/Users/aimac/.hermes/hermes-agent/venv/bin/python"

test_code = '''
import Vision
# ... OCR 代码 ...
'''

with open("/tmp/script.py", "w") as f:
    f.write(test_code)

result = subprocess.run([venv_python, "/tmp/script.py"], capture_output=True, text=True, timeout=30)
```

### Vision OCR 对终端/TUI 识别率低

终端渲染的内容（Hermes TUI、Shell 窗口）字符集不标准，置信度只有 30-50%，经常找不到。对 1688/微信/网页等高对比度内容效果好。

### 局部区域截不到目标文字

局部截图只扫一片，如果目标不在区域内会漏扫。已知目标位置时用 region 参数加速，未知时用全屏。

## 设计原则
1. **分层感知**: 能用底层API解决的不上高级模型
2. **局部优先**: 已知目标区域时只扫那片，3-4x加速
3. **零浪费**: SSIM把VLM从"验证点击"苦力中解放
4. **坐标原点**: Vision用左下角归一化，需要转换
