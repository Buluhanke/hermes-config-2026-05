---
name: action-validator
description: 动作验证层 — 每次操作后验证是否真正生效，防止假执行。包含DOM变化检测、截图diff、AX树diff、URL变化检测。
triggers:
  - "点击操作后验证是否成功"
  - "填写表单后验证值是否写入"
  - "页面跳转后验证目标是否正确"
  - "任何可能静默失败的场景"
  - "防止重复提交"
---

# Action Validator

## Overview

人类执行动作后，会自然地观察结果：
- 点完按钮，看页面有没有变化
- 发完消息，看对方有没有收到
- 填完表单，看提交是否成功

**现在Hermes的核心问题：`click(element)` 之后默认 success，这是错的。**

Action Validator在每次操作后执行多维度验证：
- DOM变化了吗？
- AX树变化了吗？
- 截图有差异吗？
- URL变了吗？
- toast/error出现了吗？

只有验证通过，才认为动作成功。否则进入重试或逃生流程。

## When to Use

- 任何点击操作
- 任何表单填写操作
- 任何页面跳转操作
- 任何可能静默失败的场景
- 连续操作前的确认

## 验证架构

```
Action → Execute → Wait → Observe → Verify → Pass/Fail
                                      ↓
                              Fail → Retry/Escape/Alert
```

## Process

### Phase 1: 执行前快照

#### 1.1 记录执行前状态
```python
def snapshot_before(state: WorldState, action: Action) -> Snapshot:
    return {
        'url': get_current_url(),
        'dom_hash': hash_dom(),
        'ax_tree_hash': hash_ax_tree(),
        'screenshot': take_screenshot(),
        'focused_element': get_focused(),
        'timestamp': now()
    }
```

#### 1.2 设定预期结果
```python
def expected_after(action: Action) -> ExpectedResult:
    if action.type == 'click':
        return {
            'type': 'one_of',
            'conditions': [
                {'check': 'url_changed', 'expected': True},
                {'check': 'dom_changed', 'expected': True},
                {'check': 'modal_appeared', 'expected': False}  # 不应该有错误弹窗
            ]
        }
    elif action.type == 'fill':
        return {
            'type': 'all_of',
            'conditions': [
                {'check': 'field_value', 'expected': action.value},
                {'check': 'no_error', 'expected': True}
            ]
        }
    elif action.type == 'submit':
        return {
            'type': 'sequence',
            'steps': [
                {'check': 'loading_appeared'},
                {'check': 'loading_disappeared'},
                {'check': 'success_indicator'}
            ]
        }
```

### Phase 2: 执行后观察

#### 2.1 等待合理时间
```python
def wait_for_stable(max_wait: float = 5.0) -> None:
    """
    等待页面稳定：
    1. 没有新的网络请求（networkidle）
    2. 没有动画/过渡
    3. 连续两次快照差异小于阈值
    """
    start = now()
    last_dom = None
    stable_count = 0
    
    while (now() - start) < max_wait:
        current_dom = hash_dom()
        if last_dom == current_dom:
            stable_count += 1
            if stable_count >= 3:  # 连续3次相同
                return
        else:
            stable_count = 0
        last_dom = current_dom
        sleep(0.5)
```

#### 2.2 多维度观察
```python
def observe_after(state: WorldState, before: Snapshot) -> Observation:
    return {
        'url': get_current_url(),
        'url_changed': get_current_url() != before['url'],
        'dom_hash': hash_dom(),
        'dom_changed': hash_dom() != before['dom_hash'],
        'ax_tree_hash': hash_ax_tree(),
        'ax_changed': hash_ax_tree() != before['ax_tree_hash'],
        'screenshot_diff': screenshot_diff(before['screenshot'], take_screenshot()),
        'new_elements': detect_new_elements(before),
        'removed_elements': detect_removed_elements(before),
        'error_toast': detect_error_toast(),
        'success_toast': detect_success_toast(),
        'network_errors': get_network_errors()
    }
```

### Phase 3: 验证判定

#### 3.1 验证规则引擎
```python
def verify(action: Action, expected: ExpectedResult, observation: Observation) -> VerificationResult:
    """
    根据预期规则验证实际观察结果
    """
    if expected['type'] == 'one_of':
        # 任一条件满足即可
        satisfied = [check_condition(c, observation) for c in expected['conditions']]
        passed = any(satisfied)
        failed_checks = [c for c, s in zip(expected['conditions'], satisfied) if not s]
    
    elif expected['type'] == 'all_of':
        # 所有条件必须满足
        results = [check_condition(c, observation) for c in expected['conditions']]
        passed = all(results)
        failed_checks = [c for c, r in zip(expected['conditions'], results) if not r]
    
    elif expected['type'] == 'sequence':
        # 按顺序检查
        passed, failed_step = check_sequence(expected['steps'])
        failed_checks = [failed_step] if failed_step else []
    
    return VerificationResult(
        passed=passed,
        failed_checks=failed_checks,
        observation=observation
    )
```

#### 3.2 常见检查类型

| 检查 | 方法 | 阈值 |
|------|------|------|
| url_changed | 对比执行前后URL | exact match |
| dom_changed | DOM结构hash | 任意变化 |
| screenshot_diff | 像素差异 | >1%视为变化 |
| field_value | input.value | exact match |
| text_appeared | 检测特定文本 | 包含匹配 |
| error_toast | 检测.error类元素 | 任意出现=失败 |
| success_toast | 检测.success类元素 | 出现=成功 |
| network_errors | 检测失败的XHR/Fetch | 任何=警告 |

### Phase 4: 失败处理

#### 4.1 失败分类
```python
class VerificationFailure:
    type: "element_not_found" | "false_success" | "error_occurred" | "timeout" | "unexpected_state"
    action: Action
    expected: ExpectedResult
    actual: Observation
    severity: "retry" | "escape" | "alert"
```

#### 4.2 处理策略
```python
def handle_failure(failure: VerificationFailure) -> Action:
    if failure.type == 'element_not_found':
        # 元素消失了，可能是动态加载问题
        return Action('scroll_down') + wait(1.0) + retry(failure.action)
    
    elif failure.type == 'false_success':
        # 点击了但什么都没发生
        return retry(failure.action, strategy='force_refresh')
    
    elif failure.type == 'error_occurred':
        # 出现了错误弹窗
        return Action('dismiss_modal') + alert(failure)
    
    elif failure.type == 'timeout':
        # 页面没响应
        return escape_to('refresh_page')
    
    elif failure.type == 'unexpected_state':
        # 跳到了意外页面
        return alert(f"意外跳转: {get_current_url()}")
```

### Phase 5: 防重复提交

#### 5.1 提交检测
```python
def detect_duplicate_submit(action: Action, state: WorldState) -> bool:
    """
    检测是否重复提交
    """
    last_action = state['task']['last_action']
    
    if last_action and last_action['type'] == 'submit':
        if now() - last_action['timestamp'] < 5.0:
            return True  # 5秒内重复提交
    
    if was_submitted_recently(action.target):
        return True  # 相同目标最近提交过
    
    return False
```

## Common Rationalizations

| 常见借口 | 真相 | 反制 |
|---------|------|------|
| "点都点了，没反应就再点一次" | 盲目重试可能造成重复提交 | 验证后再决定是否重试 |
| "页面没变化就是失败了" | 可能是静默更新（JS改了） | 用DOM hash检测 |
| "看到按钮点了就行" | 按钮可能被遮挡或禁用 | 先验证元素可交互 |
| "网络请求发了就行" | 请求可能失败了 | 验证响应结果 |

## Red Flags

- 点击后不验证结果
- 重试3次以上仍然失败
- 出现error toast但不处理
- 提交按钮可以连点
- 页面跳转不验证目标
- 没有等待页面稳定就继续操作

## Verification

验证清单：

- [ ] 每次点击后有DOM/AX变化检测
- [ ] 每次填写后有值验证
- [ ] 页面跳转有URL验证
- [ ] 提交操作有防重机制
- [ ] 失败有分类和策略
- [ ] 连续失败>3次进入逃生
- [ ] 所有验证结果可追溯
