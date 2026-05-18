"""
断点续传机制 (Checkpoint & Resume)
功能：
- 任务执行中定期保存checkpoint（状态快照）
- 失败后从最后一个checkpoint恢复
- 支持跨会话恢复（Hermes重启后也能继续）
- 记录详细的执行历史用于诊断
"""

import os
import json
import time
import hashlib
import logging
from typing import Any, Optional, List, Dict, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)


class CheckpointStatus(Enum):
    ACTIVE = "active"       # 任务进行中
    PAUSED = "paused"       # 手动暂停
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"       # 失败（无法恢复）
    RECOVERING = "recovering"  # 正在恢复


@dataclass
class TaskStep:
    """任务步骤"""
    step_id: int
    name: str
    status: str            # "pending" | "running" | "completed" | "failed" | "skipped"
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    error: Optional[str] = None
    retry_count: int = 0
    output: Optional[Any] = None


@dataclass
class Checkpoint:
    """检查点快照"""
    task_id: str
    task_name: str
    status: CheckpointStatus

    # 时间戳
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    # 执行进度
    current_step: int = 0
    total_steps: int = 0
    steps: List[TaskStep] = field(default_factory=list)

    # 世界状态（可序列化的关键上下文）
    world_state: Dict[str, Any] = field(default_factory=dict)

    # 执行历史（最近N条）
    action_history: List[Dict[str, Any]] = field(default_factory=list)

    # 恢复指令（自动生成）
    resume_instruction: Optional[str] = None

    # 统计
    attempt_count: int = 1
    last_error: Optional[str] = None

    def save(self, directory: str = "~/.hermes/checkpoints"):
        """保存checkpoint到磁盘"""
        path = Path(os.path.expanduser(directory))
        path.mkdir(parents=True, exist_ok=True)

        file_path = path / f"{self.task_id}.json"

        with open(file_path, 'w') as f:
            json.dump(asdict(self), f, indent=2, ensure_ascii=False)

        logger.info(f"[Checkpoint] 已保存: {file_path}")

    @classmethod
    def load(cls, task_id: str, directory: str = "~/.hermes/checkpoints") -> Optional["Checkpoint"]:
        """从磁盘加载checkpoint"""
        path = Path(os.path.expanduser(directory)) / f"{task_id}.json"

        if not path.exists():
            return None

        try:
            with open(path, 'r') as f:
                data = json.load(f)

            # 转换steps列表
            if 'steps' in data:
                data['steps'] = [TaskStep(**s) for s in data['steps']]

            checkpoint = cls(**data)
            logger.info(f"[Checkpoint] 已加载: {path}")
            return checkpoint

        except Exception as e:
            logger.error(f"[Checkpoint] 加载失败: {e}")
            return None

    @classmethod
    def list_checkpoints(
        cls,
        directory: str = "~/.hermes/checkpoints",
        status_filter: Optional[CheckpointStatus] = None
    ) -> List["Checkpoint"]:
        """列出所有checkpoint"""
        path = Path(os.path.expanduser(directory))
        if not path.exists():
            return []

        checkpoints = []
        for file in path.glob("*.json"):
            try:
                with open(file, 'r') as f:
                    data = json.load(f)
                cp = cls(**data)
                if status_filter is None or cp.status == status_filter:
                    checkpoints.append(cp)
            except Exception:
                pass

        return sorted(checkpoints, key=lambda c: c.updated_at, reverse=True)


@dataclass
class CheckpointManager:
    """
    Checkpoint管理器
    负责：创建checkpoint → 更新进度 → 从checkpoint恢复
    """

    task_id: str
    task_name: str
    total_steps: int

    checkpoint_dir: str = "~/.hermes/checkpoints"
    auto_save_interval: float = 30.0   # 自动保存间隔（秒）
    max_history: int = 100            # 保留最近N条操作历史

    # 内部状态
    _current_step: int = 0
    _steps: List[TaskStep] = field(default_factory=list)
    _action_history: List[Dict[str, Any]] = field(default_factory=list)
    _world_state: Dict[str, Any] = field(default_factory=dict)
    _last_save_ts: float = field(default_factory=time.time)
    _status: CheckpointStatus = CheckpointStatus.ACTIVE
    _attempt_count: int = 1

    def __post_init__(self):
        # 初始化步骤列表
        if not self._steps:
            for i in range(self.total_steps):
                self._steps.append(TaskStep(
                    step_id=i,
                    name=f"step_{i}",
                    status="pending"
                ))

    def set_steps(self, steps: List[str]):
        """设置步骤名称列表"""
        self._steps = [
            TaskStep(step_id=i, name=name, status="pending")
            for i, name in enumerate(steps)
        ]
        self.total_steps = len(steps)

    def record_action(self, action: str, params: Optional[dict] = None, result: Any = None):
        """记录一个动作"""
        self._action_history.append({
            "action": action,
            "params": params or {},
            "result": str(result)[:200] if result else None,  # 截断结果
            "timestamp": time.time(),
            "step": self._current_step
        })

        # 保留最近N条
        if len(self._action_history) > self.max_history:
            self._action_history = self._action_history[-self.max_history:]

    def start_step(self, step_id: int):
        """开始一个步骤"""
        self._current_step = step_id

        if step_id < len(self._steps):
            self._steps[step_id].status = "running"
            self._steps[step_id].started_at = time.time()
            self._steps[step_id].retry_count = self._steps[step_id].retry_count

        self._auto_save()

    def complete_step(self, step_id: int, output: Any = None):
        """完成一个步骤"""
        if step_id < len(self._steps):
            self._steps[step_id].status = "completed"
            self._steps[step_id].completed_at = time.time()
            self._steps[step_id].output = str(output)[:500] if output else None

        self._auto_save()

    def fail_step(self, step_id: int, error: str):
        """标记步骤失败"""
        if step_id < len(self._steps):
            self._steps[step_id].status = "failed"
            self._steps[step_id].completed_at = time.time()
            self._steps[step_id].error = error[:500]

        self._auto_save()

    def skip_step(self, step_id: int, reason: str = ""):
        """跳过步骤"""
        if step_id < len(self._steps):
            self._steps[step_id].status = "skipped"
            self._steps[step_id].completed_at = time.time()
            self._steps[step_id].error = reason[:200]

    def update_world_state(self, state: Dict[str, Any]):
        """更新世界状态"""
        self._world_state.update(state)

    def get_world_state(self) -> Dict[str, Any]:
        return self._world_state.copy()

    def get_next_pending_step(self) -> Optional[int]:
        """获取下一个待执行的步骤"""
        for i, step in enumerate(self._steps):
            if step.status == "pending":
                return i
        return None

    def get_resume_instruction(self) -> str:
        """生成恢复指令"""
        next_step = self.get_next_pending_step()

        if next_step is None:
            return "所有步骤已完成"

        completed_before = [
            (i, s) for i, s in enumerate(self._steps[:next_step])
            if s.status == "completed"
        ]

        completed_names = [s.name for _, s in completed_before]
        failed_steps = [
            (i, s) for i, s in enumerate(self._steps)
            if s.status == "failed"
        ]

        instruction = f"从步骤 {next_step} ('{self._steps[next_step].name}') 继续执行"
        if completed_names:
            instruction += f"\n已完成: {', '.join(completed_names)}"
        if failed_steps:
            instruction += f"\n失败步骤: {', '.join(s.name for i, s in failed_steps)}"

        return instruction

    def _auto_save(self):
        """自动保存（如果超过间隔）"""
        now = time.time()
        if now - self._last_save_ts > self.auto_save_interval:
            self.save()
            self._last_save_ts = now

    def save(self):
        """保存checkpoint"""
        checkpoint = Checkpoint(
            task_id=self.task_id,
            task_name=self.task_name,
            status=self._status,
            current_step=self._current_step,
            total_steps=self.total_steps,
            steps=self._steps.copy(),
            world_state=self._world_state.copy(),
            action_history=self._action_history.copy(),
            resume_instruction=self.get_resume_instruction(),
            attempt_count=self._attempt_count,
            last_error=self._steps[self._current_step].error
                if self._current_step < len(self._steps) else None,
        )
        checkpoint.save(directory=self.checkpoint_dir)
        self._last_save_ts = time.time()

    def save_and_pause(self):
        """保存并暂停"""
        self._status = CheckpointStatus.PAUSED
        self.save()
        logger.info(f"[CheckpointManager] 任务已暂停: {self.task_id}")

    def mark_completed(self):
        """标记任务完成"""
        self._status = CheckpointStatus.COMPLETED
        self.save()
        logger.info(f"[CheckpointManager] 任务已完成: {self.task_id}")

    def mark_failed(self, error: str):
        """标记任务失败"""
        self._status = CheckpointStatus.FAILED
        if self._current_step < len(self._steps):
            self._steps[self._current_step].error = error[:500]
        self.save()
        logger.info(f"[CheckpointManager] 任务失败: {self.task_id}")

    @classmethod
    def from_checkpoint(cls, checkpoint: Checkpoint) -> "CheckpointManager":
        """从checkpoint恢复CheckpointManager"""
        manager = cls(
            task_id=checkpoint.task_id,
            task_name=checkpoint.task_name,
            total_steps=checkpoint.total_steps,
        )
        manager._current_step = checkpoint.current_step
        manager._steps = checkpoint.steps
        manager._action_history = checkpoint.action_history
        manager._world_state = checkpoint.world_state
        manager._status = CheckpointStatus.RECOVERING
        manager._attempt_count = checkpoint.attempt_count + 1
        return manager

    @classmethod
    def resume(cls, task_id: str) -> Optional["CheckpointManager"]:
        """
        恢复指定task_id的checkpoint
        Returns: CheckpointManager 或 None
        """
        checkpoint = Checkpoint.load(task_id)
        if checkpoint is None:
            logger.warning(f"[CheckpointManager] 未找到checkpoint: {task_id}")
            return None

        if checkpoint.status == CheckpointStatus.COMPLETED:
            logger.warning(f"[CheckpointManager] 任务已完成，无需恢复: {task_id}")
            return None

        manager = cls.from_checkpoint(checkpoint)
        logger.info(f"[CheckpointManager] 已恢复checkpoint: {task_id}, "
                    f"从步骤 {checkpoint.current_step} 继续")
        return manager


# 全局单例
_checkpoint_managers: Dict[str, CheckpointManager] = {}


def get_checkpoint_manager(task_id: str, task_name: str = "", total_steps: int = 0) -> CheckpointManager:
    global _checkpoint_managers

    if task_id in _checkpoint_managers:
        return _checkpoint_managers[task_id]

    # 尝试从磁盘恢复
    manager = CheckpointManager.resume(task_id)
    if manager:
        _checkpoint_managers[task_id] = manager
        return manager

    # 创建新的
    manager = CheckpointManager(
        task_id=task_id,
        task_name=task_name or task_id,
        total_steps=total_steps
    )
    _checkpoint_managers[task_id] = manager
    return manager
