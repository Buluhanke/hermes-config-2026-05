---
name: hermes-digital-body
description: Hermes真人化技能 Phase 1+2+3 — 嘴巴(TTS)+眼睛(屏幕感知)+手(电脑控制)+反思+情绪感知+操作节奏+拟真缺陷
---

# Hermes 真人化技能

## 触发条件
用户提到"有嘴巴"、"有眼睛"、"有手"、"真人化"、"TTS"、"截屏"、"屏幕感知"、"电脑控制"等关键词时使用。

## 自我驱动原则（2026-05-17 确立，来自老板指令）

- **目标**：真人化——让老板能安心忘掉多少事
- **执行**：不等授权，不问问题，只管结果出
- **学习**：遇到卡点先全网搜索/与各AI平台对话获取知识
- **授权**：获取知识、安装技能，默认同意（尽量免费）
- **删除**：大量删文件必须告知，小操作自己判断
- **反馈**：只汇报结果+问题+建议，不抛问题给老板

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

### 眼睛 (HermesEye) — 2026-05-17 重大更新

**屏幕感知链路已打通**：

```python
# 截图 → 压缩 → Qwen2.5VL CPU推理 → 语义理解
import subprocess, base64, requests

subprocess.run(["screencapture", "-x", "/tmp/hermes_screen.png"])
subprocess.run(["sips", "-z", "600", "800", "-s", "formatOptions", "40",
                "/tmp/hermes_screen.png", "--out", "/tmp/small.jpg"])

with open('/tmp/small.jpg', 'rb') as f:
    img_b64 = base64.b64encode(f.read()).decode('utf-8')

payload = {
    "model": "qwen2.5vl:7b",
    "prompt": "描述这张图片的所有内容，用中文回答",
    "images": [img_b64],
    "stream": False,
    "options": {"num_gpu": 0}  # M4 Mac必须加，否则OOM
}
resp = requests.post('http://localhost:11434/api/generate', json=payload, timeout=180)
print(resp.json()['response'])
```

**实测速度**：~20秒/次（CPU模式）
**可用脚本**：`~/.hermes/scripts/hermes_vision.py --goal "目标"`
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

## Phase 3 新增模块（2026-05-17）

### 情绪感知层 (HermesEmotion)
- 触发条件：用户语气词、标点（！！！、？？？）、长沉默、频繁修改
- 输入信号：文本情感（感叹号密度、问号密度、表情符号）+ 屏幕内容情绪暗示（错误提示、loading、弹窗）
- 推理规则：
  - 感叹号 > 2 个 → 兴奋/急切
  - 问号 > 2 个 → 疑惑/焦虑
  - 省略号 "..." → 犹豫/等待
  - 全小写 + 无标点 → 随意/疲惫
  - 屏幕出现红色错误 → 紧张/沮丧
  - 屏幕长时间 loading → 不耐烦风险
- 输出：emotion 状态映射到 TTS 参数（语速、音调、停顿）
- 用法：
```python
from hermes_body import HermesEmotion
emotion = HermesEmotion()
# 分析用户输入情绪
mood = emotion.analyze_text("你怎么这么慢！！！")  # → "urgent"
mood = emotion.analyze_text("好吧...")              # → "hesitant"
# 结合屏幕状态
screen_mood = emotion.analyze_screen(eye.screenshot())  # 错误=red, loading=waiting
# 合并输出 TTS 参数
tts_params = emotion.get_tts_params(mood, screen_mood)
mouth.speak("好的！", **tts_params)
```
- 内部状态：last_emotion（上次情绪）、emotion_history（最近5条，衰减权重）
- 情绪持续时间：用户在情绪窗口（30秒）内无新输入则重置为 neutral

---

### 操作节奏 (HermesRhythm)
- 目标：让操作间隔不像机器（均匀精准），而是有人类的不确定性
- **基础延迟**（每次操作前）：
  - click：80–200ms 随机
  - typewrite：30–80ms/字符（随机，不是固定值）
  - key press：50–150ms
  - scroll：100–250ms
- **批次间隔**：连续操作之间插入 200–600ms（模拟人读屏时间）
- **操作前停顿时长**（决策延迟）：
  - 简单操作（点击已知按钮）：100–300ms
  - 中等操作（需要确认位置）：300–800ms
  - 复杂操作（要找/要思考）：800–2000ms
- **随机变量**：使用均匀分布或正态分布（推荐正态，中心值±标准差）
- **鼠标移动轨迹**（非直线，点击终点前有微抖动）：
```python
import random, math

def human_click(hand, x, y):
    # 先移动到目标附近（人类不会直接到达）
    jitter_x = random.uniform(-15, 15)
    jitter_y = random.uniform(-10, 10)
    hand.moveTo(x + jitter_x, y + jitter_y, duration=random.uniform(0.2, 0.5))
    time.sleep(random.uniform(0.1, 0.3))
    hand.click(x, y)
```
- **操作节奏记录**：refl.record() 时同时记录操作耗时，用于事后分析
- 用法：
```python
from hermes_body import HermesRhythm
rhythm = HermesRhythm()
# 包裹任何 hand 操作
rhythm.click(x, y)           # 自动加延迟+抖动
rhythm.typewrite("hello")   # 字符间随机停顿
rhythm.think()              # 纯等待（模拟思考），1-3秒
rhythm.idle()               # 发呆机制，见下文
```

---

### 错字/过冲/发呆机制 (HermesImperfection)

#### 3.1 打字错字（Typo）
- 概率：每批次输入（>3字符）有 8–15% 概率触发
- 错字类型分布：
  - 相邻字母互换（teh → the）：40%
  - 少打一个字母（hes → hes）：30%
  - 打错一个字母（helo → hello）：20%
  - 多打一个字母（herre → heres）：10%
- 修正策略：打完后检测到错误 → 立即退格（backspace）修正 → 重打正确内容
- 修正停顿：200–500ms（犹豫→发现→修正的自然过程）
- 特殊：用户名、密码、技术术语错字率降至 2%（不打断关键内容）

```python
def human_typewrite(hand, text):
    typo_chance = 0.10  # 10%
    if len(text) > 3 and random.random() < typo_chance:
        # 随机选择错字类型
        error_type = random.choice(["swap", "omit", "wrong", "extra"])
        corrupted = apply_typo(text, error_type)
        hand.typewrite(corrupted)
        time.sleep(random.uniform(0.2, 0.5))
        # 退格清除
        for _ in range(len(corrupted)):
            hand.press("backspace")
        time.sleep(random.uniform(0.1, 0.2))
        # 重打正确内容
        hand.typewrite(text)
    else:
        hand.typewrite(text)
```

#### 3.2 过冲（Overshoot）
- 触发：鼠标点击，坐标在可点击元素附近时
- 表现：鼠标先到达元素外围 → 修正方向 → 到达目标（比直接点击多一步）
- 概率：10–20%
- 轨迹：bezier曲线而非直线，终点有小幅抖动
- 修正时间：150–400ms

#### 3.3 发呆（Idling）
- 触发条件：
  - 等待某个结果（screen loading）
  - 操作后等待 UI 反馈
  - 用户沉默（用户输入间隔 > 60秒）
- 表现：
  - 无实际操作
  - 鼠标在屏幕某个合理位置静止
  - 可选：微幅鼠标抖动（模拟人盯着屏幕想事情）
- 发呆时长：2–8秒（随机），期间保持屏幕感知
- 发呆结束：重新扫描屏幕，若状态已满足则继续，否则重新规划

```python
def idle(eye, hand, duration=None):
    # 随机选择一个"看"的位置
    focus_points = [(400, 300), (600, 400), (300, 500), (700, 350)]
    x, y = random.choice(focus_points)
    hand.moveTo(x, y)
    if duration is None:
        duration = random.uniform(2, 8)
    time.sleep(duration)
    # 发呆结束，眨眼（截屏一次确认状态）
    eye.screenshot()
```

---

## 进一步改进方向
1. **atomacos**：macOS原生UI树读取，比pyautogui更精准
2. **Moondream2**：本地VL模型做语义屏幕理解
3. **MeloTTS-MLX**：完全本地TTS，无需网络
4. **iPhone Mirroring**：macOS 15+iPhone镜像，控制手机窗口
5. **情绪时序建模**：LSTM 网络建模用户情绪随时间的演变
6. **操作拟真度评估**：记录每次操作的"人类相似度分数"，用于自我优化
