"""
白屏检测器
检测：纯白/黑屏、渲染失败、DOM为空、字体/图片加载失败
"""

import time
import logging
from typing import Tuple, Optional, List
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class BlankScreenType(Enum):
    PURE_WHITE = "pure_white"           # 纯白屏
    PURE_BLACK = "pure_black"           # 纯黑屏
    EMPTY_DOM = "empty_dom"             # DOM为空
    RENDER_FAILED = "render_failed"     # 渲染失败标记
    RESOURCE_LOAD_FAILED = "resource_failed"  # 资源加载失败
    CAPTCHA_PAGE = "captcha_page"        # 验证码/安全页
    LOGIN_REDIRECT = "login_redirect"  # 跳转到了登录页


@dataclass
class BlankScreenDetector:
    """
    白屏检测器
    通过多种方式判断页面是否正常渲染
    """

    # 白屏判断阈值
    white_pixel_ratio_threshold: float = 0.85  # 超过85%白色像素认为是白屏
    black_pixel_ratio_threshold: float = 0.90   # 超过90%黑色像素认为是黑屏
    min_dom_text_length: int = 50              # DOM文本少于50字符认为异常
    min_images_count: int = 1                 # 页面图片数量下限

    # 检测历史（用于判断临时加载 vs 真正白屏）
    _consecutive_blank_count: int = 0
    _last_check_ts: float = field(default_factory=time.time)

    def reset(self):
        self._consecutive_blank_count = 0
        self._last_check_ts = time.time()

    def check_by_screenshot(
        self,
        screenshot_bytes: bytes,
        width: int = 1920,
        height: int = 1080
    ) -> Tuple[bool, BlankScreenType, float]:
        """
        通过截图分析白屏
        Args:
            screenshot_bytes: PNG/JPEG截图bytes
            width, height: 截图分辨率
        Returns: (is_blank, blank_type, white_pixel_ratio)
        """
        # 简化实现：实际应分析像素颜色分布
        # 这里给出逻辑框架

        try:
            # 统计白色/黑色像素比例
            # 白色: RGB > 240, 黑色: RGB < 15
            # 实际实现需要用PIL或opencv

            # 伪代码：
            # white_count = sum(1 for pixel in pixels if all(c > 240 for c in pixel[:3]))
            # white_ratio = white_count / total_pixels

            # 临时用文件大小估算（仅作框架演示）
            file_size_mb = len(screenshot_bytes) / 1024 / 1024

            # 正常页面截图通常 > 100KB，纯白/黑屏通常 < 30KB
            if file_size_mb < 0.03:
                self._consecutive_blank_count += 1
                return True, BlankScreenType.PURE_WHITE, 0.95

            self._consecutive_blank_count = 0
            return False, BlankScreenType.PURE_WHITE, 0.0

        except Exception as e:
            logger.error(f"[BlankScreenDetector] 截图分析失败: {e}")
            return False, BlankScreenType.PURE_WHITE, 0.0

    def check_by_dom(
        self,
        dom_text: str,
        images_count: int = 0,
        scripts_count: int = 0
    ) -> Tuple[bool, BlankScreenType, str]:
        """
        通过DOM分析白屏
        Args:
            dom_text: document.body.innerText 或完整DOM文本
            images_count: <img> 标签数量
            scripts_count: <script> 标签数量
        Returns: (is_blank, blank_type, reason)
        """
        dom_length = len(dom_text.strip())

        # 情况1：DOM几乎为空
        if dom_length < self.min_dom_text_length:
            self._consecutive_blank_count += 1
            return True, BlankScreenType.EMPTY_DOM, f"DOM文本仅 {dom_length} 字符"

        # 情况2：没有任何图片和脚本（正常页面通常有）
        # 但如果DOM文本够长，可能是单文字页面
        if images_count == 0 and scripts_count == 0 and dom_length < 200:
            self._consecutive_blank_count += 1
            return True, BlankScreenType.EMPTY_DOM, "无图片无脚本且文本短"

        # 情况3：常见验证码/安全页关键词
        captcha_keywords = [
            "验证码", "captcha", "安全验证", "请拖动", "滑动验证",
            "人机验证", "challenge", "prove you are human"
        ]
        if any(kw in dom_text.lower() for kw in captcha_keywords):
            self._consecutive_blank_count += 1
            return True, BlankScreenType.CAPTCHA_PAGE, "检测到验证码页面"

        # 情况4：跳转到了登录页
        login_keywords = ["登录", "login", "sign in", "账户登录", "密码登录"]
        if any(kw in dom_text.lower() for kw in login_keywords):
            # 登录页本身不是白屏，但可能说明会话失效
            return True, BlankScreenType.LOGIN_REDIRECT, "页面跳转到登录页"

        self._consecutive_blank_count = 0
        return False, BlankScreenType.PURE_WHITE, ""

    def check_by_network_errors(
        self,
        failed_requests: List[dict]
    ) -> Tuple[bool, BlankScreenType, str]:
        """
        通过网络请求失败判断资源加载问题
        Args:
            failed_requests: [{"url": "...", "error": "..."}, ...]
        Returns: (is_blank, blank_type, reason)
        """
        if not failed_requests:
            return False, BlankScreenType.PURE_WHITE, ""

        # 关键资源加载失败（CSS/JS/图片）
        critical_failures = [
            r for r in failed_requests
            if any(ext in r.get("url", "") for ext in [".css", ".js", ".png", ".jpg", ".svg"])
        ]

        if len(critical_failures) >= 3:
            self._consecutive_blank_count += 1
            return True, BlankScreenType.RESOURCE_LOAD_FAILED, \
                f"关键资源加载失败: {len(critical_failures)} 个"

        return False, BlankScreenType.PURE_WHITE, ""

    def check_by_js_errors(
        self,
        js_errors: List[str]
    ) -> Tuple[bool, BlankScreenType, str]:
        """
        通过JS错误判断渲染是否失败
        Args:
            js_errors: console error messages
        Returns: (is_blank, blank_type, reason)
        """
        # 致命JS错误
        fatal_errors = [
            "Failed to load resource",
            "net::ERR_",
            "TypeError: Cannot",
            "SyntaxError:",
            "ReferenceError:",
        ]

        fatal_count = sum(
            1 for err in js_errors
            if any(fe in err for fe in fatal_errors)
        )

        if fatal_count >= 2:
            self._consecutive_blank_count += 1
            return True, BlankScreenType.RENDER_FAILED, \
                f"JS错误 {fatal_count} 条，可能渲染失败"

        return False, BlankScreenType.PURE_WHITE, ""

    def is_consecutive_blank(self, threshold: int = 2) -> bool:
        """连续多次检测都是白屏（排除临时加载抖动）"""
        return self._consecutive_blank_count >= threshold


@dataclass
class BlankScreenRecovery:
    """白屏恢复策略"""

    @staticmethod
    def get_recovery_actions(blank_type: BlankScreenType) -> List[str]:
        """根据白屏类型返回恢复动作序列"""
        strategies = {
            BlankScreenType.PURE_WHITE: [
                "wait:2",                    # 等2秒看是否临时加载
                "refresh",                  # 刷新
                "check_network",            # 检查网络
                "clear_cache:hard",         # 硬清除缓存
                "restart_browser_tab",      # 重开标签页
            ],
            BlankScreenType.PURE_BLACK: [
                "wait:1",
                "check_display_settings",   # 检查显示器设置
                "restart_browser_tab",
            ],
            BlankScreenType.EMPTY_DOM: [
                "wait:3",                    # 等待JS动态渲染
                "check_js_errors",
                "evaluate_js:window.scrollTo(0,0)",
                "refresh",
            ],
            BlankScreenType.RENDER_FAILED: [
                "check_js_errors",
                "refresh",
                "disable_extensions",
                "restart_browser",
            ],
            BlankScreenType.RESOURCE_LOAD_FAILED: [
                "check_proxy",
                "check_network",
                "bypass_cache",
                "retry_with_longer_timeout",
            ],
            BlankScreenType.CAPTCHA_PAGE: [
                "alert:人工介入",            # 通知人工处理
                "save_state",
                "escape_hatch",
            ],
            BlankScreenType.LOGIN_REDIRECT: [
                "check_login_state",
                "relogin_if_needed",
                "resume_task",
            ],
        }
        return strategies.get(blank_type, ["refresh", "alert:未知白屏类型"])

    @staticmethod
    def format_recovery_plan(blank_type: BlankScreenType, reason: str) -> str:
        """格式化恢复计划为可读文本"""
        actions = BlankScreenRecovery.get_recovery_actions(blank_type)
        plan = "\n".join(f"  {i+1}. {a}" for i, a in enumerate(actions))
        return f"""\
白屏检测报告:
  类型: {blank_type.value}
  原因: {reason}
  恢复计划:
{plan}
"""


# 全局单例
_blank_detector: Optional[BlankScreenDetector] = None


def get_blank_screen_detector() -> BlankScreenDetector:
    global _blank_detector
    if _blank_detector is None:
        _blank_detector = BlankScreenDetector()
    return _blank_detector
