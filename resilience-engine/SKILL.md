---
name: resilience-engine
description: 生存引擎 — 自动恢复能力，处理卡死、白屏、验证码、登录失效等异常，让任务不卡死。
triggers:
  - "任务执行超过30秒无响应"
  - "页面白屏或加载失败"
  - "遇到验证码或风控"
  - "登录态失效"
  - "网络断开"
  - "任何可能导致任务卡死的情况"
---

## Implementation Status (2026-05-13) — UPDATED

**2026-05-13: Python模块已创建并验证可导入。**

实际文件（`~/.hermes/skills/engineering/resilience_engine/`）：
- `watchdog.py` — `Watchdog`, `RecoveryStrategy`, `CircuitState`, `get_watchdog()`
- `__init__.py` — 统一导出

**使用方式：**
```python
import sys
sys.path.insert(0, "/Users/aimac/.hermes/skills/engineering")
from resilience_engine import Watchdog, get_watchdog

wd = get_watchdog()
result = await wd.protect(async_operation_fn, context={"page": page})
```

**核心接口：**
- `Watchdog.protect(operation, context=None)` — 包装需要自愈的操作，支持async/sync
- `RecoveryStrategy` — 6种恢复策略：WAIT_LONGER, RELOCATE, SCROLL, REFRESH, HUMAN_CONFUSION, ESCAPE_HATCH
- `CircuitState` — 熔断器状态：CLOSED / OPEN / HALF_OPEN

**CDP执行层整合：待完成。** 当前 BrowserWorker 无 Watchdog 保护。

---

# Resilience Engine

## 4.5 异常分类决策表（2026-06-25 补）

**自动异常诊断**：遇到错误时，调用 `~/.hermes/scripts/load_common_sense.py auto_diagnose(error_msg)` 拿到匹配的处理建议。

```python
import sys
sys.path.insert(0, "/Users/aimac/.hermes/scripts")
from load_common_sense import CommonSense

cs = CommonSense()
diagnosis = cs.auto_diagnose("Connection refused on port 9222")
# → {"pattern": "CONN_REFUSED", "action": "检查进程/重启服务/换端口", "severity": "error"}
```

**常见异常分类**（按 4.5 章定义）：
| 异常类型 | 检测方法 | 自动恢复动作 |
|---|---|---|
| CONN_REFUSED | 端口扫不到 | 重启服务/换端口 |
| 401 Unauthorized | CDP 401/cookie 失效 | 重新登录态 |
| 验证码/CAPTCHA | 视觉识别 | 调 slide-solver / OCR |
| 任务超时 >30s | watchdog 触发 | 自动 reload / 跳过 |
| OOM | memory_pressure 红 | 降并发/重启 |
| 5xx 网关错 | HTTP 502/503/504 | 重试+指数退避 |

**接入位置**：所有 BrowserWorker.protect() 调用前先 auto_diagnose。

## Overview

人类的行动遇到障碍时，会自动调整策略：
- 门推不开，会拉一下试试
- 验证码出现，会想办法识别
- 登录失效，会重新登录
- 网络断了，会等恢复后重试

**Resilience Engine是Hermes的"生存本能"——遇到异常时不卡死，自动进入恢复流程。**

三层保障：
1. **Watchdog**：超时检测，防止永久卡死
2. **Auto-Recovery**：常见异常自动处理
3. **Escape-Hatch**：无法恢复时安全退出，保留状态

## When to Use

- 任何可能执行超过30秒的任务
- 任何在1688/微信/QQ上的操作
- 任何有网络依赖的操作
- 任何需要登录的操作
- 任何多步骤连续任务

## 架构

```
Watchdog (计时器)
    ↓ 检测到异常
Recovery Strategies (恢复策略库)
    ↓ 可恢复 → 执行恢复 → 重试
    ↓ 不可恢复 → Escape Hatch → 保留状态退出
    ↓ 连续失败 → 人工接管
```

## Process

### Phase 1: Watchdog（防卡死）

#### 1.1 超时检测
```python
class Watchdog:
    def __init__(self, timeout: float = 30.0, check_interval: float = 5.0):
        self.timeout = timeout
        self.check_interval = check_interval
        self.last_activity = now()
        self.baseline_metrics = self._capture_baseline()
    
    def _capture_baseline(self) -> dict:
        """捕获基准状态"""
        return {
            'mouse_position': get_mouse_position(),
            'focused_window': get_focused_window(),
            'page_url': get_current_url(),
            'screen_content_hash': hash_screen()
        }
    
    def check(self) -> WatchdogResult:
        """定期检查是否有进展"""
        current = self._capture_baseline()
        
        # 检测1：鼠标位置没变
        mouse_stuck = (current['mouse_position'] == self.baseline_metrics['mouse_position']
                       and now() - self.last_activity > self.timeout)
        
        # 检测2：页面没变
        page_stuck = (current['page_url'] == self.baseline_metrics['page_url']
                      and current['screen_content_hash'] == self.baseline_metrics['screen_content_hash']
                      and now() - self.last_activity > self.timeout)
        
        # 检测3：窗口失去焦点且长时间无操作
        window_switched = (current['focused_window'] != self.baseline_metrics['focused_window']
                          and now() - self.last_activity > self.timeout * 2)
        
        self.last_activity = now()
        
        if mouse_stuck or page_stuck:
            return WatchdogResult(
                triggered=True,
                reason='no_progress',
                duration=now() - self.last_activity,
                stuck_type='mouse' if mouse_stuck else 'page'
            )
        
        return WatchdogResult(triggered=False)
    
    def reset(self):
        """重置Watchdog（每次有效操作后调用）"""
        self.last_activity = now()
        self.baseline_metrics = self._capture_baseline()
```

#### 1.2 Watchdog触发后的处理
```python
def on_watchdog_triggered(result: WatchdogResult, state: WorldState):
    """Watchdog触发后的处理"""
    
    if result.stuck_type == 'mouse':
        # 鼠标位置没变，可能是点击没生效
        recovery_actions = [
            'click_current_element',  # 重试点击
            'force_refresh_mouse_position',  # 强制刷新鼠标位置
            'try_alternative_element',  # 尝试其他元素
            'scroll_and_retry'  # 滚动后重试
        ]
    
    elif result.stuck_type == 'page':
        # 页面没变化，可能是网络问题或JS没执行
        recovery_actions = [
            'wait_and_check',  # 再等一下
            'refresh_page',  # 刷新页面
            'check_network',  # 检查网络
            'restart_browser_tab'  # 重开标签页
        ]
    
    return execute_recovery_sequence(recovery_actions)
```

### Phase 2: Recovery Strategies（自动恢复策略）

#### 2.1 策略库
```python
RECOVERY_STRATEGIES = {
    # 网络问题
    'network_error': [
        {'action': 'wait', 'duration': 2},
        {'action': 'retry', 'max_attempts': 3, 'backoff': 'exponential'},
        {'action': 'check_proxy'},  # 检查代理是否失效
        {'action': 'switch_network'}
    ],
    
    # 验证码
    'captcha': [
        {'action': 'ocr_solve'},  # 尝试OCR识别
        {'action': 'manual_resolve', 'alert': True},  # 需要人工
        {'action': 'skip_task', 'save_state': True}  # 跳过但保存状态
    ],
    
    # 登录失效
    'login_expired': [
        {'action': 'navigate', 'url': '/login'},
        {'action': 'fill_credentials'},
        {'action': 'login'},
        {'action': 'verify_login'},
        {'action': 'resume_task'}
    ],
    
    # 白屏
    'blank_page': [
        {'action': 'wait', 'duration': 3},
        {'action': 'refresh'},
        {'action': 'check_js_errors'},
        {'action': 'restart_tab'}
    ],
    
    # 弹窗阻塞
    'modal_blocking': [
        {'action': 'dismiss_modal'},
        {'action': 'check_modal_type'},
        {'action': 'handle_according_to_type'}
    ],
    
    # 页面跳转异常
    'unexpected_navigation': [
        {'action': 'log', 'message': '意外跳转'},
        {'action': 'check_if_logged_in'},
        {'action': 'navigate_back_if_needed'},
        {'action': 'alert', 'message': '可能触发了反爬'}
    ],
    
    # 页面加载超时
    'page_load_timeout': [
        {'action': 'check_network'},
        {'action': 'bypass_cache'},
        {'action': 'retry_with_longer_timeout'},
        {'action': 'try_alternative_url'}
    ],
    
    # 元素消失
    'element_disappeared': [
        {'action': 'wait', 'duration': 1},
        {'action': 're_query_element'},
        {'action': 'scroll_to_element'},
        {'action': 'retry_with_new_locator'}
    ]
}
```

#### 2.2 执行恢复序列
```python
def execute_recovery_sequence(actions: list, context: dict) -> RecoveryResult:
    """
    按顺序执行恢复动作
    每个动作执行后检查是否恢复
    """
    attempt = 0
    max_attempts = 5
    
    while attempt < max_attempts:
        for action_spec in actions:
            action = action_spec['action']
            params = {k: v for k, v in action_spec.items() if k != 'action'}
            
            # 执行恢复动作
            result = execute_action(action, params)
            
            # 检查是否恢复
            if check_recovery_success():
                return RecoveryResult(
                    recovered=True,
                    strategy_used=action,
                    attempts=attempt
                )
            
            attempt += 1
            sleep(1)
    
    return RecoveryResult(recovered=False, attempts=attempt)
```

### Phase 3: Escape Hatch（逃生舱）

#### 3.1 安全退出条件
```python
ESCAPE_CONDITIONS = {
    'max_retries_exceeded': 5,
    'critical_error': ['captcha', 'account_locked', 'access_denied'],
    'safety_boundary': ['payment', 'delete_file', 'send_money'],
    'user_abort': True
}
```

#### 3.2 逃生前的状态保存
```python
def safe_escape(task_state: TaskState, reason: str):
    """
    逃生时保存完整状态，供后续恢复
    """
    escape_data = {
        'reason': reason,
        'timestamp': now(),
        'task_state': task_state,
        'world_state': get_current_world_state(),
        'action_history': task_state['history'],
        'retry_count': task_state.get('retry_count', 0),
        'last_successful_step': find_last_successful_step(task_state),
        'resume_instructions': generate_resume_instructions(task_state)
    }
    
    # 保存到文件
    escape_file = f"~/.hermes/escape/{task_state['task_id']}_{now().strftime('%Y%m%d_%H%M%S')}.json"
    write_json(escape_file, escape_data)
    
    return escape_file
```

#### 3.3 逃生后的通知
```python
def escape_notification(escape_data: dict):
    """逃生时通知用户"""
    message = f"""
⚠️ 任务需要人工介入

任务：{escape_data['task_state']['task_name']}
原因：{escape_data['reason']}
进度：{escape_data['task_state']['current_step']}/{escape_data['task_state']['total_steps']}

保存位置：{escape_data['save_file']}
可直接从此状态恢复。
"""
    send_notification(message)
```

### Phase 4: 连续失败检测

#### 4.1 失败模式识别
```python
class FailurePattern:
    def __init__(self):
        self.failure_log = []
        self.pattern_threshold = 3  # 连续3次同类失败
    
    def record(self, failure: Failure):
        self.failure_log.append({
            'type': failure.type,
            'timestamp': now(),
            'context': failure.context
        })
        
        # 清理超过1小时的记录
        self.failure_log = [
            f for f in self.failure_log
            if now() - f['timestamp'] < 3600
        ]
    
    def detect_pattern(self) -> Pattern | None:
        """检测连续失败模式"""
        if len(self.failure_log) < self.pattern_threshold:
            return None
        
        recent = self.failure_log[-self.pattern_threshold:]
        types = [f['type'] for f in recent]
        
        if all(t == types[0] for t in types):
            return Pattern(type=types[0], count=self.pattern_threshold)
        
        return None
```

## Common Rationalizations

| 常见借口 | 真相 | 反制 |
|---------|------|------|
| "网络慢等一下就行" | 无限等待是卡死的根源 | Watchdog强制检测 |
| "重试3次还失败就放弃" | 重试策略需要更智能 | 检测失败模式决定策略 |
| "失败了就重新开始" | 任务状态是宝贵的 | 逃生时必须保存状态 |
| "偶尔失败没关系" | 连续失败说明有系统问题 | 模式识别触发警报 |

## Red Flags

- 任务执行超过5分钟无结果
- 连续3次相同类型的失败
- 突然跳转到意外页面
- 验证码出现但继续执行
- 登录态失效但继续操作
- 页面白屏但继续等待
- 网络错误但无限重试

## Verification

验证清单：

- [ ] Watchdog在30秒无进展时触发
- [ ] 每种异常类型有对应恢复策略
- [ ] 逃生时状态完整保存
- [ ] 连续失败被检测和告警
- [ ] 恢复后能从断点继续
- [ ] 人工接管时有完整上下文
