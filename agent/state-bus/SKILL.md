# Unified State Bus（统一状态总线）

## 1. 什么是状态总线

状态总线是Agent架构中各层级（perception/cognition/planning/action/feedback）之间的通信中枢。所有层级通过总线发布和订阅消息，而不是直接相互调用。

类比ROS的话题（Topic）和服务（Service）机制：
- **话题（Pub/Sub）**：异步广播，发布者不关心谁订阅，如ROS的`/scan`、`/cmd_vel`
- **服务（RPC）**：同步请求-响应，如ROS的`/get_map`

状态总线本质上是应用层的Pub/Sub总线，所有状态变更通过总线分发，层级之间完全解耦。

---

## 2. 为什么需要状态总线

### 各层级解耦

没有总线时，层级之间直接引用：
```
perception → cognition → planning → action → feedback
     ↓           ↓           ↓          ↓
   直接调用 → 紧耦合 → 难以测试 → 循环依赖
```

有总线时，层级只关心总线：
```
perception  →  [State Bus]  ←  cognition
planning    →  [State Bus]  ←  action
feedback    →  [State Bus]  ←  (任意订阅者)
```

### 核心价值

| 收益 | 说明 |
|------|------|
| **解耦** | 层级可以独立开发、测试、替换 |
| **可观测** | 所有状态流转经过总线，便于日志和调试 |
| **可扩展** | 新增订阅者无需修改发布者 |
| **容错** | 订阅者崩溃不阻塞发布者 |
| **复用** | 同一消息可被多个订阅者使用 |

---

## 3. 三种实现方案

### 方案A：Python EventBus（轻量·推荐）

适用于单进程内通信，Mac Mini M4单进程足够。

```python
# event_bus.py
from typing import Callable, Dict, List
from dataclasses import dataclass, field
from datetime import datetime
import threading

@dataclass
class BusMessage:
    topic: str
    payload: dict
    timestamp: datetime = field(default_factory=datetime.now)
    source: str = ""

class EventBus:
    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}
        self._lock = threading.Lock()

    def subscribe(self, topic: str, callback: Callable):
        with self._lock:
            if topic not in self._subscribers:
                self._subscribers[topic] = []
            self._subscribers[topic].append(callback)

    def unsubscribe(self, topic: str, callback: Callable):
        with self._lock:
            if topic in self._subscribers:
                self._subscribers[topic] = [
                    cb for cb in self._subscribers[topic] if cb != callback
                ]

    def publish(self, topic: str, payload: dict, source: str = ""):
        msg = BusMessage(topic=topic, payload=payload, source=source)
        with self._lock:
            subscribers = list(self._subscribers.get(topic, []))
        for cb in subscribers:
            try:
                cb(msg)
            except Exception as e:
                print(f"[EventBus] callback error on {topic}: {e}")

# 全局单例
bus = EventBus()
```

使用示例：
```python
# perception 层发布
bus.publish("/perception/vision/objects", {"objects": [...], "confidence": 0.92})

# cognition 层订阅
def on_objects(msg: BusMessage):
    print(f"Received: {msg.payload}")
bus.subscribe("/perception/vision/objects", on_objects)
```

### 方案B：Redis PubSub（跨进程）

适用于多进程或需要跨机器通信的场景。

```python
# redis_bus.py
import redis
import json
from typing import Callable

class RedisPubSubBus:
    def __init__(self, host="localhost", port=6379):
        self.redis = redis.Redis(host=host, port=port)
        self.pubsub = self.redis.pubsub()

    def publish(self, topic: str, payload: dict):
        self.redis.publish(topic, json.dumps(payload))

    def subscribe(self, topic: str, callback: Callable):
        self.pubsub.subscribe(topic)
        for msg in self.pubsub.listen():
            if msg["type"] == "message":
                callback(json.loads(msg["data"]))

# 注意：Redis PubSub是fire-and-forget，不保证消息持久化
# 如需可靠投递，考虑使用Redis Streams
```

### 方案C：n8n Webhook（工作流集成）

适用于需要触发外部工作流的场景。

```python
# webhook_bus.py
import requests
from typing import List

class WebhookBus:
    def __init__(self, n8n_webhook_url: str):
        self.webhook_url = n8n_webhook_url

    def publish(self, topic: str, payload: dict):
        requests.post(
            self.webhook_url,
            json={"topic": topic, "payload": payload},
            timeout=5
        )

    def subscribe(self, topic: str, callback: callable):
        # n8n webhook作为订阅端，通过HTTP回调触发
        pass
```

**方案对比：**

| 方案 | 延迟 | 跨进程 | 消息持久化 | 复杂度 | 适用场景 |
|------|------|--------|------------|--------|----------|
| Python EventBus | <1ms | ❌ | ❌ | 低 | Mac Mini单进程 |
| Redis PubSub | 1-5ms | ✅ | ❌ | 中 | 多进程/轻量分布 |
| n8n Webhook | 100ms+ | ✅ | ✅ | 低 | 工作流触发 |

---

## 4. 话题设计

### 命名规范

话题名称格式：`/<layer>/<sub-layer>/<event>`

### 各层话题定义

#### perception 层（感知）
```
/perception/vision/objects      # 视觉检测到的物体列表
/perception/vision/faces        # 人脸检测结果
/perception/audio/transcript    # 语音转文字结果
/perception/sensor/lidar        # 激光雷达数据
/perception/context/summary     # 当前环境上下文摘要
```

#### cognition 层（认知/记忆）
```
/cognition/intent               # 识别的用户意图
/cognition/memory/retrieve      # 记忆检索结果
/cognition/memory/store         # 需要存储的记忆
/cognition/context/update       # 上下文更新
```

#### planning 层（规划）
```
/planning/goal                  # 当前目标
/planning/task                  # 当前任务分解
/planning/decision              # 决策结果
/planning/replan                # 重规划触发
```

#### action 层（执行）
```
/action/execute                 # 执行动作指令
/action/status                  # 动作执行状态
/action/complete                # 动作完成通知
/action/cancel                  # 取消动作指令
```

#### feedback 层（反馈）
```
/feedback/success               # 成功反馈
/feedback/failure               # 失败反馈
/feedback/progress              # 进度反馈
```

#### error 层（错误·统一）
```
/error/perception               # 感知层错误
/error/cognition                # 认知层错误
/error/planning                 # 规划层错误
/error/action                   # 执行层错误
/error/system                   # 系统级错误
```

### 消息格式标准

```python
{
    "topic": "/perception/vision/objects",
    "payload": {
        "data": {...},           # 业务数据
        "metadata": {
            "timestamp": "2026-05-17T18:30:00Z",
            "source": "vision_module",
            "confidence": 0.92,
            "seq": 12345
        }
    }
}
```

---

## 5. Mac Mini M4 实现建议

### 推荐架构

```
单进程 + Python EventBus
```

### 为什么不要过度设计

1. **M4性能足够**：单进程EventBus在M4上处理数千条消息/秒毫无压力
2. **降低复杂度**：多进程/Redis引入运维负担（进程间通信、Redis服务维护）
3. **简化调试**：单进程内所有状态流转一目了然
4. **避免过早优化**：除非实测性能不足，不要引入分布式复杂度

### 目录结构

```
agent/
├── event_bus.py          # EventBus单例
├── topics.py              # 话题常量定义
├── layers/
│   ├── perception/       # 感知层
│   ├── cognition/        # 认知层
│   ├── planning/         # 规划层
│   └── action/           # 执行层
└── main.py               # 入口
```

### topics.py 示例

```python
# topics.py - 集中定义所有话题常量
class Topics:
    # Perception
    PERCEPTION_VISION_OBJECTS = "/perception/vision/objects"
    PERCEPTION_AUDIO_TRANSCRIPT = "/perception/audio/transcript"
    PERCEPTION_CONTEXT_SUMMARY = "/perception/context/summary"

    # Cognition
    COGNITION_INTENT = "/cognition/intent"
    COGNITION_MEMORY_RETRIEVE = "/cognition/memory/retrieve"
    COGNITION_MEMORY_STORE = "/cognition/memory/store"

    # Planning
    PLANNING_GOAL = "/planning/goal"
    PLANNING_TASK = "/planning/task"
    PLANNING_DECISION = "/planning/decision"

    # Action
    ACTION_EXECUTE = "/action/execute"
    ACTION_STATUS = "/action/status"
    ACTION_COMPLETE = "/action/complete"

    # Feedback
    FEEDBACK_SUCCESS = "/feedback/success"
    FEEDBACK_FAILURE = "/feedback/failure"
    FEEDBACK_PROGRESS = "/feedback/progress"

    # Error
    ERROR_PERCEPTION = "/error/perception"
    ERROR_COGNITION = "/error/cognition"
    ERROR_PLANNING = "/error/planning"
    ERROR_ACTION = "/error/action"
    ERROR_SYSTEM = "/error/system"
```

### 实际经验阈值

| 指标 | 阈值 | 说明 |
|------|------|------|
| 消息/秒 | < 1000 | Python EventBus单进程无压力 |
| 消息/秒 | 1000-5000 | 考虑异步处理优化 |
| 消息/秒 | > 5000 | 才考虑Redis或进程分离 |

**结论**：Mac Mini M4上，单进程Python EventBus足够应对绝大多数场景。不要因为"将来可能需要"而过度设计。
