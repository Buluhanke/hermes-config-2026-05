---
name: hermes-digital-body
description: Hermes真人化技能 - 嘴巴(TTS)+眼睛(屏幕感知)+手(电脑控制)+反思
---

# Hermes 真人化技能

## 触发条件
用户提到"有嘴巴"、"有眼睛"、"有手"、"真人化"、"TTS"、"截屏"、"屏幕感知"、"电脑控制"等关键词时使用。

## 核心模块

### 嘴巴 (HermesMouth)
- 驱动：edge-tts（已内置，免费，中文自然）
- 情感参数：happy/sad/excited/calm/angry/neutral
- 用法：
```python
from hermes_body import HermesMouth
mouth = HermesMouth()
mouth.speak("你好！", emotion="happy")  # 直接生成并播放
```
- 语音文件路径：/tmp/hermes_voice_*.mp3
- 可用音色：zh-CN-XiaoxiaoNeural（默认），支持SSML语速/音调控制

### 眼睛 (HermesEye)
- 截屏：pyautogui截图，返回PIL Image
- OCR：tesseract（`brew install tesseract tesseract-lang`），中文+英文
- 图片查找：pyautogui.locateOnScreen，支持confidence阈值
- 用法：
```python
from hermes_body import HermesEye
eye = HermesEye()
eye.screenshot()           # 全屏
eye.ocr(region=(x,y,w,h))  # 指定区域OCR
eye.find_image("button.png")  # 找图
```
- 截屏保存路径：/tmp/hermes_screen_*.png

### 手 (HermesHand)
- 驱动：pyautogui，跨平台鼠标键盘控制
- 用法：
```python
from hermes_body import HermesHand
hand = HermesHand()
hand.click(x, y)           # 点击坐标
hand.typewrite("hello")    # 输入文字
hand.press("enter")        # 按键
hand.hotkey("cmd", "c")    # 组合键
hand.scroll(-3)            # 滚动
hand.drag(x1, y1, x2, y2)  # 拖拽
```
- 注意：macOS需在"系统设置→隐私与安全→辅助功能"授权

### 反思 (HermesReflector)
- 记录动作 + 截屏验证
```python
from hermes_body import HermesReflector
refl = HermesReflector(eye)
refl.record("点击发送", "消息发送成功")
found = refl.verify("发送成功")  # OCR检测关键词
```

## 已验证可用性
- ✅ edge-tts 正常工作（4种情感测试通过）
- ✅ pyautogui 截屏+鼠标控制 正常
- ✅ tesseract OCR 正常（读取到屏幕文字）
- ⚠️ atomacos（macOS Accessibility API）待集成

## 进一步改进方向
1. **atomacos**：macOS原生UI树读取，比pyautogui更精准
2. **Moondream2**：本地VL模型做语义屏幕理解
3. **MeloTTS-MLX**：完全本地TTS，无需网络
4. **iPhone Mirroring**：macOS 15+iPhone镜像，控制手机窗口
