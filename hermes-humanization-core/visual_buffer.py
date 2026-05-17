#!/usr/bin/env python3
"""
视觉环形缓冲区 —— Hermes 的"记忆眼"
每 2 秒静默截屏，保留最近 5 帧。
当操作失败时，把最近 5 帧串联发给 VLM：
"我刚才在操作，屏幕上发生了什么？"

用法：
    from visual_buffer import VisualRingBuffer, get_buffer

    buffer = VisualRingBuffer(max_frames=5, interval=2.0)
    buffer.start()  # 后台开始捕获

    # 操作失败时用：
    context = buffer.get_context_for_vlm()
    # → 返回 "帧1时间: 描述\\n帧2时间: 描述..."
"""

import threading
import time
import os
import sys
from datetime import datetime
from pathlib import Path

# 确保能导入 humanization_core 的截屏函数
HERMES_SKILL_DIR = Path(__file__).parent
sys.path.insert(0, str(HERMES_SKILL_DIR))

try:
    from humanization_core import capture_screen
except ImportError:
    # 降级：自己截
    import mss
    def capture_screen(output_path="/tmp/hermes_rb.png"):
        with mss.MSS() as sct:
            sct.shot(output=output_path, mon=1)
        return output_path


class VisualRingBuffer:
    """线程安全的环形视觉缓冲区"""

    def __init__(self, max_frames: int = 5, interval: float = 2.0):
        self.max_frames = max_frames
        self.interval = interval
        self._buffer = []          # [(timestamp, filepath), ...]
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._capture_thread = None
        self._capture_count = 0  # 用于计算发呆

    def start(self):
        """启动后台截屏线程（只启动一次）"""
        if self._capture_thread and self._capture_thread.is_alive():
            return  # 已启动
        self._stop_event.clear()
        self._capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._capture_thread.start()

    def stop(self):
        """停止后台截屏"""
        self._stop_event.set()
        if self._capture_thread:
            self._capture_thread.join(timeout=3)

    def _capture_loop(self):
        """后台循环：每 interval 秒截一张"""
        tmp_dir = Path("/tmp/hermes_rb")
        tmp_dir.mkdir(exist_ok=True)

        while not self._stop_event.is_set():
            self._capture_count += 1
            ts = datetime.now().strftime("%H%M%S")
            path = str(tmp_dir / f"frame_{self._capture_count:04d}_{ts}.png")

            try:
                capture_screen(output_path=path)
                with self._lock:
                    self._buffer.append((ts, path))
                    # 保持 max_frames 帧
                    while len(self._buffer) > self.max_frames:
                        old_path = self._buffer.pop(0)[1]
                        if os.path.exists(old_path):
                            os.remove(old_path)
            except Exception as e:
                print(f"[VisualRingBuffer] 截屏失败: {e}")

            self._stop_event.wait(self.interval)

    def get_recent_frames(self, count: int = None) -> list:
        """返回最近 N 帧 [(timestamp, filepath), ...]"""
        count = count or self.max_frames
        with self._lock:
            return list(self._buffer[-count:])

    def get_context_for_vlm(self) -> str:
        """生成发给 VLM 的连续上下文描述"""
        frames = self.get_recent_frames()
        if not frames:
            return "（无视觉历史）"

        lines = []
        for i, (ts, path) in enumerate(frames):
            size_kb = os.path.getsize(path) // 1024
            lines.append(f"【第{i+1}帧 {ts} 大小{size_kb}KB】{path}")
        return "\n".join(lines)

    def get_frame_paths(self) -> list:
        """返回所有帧的路径列表（用于发给 VLM）"""
        with self._lock:
            return [p for _, p in self._buffer]


# 全局单例（整个进程共享一个缓冲区）
_global_buffer = None
_global_lock = threading.Lock()


def get_buffer() -> VisualRingBuffer:
    global _global_buffer
    with _global_lock:
        if _global_buffer is None:
            _global_buffer = VisualRingBuffer(max_frames=5, interval=2.0)
            _global_buffer.start()
        return _global_buffer


if __name__ == "__main__":
    print("[VisualRingBuffer] 测试模式，5 帧后自动停止...")
    buf = VisualRingBuffer(max_frames=5, interval=1.5)
    buf.start()
    buf._capture_thread.join()
    print(f"[VisualRingBuffer] 已捕获 {len(buf._buffer)} 帧:")
    for ts, p in buf._buffer:
        print(f"  {ts} → {p}")
