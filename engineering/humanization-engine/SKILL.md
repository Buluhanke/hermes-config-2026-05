---
name: humanization-engine
description: 行为拟人化引擎 — 模拟人类的操作节奏、鼠标轨迹、停顿模式，突破反机器人检测。
triggers:
  - "在1688、微信、QQ等平台操作"
  - "需要绕过反爬/反机器人检测"
  - "需要模拟真实用户行为"
  - "操作频率需要更自然"
---

# Humanization Engine

## ⚠️ Implementation Status (2026-05-13) — UPDATED

**2026-05-13: Python模块已创建并验证可导入。**

实际文件（`~/.hermes/skills/engineering/humanization_engine/`）：
- `mouse.py` — `generate_human_trajectory()`, `get_speed_factor()`, `set_cognitive_load()`, `Point` type
- `keyboard.py` — `type_text()`, 依赖 mouse.py 的 `cognitive_load`
- `__init__.py` — 统一导出

**使用方式：**
```python
import sys
sys.path.insert(0, "/Users/aimac/.hermes/skills/engineering")
from humanization_engine import generate_human_trajectory, set_cognitive_load

traj = generate_human_trajectory((100, 100), (500, 300), cognitive_load=1.0)
# 返回 List[Point] — 需通过 CDP Input.dispatchMouseEvent 逐点发送
```

**CDP执行层整合状态：待完成。**
当前CDP执行路径：`browser_click() → _run_browser_command() → agent-browser CLI → CDP`
agent-browser CLI 内部处理鼠标移动，无法直接从Python层注入贝塞尔曲线。
整合方案：用 `browser_cdp()` 发送 `Input.dispatchMouseEvent` 绕过CLI（需要tab_id）。
详见 `references/engineering-integration-path-2026-05-13.md`

**知识获取铁律（2026-05-13）：**
- 事实类信息默认联网搜索，模型知识只是参考。
- 遇到不熟悉的领域，直接搜索，不要依赖模型记忆。
- 1688价格、供应商、行业动态——凡是不确定的，先搜再答。

---

## ⚡ 今日可用：human-click（轻量级替代）

**如果只需要"随机偏移点击 + 视觉等待"，不需要贝塞尔轨迹/打字节奏等全部功能，**
**使用今天创建的 `human-click` skill（`procurement/human-click`）：**

```python
# 轻量方案：直接可用，无需CDP整合
from skills.human_click.references.random_click import click_with_offset
from skills.human_click.references.visual_wait import wait_for_stable

# 随机偏移点击（高斯分布）
click_with_offset(cdp_client, bbox=(100, 200, 300, 350), randomize=True)

# 视觉等待稳定
wait_for_stable(screenshot_func=lambda: cdp.screenshot(), region=(100,200,300,350), timeout=10)
```

**`humanization-engine`** 的范围：贝塞尔鼠标轨迹 + 打字节奏 + 滚动模拟 + 完整拟人化策略。
**`human-click`** 的范围：随机偏移点击 + 视觉等待。两技能互补，human-click 是"今天能上"的子集。

---

## Overview

1688、微信、QQ、1688这些平台有严格的反机器人检测：
- 检测鼠标轨迹（直线=机器）
- 检测操作节奏（固定间隔=机器）
- 检测停顿模式（无阅读时间=机器）
- 检测滚动行为（匀速=机器）

**Humanization Engine让Hermes的操作看起来像真人，而不是脚本。**

核心模块：
- 贝塞尔鼠标轨迹（随机曲线而非直线）
- 操作节奏随机化（非固定间隔）
- 阅读时间模拟（滚动时停顿）
- 打字节奏模拟（不匀速）
- 点击区域随机偏移（不总点中心）

## When to Use

- 任何在1688/微信/QQ上的操作
- 任何可能被反爬的平台
- 任何需要模拟真实用户的场景
- 登录态需要保持不被检测

## 核心算法

### 1. 贝塞尔鼠标轨迹（增强版）

```python
import random
import math

def normalvariate_float(mu: float, sigma: float) -> float:
    """Box-Muller变换：从均匀分布生成正态分布随机数"""
    u1 = random.random()
    u2 = random.random()
    z = math.sqrt(-2.0 * math.log(u1)) * math.cos(2.0 * math.pi * u2)
    return mu + sigma * z

def bezier_mouse_trace(start: tuple, end: tuple, duration: float = 0.5,
                       curve_intensity: float = 1.0) -> list:
    """
    生成贝塞尔曲线鼠标轨迹（增强版）

    人类移动特征：
    - 移动时间服从正态分布（μ=目标时间，σ=50ms）
    - 速度曲线：启动慢 → 加速 → 接近目标时减速（手腕在目标前减速）
    - 路径有轻微抖动（人手不是完全稳定的）
    - 方向改变时有圆弧过渡（不是尖角）

    Args:
        start: (x, y) 起点
        end: (x, y) 终点
        duration: 基础移动时间（秒），实际时间从正态分布采样
        curve_intensity: 0-1，曲线强度（0=直线，1=大弧度）
    """
    # 正态分布采样实际移动时间（人类移动时间有随机性）
    actual_duration = max(0.15, normalvariate_float(duration, 0.05))
    steps = max(8, int(actual_duration * 60))  # 60fps

    # 控制点：用正态分布生成偏移，而非均匀分布
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    distance = math.hypot(dx, dy)

    # 主控制点：在路径中点附近，正态分布偏移
    mid_x = start[0] + dx * 0.5 + normalvariate_float(0, distance * 0.25 * curve_intensity)
    mid_y = start[1] + dy * 0.5 + normalvariate_float(0, distance * 0.25 * curve_intensity)

    # 第二控制点：控制弧度方向
    # 人类移动倾向于在运动方向上产生弧度，而不是垂直偏离
    perp_x = -dy / distance if distance > 0 else 0
    perp_y = dx / distance if distance > 0 else 0
    perp_offset = normalvariate_float(0, distance * 0.2 * curve_intensity)
    cp2_x = start[0] + dx * random.uniform(0.3, 0.7) + perp_x * perp_offset
    cp2_y = start[1] + dy * random.uniform(0.3, 0.7) + perp_y * perp_offset

    # 人类速度曲线：启动加速 → 峰值 → 接近目标减速
    def human_speed_curve(t: float) -> float:
        """返回0-1之间的速度因子，人类在t=0.5时最快"""
        # 用正弦函数模拟：v = sin(t * π)，启动和结束慢
        raw = math.sin(t * math.pi)
        # 加一点随机性（不是完美对称）
        jitter = normalvariate_float(1.0, 0.1)
        return max(0.1, min(1.5, raw * jitter))

    points = []
    accumulated_distance = 0.0

    for i in range(steps + 1):
        t = i / steps

        # 三次贝塞尔公式
        mt = 1 - t
        mt2 = mt * mt
        mt3 = mt2 * mt
        t2 = t * t
        t3 = t2 * t

        x = mt3 * start[0] + 3 * mt2 * t * mid_x + 3 * mt * t2 * cp2_x + t3 * end[0]
        y = mt3 * start[1] + 3 * mt2 * t * mid_y + 3 * mt * t2 * cp2_y + t3 * end[1]

        # 添加微小抖动（人手不稳定）
        jitter_x = normalvariate_float(0, 1.5) if i > 0 else 0
        jitter_y = normalvariate_float(0, 1.5) if i > 0 else 0

        px = round(x + jitter_x)
        py = round(y + jitter_y)

        if i > 0:
            # 累积距离用于速度控制（实际速度由帧间隔控制）
            prev = points[-1]
            accumulated_distance += math.hypot(px - prev[0], py - prev[1])

        points.append((px, py))

    return points
```

### 2. 操作节奏随机化

```python
import random
import time

class HumanRhythm:
    """人类操作节奏模拟"""
    
    def __init__(self):
        self.base_delays = {
            'tiny': (0.05, 0.15),      # 微小操作后
            'small': (0.2, 0.5),       # 小操作后
            'medium': (0.5, 1.5),       # 中等操作后
            'large': (1.0, 3.0),        # 大操作后
            'reading': (2.0, 5.0),      # 阅读页面时
            'typing': (0.05, 0.15),     # 每个字符
        }
    
    def delay_after(self, operation_type: str) -> float:
        """返回操作后的随机延迟"""
        min_d, max_d = self.base_delays.get(operation_type, (0.2, 0.5))
        # 添加随机抖动
        return random.uniform(min_d, max_d)
    
    def think_pause(self) -> float:
        """思考停顿：人类在决定前会有随机停顿"""
        return random.uniform(0.5, 2.0)
    
    def scroll_pause(self) -> float:
        """滚动停顿：滚动时偶尔停顿模拟阅读"""
        if random.random() < 0.3:  # 30%概率停顿
            return random.uniform(0.5, 2.0)
        return 0
```

### 3. 点击区域随机偏移

```python
def human_click_point(element_bounds: tuple) -> tuple:
    """
    人类不会每次都精准点击元素中心
    随机偏移模拟人类的不精确性
    """
    x1, y1, x2, y2 = element_bounds
    width = x2 - x1
    height = y2 - y1
    
    # 中心点
    cx = (x1 + x2) / 2
    cy = (y1 + y2) / 2
    
    # 随机偏移：通常在中心，偶有偏离
    # 70%概率在中心区域，30%概率在边缘
    if random.random() < 0.7:
        # 中心区域（半径50%内）
        offset_x = random.uniform(-width * 0.25, width * 0.25)
        offset_y = random.uniform(-height * 0.25, height * 0.25)
    else:
        # 边缘区域
        offset_x = random.uniform(-width * 0.45, width * 0.45)
        offset_y = random.uniform(-height * 0.45, height * 0.45)
    
    return (round(cx + offset_x), round(cy + offset_y))
```

### 4. 打字节奏模拟

```python
def human_typing_rhythm(text: str) -> list:
    """
    模拟人类打字节奏
    不是匀速打字，而是有快有慢，偶尔停顿
    """
    import random
    
    events = []  # [(time, action), ...]
    current_time = 0
    
    for char in text:
        # 基础延迟：每个字符
        base_delay = random.uniform(0.05, 0.12)
        
        # 添加变异性：有些字符快，有些慢
        if char in 'aeiou':  # 元音稍慢
            base_delay *= random.uniform(1.1, 1.4)
        elif char in 'tshn':  # 常用辅音稍快
            base_delay *= random.uniform(0.7, 0.9)
        
        # 随机停顿：打错后回退
        if random.random() < 0.02:  # 2%概率"打错"
            events.append((current_time, ('backspace',)))
            current_time += random.uniform(0.1, 0.2)
        
        events.append((current_time, ('type', char)))
        current_time += base_delay
    
    return events
```

### 5. 滚动行为模拟

```python
def human_scroll(start_y: int, end_y: int, page_height: int) -> list:
    """
    模拟人类滚动：不是匀速，而是分段的
    每次滚动后会停顿，模拟阅读
    """
    import random
    
    scroll_events = []
    current_pos = start_y
    total_distance = end_y - start_y
    
    while abs(current_pos - end_y) > 20:
        # 每次滚动的距离：随机，不是固定的
        scroll_amount = random.choice([200, 300, 400, -200, -100])  # 可以回滚
        
        # 限制在页面范围内
        scroll_amount = max(-current_pos, min(scroll_amount, page_height - current_pos))
        
        scroll_events.append(('scroll', scroll_amount))
        current_pos += scroll_amount
        
        # 滚动后停顿：模拟阅读
        if random.random() < 0.7:  # 70%概率停顿
            pause = random.uniform(0.3, 1.5)
            scroll_events.append(('pause', pause))
        
        # 偶有"回到顶部"行为
        if random.random() < 0.05:
            scroll_events.append(('scroll_to', 0))
    
    return scroll_events
```

### 6. 打字节奏正态分布

```python
import random
import math

def normalvariate_float(mu: float, sigma: float) -> float:
    """Box-Muller变换：从均匀分布生成正态分布随机数"""
    u1 = random.random()
    u2 = random.random()
    z = math.sqrt(-2.0 * math.log(u1)) * math.cos(2.0 * math.pi * u2)
    return mu + sigma * z

class HumanTypingRhythm:
    """
    人类打字节奏 — 基于正态分布
    真人打字不是均匀的，有快有慢，符合正态分布：
    - 大部分字符在"平均速度"附近（68%概率在μ±σ内）
    - 偶尔极快（手指惯性），偶尔极慢（思考或按错）
    - 手腕/手指移动有惯性，打完一串后会加速
    """

    def __init__(self, base_delay: float = 0.09, sigma: float = 0.035):
        self.base_delay = base_delay      # 均值 ms
        self.sigma = sigma                 # 标准差 — 越大越不规律
        # 按键特征：不同键有不同的"手感"延迟
        self.key_ease = {
            'a': 0.85, 's': 0.88, 'd': 0.90, 'f': 0.92, 'g': 0.93,
            'h': 0.93, 'j': 0.92, 'k': 0.88, 'l': 0.85,
            'q': 0.75, 'w': 0.80, 'e': 0.85, 'r': 0.88, 't': 0.82,
            'y': 0.82, 'u': 0.88, 'i': 0.90, 'o': 0.85, 'p': 0.78,
            ' ': 0.55,  # 空格明显更快
        }

    def get_char_delay(self, char: str, prev_char: str = None) -> float:
        """计算单个字符的击键延迟（秒）"""
        # 正态分布采样
        delay = normalvariate_float(self.base_delay, self.sigma)
        delay = max(0.02, min(0.25, delay))  # 裁剪到合理范围

        # 键位难度系数
        ease = self.key_ease.get(char.lower(), 1.0)
        delay /= ease

        # 连击加速：连续相同手指/动作后加速（惯性效应）
        if prev_char and char.lower() == prev_char.lower():
            delay *= random.uniform(0.6, 0.8)  # 快约20-40%

        # 换行/回车有额外停顿
        if char in '\n\r':
            delay += normalvariate_float(0.15, 0.05)

        # 大写字母（需要Shift）明显更慢
        if char.isupper() and char.isalpha():
            delay += normalvariate_float(0.08, 0.03)

        return delay

    def generate_typing_events(self, text: str) -> list:
        """
        生成完整打字序列：[(time_offset, action, char_or_key), ...]
        action: 'type' | 'backspace' | 'pause'
        """
        events = []
        current_time = 0.0
        prev_char = None

        for i, char in enumerate(text):
            # 随机回退（打错）— 概率与内容无关，纯拟人
            if random.random() < 0.015:  # 1.5% 打错率
                # 回退前停顿（发现自己打错了）
                events.append((current_time, 'pause', normalvariate_float(0.08, 0.03)))
                current_time += normalvariate_float(0.08, 0.03)
                events.append((current_time, 'backspace', None))
                current_time += normalvariate_float(0.06, 0.02)
                prev_char = None  # 重置

            delay = self.get_char_delay(char, prev_char)
            events.append((current_time, 'type', char))
            current_time += delay
            prev_char = char

            # 词间停顿（换词时多一点点延迟）
            if char in ' \t' and i < len(text) - 1:
                next_char = text[i + 1]
                if next_char not in ' \t\n\r':
                    current_time += normalvariate_float(0.03, 0.015)

        return events
```

### 7. 视觉焦点模拟

```python
import random
import math

class VisualFocusSimulator:
    """
    模拟人类视觉焦点行为：
    - 眼睛不会一直盯着鼠标，有自己的移动路径
    - 视线在"感兴趣区域"停留
    - 鼠标移动通常滞后于视线（先看后点）
    - 偶尔鼠标突然移向视线焦点（协调动作）
    """

    def __init__(self):
        self.gaze_pos = (0, 0)          # 当前视线位置
        self.mouse_pos = (0, 0)          # 当前鼠标位置
        self.focus_targets = []          # 当前页面上的焦点区域列表
        self.last_coordination = 0       # 上次视线-鼠标协调时间

    def set_page_focus_regions(self, regions: list):
        """
        设置页面焦点区域 [(x1, y1, x2, y2, weight), ...]
        weight越高，越容易被注视
        """
        self.focus_targets = regions

    def select_next_gaze_target(self) -> tuple:
        """根据权重随机选择一个视线目标区域中心"""
        if not self.focus_targets:
            return self.mouse_pos  # 回退到鼠标位置
        # 加权随机选择
        total_weight = sum(r[4] for r in self.focus_targets)
        r = random.uniform(0, total_weight)
        cumsum = 0
        for x1, y1, x2, y2, w in self.focus_targets:
            cumsum += w
            if r <= cumsum:
                cx = (x1 + x2) / 2 + random.uniform(-(x2-x1)*0.2, (x2-x1)*0.2)
                cy = (y1 + y2) / 2 + random.uniform(-(y2-y1)*0.2, (y2-y1)*0.2)
                return (round(cx), round(cy))
        return self.focus_targets[-1][:2]

    def gaze_dwell(self) -> float:
        """视线停留在当前焦点的时长（秒）"""
        return normalvariate_float(1.2, 0.6)  # μ=1.2s, σ=0.6s

    def move_gaze_to(self, target: tuple, duration: float = None):
        """移动视线，带有平滑的眼动轨迹"""
        if duration is None:
            duration = math.hypot(target[0]-self.gaze_pos[0], target[1]-self.gaze_pos[1]) / 150
            duration = max(0.05, min(0.3, duration))

        steps = max(3, int(duration * 60))
        for t in range(steps + 1):
            progress = t / steps
            # 眼动有"saccade"特征：开始快，接近目标时减速
            eased = math.sin(progress * math.pi / 2)
            gx = self.gaze_pos[0] + (target[0] - self.gaze_pos[0]) * eased
            gy = self.gaze_pos[1] + (target[1] - self.gaze_pos[1]) * eased
            yield (round(gx), round(gy))
        self.gaze_pos = target

    def sync_mouse_to_gaze(self, intensity: float = 0.3):
        """
        鼠标向视线方向轻微移动（协调性）
        intensity: 0-1，越高鼠标越贴近视线
        """
        dx = (self.gaze_pos[0] - self.mouse_pos[0]) * intensity
        dy = (self.gaze_pos[1] - self.mouse_pos[1]) * intensity
        # 加一点随机偏移，不要100%协调
        dx += random.uniform(-20, 20)
        dy += random.uniform(-20, 20)
        new_x = round(self.mouse_pos[0] + dx)
        new_y = round(self.mouse_pos[1] + dy)
        self.mouse_pos = (new_x, new_y)
        return self.mouse_pos
```

### 8. 操作犹豫与自我纠正机制

```python
import random
import time

class HesitationAndCorrection:
    """
    模拟人类的"犹豫-决策-执行-纠正"行为链：

    犹豫阶段：人类在点击/操作前会有停顿，长短不一
    决策时间：取决于操作的重要性（重要=更长犹豫）
    自我纠正：人类犯错后会停顿、再纠正，而不是立刻重做

    核心行为：
    - Hover停留（犹豫要点击哪里）
    - 点击前犹豫（最后关头取消或改变目标）
    - 点击后微调（点了后发现不对，短暂停顿后纠正）
    - 滚回重新看（纠正策略前先回顾）
    """

    def __init__(self):
        self.last_action_was_error = False  # 标记上次操作是否出错
        self.hover_start_time = None
        self.hover_target = None

    def pre_click_hesitation(self, element_importance: str = 'normal') -> float:
        """
        点击前的犹豫时间
        element_importance: 'low' | 'normal' | 'high' | 'critical'
        """
        hesitation_map = {
            'low':      (0.05, 0.20),   # 不重要，随便点
            'normal':   (0.15, 0.50),   # 普通操作
            'high':     (0.40, 1.20),   # 重要按钮
            'critical': (0.80, 2.50),   # 危险操作（删除、支付）
        }
        mn, mx = hesitation_map[element_importance]
        return random.uniform(mn, mx)

    def hover_then_move(self, from_pos: tuple, to_pos: tuple) -> list:
        """
        鼠标悬停后移动：先hover到元素边缘，犹豫，再移动到目标
        返回事件序列
        """
        events = []

        # 悬停开始：在起点稍作停留
        events.append(('hover_start', from_pos, random.uniform(0.1, 0.3)))

        # 悬停期间的微小抖动（模拟人类手的不稳定）
        hover_during = random.uniform(0.3, 1.2)
        jitter_count = int(hover_during / 0.05)
        for _ in range(jitter_count):
            jitter = (random.uniform(-3, 3), random.uniform(-3, 3))
            pos = (from_pos[0] + jitter[0], from_pos[1] + jitter[1])
            events.append(('jitter', pos, 0.05))
            # 视线跟随
            events.append(('gaze_follow', pos, 0))

        # 犹豫：是否继续移动？
        if random.random() < 0.15:  # 15%概率"犹豫后放弃"
            events.append(('abort', None, random.uniform(0.5, 1.5)))
            return events

        # 视线提前移到目标（眼睛先到）
        events.append(('gaze_advance', to_pos, random.uniform(0.1, 0.25)))

        # 最后关头改变目标（5%概率）
        if random.random() < 0.05:
            # 随机轻微偏移目标
            offset = (random.uniform(-15, 15), random.uniform(-15, 15))
            to_pos = (to_pos[0] + offset[0], to_pos[1] + offset[1])
            events.append(('target_adjusted', to_pos, 0))

        # 犹豫后执行
        hesitation = self.pre_click_hesitation()
        events.append(('move_to', to_pos, hesitation))

        return events

    def post_click_microcorrection(self, click_pos: tuple, element_bounds: tuple) -> tuple:
        """
        点击后发现不对，需要微调/纠正
        人类不会立刻"撤销"，而是停顿后用小动作修正
        返回修正后的目标位置
        """
        if not self.last_action_was_error:
            return None  # 无需纠正

        # 停顿（发现错了）
        correction_pause = random.uniform(0.3, 1.0)

        # 微调：从错误位置到正确位置的短距离移动
        x1, y1, x2, y2 = element_bounds
        cx = (x1 + x2) / 2
        cy = (y1 + y2) / 2

        # 移动方向：从click_pos向center的向量
        dx = cx - click_pos[0]
        dy = cy - click_pos[1]
        dist = math.hypot(dx, dy)

        if dist < 5:
            return None  # 已经足够近，无需纠正

        # 只纠正一部分（不会100%精准）
        correction_ratio = random.uniform(0.5, 0.9)
        new_x = round(click_pos[0] + dx * correction_ratio)
        new_y = round(click_pos[1] + dy * correction_ratio)

        return (correction_pause, (new_x, new_y))

    def strategy_reconsideration(self, context: dict) -> float:
        """
        操作失败后的"重新思考"停顿
        人类犯错后会停下来想一想，而不是立即重试
        """
        # 停顿时间与失败次数正相关
        fail_count = context.get('consecutive_fails', 1)
        base = normalvariate_float(1.5, 0.8)
        return min(base * math.sqrt(fail_count), 5.0)  # 最多5秒

    def should_abort_and_retry(self, fail_count: int) -> bool:
        """
        判断是否应该放弃当前策略（换一种方式）
        连续失败3+次后，人类会怀疑"方法错了"
        """
        if fail_count < 2:
            return False
        # 2次失败：20%概率换策略
        # 3次失败：50%概率换策略
        # 4次+：80%概率换策略
        prob_switch = min(0.2 * fail_count, 0.9)
        return random.random() < prob_switch
```

## Process

### Phase 1: 行为配置

#### 1.1 平台特征
```python
PLATFORM_HUMANIZATION = {
    '1688': {
        'click_delay': (0.3, 1.0),
        'scroll_pause_prob': 0.5,
        'typing_speed': (0.08, 0.15),
        'mouse_curve_intensity': 0.8,
        'max_consecutive_fast_actions': 3
    },
    'weixin': {
        'click_delay': (0.2, 0.5),
        'scroll_pause_prob': 0.3,
        'typing_speed': (0.1, 0.2),
        'mouse_curve_intensity': 0.5,
        'max_consecutive_fast_actions': 5
    },
    'qq': {
        'click_delay': (0.2, 0.6),
        'scroll_pause_prob': 0.4,
        'typing_speed': (0.08, 0.18),
        'mouse_curve_intensity': 0.6,
        'max_consecutive_fast_actions': 4
    }
}
```

#### 1.2 全局配置
```python
HUMANIZATION_CONFIG = {
    'enabled': True,
    'platform': 'auto',  # auto检测或指定
    'aggression': 'normal',  # 'light' | 'normal' | 'aggressive'
    'fail_safe': True,  # 连续失败时降级
    'mouse_curve': True,
    'random_delays': True,
    'human_scroll': True,
    'human_typing': True
}
```

### Phase 2: 执行时的Humanization包装

#### 2.1 鼠标轨迹包装
```python
def humanized_move_to(element, config=HUMANIZATION_CONFIG):
    if not config['mouse_curve']:
        return element.click()
    
    # 获取当前位置和目标位置
    current_pos = get_mouse_position()
    target_pos = human_click_point(element.bounds)
    
    # 生成贝塞尔轨迹
    duration = random.uniform(0.3, 0.8)
    trace = bezier_mouse_trace(current_pos, target_pos, duration)
    
    # 沿轨迹移动
    for point in trace:
        move_mouse_to(point)
        # 每帧之间加延迟，模拟真实速度
        sleep(duration / len(trace))
    
    # 最后点击
    human_click_point(element.bounds)
```

#### 2.2 延迟包装
```python
def humanized_delay(operation_type: str, config=HUMANIZATION_CONFIG):
    if not config['random_delays']:
        return
    
    rhythm = HumanRhythm()
    delay = rhythm.delay_after(operation_type)
    sleep(delay)
```

### Phase 3: 行为序列生成

#### 3.1 完整用户行为模拟
```python
def generate_human_behavior_sequence(task: str) -> list:
    """
    把一个任务分解成拟人化的行为序列
    """
    if task == '1688_login':
        return [
            ('open_page', 'https://login.1688.com'),
            ('think', None),  # 停顿思考
            ('scroll', 300), ('pause', 1.0),  # 滚动看页面
            ('type', 'username'), ('pause', 0.5),
            ('click', 'password_field'),
            ('type', 'password'), ('pause', 0.5),
            ('click', 'login_button'),
            ('wait_for', 'page_load')
        ]
    elif task == 'send_qq_message':
        return [
            ('click', 'message_input'),
            ('pause', 0.3),
            ('human_type', 'message_content'),
            ('pause', 0.5),
            ('click', 'send_button')
        ]
```

### Phase 4: 异常检测

#### 4.1 检测是否被风控
```python
def detect_anti_bot_trap(indicators: list) -> bool:
    """
    检测是否触发反机器人机制
    """
    if 'captcha' in indicators:
        return True
    if 'login_required' in indicators and not was_logged_out():
        return True  # 突然要求登录 = 被检测
    if 'access_denied' in indicators:
        return True
    return False
```

## Common Rationalizations

| 常见借口 | 真相 | 反制 |
|---------|------|------|
| "快点操作效率高" | 快速操作必然被检测 | 使用Humanization降速 |
| "Playwright默认速度就够了" | 默认速度仍被检测为机器 | 加随机延迟和轨迹 |
| "只操作一次不需要拟人化" | 单次操作也可能被标记 | 始终使用拟人化 |
| "平台不严格，不需要" | 平台越来越严格 | 始终保持最低风险 |

## External Anti-Detection Tools

Beyond behavioral simulation (mouse curves, typing rhythm), two categories of **external tools** complement the Humanization Engine:

### Layer A: Browser Fingerprint Evasion

**Camoufox** (a Firefox fork) — pre-hardens browser fingerprints so websites see a "normal" browser:
- Spoofs Canvas/WebGL/WebRTC fingerprints
- Rotates user-agent, timezone, language
- Handles `navigator.webdriver` flag
- Integrated via `camoufox-js` package (Playwright-compatible)

**Pitfalls (macOS 26.4.1+, discovered 2026-05-12):**
- Camoufox binary v135.0.1-beta.24 (Mar 2025) **hangs on launch** on macOS 26.4.1 — process starts but never connects Playwright pipe (180s timeout). Incompatible binary.
- Fresh download via `npx camoufox-js fetch` requires **GitHub connectivity** (github.com:443). If GitHub is unreachable, installation stalls.
- Cache dir: `~/Library/Caches/camoufox/` (expected by camoufox-js)
- Old binary may exist at `~/.camoufox/` (older version, same compatibility risk)

### Layer B: OS-Level Input Simulation

**Peekaboo** (`@steipete/peekaboo`) — simulates real mouse/keyboard at macOS OS level, not through browser API:
- Commands: `peekaboo see / click / type / agent / image`
- Bypasses `navigator.webdriver` and Playwright detection because it uses macOS Accessibility API
- Requires: Screen Recording, Accessibility, Event Synthesizing permissions

**Install (preferred):** `npm install -g @steipete/peekaboo`
- Homebrew (`brew install steipete/tap/peekaboo`) may **time out** repeatedly — use npm global install instead
- **⚠️ 授权未完成（2026-05-13）**：安装成功但 `peekaboo permissions grant` 从未执行，实际运行会失败
- Verify: `peekaboo permissions status` (should show all Granted)
- To authorize: `peekaboo permissions grant`

### Decision Matrix

| Scenario | Recommended Tool |
|----------|-----------------|
| Browser fingerprint not important, simple form fill | Humanization Engine (Playwright + curves) |
| Strict fingerprint checking (Cloudflare, banks) | Camoufox + Humanization Engine |
| Browser can't be automated (detects Playwright) | Peekaboo (OS-level click) |
| macOS 26.4.1 + Camoufox binary hangs | Fall back to Humanization Engine + Peekaboo |
| **Today** — need random offset click + visual wait, 半天上线 | **`human-click` skill** (无CDP整合依赖) |

## Red Flags

- 鼠标移动是直线
- 点击间隔完全相同
- 滚动是匀速的
- 打字速度恒定
- 从不停顿阅读
- 总是精准点击元素中心
- 操作时间完全可预测

## Human vs Machine Behavior Comparison

| 维度 | 机器/脚本特征 | 真人特征 | 对应拟真机制 |
|------|------------|---------|------------|
| **鼠标轨迹** | | | |
| 移动方式 | 直线、瞬间到达 | 曲线、有加速减速 | 贝塞尔曲线轨迹 |
| 速度 | 匀速 | 先快后慢，接近目标时减速 | 速度曲线（非线性插值） |
| 路径 | 最短直线 | 绕远、有弧度 | 控制点随机偏移 |
| **点击行为** | | | |
| 点击位置 | 精准中心 | 随机偏移（中心+边缘） | `human_click_point()` 高斯偏移 |
| 点击前 | 无犹豫、直接点击 | 犹豫 0.1-2.5s | `pre_click_hesitation()` |
| 点击后 | 立刻下一步 | 偶尔停顿、可能纠正 | 微调机制 |
| **打字节奏** | | | |
| 速度 | 固定 WPM | 波动±30%，正态分布 | `HumanTypingRhythm` |
| 按键间隔 | 几乎相同 | 元音慢、辅音快、空格极快 | 键位难度系数 |
| 错误率 | 0% | ~1.5% 自然打错 | 随机 backspace |
| **视线/鼠标协调** | | | |
| 鼠标与视线 | 无关 | 视线先于鼠标 100-300ms | `VisualFocusSimulator` |
| 视线停留 | 无规律 | 焦点区域停留 0.5-2s | `gaze_dwell()` |
| 协调性 | 0% | 30-50% 协调 | `sync_mouse_to_gaze()` |
| **操作节奏** | | | |
| 间隔 | 固定、极短 | 随机 0.2-3s | `HumanRhythm` |
| 连续操作 | 无限制 | 3-5次后必停 | `max_consecutive_fast_actions` |
| 阅读停顿 | 0 | 30-50% 概率滚动停顿 | `scroll_pause()` |
| **操作决策** | | | |
| 失败后 | 立刻重试 | 停顿思考、可能换策略 | `strategy_reconsideration()` |
| 放弃概率 | 0 | 随失败次数增加 | `should_abort_and_retry()` |
| 悬停 | 无 | 0.3-1.2s 悬停后移动 | `hover_then_move()` |
| **滚动行为** | | | |
| 滚动量 | 固定 | 随机 200-400px | `human_scroll()` |
| 回滚 | 从不 | 5% 概率偶发回滚 | `random.choice()` |
| 匀速 | 是 | 分段+停顿 | 分段滚动+随机停顿 |

### 时序对比示例

**机器操作时序（反检测特征）：**
```
t=0.000: mouseMove(100,100) → (500,300)  [直线，瞬间]
t=0.000: mousePressed @ (500,300)
t=0.000: mouseReleased @ (500,300)
t=0.050: keyDown 'a'
t=0.050: keyUp 'a'
t=0.100: keyDown 'b'
t=0.100: keyUp 'b'
t=0.150: keyDown 'c'
t=0.150: keyUp 'c'
```

**真人操作时序（拟真输出）：**
```
t=0.000: mouseMove(100,100) → curve through (250,180) → (490,285) [贝塞尔, 620ms]
t=0.620: pause (hesitation) 0.38s  [犹豫是否点击]
t=0.998: mousePressed @ (487,291)   [偏移，非中心]
t=1.050: mouseReleased @ (487,291)
t=1.200: pause 0.2s
t=1.400: keyDown 'a' [~95ms，实际节奏]
t=1.495: keyUp 'a'
t=1.560: pause 0.065s
t=1.625: keyDown 'b'
t=1.718: keyUp 'b'
t=1.850: pause (word transition) 0.03s
t=1.880: keyDown 'c'
t=1.965: keyUp 'c'
t=2.100: scroll [-300px] + pause 0.8s  [阅读停顿]
t=2.900: scroll [-200px]
```

### 检测阈值参考

| 检测维度 | 机器阈值（会触发） | 安全范围 |
|---------|-----------------|---------|
| 鼠标速度 | < 50px/s 或 > 3000px/s | 200-1500px/s |
| 轨迹曲率 | < 5° 偏离直线 | > 15° 偏离 |
| 点击间隔标准差 | < 50ms | > 100ms |
| 连续操作上限 | 10+ 次无缝操作 | 3-5 次后停 |
| 滚动停顿率 | < 10% | > 30% |

## Integration Path (CDP Execution Layer)

### 目标文件
`~/.hermes/hermes-agent/gateway/core/cdp_client.py` — `def click()` 方法

### 整合三处
1. **humanization-engine → CDP执行层**
   - 当前：`def click(self, x, y)` 直接发送 `mousePressed/mouseReleased`（跳跃式）
   - 目标：调用贝塞尔轨迹生成，用 `Input.dispatchMouseEvent` 逐点移动后再点击
   - 需先实现 `skills/engineer/humanization_engine/mouse.py` 导出 `move_with_bezier(start, end) → list[(x,y), ...]`

2. **resilience-engine → browser worker主循环**
   - 当前：`execute_operation()` 无保护
   - 目标：在 `BrowserWorker` 初始化时注入 `Watchdog`，执行时包 `self.watchdog.protect()`
   - 需先实现 `skills/engineer/resilience_engine/watchdog.py`

3. **desktop-consciousness → Hermes session**
   - 当前：`HermesSession` 无状态追踪
   - 目标：集成 `SessionState` + `MemoryLayer`，在 `execute_step()` 前后调用 `record_action()`
   - 需先实现 `skills/engineer/desktop_consciousness/session_state.py`

### Adapter模式（如果技能输出格式不匹配CDP接口）
```python
def adapt_trajectory_to_cdp(bezier_points):
    """将贝塞尔轨迹点转为CDP mouseMoved事件格式"""
    return [{"type": "mouseMoved", "x": p[0], "y": p[1]} for p in bezier_points]
```

### 验证方法
1. 观察实际鼠标轨迹是否产生曲线（非直线跳跃）
2. 检查日志是否有 Watchdog 记录
3. 检查 `session.history` 是否记录每步操作

## Verification

验证清单：

- [ ] 鼠标轨迹是曲线而非直线（贝塞尔，有速度曲线）
- [ ] 鼠标轨迹时间正态分布（非固定duration）
- [ ] 点击间隔有随机变化
- [ ] 滚动有停顿模拟阅读
- [ ] 打字速度是正态分布（不均匀，有快有慢）
- [ ] 打字有1.5%自然打错率（backspace）
- [ ] 点击位置有随机偏移
- [ ] 视觉焦点模拟：视线先于鼠标移动
- [ ] 操作犹豫：点击前有0.1-2.5s停顿
- [ ] 操作纠正：失败后有停顿思考，不会立刻重试
- [ ] 行为序列不可预测
- [ ] 平台检测不触发captcha
- [ ] Human vs Machine对比：机器特征（直线/均匀间隔/无犹豫）全部消除
