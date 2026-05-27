"""
Resilience Engine - 自愈引擎
Watchdog + 熔断器 + 恢复策略链

导出:
    Watchdog, RecoveryStrategy, CircuitState, get_watchdog
"""

from resilience_engine.watchdog import (
    Watchdog,
    RecoveryStrategy,
    CircuitState,
    get_watchdog,
)

__all__ = [
    "Watchdog",
    "RecoveryStrategy",
    "CircuitState",
    "get_watchdog",
]
