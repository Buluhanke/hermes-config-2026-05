---
name: humanization-engine
description: "行为拟人 鼠标轨迹停顿节奏过反机器人检测。Use when 自动化被风控识别为机器人"
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

### 1. 贝塞尔鼠标轨迹

```python
import random
import math

def bezier_mouse_trace(start: tuple, end: tuple, duration: float = 0.5) -> list:
    """
    生成贝塞尔曲线鼠标轨迹
    从起点到终点，经过随机控制点，模拟人类手部移动
    """
    # 控制点：在起点和终点之间随机偏移
    mid_x = (start[0] + end[0]) / 2 + random.uniform(-100, 100)
    mid_y = (start[1] + end[1]) / 2 + random.uniform(-100, 100)
    
    # 第二控制点：偏上或偏下
    cp2_x = start[0] + random.uniform(0.3, 0.7) * (end[0] - start[0])
    cp2_y = end[1] + random.uniform(-80, -20)
    
    # 生成轨迹点
    points = []
    steps = int(duration * 60)  # 60fps
    for t in [i / steps for i in range(steps + 1)]:
        # 三次贝塞尔公式
        t2 = t * t
        t3 = t2 * t
        mt = 1 - t
        mt2 = mt * mt
        mt3 = mt2 * mt
        
        x = mt3 * start[0] + 3 * mt2 * t * mid_x + 3 * mt * t2 * cp2_x + t3 * end[0]
        y = mt3 * start[1] + 3 * mt2 * t * mid_y + 3 * mt * t2 * cp2_y + t3 * end[1]
        
        points.append((round(x), round(y)))
    
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

- [ ] 鼠标轨迹是曲线而非直线
- [ ] 点击间隔有随机变化
- [ ] 滚动有停顿模拟阅读
- [ ] 打字速度有变化
- [ ] 点击位置有随机偏移
- [ ] 行为序列不可预测
- [ ] 平台检测不触发captcha

---

## 5 阶段定位（2026-06-25 补）

按 `agent-human-level-computer-use` umbrella 5 阶段模型，本 skill 是 **阶段 3 → 4 突破的关键**:

| 阶段 | 本 skill 角色 |
|---|---|
| 1 RPA | 不涉及（无决策） |
| 2 工具调用 Agent | 不涉及（不操作 GUI） |
| **3 GUI 操作 Agent** | **基础能力**：能 click/type/scroll |
| **4 类人自适应 Agent** | **本 skill 核心**：模拟人类操作节律+停顿+轨迹+认知负载 |
| 5 真人级 | 必须配合 `web-agent-os` 的 StateEmbedding + GoalController |

**屏幕图灵测试贡献**：
- 鼠标轨迹加减速 → 通过"看光标判断 AI/真人"
- 认知负载影响速度 → 通过"打字/点击速度变化"判断
- 双峰延迟 → 通过"反应时间有快有慢"判断
- hesitation 停顿 → 通过"操作间停顿"判断

**配合 skill**：
- `web-agent-os` — StateEmbedding 跨页面泛化
- `agent-human-level-computer-use` — 5 阶段总纲
- `macos-computer-use` — 底层键鼠接口
