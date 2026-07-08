---
name: error-patterns
description: 常见错误模式的根因分析 + 修复方案。来源：auto_skill_from_failure.py 从 agent.log 每日抽取，6类核心模式。
triggers:
  - "TimeoutError"
  - "ConnectionError"
  - "JSON parse error"
  - "Import error"
  - "Permission denied"
  - "CDP attach failed"
pitfalls:
  - 看到错误直接猜原因——应先读完整 traceback
  - 只看错误行不看不支持的方法——先确认字段存在
  - 重复同一个错误3次以上不沉淀——立即写fact_store

# 错误模式速查手册

## 🔴 CDP attach failed (严重度4)

**频率**: 4次（低频但每次都阻断浏览器操作）

**触发**: browser_cdp 调用时 target 已消失或尚未就绪

**根因**: 
- 页面还在导航，CDP tab 未完全加载
- WS URL 指向的 page 已关闭
- mirror Chrome (9222) 和用户主 Chrome 是独立实例

**修法**:
```python
# 方案1：等 page 就绪
import time
for _ in range(10):
    targets = browser_cdp(method='Target.getTargets', params={})
    if any(t['type']=='page' for t in targets['targetInfos']):
        break
    time.sleep(0.5)

# 方案2：取 live WS URL（不用 mirror）
import subprocess
result = subprocess.run(['lsof', '-i', ':9222', '-s', 'TCP:LISTEN'], capture_output=True, text=True)
```

---

## 🟡 TimeoutError (严重度2)

**频率**: 479次（最高频，其中420次是QQBot WebSocket code=4009）

**触发**: QQBot WebSocket session timeout / API call 超时

**根因**:
- QQBot WS 每30分钟 idle 超时（code=4009）
- NVIDIA API / GLM API 响应慢
- 慢查询未设 timeout

**修法**:
- QQBot code=4009: adapter 有自动重连，观察日志确认心跳生效
- API call failed: 加 retry + exponential backoff
- Command timed out: cron 脚本加 timeout 参数

---

## 🟡 ConnectionError (严重度3)

**频率**: 214次

**触发**: NVIDIA/GLM API 连接失败

**根因**: API endpoint 不达 / 网络抖动 / API key 权限问题

**修法**:
```python
from tenacity import retry, stop_after_attempt, wait_exponential
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def call_api():
    ...
```

---

## 🟡 Import error / Permission denied (严重度2/3)

**频率**: 14次（9+5）

**触发**: launchd 启动的脚本 cwd=/（只读），相对路径资源加载失败

**根因**: launchd 启动 Python 时 cwd=/，所有相对路径失效

**修法**:
```python
import os
from pathlib import Path
os.chdir(Path.home() / '.hermes')  # 启动第一时间执行
```

---

## 🟢 JSON parse error (严重度1)

**频率**: 13次

**触发**: API 返回非 JSON 或截断的响应

**根因**: API 超时返回空 body / partial body / HTML 错误页

**修法**:
```python
try:
    data = response.json()
except JSONDecodeError:
    if response.status_code == 200:
        logger.warning(f"Non-JSON response: {response.text[:200]}")
```

---

## 修法通用流程

1. 确认根因：读完整 traceback，不只看错误行
2. 加容错：try/except，字段先 .get()
3. 写 fact_store 标记已修（trust=0.9）
4. 高频错误(>3次/天) → 立即生成/更新 skill
