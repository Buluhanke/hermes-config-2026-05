"""
卡死检测器
检测：鼠标静止、页面无变化、元素僵死、JS无响应
"""

import time
import hashlib
import logging
from typing import Optional, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class StuckType(Enum):
    MOUSE_STUCK = "mouse_stuck"           # 鼠标位置不变
    PAGE_STUCK = "page_stuck"              # 页面内容不变
    ELEMENT_STUCK = "element_stuck"        # 目标元素僵死
    JS_STUCK = "js_stuck"                  # JS无响应
    WINDOW_FOCUS_LOST = "focus_lost"       # 窗口失去焦点


@dataclass
class StuckDetector:
    """卡死检测器"""
    timeout: float = 30.0          # 超时阈值（秒）
    check_interval: float = 5.0    # 检测间隔
    mouse_move_threshold: int = 5  # 鼠标移动阈值（像素）

    _last_mouse_pos: Optional[Tuple[int, int]] = None
    _last_page_url: Optional[str] = None
    _last_screen_hash: Optional[str] = None
    _last_activity_ts: float = field(default_factory=time.time)
    _baseline_js_load_time: Optional[float] = None
    _failure_count: int = 0

    def reset(self):
        """重置检测器状态"""
        self._last_mouse_pos = None
        self._last_page_url = None
        self._last_screen_hash = None
        self._last_activity_ts = time.time()
        self._baseline_js_load_time = None
        self._failure_count = 0
        logger.info("[StuckDetector] 已重置")

    def record_activity(self):
        """记录一次有效活动"""
        self._last_activity_ts = time.time()
        self._failure_count = 0

    def check_mouse_stuck(
        self,
        current_pos: Tuple[int, int],
        threshold: Optional[int] = None
    ) -> Tuple[bool, str]:
        """
        检测鼠标是否卡死
        Returns: (is_stuck, reason)
        """
        if self._last_mouse_pos is None:
            self._last_mouse_pos = current_pos
            return False, ""

        threshold = threshold or self.mouse_move_threshold
        dx = abs(current_pos[0] - self._last_mouse_pos[0])
        dy = abs(current_pos[1] - self._last_mouse_pos[1])

        if dx < threshold and dy < threshold:
            elapsed = time.time() - self._last_activity_ts
            if elapsed > self.timeout:
                self._failure_count += 1
                return True, f"鼠标静止 {elapsed:.0f}s，位置未变"
        else:
            # 鼠标移动了
            self._last_activity_ts = time.time()

        self._last_mouse_pos = current_pos
        return False, ""

    def check_page_stuck(
        self,
        current_url: str,
        current_screen_hash: str,
        threshold: Optional[float] = None
    ) -> Tuple[bool, str]:
        """
        检测页面是否卡死（URL+内容都没变）
        Returns: (is_stuck, reason)
        """
        threshold = threshold or self.timeout

        if self._last_page_url is None or self._last_screen_hash is None:
            self._last_page_url = current_url
            self._last_screen_hash = current_screen_hash
            return False, ""

        # URL没变 + 屏幕内容没变 = 卡死
        url_same = (current_url == self._last_page_url)
        screen_same = (current_screen_hash == self._last_screen_hash)

        if url_same and screen_same:
            elapsed = time.time() - self._last_activity_ts
            if elapsed > threshold:
                self._failure_count += 1
                return True, f"页面僵死 {elapsed:.0f}s，URL+内容无变化"
        else:
            self._last_activity_ts = time.time()

        self._last_page_url = current_url
        self._last_screen_hash = current_screen_hash
        return False, ""

    def check_js_responsive(self, js_execute_fn: Callable[[], bool]) -> Tuple[bool, str]:
        """
        检测JS是否响应（通过执行测试JS）
        Returns: (is_stuck, reason)
        """
        elapsed = time.time() - self._last_activity_ts

        if elapsed < self.timeout:
            return False, ""

        try:
            # 尝试执行一个简单的JS命令
            result = js_execute_fn()
            if result:
                self._last_activity_ts = time.time()
                return False, ""
        except Exception as e:
            logger.warning(f"[StuckDetector] JS执行失败: {e}")

        self._failure_count += 1
        return True, f"JS无响应超过 {elapsed:.0f}s"

    def is_stuck(self) -> Tuple[bool, Optional[StuckType], str]:
        """
        综合检测：返回 (是否卡死, 卡死类型, 原因)
        需要外部传入当前鼠标位置、页面URL、屏幕hash、JS检测函数
        """
        # 注意：实际使用时需要外部传入这些值
        # 这里只记录时间状态
        elapsed = time.time() - self._last_activity_ts

        if elapsed > self.timeout * 2:
            # 超过2倍超时，认为卡死
            self._failure_count += 1
            return True, StuckType.PAGE_STUCK, f"超过 {elapsed:.0f}s 无活动"

        return False, None, ""


@dataclass
class ScreenHasher:
    """屏幕内容哈希（用于检测页面是否真正变化）"""

    @staticmethod
    def hash_screenshot(screenshot_bytes: bytes) -> str:
        """对截图bytes做MD5哈希"""
        return hashlib.md5(screenshot_bytes).hexdigest()[:12]

    @staticmethod
    def hash_dom(dom_text: str) -> str:
        """对DOM文本做哈希（用于纯文本检测）"""
        return hashlib.md5(dom_text.encode()).hexdigest()[:12]

    @staticmethod
    def hash_page_metrics(metrics: dict) -> str:
        """对页面指标做哈希（更轻量）"""
        key_parts = [
            str(metrics.get("url", "")),
            str(metrics.get("title", "")),
            str(metrics.get("body_text_length", 0)),
        ]
        return hashlib.md5("|".join(key_parts).encode()).hexdigest()[:12]


# 全局单例
_stuck_detector: Optional[StuckDetector] = None


def get_stuck_detector() -> StuckDetector:
    global _stuck_detector
    if _stuck_detector is None:
        _stuck_detector = StuckDetector()
    return _stuck_detector
