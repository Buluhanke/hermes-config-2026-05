"""
桌面状态管理
实现：操作记忆、回滚、快照、LLM上下文摘要
"""

import json
import time
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any


class SessionState:
    """
    Hermes 单次会话状态管理
    能力：记录操作步骤、支持回滚、生成LLM上下文摘要
    """

    def __init__(self, persistence_path: Optional[str] = None):
        self.persistence_path = Path(
            persistence_path or "~/.hermes/session_memory/"
        ).expanduser()
        self.persistence_path.mkdir(parents=True, exist_ok=True)

        self.steps: List[Dict] = []
        self.current_step: int = 0
        self.context: Dict[str, Any] = {}
        self._session_id = hashlib.md5(
            str(time.time()).encode()
        ).hexdigest()[:8]

    def record(
        self,
        action: str,
        result: Any,
        metadata: Optional[Dict] = None,
    ) -> int:
        """记录一步操作"""
        step = {
            "step_id": self.current_step,
            "session_id": self._session_id,
            "timestamp": time.time(),
            "action": action,
            "result": str(result)[:500] if result else None,
            "metadata": metadata or {},
            "context_snapshot": self.context.copy(),
        }
        self.steps.append(step)
        self._save_step(step)
        self.current_step += 1
        return self.current_step - 1

    def update_context(self, key: str, value: Any):
        """更新上下文（跨步骤保持状态）"""
        self.context[key] = value

    def get_context(self, key: str, default: Any = None) -> Any:
        return self.context.get(key, default)

    def get_last_n_steps(self, n: int = 5) -> List[Dict]:
        """获取最近 N 步"""
        return self.steps[-n:] if n > 0 else self.steps

    def rollback(self, target_step: int) -> Optional[Dict]:
        """回滚到指定步骤（不包括该步骤本身）"""
        if target_step < 0 or target_step >= len(self.steps):
            return None

        target = self.steps[target_step]
        self.context = target.get("context_snapshot", {}).copy()
        self.steps = self.steps[:target_step + 1]
        self.current_step = target_step + 1
        return target

    def get_context_summary(self) -> str:
        """生成LLM可读的上下文摘要"""
        if not self.steps:
            return "会话刚开始，暂无操作记录。"

        recent = self.get_last_n_steps(3)
        summary = f"会话 {self._session_id} | 已完成 {len(self.steps)} 步\n"

        for step in recent:
            ts = time.strftime("%H:%M:%S", time.localtime(step["timestamp"]))
            summary += f"  [{ts}] #{step['step_id']} {step['action']}: {str(step['result'])[:60]}\n"

        if len(self.steps) > 3:
            summary += f"  ... 共 {len(self.steps)} 步\n"

        return summary

    def get_full_trace(self) -> List[Dict]:
        """获取完整操作链（用于分析）"""
        return self.steps

    def _save_step(self, step: Dict):
        """持久化单步到磁盘"""
        filename = f"session_{self._session_id}_step_{step['step_id']:04d}.json"
        filepath = self.persistence_path / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(step, f, ensure_ascii=False, indent=2, default=str)


class MemoryLayer:
    """
    长期记忆层
    简单KV持久化，为后续接入向量数据库预留接口
    """

    def __init__(self, storage_path: str = "~/.hermes/long_term_memory/"):
        self.storage_path = Path(storage_path).expanduser()
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self._memories: List[Dict] = []
        self._load()

    def store(
        self,
        key: str,
        value: Any,
        tags: Optional[List[str]] = None,
    ):
        """存储记忆"""
        memory = {
            "key": key,
            "value": value,
            "tags": tags or [],
            "timestamp": time.time(),
        }
        self._memories.append(memory)
        self._save()

    def recall(self, key: str) -> Optional[Any]:
        """按key召回（返回最新匹配）"""
        for mem in reversed(self._memories):
            if mem["key"] == key:
                return mem["value"]
        return None

    def search_by_tag(self, tag: str) -> List[Any]:
        """按标签搜索"""
        return [
            m["value"] for m in self._memories
            if tag in m.get("tags", [])
        ]

    def _save(self):
        """最多保留最近1000条"""
        filepath = self.storage_path / "memories.json"
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self._memories[-1000:], f, ensure_ascii=False, indent=2, default=str)

    def _load(self):
        filepath = self.storage_path / "memories.json"
        if filepath.exists():
            with open(filepath, 'r', encoding='utf-8') as f:
                self._memories = json.load(f)


# 全局单例
_global_session: Optional[SessionState] = None
_global_memory: Optional[MemoryLayer] = None


def get_session_state() -> SessionState:
    global _global_session
    if _global_session is None:
        _global_session = SessionState()
    return _global_session


def get_memory_layer() -> MemoryLayer:
    global _global_memory
    if _global_memory is None:
        _global_memory = MemoryLayer()
    return _global_memory
