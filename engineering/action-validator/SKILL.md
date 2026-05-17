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

## 新增验证层（扩展）

---

## 6. 截图 SSIM 验证

### 6.1 概念

Structural Similarity Index (SSIM) 是比像素diff更智能的图像相似度算法，比RGB差值更接近人类视觉感知。适用于：
- 页面整体外观变化检测
- UI元素位置/状态变化的视觉确认
- 无法用DOM/AX表达的视觉反馈（如动画、图表渲染）

### 6.2 SSIM 实现

```python
import cv2
import numpy as np

def compute_ssim(img1_path: str, img2_path: str, win_size: int = 7) -> float:
    """
    计算SSIM相似度
    返回: 0.0(完全不同) ~ 1.0(完全相同)
    阈值: >0.95 认为相似, <0.90 认为差异明显
    """
    img1 = cv2.imread(img1_path, cv2.IMREAD_GRAYSCALE)
    img2 = cv2.imread(img2_path, cv2.IMREAD_GRAYSCALE)
    
    # 调整大小一致
    if img1.shape != img2.shape:
        img2 = cv2.resize(img2, (img1.shape[1], img1.shape[0]))
    
    C1 = (0.01 * 255) ** 2
    C2 = (0.03 * 255) ** 2
    
    mu1 = cv2.GaussianBlur(img1.astype(float), (win_size, win_size), 1.5)
    mu2 = cv2.GaussianBlur(img2.astype(float), (win_size, win_size), 1.5)
    mu1_sq = mu1 ** 2
    mu2_sq = mu2 ** 2
    mu1_mu2 = mu1 * mu2
    
    sigma1_sq = cv2.GaussianBlur(img1.astype(float)**2, (win_size, win_size), 1.5) - mu1_sq
    sigma2_sq = cv2.GaussianBlur(img2.astype(float)**2, (win_size, win_size), 1.5) - mu2_sq
    sigma12 = cv2.GaussianBlur(img1.astype(float)*img2.astype(float), (win_size, win_size), 1.5) - mu1_mu2
    
    ssim_map = ((2*mu1_mu2+C1)*(2*sigma12+C2)) / ((mu1_sq+mu2_sq+C1)*(sigma1_sq+sigma2_sq+C2))
    return float(np.mean(ssim_map))

def verify_ssim(before_path: str, after_path: str, threshold: float = 0.95) -> dict:
    score = compute_ssim(before_path, after_path)
    return {
        'ssim_score': round(score, 4),
        'passed': score >= threshold,
        'threshold': threshold,
        'diff': 'similar' if score >= threshold else ('marginal' if score >= 0.90 else 'different')
    }
```

### 6.3 区域SSIM（关注特定区域）

```python
def ssim_region(img1_path: str, img2_path: str, bbox: tuple[int,int,int,int], threshold: float = 0.95) -> dict:
    """
    bbox: (x1, y1, x2, y2) 感兴趣区域
    仅比较指定区域的SSIM
    """
    img1 = cv2.imread(img1_path)
    img2 = cv2.imread(img2_path)
    x1, y1, x2, y2 = bbox
    
    roi1 = img1[y1:y2, x1:x2]
    roi2 = img2[y1:y2, x1:x2]
    
    # 扩大区域再resize
    if roi1.shape != roi2.shape:
        roi2 = cv2.resize(roi2, (roi1.shape[1], roi1.shape[0]))
    
    score = compute_ssim_from_arrays(roi1, roi2)
    return {'ssim_score': round(score, 4), 'passed': score >= threshold, 'region': bbox}

def compute_ssim_from_arrays(img1: np.ndarray, img2: np.ndarray) -> float:
    """直接从numpy数组计算SSIM"""
    if len(img1.shape) == 3:
        img1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    if len(img2.shape) == 3:
        img2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
    
    C1, C2, win_size = (0.01*255)**2, (0.03*255)**2, 7
    
    mu1 = cv2.GaussianBlur(img1.astype(float), (win_size, win_size), 1.5)
    mu2 = cv2.GaussianBlur(img2.astype(float), (win_size, win_size), 1.5)
    mu1_sq, mu2_sq, mu1_mu2 = mu1**2, mu2**2, mu1*mu2
    sigma1_sq = cv2.GaussianBlur(img1.astype(float)**2, (win_size, win_size), 1.5) - mu1_sq
    sigma2_sq = cv2.GaussianBlur(img2.astype(float)**2, (win_size, win_size), 1.5) - mu2_sq
    sigma12 = cv2.GaussianBlur(img1.astype(float)*img2.astype(float), (win_size, win_size), 1.5) - mu1_mu2
    
    ssim_map = ((2*mu1_mu2+C1)*(2*sigma12+C2)) / ((mu1_sq+mu2_sq+C1)*(sigma1_sq+sigma2_sq+C2))
    return float(np.mean(ssim_map))
```

### 6.4 截图SSIM验证流程

```python
def snapshot_ssim_before(state: WorldState) -> str:
    """执行前截图"""
    screenshot = take_screenshot()
    path = f"/tmp/ssim_before_{now_ts()}.png"
    cv2.imwrite(path, screenshot)
    return path

def verify_ssim_after(before_path: str, after_path: str, region: tuple = None, threshold: float = 0.95) -> dict:
    """执行后SSIM验证"""
    if region:
        return ssim_region(before_path, after_path, region, threshold)
    return verify_ssim(before_path, after_path, threshold)

# 集成到主验证流程
def verify_action_ssim(action: Action, state: WorldState) -> VerificationResult:
    before_path = snapshot_ssim_before(state)
    execute_action(action)
    wait_for_stable()
    after_path = take_screenshot()
    
    result = verify_ssim_after(before_path, after_path, threshold=0.95)
    return VerificationResult(
        passed=result['passed'],
        check='ssim_verification',
        details=result
    )
```

---

## 7. API 响应验证

### 7.1 概念

直接验证后端API响应，而不仅依赖前端UI变化。适用于：
- 提交表单后验证数据是否真正写入
- 搜索后验证结果是否正确
- 状态变更后验证后端状态

### 7.2 API 响应拦截与验证

```python
import json
import re
from dataclasses import dataclass
from typing import Any

@dataclass
class APIExpectation:
    method: str  # GET/POST/PUT/DELETE
    url_pattern: str  # URL正则或精确匹配
    status_code: int  # 预期状态码
    response_contains: dict | list | str | None  # 响应体应包含的内容
    response_not_contains: dict | None  # 响应体不应包含的内容
    latency_max_ms: float | None  # 最大响应时间

class APIVerifier:
    def __init__(self, network_capture):
        self.capture = network_capture
        self.expectations: list[APIExpectation] = []
    
    def register(self, expectation: APIExpectation):
        self.expectations.append(expectation)
    
    def verify(self, captured_requests: list[dict]) -> VerificationResult:
        failures = []
        
        for exp in self.expectations:
            matched = self._find_matching_request(exp, captured_requests)
            if not matched:
                failures.append(f"No request matched: {exp.method} {exp.url_pattern}")
                continue
            
            # 检查状态码
            if matched['status'] != exp.status_code:
                failures.append(f"Status {matched['status']} != {exp.status_code} for {exp.url_pattern}")
            
            # 检查响应内容
            body = matched.get('response_body', {})
            if exp.response_contains:
                missing = self._find_missing(exp.response_contains, body)
                if missing:
                    failures.append(f"Missing in response: {missing}")
            
            if exp.response_not_contains:
                found = self._find_present(exp.response_not_contains, body)
                if found:
                    failures.append(f"Should not contain but found: {found}")
            
            # 检查延迟
            if exp.latency_max_ms and matched.get('latency_ms', 0) > exp.latency_max_ms:
                failures.append(f"Latency {matched['latency_ms']}ms > {exp.latency_max_ms}ms")
        
        return VerificationResult(passed=len(failures) == 0, failed_checks=failures)
    
    def _find_matching_request(self, exp: APIExpectation, requests: list[dict]) -> dict | None:
        for req in requests:
            if req['method'] != exp.method:
                continue
            if re.match(exp.url_pattern, req['url']):
                return req
        return None
    
    def _find_missing(self, expected: Any, actual: Any, path: str = "") -> list[str]:
        """递归检查expected是否都在actual中"""
        missing = []
        if isinstance(expected, dict):
            for k, v in expected.items():
                if k not in actual:
                    missing.append(f"{path}.{k}")
                else:
                    missing.extend(self._find_missing(v, actual[k], f"{path}.{k}"))
        elif isinstance(expected, list):
            for i, item in enumerate(expected):
                if item not in actual:
                    missing.append(f"{path}[{i}]")
        elif expected != actual:
            missing.append(f"{path} = {actual}, expected {expected}")
        return missing
    
    def _find_present(self, unwanted: Any, actual: Any, path: str = "") -> list[str]:
        """递归检查unwanted是否出现在actual中"""
        found = []
        if isinstance(unwanted, dict):
            for k, v in unwanted.items():
                if k in actual:
                    found.extend(self._find_present(v, actual[k], f"{path}.{k}"))
        elif isinstance(unwanted, list):
            for item in unwanted:
                if item in actual:
                    found.append(f"{path} contains {item}")
        elif unwanted in actual:
            found.append(f"{path} = {actual}")
        return found
```

### 7.3 常用API验证模式

```python
# 场景1: 验证POST创建成功
def expect_create(url: str, created_object: dict):
    return APIExpectation(
        method='POST',
        url_pattern=url,
        status_code=201,
        response_contains={'id': created_object['id']}
    )

# 场景2: 验证列表查询返回正确数据
def expect_list(url: str, expected_items: int, item_pattern: dict):
    return APIExpectation(
        method='GET',
        url_pattern=url,
        status_code=200,
        response_contains={'total': expected_items, 'items': [item_pattern]}
    )

# 场景3: 验证更新操作
def expect_update(url: str, updated_fields: dict):
    return APIExpectation(
        method='PUT',
        url_pattern=url,
        status_code=200,
        response_contains=updated_fields
    )

# 场景4: 验证删除操作
def expect_delete(url: str):
    return APIExpectation(
        method='DELETE',
        url_pattern=url,
        status_code=204,
        response_contains=None
    )
```

### 7.4 集成到验证流程

```python
def verify_api_response(action: Action, state: WorldState) -> VerificationResult:
    """
    启动网络捕获 -> 执行动作 -> 停止捕获 -> 验证API响应
    """
    verifier = APIVerifier(None)
    
    # 根据动作类型注册预期
    if action.type == 'submit':
        verifier.register(expect_create('/api/items', action.data))
    elif action.type == 'search':
        verifier.register(expect_list('/api/search', expected_items=5))
    
    # 启动捕获
    start_capture()
    
    # 执行
    execute_action(action)
    wait_for_network_idle()
    
    # 获取并验证
    captured = stop_capture()
    return verifier.verify(captured)
```

---

## 8. 数据库状态验证

### 8.1 概念

直接查询数据库验证数据是否正确写入/修改/删除。适用于：
- 表单提交后验证数据持久化
- 批量操作后验证所有记录
- 状态机转换后验证状态字段

### 8.2 数据库验证器

```python
import sqlite3
import mysql.connector
from abc import ABC, abstractmethod
from typing import Any
from dataclasses import dataclass

@dataclass
class DBExpectation:
    query: str  # SQL查询
    expected_rows: int | None  # 预期行数
    expected_first_row: dict | None  # 预期第一行数据
    expected_pattern: dict | None  # 预期所有行匹配的模式
    timeout_seconds: float = 5.0

class DatabaseVerifier(ABC):
    @abstractmethod
    def connect(self): pass
    
    @abstractmethod
    def execute(self, query: str) -> list[dict]: pass
    
    def verify(self, expectations: list[DBExpectation]) -> VerificationResult:
        failures = []
        self.connect()
        
        for exp in expectations:
            try:
                rows = self.execute(exp.query)
                
                if exp.expected_rows is not None and len(rows) != exp.expected_rows:
                    failures.append(f"Row count {len(rows)} != {exp.expected_rows}")
                
                if exp.expected_first_row and rows:
                    for k, v in exp.expected_first_row.items():
                        if rows[0].get(k) != v:
                            failures.append(f"First row '{k}': {rows[0].get(k)} != {v}")
                
                if exp.expected_pattern and rows:
                    for row in rows:
                        for k, v in exp.expected_pattern.items():
                            if row.get(k) != v:
                                failures.append(f"Pattern mismatch at row {row}: '{k}' != {v}")
                
                if exp.timeout_seconds and self.last_query_time > exp.timeout_seconds:
                    failures.append(f"Query timeout: {self.last_query_time:.2f}s > {exp.timeout_seconds}s")
                    
            except Exception as e:
                failures.append(f"Query error: {e}")
        
        self.disconnect()
        return VerificationResult(passed=len(failures) == 0, failed_checks=failures)

class SQLiteVerifier(DatabaseVerifier):
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None
        self.last_query_time = 0
    
    def connect(self):
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
    
    def disconnect(self):
        if self.conn:
            self.conn.close()
    
    def execute(self, query: str) -> list[dict]:
        import time
        start = time.time()
        cursor = self.conn.cursor()
        cursor.execute(query)
        rows = [dict(row) for row in cursor.fetchall()]
        self.last_query_time = time.time() - start
        return rows

class MySQLVerifier(DatabaseVerifier):
    def __init__(self, host: str, port: int, user: str, password: str, database: str):
        self.config = {'host': host, 'port': port, 'user': user, 'password': password, 'database': database}
        self.conn = None
        self.last_query_time = 0
    
    def connect(self):
        self.conn = mysql.connector.connect(**self.config)
    
    def disconnect(self):
        if self.conn:
            self.conn.close()
    
    def execute(self, query: str) -> list[dict]:
        import time
        start = time.time()
        cursor = self.conn.cursor(dictionary=True)
        cursor.execute(query)
        rows = cursor.fetchall()
        self.last_query_time = time.time() - start
        return rows
```

### 8.3 常用数据库验证模式

```python
# 场景1: 验证记录创建
def expect_record_created(table: str, record: dict, db: DatabaseVerifier):
    conditions = ' AND '.join([f"{k} = '{v}'" for k, v in record.items()])
    return DBExpectation(
        query=f"SELECT * FROM {table} WHERE {conditions}",
        expected_rows=1,
        expected_first_row=record
    )

# 场景2: 验证记录存在（用于检测是否重复创建）
def expect_record_not_duplicated(table: str, unique_fields: dict, db: DatabaseVerifier):
    conditions = ' AND '.join([f"{k} = '{v}'" for k, v in unique_fields.items()])
    return DBExpectation(
        query=f"SELECT COUNT(*) as cnt FROM {table} WHERE {conditions}",
        expected_rows=1,
        expected_first_row={'cnt': 1}
    )

# 场景3: 验证计数
def expect_count(table: str, where_clause: str, expected_count: int):
    return DBExpectation(
        query=f"SELECT COUNT(*) as cnt FROM {table} WHERE {where_clause}",
        expected_rows=1,
        expected_first_row={'cnt': expected_count}
    )

# 场景4: 验证状态转换
def expect_state(table: str, record_id: Any, expected_state: str, db: DatabaseVerifier):
    return DBExpectation(
        query=f"SELECT state FROM {table} WHERE id = '{record_id}'",
        expected_rows=1,
        expected_first_row={'state': expected_state}
    )

# 场景5: 验证记录删除
def expect_record_deleted(table: str, record_id: Any):
    return DBExpectation(
        query=f"SELECT * FROM {table} WHERE id = '{record_id}'",
        expected_rows=0
    )
```

### 8.4 集成到验证流程

```python
def verify_database_state(action: Action, state: WorldState) -> VerificationResult:
    """
    执行动作 -> 等待 -> 查询数据库 -> 验证
    """
    db_verifier = SQLiteVerifier('/path/to/app.db')
    expectations = []
    
    if action.type == 'submit':
        expectations.append(expect_record_created('items', action.data, db_verifier))
    elif action.type == 'delete':
        expectations.append(expect_record_deleted('items', action.target_id))
    elif action.type == 'update_status':
        expectations.append(expect_state('tasks', action.target_id, action.new_status))
    
    execute_action(action)
    sleep(0.5)  # 等待事务提交
    
    return db_verifier.verify(expectations)
```

---

## 9. 跨系统数据一致性验证

### 9.1 概念

验证数据在多个系统间的一致性。适用于：
- 同步场景：主系统操作 -> 验证从系统同步
- 缓存场景：更新数据库 -> 验证缓存更新
- 派生数据：源头更新 -> 验证聚合/汇总计算正确

### 9.2 一致性验证框架

```python
from typing import Any
from dataclasses import dataclass, field
from enum import Enum

class ConsistencyLevel(Enum):
    STRICT      # 严格相等
    APPROXIMATE # 允许数值误差（如金额舍入）
    CONTAINS    # A包含B的关键字段
    TIMEOUT     # 最终一致（有延迟上限）

@dataclass
class ConsistencyRule:
    source: str  # 来源系统标识
    targets: list[str]  # 目标系统列表
    extract_key: str  # 用于匹配的字段名
    compare_fields: list[str]  # 需要比较的字段
    level: ConsistencyLevel
    tolerance: dict[str, float] | None = None  # 字段容差: {field: max_error}
    max_delay_ms: float = 5000  # 最终一致超时

@dataclass  
class SystemQuery:
    system: str
    query: str | dict  # SQL或API或任何查询方式
    transform: callable | None = None  # 结果转换函数

class ConsistencyVerifier:
    def __init__(self):
        self.rules: list[ConsistencyRule] = []
        self.system_queries: dict[str, callable] = {}  # system -> query function
    
    def register_system(self, name: str, query_fn: callable):
        """注册系统查询函数"""
        self.system_queries[name] = query_fn
    
    def register_rule(self, rule: ConsistencyRule):
        self.rules.append(rule)
    
    def verify_all(self) -> VerificationResult:
        failures = []
        
        for rule in self.rules:
            try:
                # 从每个系统查询数据
                results = {}
                for sys_name in [rule.source] + rule.targets:
                    if sys_name not in self.system_queries:
                        failures.append(f"System not registered: {sys_name}")
                        continue
                    results[sys_name] = self._query_system(sys_name, rule.extract_key, rule.compare_fields)
                
                # 两两比对
                source_data = results.get(rule.source, {})
                for target in rule.targets:
                    target_data = results.get(target, {})
                    diff = self._compare(source_data, target_data, rule)
                    if diff:
                        failures.append(f"Inconsistency {rule.source} -> {target}: {diff}")
                        
            except Exception as e:
                failures.append(f"Consistency check error: {e}")
        
        return VerificationResult(passed=len(failures) == 0, failed_checks=failures)
    
    def _query_system(self, system: str, key_field: str, fields: list[str]) -> dict:
        """查询系统并提取所需字段"""
        raw = self.system_queries[system]()
        # 简化：假设返回dict或dict列表
        if isinstance(raw, list):
            return {r[key_field]: {f: r.get(f) for f in fields} for r in raw}
        return {raw[key_field]: {f: raw.get(f) for f in fields}}
    
    def _compare(self, source: dict, target: dict, rule: ConsistencyRule) -> list[str]:
        """比较两个系统的数据，返回差异列表"""
        diffs = []
        
        for key, src_val in source.items():
            if key not in target:
                diffs.append(f"Key {key} missing in target")
                continue
            
            tgt_val = target[key]
            
            for field in rule.compare_fields:
                src = src_val.get(field)
                tgt = tgt_val.get(field)
                
                if rule.level == ConsistencyLevel.STRICT:
                    if src != tgt:
                        diffs.append(f"{key}.{field}: {src} != {tgt}")
                
                elif rule.level == ConsistencyLevel.APPROXIMATE:
                    tolerance = (rule.tolerance or {}).get(field, 0)
                    try:
                        if abs(float(src) - float(tgt)) > tolerance:
                            diffs.append(f"{key}.{field}: {src} vs {tgt} (diff > {tolerance})")
                    except (TypeError, ValueError):
                        if src != tgt:
                            diffs.append(f"{key}.{field}: {src} != {tgt}")
                
                elif rule.level == ConsistencyLevel.CONTAINS:
                    for k, v in src.items():
                        if k not in tgt or tgt[k] != v:
                            diffs.append(f"{key}.{k}: {v} not in target")
        
        return diffs
```

### 9.3 常用一致性验证场景

```python
# 场景1: 数据库与缓存一致
def verify_cache_consistency(verifier: ConsistencyVerifier):
    verifier.register_system('db', lambda: db.query("SELECT id, name, price FROM products"))
    verifier.register_system('cache', lambda: redis.hgetall('products:*'))
    
    verifier.register_rule(ConsistencyRule(
        source='db',
        targets=['cache'],
        extract_key='id',
        compare_fields=['name', 'price'],
        level=ConsistencyLevel.STRICT
    ))

# 场景2: 主系统与只读副本一致
def verify_replica_consistency(verifier: ConsistencyVerifier, table: str):
    verifier.register_system('primary', lambda: primary_db.query(f"SELECT * FROM {table}"))
    verifier.register_system('replica', lambda: replica_db.query(f"SELECT * FROM {table}"))
    
    verifier.register_rule(ConsistencyRule(
        source='primary',
        targets=['replica'],
        extract_key='id',
        compare_fields=['*'],  # 所有字段
        level=ConsistencyLevel.STRICT
    ))

# 场景3: 订单金额与支付金额一致
def verify_order_payment_consistency(verifier: ConsistencyVerifier):
    verifier.register_system('orders', lambda: db.query("SELECT order_id, total_amount FROM orders"))
    verifier.register_system('payments', lambda: db.query("SELECT order_id, amount FROM payments"))
    
    verifier.register_rule(ConsistencyRule(
        source='orders',
        targets=['payments'],
        extract_key='order_id',
        compare_fields=['total_amount', 'amount'],
        level=ConsistencyLevel.CONTAINS  # payments.amount <= orders.total_amount
    ))

# 场景4: 库存与销售系统一致
def verify_inventory_sales_consistency(verifier: ConsistencyVerifier):
    verifier.register_system('inventory', lambda:erp.query("SELECT sku, quantity FROM inventory"))
    verifier.register_system('sales', lambda: crm.query("SELECT sku, SUM(quantity) FROM sales GROUP BY sku"))
    
    verifier.register_rule(ConsistencyRule(
        source='inventory',
        targets=['sales'],
        extract_key='sku',
        compare_fields=['quantity'],
        level=ConsistencyLevel.APPROXIMATE,
        tolerance={'quantity': 1}  # 允许1件误差
    ))

# 场景5: 时间序列数据最终一致（允许延迟）
def verify_eventual_consistency(verifier: ConsistencyVerifier):
    verifier.register_system('source', lambda: kafka.get_latest_offsets())
    verifier.register_system('sink', lambda: warehouse.get_latest_offsets())
    
    verifier.register_rule(ConsistencyRule(
        source='source',
        targets=['sink'],
        extract_key='topic',
        compare_fields=['offset'],
        level=ConsistencyLevel.TIMEOUT,
        max_delay_ms=10000
    ))
```

### 9.4 集成到验证流程

```python
def verify_cross_system(action: Action, state: WorldState) -> VerificationResult:
    """
    执行跨系统一致性验证
    """
    verifier = ConsistencyVerifier()
    
    # 根据动作类型设置验证
    if action.type == 'sync':
        verify_cache_consistency(verifier)
    elif action.type == 'payment':
        verify_order_payment_consistency(verifier)
    
    execute_action(action)
    sleep(1.0)  # 等待同步完成
    
    return verifier.verify_all()
```

---

## 验证清单

- [ ] 每次点击后有DOM/AX变化检测
- [ ] 每次填写后有值验证
- [ ] 页面跳转有URL验证
- [ ] 提交操作有防重机制
- [ ] 失败有分类和策略
- [ ] 连续失败>3次进入逃生
- [ ] 所有验证结果可追溯
- [ ] SSIM验证集成（截图差异检测）
- [ ] API响应验证（网络层断言）
- [ ] 数据库状态验证（持久化确认）
- [ ] 跨系统一致性验证（多源数据校验）
