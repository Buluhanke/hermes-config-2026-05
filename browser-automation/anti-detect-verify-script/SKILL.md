---
name: anti-detect-verify-script
description: |
  验证 Hermes anti-detect 浏览器反指纹是否真的100分。基于 CDP 9333 检查 4 个缺口:
  (1) plugins 指纹补丁 (2) 12 字段反指纹 (3) SelfHealingDriver (4) trajectory_recorder。
  
  触发词: "跑一下 verify_all_3.py" / "测一下反指纹" / "anti-detect 跑分" /
  "verify 100 分" / "browserleaks 验证"。
---

# Anti-Detect 100分验证脚本

## 1. 目标
真实验证 4 个反指纹缺口是否 100/100。不输出硬编码的庆祝文案 — 分数必须真实计算。

## 2. 路径
- 脚本: `/tmp/verify_all_3.py`
- 注入器: `~/.hermes/scripts/anti_detect_inject.py`
- 注入脚本: `~/.hermes/anti_detect.js` + `~/.hermes/anti_detect_plugins.js`

## 3. 跑分流程

### Step 1: 确认浏览器 + 注入
```bash
# 1.1 确认 CDP 9333 在线
curl -s http://127.0.0.1:9333/json | python3 -c "import json,sys; print(len(json.loads(sys.stdin.read())))"

# 1.2 注入到所有 tab (Page.addScriptToEvaluateOnNewDocument)
python3 /Users/aimac/.hermes/scripts/anti_detect_inject.py
# 期望: "1 个 page tab 注入成功" + loaded_in_dom=True
```

### Step 2: 跑验证脚本
```bash
python3 /tmp/verify_all_3.py
```

## 4. 4 个缺口判定标准

| 缺口 | 判定 | 加分 |
|---|---|---|
| 1. plugins | 数量=3, 含 'Native Client', plugins_loaded=True | +3 |
| 2. 12 字段 | 12/12 全 ✓ | (基线, 不加分) |
| 3. SelfHealingDriver | 输出含 "总累计 attempts: 9" | +5 |
| 4. trajectory_recorder | list 输出含 "turns" + "has_video" | +4 |

## 5. 12 字段的精确判定 (坑点!)

### 5.1 注入端不能用 String() 包装
```js
// ❌ 错: String() 包装后 JSON 反序列化成 str, isinstance(int) 全 false
webdriver: String(navigator.webdriver),       // → "undefined" 字符串
hw: String(navigator.hardwareConcurrency),    // → "8" 字符串
has_touch: String('ontouchstart' in window),  // → "false" 字符串

// ✅ 对: 直接传原值
webdriver: navigator.webdriver,               // → undefined → None
hw: navigator.hardwareConcurrency,            // → 8 (int)
has_touch: 'ontouchstart' in window,          // → false (bool)
```

### 5.2 Python 端断言必须宽松
```python
def is_falsy(v):  # webdriver: 接受 None/False/字符串'undefined'
def is_truthy(v):  # chrome 对象: 真实 boolean True
def is_positive_number(v):  # hw/mem: 数字>0 或 字符串可转>0
def is_bool(v):  # touchstart: 真实 boolean
def is_valid_platform(v):  # MacIntel/Win32/Linux x86_64
def is_valid_langs(v):  # list 且 len>=1
def is_realistic_plugins(count):  # 1<=count<=4
def is_valid_notification(v):  # 'default'/'granted'/'denied'
```

## 6. 总分行不要硬编码
```python
# ❌ 错: 无论 12 字段实际命中几个, 都打印 ✅ 12/12
print("缺口 2 (12 字段): ✅ 12/12 稳定命中 (基线)")

# ✅ 对: 基于 ok2_count 真实反映
print(f"缺口 2 (12 字段): {'✅ 12/12' if ok2 else f'⚠️ {ok2_count}/12'}")
```

## 7. 已知坑

1. **CDP 端口**: 必须是 9333 (本地调试 Chrome), 不是默认 9222
2. **页面未加载完时跑**: 可能命中 0/12, 必须等 `__anti_detect_loaded__=True`
3. **navigate 新页后**: 不需要重跑 inject, `addScriptToEvaluateOnNewDocument` 自动生效
4. **JSON.stringify 跳过 undefined**: `navigator.webdriver` 是 undefined 时, 字段会从输出里消失, 用 `v2.get('webdriver')` 而不是 `v2['webdriver']`

## 8. 验证脚本自身的常见 bug (2026-06-05 实战踩出)

**修任何 verify 脚本前, 先检查这 4 个坑**:

### 8.1 不要用 `String()` 包装 boolean/number
```js
// ❌ 错: String(undefined) → "undefined" 字符串, JSON 反序列化后 isinstance(int) 全 false
webdriver: String(navigator.webdriver),
hw: String(navigator.hardwareConcurrency),

// ✅ 对: 直接传原值, Python 端做宽松类型判断
webdriver: navigator.webdriver,  // → None
hw: navigator.hardwareConcurrency,  // → int
```

### 8.2 不要用 Python `hash()` 做跨进程 key
```python
# ❌ 错: hash() 每次进程启动值不同 (PYTHONHASHSEED)
key = str(hash(some_string))

# ✅ 对: 用 sha256
import hashlib
key = hashlib.sha256(some_string.encode('utf-8')).hexdigest()[:16]
```

### 8.3 总分行不要硬编码
```python
# ❌ 错: 无论实际命中几个, 都打印 ✅ 12/12
print("缺口 X: ✅ 12/12 稳定命中")

# ✅ 对: 基于 ok_count 真实反映
print(f"缺口 X: {'✅ 12/12' if ok else f'⚠️ {ok_count}/12'}")
```
**用户原话**: *"有问题的以后都默认要修，不用问"* — 硬编码庆祝文案 = 隐瞒 bug, 直接改。

### 8.4 单位显示要自适应
```python
# ❌ 错: 551 字节显示成 "0KB"
size_str = f"{bytes_count // 1024}KB"

# ✅ 对: 自适应 B/KB
if bytes_count >= 1024:
    size_str = f"{bytes_count / 1024:.1f}KB"
else:
    size_str = f"{bytes_count}B"
```

## 9. 完整工作流 (1 行)
```bash
# 注入 + 验证一步到位
python3 /Users/aimac/.hermes/scripts/anti_detect_inject.py && python3 /tmp/verify_all_3.py
```

## 9. 期望输出
```
缺口 1 (plugins): ✅ +3
缺口 2 (12 字段): ✅ 12/12 稳定命中
缺口 3 (自愈驱动): ✅ +5
缺口 4 (轨迹录制): ✅ +4

总分: 88 + 3+5+4=12 = 100 / 100
```

任何缺口打 ❌ 都说明真的有 bug, 立刻定位修复。
