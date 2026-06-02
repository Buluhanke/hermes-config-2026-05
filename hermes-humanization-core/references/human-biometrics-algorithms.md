# Human Biometrics Algorithms — 真人化底层算法详解

> **配套模块**：`~/.hermes/scripts/hermes_human_biometrics.py` (~25KB)
> **被 reactor_v3 / vision_click / hardcore_type 引用**

本文档解释两个核心真人化算法的数学原理和风控绕过的依据。完整代码见上述模块。

---

## 一、贝塞尔曲线鼠标划行（Bezier Mouse Trajectory）

### 为什么不用直线？
直线 `mouseMoved` 100% 是机器行为。真人鼠标轨迹具有：

| 特征 | 真人 | 直线匀速 |
|------|------|----------|
| 路径曲率 | 总是偏离直线 5-30px | 严格 0 |
| 速度曲线 | 起步慢→中段快→末端慢（S型） | 恒定 |
| 末端行为 | 悬停 / 过冲 / 微抖动 | 直线命中 |
| 物理惯性 | 加速度连续（二阶导数连续） | 一阶导数有拐点冲击 |

前端风控（Mouse Tracking JS）会采集这四维特征做模型推理。

### 三次贝塞尔公式
```
B(t) = (1-t)³·P0 + 3(1-t)²t·P1 + 3(1-t)t²·P2 + t³·P3   t ∈ [0,1]
```
- P0 = 起点，P3 = 终点
- P1, P2 = 两个控制点，控制曲线形状

### 真人化关键点

#### 1. 控制点偏移（让曲线弯曲）
控制点不在起点到终点的连线上，而是沿**垂直方向偏移**一段距离：

```python
# 距离向量
dx, dy = x2 - x1, y2 - y1
dist = math.hypot(dx, dy)
# 垂直单位向量
nx, ny = -dy/dist, dx/dist
# 第一个控制点：在 1/3 路径处，沿垂直方向偏 80-240px（随机）
cp1 = (x1 + dx*0.33 + nx*cp1_dist*side, y1 + dy*0.33 + ny*cp1_dist*side)
```

效果：轨迹呈现自然弧度而非直线。

#### 2. cos-S 速度曲线（无拐点冲击）
真人手部加速/减速过程是**物理惯性**的，加速度连续。错误的实现用 smoothstep（分段），会在 ease_in/ease_out 边界产生一阶导数不连续点。

**正确公式**（二阶导数连续）：
```python
t' = (1 - cos(t·π)) / 2
```

| t | t' | 含义 |
|---|----|------|
| 0.00 | 0.000 | 起点静止 |
| 0.10 | 0.024 | 慢速起步 |
| 0.18 | 0.078 | 加速中 |
| 0.50 | 0.500 | 中段半速 |
| 0.78 | 0.885 | 高速接近 |
| 0.90 | 0.976 | 开始减速 |
| 1.00 | 1.000 | 终点停止 |

#### 3. 渐进减抖（神经"对准"）
真人手部肌肉**越接近目标抖动越小**（视觉引导，神经集中控制）：
```python
shake_reduce = 1.0 - progress   # progress: 0→1
jitter = gauss(0, σ) * shake_reduce
```

#### 4. 过冲修正（真人冲过头）
18% 概率触发"过冲 → 修正回拉"行为：
- 沿终点切线方向冲出 4-14px
- 停顿 40-90ms
- 用更慢的 8 步轨迹修正回目标

#### 5. 末端悬停
到达目标前最后 3 步用 18ms 慢延迟，模拟"瞄准"犹豫。

#### 6. 距离自适应
| 距离 | 步数 | 步间延迟 |
|------|------|----------|
| < 8px | 1 步（直接移动） | - |
| < 120px | 28 步 | 6ms |
| 120-600px | 28-55 步线性插值 | 6ms × 速度因子 |
| > 600px | 55 步 | 6ms × 1.4 |

---

## 二、生物识别打字律动（Biometric Typing Rhythm）

### 为什么不用匀速？
匀速 `keyDown → keyUp` 循环的键间延迟方差为 0，机器特征 100%。

真人打字具有：

| 特征 | 真人 | 匀速循环 |
|------|------|----------|
| 基础延迟 | 高斯分布 120-180ms | 恒定 50ms |
| 词边界停顿 | 80-220ms（思考下一个词） | 0 |
| 标点停顿 | 280-480ms | 0 |
| 句末停顿 | 420-780ms | 0 |
| 思维停顿 | 4% 概率 600-1400ms | 0 |
| 笔误纠正 | 0.5-1.5% 概率 | 0 |
| 双手交替 | 同手 +20ms, 异手 -10ms | 0 |
| 爆发模式 | 3-7 字符连打→短停顿 | 恒定 |

键盘风控（Keystroke Dynamics）会分析 7-15 维时序特征。

### 真人化关键点

#### 1. 基础延迟高斯分布
```python
base = gauss(μ=142ms, σ=38ms)
base = max(40, min(400, base))   # 裁剪防止异常
```

#### 2. 爆发-停顿模式（Burst-Boundary）
真人常 3-7 个字符**快速连打**，然后短暂停顿重新定位手指：
```python
burst_remaining = randint(3, 7)
while typing:
    if burst_remaining == 0:
        sleep(burst_boundary_ms)   # 140-260ms
        burst_remaining = randint(3, 7)
    else:
        sleep(burst_inter_ms)      # 50-95ms（爆发内快速）
        burst_remaining -= 1
```

#### 3. 思维停顿
每字符 4% 概率触发 600-1400ms 长停顿，模拟"思考下一个词"：
```python
if random() < 0.04:
    sleep(randint(600, 1400))
    prev_key = None   # 思维停顿后重置上下文
```

#### 4. 笔误 + 退格纠正
真人打字约 0.5-1.5% 字符会打错，然后立即退格重打：
```python
if random() < 0.006:   # 0.6% 笔误
    typo_key = random.choice("qwertyuiopasdfghjklzxcvbnm")
    type(typo_key)
    sleep(60-180ms)    # 意识到打错
    type("Backspace")
```

#### 5. 双手交替
英文键盘按 QWERTY 划分左右手，同手键比异手键延迟略高（手指移动更远）：
```python
left_hand = "qwertasdfgzxcvb"
right_hand = "yuiopghjklnm"

if prev_hand == curr_hand:
    delay += randint(15, 35)   # 同手 +20ms
elif prev_hand != curr_hand:
    delay -= randint(5, 15)    # 异手 -10ms
```

#### 6. 标点/句末/段落特殊停顿
- `,` `;` `:` → 280-480ms
- `.` `!` `?` → 420-780ms（句末更长）
- ` ` 词边界 → 80-220ms

---

## 三、CDP 集成要点

### 1. session_id 必填
`Input.dispatchMouseEvent` / `Input.dispatchKeyEvent` 必须带 `sessionId: <tab_id>` 才能命中具体 tab（CDP 支持多 tab 并发）：

```python
await cdp.send("Input.dispatchMouseEvent", {
    "type": "mouseMoved", "x": jx, "y": jy
}, session_id=tab_id)
```

### 2. keyDown text="" 硬规则
`Input.dispatchKeyEvent` `text=""` 是 MANDATORY in keyDown when followed by char event. With text set, React double-counts and you get "用用33句句话话". This is the #1 reason hardcore_type fails silently.

正确三段式：
```python
# 1. keyDown, text="" (空字符串)
{"type": "keyDown", "text": "", "key": ch}
# 2. char, text=ch (实际写入)
{"type": "char", "text": ch}
# 3. keyUp
{"type": "keyUp", "key": ch}
```

### 3. Shift 真实时序
大写字母需要先按 Shift、键入、再释放 Shift：
```python
send_keyDown(Shift)
sleep(20-50ms)        # Shift 按下到目标键的延迟
send_keyDown(ch, text="")
send_char(ch)
send_keyUp(ch)
sleep(20-50ms)
send_keyUp(Shift)
```

### 4. 特殊键 (Backspace/Enter/Tab)
走 keyDown/keyUp 而非 char 事件，用 `windowsVirtualKeyCode`：
- Backspace: 8
- Enter: 13
- Tab: 9

---

## 四、风控对抗验证

| 风控采集维度 | 真人化方案 | 效果 |
|--------------|------------|------|
| Mouse Tracking (轨迹) | cos-S 贝塞尔 + 双控制点偏移 | ✅ 物理曲线 |
| Mouse Velocity (速度) | cos-S 速度曲线 (二阶导数连续) | ✅ 物理加速 |
| Mouse Overshoot (过冲) | 18% 概率触发 + 8 步修正 | ✅ 真人冲过头 |
| Keystroke Dynamics (键间延迟) | 高斯 μ=142 σ=38 | ✅ 自然方差 |
| Burst Patterns (爆发模式) | 3-7 字符连打 + burst boundary | ✅ 真人节奏 |
| Thinking Pauses (思维停顿) | 4% 概率 600-1400ms | ✅ 人类特征 |
| Typo Recovery (笔误纠正) | 0.6% 概率 + 退格 | ✅ 自然现象 |
| Hand Alternation (手交替) | 同手+20ms / 异手-10ms | ✅ 物理约束 |

---

## 五、参考实现

完整代码在 `~/.hermes/scripts/hermes_human_biometrics.py`：

```python
from hermes_human_biometrics import (
    human_click,    # 贝塞尔+过冲+悬停+按下
    human_type,     # 生物识别打字
    human_pause,    # 随机停顿
    human_thinking_pause,  # 长思维停顿
    human_quick_pause,     # 短反应停顿
    BezierConfig,   # 贝塞尔配置（可调）
    TypingBiometrics,  # 打字配置（可调）
)
```

**自测**：`python3 ~/.hermes/scripts/hermes_human_biometrics.py` 输出贝塞尔曲线 + 速度曲线 + 打字计划 + 估算 WPM。
