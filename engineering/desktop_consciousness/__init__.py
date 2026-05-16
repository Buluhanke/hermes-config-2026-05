"""
Desktop Consciousness - 桌面状态管理
SessionState + MemoryLayer + 全局单例

导出:
    SessionState, MemoryLayer, get_session_state, get_memory_layer
"""

from desktop_consciousness.session_state import (
    SessionState,
    MemoryLayer,
    get_session_state,
    get_memory_layer,
)

__all__ = [
    "SessionState",
    "MemoryLayer",
    "get_session_state",
    "get_memory_layer",
]
