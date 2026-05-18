"""
自愈引擎
Watchdog + 恢复策略链 + 熔断器 + 指数退避
"""

import asyncio
import random
import time
import logging
from enum import Enum
from typing import Callable, Any, Optional, List

logger = logging.getLogger(__name__)


class RecoveryStrategy(Enum):
    """恢复策略枚举"""
    WAIT_LONGER = "wait"         # 延长等待
    RELOCATE = "relocate"         # 重新定位元素
    SCROLL = "scroll"             # 滚动页面
    REFRESH = "refresh"           # 刷新页面
    FALLBACK = "fallback"         # 备用选择器
    HUMAN_CONFUSION = "human_confusion"  # 人类困惑行为
    ESCAPE_HATCH = "escape_hatch"       # 逃生舱（保存状态后放弃）


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class Watchdog:
    """
    自愈执行包装器
    核心能力：
    - 指数退避重试
    - 熔断器（circuit breaker）
    - 策略链自动升级
    - 人类困惑行为模拟
    """

    def __init__(
        self,
        max_retries: int = 3,
        circuit_threshold: int = 5,
        recovery_strategies: Optional[List[RecoveryStrategy]] = None,
        state_persistence_path: str = "~/.hermes/watchdog_state.json",
    ):
        self.max_retries = max_retries
        self.circuit_threshold = circuit_threshold
        self.failure_count = 0
        self.circuit_state = CircuitState.CLOSED
        self.last_failure_time = 0

        self.recovery_strategies = recovery_strategies or [
            RecoveryStrategy.WAIT_LONGER,
            RecoveryStrategy.RELOCATE,
            RecoveryStrategy.SCROLL,
            RecoveryStrategy.REFRESH,
            RecoveryStrategy.HUMAN_CONFUSION,
            RecoveryStrategy.ESCAPE_HATCH,
        ]

    async def protect(self, operation: Callable[..., Any], context: Optional[dict] = None) -> Any:
        """
        包装需要自愈能力的操作

        参数:
            operation: 异步或同步的可调用对象
            context: 操作上下文（包含selector, page等）
        """
        if self.circuit_state == CircuitState.OPEN:
            # 熔断器打开，10秒后尝试半开
            if time.time() - self.last_failure_time > 10:
                self.circuit_state = CircuitState.HALF_OPEN
            else:
                raise Exception("Circuit breaker OPEN - 熔断器打开，拒绝执行")

        for attempt in range(self.max_retries):
            try:
                # 判断是async还是sync
                if asyncio.iscoroutinefunction(operation):
                    result = await operation()
                else:
                    result = operation()

                # 成功，重置计数
                if self.circuit_state == CircuitState.HALF_OPEN:
                    self.circuit_state = CircuitState.CLOSED
                self.failure_count = 0
                return result

            except Exception as e:
                logger.warning(f"[Watchdog] 尝试 {attempt+1}/{self.max_retries} 失败: {e}")

                if attempt < self.max_retries - 1:
                    # 应用恢复策略
                    strategy = self.recovery_strategies[
                        min(attempt, len(self.recovery_strategies) - 1)
                    ]
                    await self._apply_recovery(strategy, context)

                    # 指数退避 + 抖动
                    delay = self._exponential_backoff(attempt)
                    time.sleep(delay)
                else:
                    # 所有重试失败
                    self.failure_count += 1
                    self.last_failure_time = time.time()

                    if self.failure_count >= self.circuit_threshold:
                        self.circuit_state = CircuitState.OPEN
                        logger.error(f"[Watchdog] 熔断器打开（连续{self.failure_count}次失败）")

                    raise

        return None

    async def _apply_recovery(self, strategy: RecoveryStrategy, context: Optional[dict] = None):
        """执行具体恢复策略"""
        logger.info(f"[Watchdog] 执行恢复策略: {strategy.value}")

        if strategy == RecoveryStrategy.HUMAN_CONFUSION:
            # 人类困惑行为：画小圈 + 犹豫
            await self._human_confusion_behavior(context)

        elif strategy == RecoveryStrategy.WAIT_LONGER:
            delay = random.uniform(2.0, 5.0)
            logger.info(f"[Watchdog] 等待 {delay:.1f}s")
            time.sleep(delay)

        elif strategy == RecoveryStrategy.REFRESH:
            if context and 'page' in context:
                logger.info("[Watchdog] 刷新页面")
                # context['page'].reload()
                time.sleep(2)

        elif strategy == RecoveryStrategy.SCROLL:
            if context and 'page' in context:
                logger.info("[Watchdog] 滚动页面")
                # context['page'].evaluate("window.scrollBy(0, 200)")
                time.sleep(0.5)

        elif strategy == RecoveryStrategy.RELOCATE:
            # 等待元素重新出现
            time.sleep(random.uniform(1.0, 2.5))

        elif strategy == RecoveryStrategy.ESCAPE_HATCH:
            # 逃生舱：保存当前状态，返回哨兵值
            logger.warning("[Watchdog] 触发逃生舱，保存状态")
            self._save_escape_state(context)
            raise Exception("ESCAPE_HATCH triggered - 放弃当前操作")

    async def _human_confusion_behavior(self, context: Optional[dict] = None):
        """模拟人类困惑行为：犹豫、画圈、微调"""
        logger.info("[Watchdog] 模拟人类困惑行为...")

        # 画小圈
        center_x, center_y = 500, 400
        radius = random.randint(15, 30)

        # 用 CDP 发送鼠标事件（如果有 CDP client）
        try:
            from gateway.core.cdp_client import CDPClient
            client = CDPClient.get_instance()

            for angle in range(0, 360, 30):
                rad = angle * 3.14159 / 180
                x = center_x + radius * (1 + random.uniform(-0.1, 0.1)) * (1 if angle % 90 == 0 else -1 if angle > 180 else 1) * abs(rad % (3.14159/2) - 3.14159/4)
                y = center_y + radius * abs(3.14159/2 - rad)

                client.send("Input.dispatchMouseEvent", {
                    "type": "mouseMoved",
                    "x": x,
                    "y": y
                })
                time.sleep(random.uniform(0.05, 0.15))

            time.sleep(random.uniform(0.3, 0.8))
        except Exception:
            # 没有CDP client，纯等待
            time.sleep(random.uniform(1.5, 3.0))

    def _exponential_backoff(self, attempt: int) -> float:
        """指数退避 + 随机抖动"""
        base = min(30, 0.5 * (2 ** attempt))
        jitter = random.uniform(0.7, 1.3)
        return base * jitter

    def _save_escape_state(self, context: Optional[dict] = None):
        """逃生舱：保存状态到磁盘"""
        import json
        from pathlib import Path

        state = {
            "timestamp": time.time(),
            "context_keys": list(context.keys()) if context else [],
            "failure_count": self.failure_count,
        }

        path = Path("~/.hermes/watchdog_escape.json").expanduser()
        with open(path, 'w') as f:
            json.dump(state, f, indent=2)


# 全局单例
_default_watchdog: Optional[Watchdog] = None


def get_watchdog() -> Watchdog:
    global _default_watchdog
    if _default_watchdog is None:
        _default_watchdog = Watchdog()
    return _default_watchdog
