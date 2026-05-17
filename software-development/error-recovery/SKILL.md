---
name: error-recovery
description: "错误恢复与系统自愈 — 错误分类/自动恢复/重试机制/降级策略"
version: 1.0.0
tags: [错误恢复, 自愈, 重试, 降级, 稳定性]
author: Hermes Agent
---

# 错误恢复与系统自愈

## 概述

Hermes作为自动化Agent，必须具备错误检测和自动恢复能力，不能一遇到问题就卡死等老板救场。

## 错误分类

### 四类错误
```python
错误分类 = {
    "网络错误": {
        "症状": ["ConnectionError", "Timeout", "HTTP 5xx"],
        "例子": "1688接口超时、CDP断开",
        "自动恢复": True,
    },
    "认证错误": {
        "症状": ["401 Unauthorized", "Cookie失效", "Token过期"],
        "例子": "1688 Cookie过期、n8n JWT失效",
        "自动恢复": "需要重新认证",
    },
    "状态错误": {
        "症状": ["ElementNotFound", "StateError", "AssertionError"],
        "例子": "页面元素消失、任务状态异常",
        "自动恢复": True,  # 截图重新定位
    },
    "外部服务错误": {
        "症状": ["503 Service Unavailable", "限流429", "第三方故障"],
        "例子": "1688风控、百度OCR配额用尽",
        "自动恢复": "等待后重试",
    },
}
```

### 错误识别策略
```python
def 识别错误类型(error):
    if "Connection" in str(error) or "Timeout" in str(error):
        return "网络错误"
    elif "401" in str(error) or "Cookie" in str(error):
        return "认证错误"
    elif "ElementNotFound" in str(error) or "not found" in str(error):
        return "状态错误"
    elif "429" in str(error) or "503" in str(error):
        return "外部服务错误"
    else:
        return "未知错误"
```

## 自动恢复策略

### 网络错误恢复
```python
def 网络错误恢复(max_retries=3):
    for attempt in range(max_retries):
        try:
            # 重试操作
            return 操作()
        except 网络错误:
            # 等待指数退避
            wait_time = 2 ** attempt  # 1s, 2s, 4s
            time.sleep(wait_time)
            # 重新建立连接
            重新连接CDP()
            continue
    return {"status": "failed", "reason": "网络错误超过重试次数"}
```

### 认证错误恢复
```python
def 认证错误恢复():
    """Cookie失效，需要重新扫码登录"""
    # 1. 检测到401/登录状态失效
    if 检测登录状态() == False:
        # 2. 发送通知给老板
        发送通知("1688 Cookie失效，需要重新扫码")
        # 3. 暂停自动化任务
        暂停任务()
        # 4. 等待老板重新扫码
        等待老板扫码确认()
        # 5. 恢复任务
        恢复任务()
```

### 状态错误恢复
```python
def 状态错误恢复():
    """页面元素消失，尝试重新定位"""
    # 1. 截当前状态
    screenshot = 截图()
    
    # 2. 尝试多种定位方式
    for 定位方式 in ["AX树", "VLM", "规则坐标"]:
        try:
            元素位置 = 定位方式.查找目标元素()
            if 元素位置:
                点击(元素位置)
                return True
        except:
            continue
    
    # 3. 所有方式都失败
    发送通知(f"无法定位目标元素，截图已保存")
    return False
```

### 外部服务错误恢复
```python
def 外部服务错误恢复(error):
    """限流/服务不可用"""
    if "429" in str(error) or "限流" in str(error):
        # 降级等待
        wait_time = 60  # 等待1分钟
        for i in range(wait_time):
            time.sleep(1)
        return {"status": "retry", "waited": wait_time}
    
    elif "503" in str(error):
        # 第三方服务故障，切换备用方案
        return {"status": "fallback", "action": "使用备用服务"}
    
    elif "额度" in str(error) or "配额" in str(error):
        # 配额用尽，切换免费方案
        return {"status": "fallback", "action": "切换免费API"}
```

## 重试机制设计

### 指数退避
```python
import random

def 重试操作(操作函数, max_retries=5, base_delay=1):
    for attempt in range(max_retries):
        try:
            return 操作函数()
        except 临时错误 as e:
            if attempt == max_retries - 1:
                raise
            
            # 指数退避 + 随机抖动
            delay = base_delay * (2 ** attempt)
            jitter = random.uniform(0, delay * 0.1)  # 10%抖动
            time.sleep(delay + jitter)
            
            log(f"重试 {attempt + 1}/{max_retries}，等待 {delay:.1f}s")
```

### 重试条件判断
```python
def 应该重试(error, attempt, max_retries):
    """判断这个错误是否值得重试"""
    # 永久性错误不重试
    if isinstance(error, (ValueError, TypeError)):
        return False
    
    # 达到最大重试次数不重试
    if attempt >= max_retries:
        return False
    
    # 临时性错误重试
    if isinstance(error, (ConnectionError, Timeout)):
        return True
    
    # 其他错误，根据attempt次数递减重试概率
    return random.random() < (1 - attempt / max_retries)
```

## 降级策略

### 降级原则
1. 优雅降级：核心功能必须可用，附加功能可牺牲
2. 降级前通知：告诉用户正在降级
3. 降级后记录：方便后续排查

### 降级示例：OCR服务
```
优先：百度OCR（准确率高）
  ↓ 失败
降级：Tesseract OCR（本地免费）
  ↓ 失败
降级：VLM描述（最慢但最通用）
  ↓ 失败
降级：返回"无法识别，请手动处理"
```

### 降级示例：1688数据获取
```
优先：1688开放平台API
  ↓ 失败/限流
降级：CDP浏览器自动化抓取
  ↓ 失败/检测
降级：手工录入（老板协助）
  ↓ 老板也无法
降级：标记"待处理"，继续其他任务
```

### 降级代码模板
```python
def 执行带降级的操作(操作函数, 降级函数, 错误类型):
    try:
        return 操作函数()
    except 错误类型:
        log(f"主方案失败，尝试降级")
        try:
            return 降级函数()
        except Exception as e:
            log(f"降级也失败: {e}")
            return {"status": "failed", "fallback": True}
```

## 错误日志和告警

### 日志记录规范
```python
log_format = {
    "timestamp": "2024-01-15 10:30:00",
    "level": "ERROR",
    "task": "1688询价",
    "error_type": "网络错误",
    "error_message": "ConnectionTimeout: 1688 API超时",
    "attempt": 2,
    "max_retries": 3,
    "recovered": True,  # 是否恢复
    "screenshot": "/tmp/hermes/error_20240115_103000.png",
}
```

### 告警触发条件
```python
告警条件 = {
    "连续失败": "同一任务失败3次",
    "认证失效": "Cookie/JWT过期",
    "磁盘空间": "使用率>90%",
    "进程崩溃": "Hermes主进程退出",
    "服务不可用": "1688无法访问持续>5分钟",
}
```

### 告警通知内容
```
【Hermes告警】

类型：1688询价失败（连续3次）
时间：2024-01-15 10:30:00
原因：网络超时
已尝试：自动重试3次，均失败
最后错误：ConnectionTimeout after 30s
截图：已保存

需要人工介入：是
建议操作：检查网络或1688服务状态
```