"""
验证码自动路由
检测：滑块、点选、短信、QQ/微信扫码、行为验证码
自动路由：OCR破解 / 人工介入 / 任务跳过
"""

import time
import logging
from typing import Tuple, Optional, List, Callable
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class CaptchaType(Enum):
    SLIDER = "slider"                   # 滑块验证
    CLICK_SELECT = "click_select"       # 点选验证（文字/图片）
    SMS_CODE = "sms_code"               # 短信验证码
    EMAIL_CODE = "email_code"           # 邮件验证码
    QR_SCAN = "qr_scan"                 # 二维码扫码（QQ/微信）
    BEHAVIOR = "behavior"               # 行为验证码（极验等）
    GEETEST = "geetest"                 # 极验第三代
    TINGTING = "tingting"               # 腾讯防水帽
    UNKNOWN = "unknown"


@dataclass
class CaptchaRouter:
    """
    验证码自动路由
    检测验证码类型 → 选择破解策略 → 执行或人工介入
    """

    # OCR/图像识别能力（需要外部接入）
    ocr_enabled: bool = False           # 是否启用OCR
    image_match_enabled: bool = False    # 是否启用图像匹配
    human_tolerance: int = 3            # 连续多少次验证码后通知人工

    # 状态
    _captcha_count: int = 0
    _last_captcha_ts: float = field(default_factory=time.time)
    _captcha_history: List[dict] = field(default_factory=list)

    def reset(self):
        self._captcha_count = 0
        self._captcha_history = []

    def detect_captcha(
        self,
        page_text: str,
        page_url: str,
        modal_text: str = "",
        screenshot_hint: str = ""
    ) -> Tuple[bool, Optional[CaptchaType], str]:
        """
        检测页面是否有验证码
        Returns: (is_captcha, captcha_type, hint)
        """
        combined = (page_text + modal_text).lower()

        # 滑块验证码特征
        slider_keywords = [
            "滑动验证", "拖动滑块", "拖动完成拼图", "向右滑动",
            "slide to verify", "drag the slider", "sliders puzzle"
        ]
        if any(kw in combined for kw in slider_keywords):
            self._captcha_count += 1
            return True, CaptchaType.SLIDER, "检测到滑块验证"

        # 点选验证码特征
        click_keywords = [
            "点击", "依次点击", "验证图", "文字点选", "图片点选",
            "click on the", "select all images with", "verify by clicking"
        ]
        if any(kw in combined for kw in click_keywords):
            self._captcha_count += 1
            return True, CaptchaType.CLICK_SELECT, "检测到点选验证"

        # 短信/邮箱验证码
        sms_keywords = [
            "验证码", "code", "动态码", "短信验证码",
            "请输入手机验证码", "请输入邮箱验证码", "verification code"
        ]
        if any(kw in combined for kw in sms_keywords):
            if "短信" in combined or "sms" in combined:
                self._captcha_count += 1
                return True, CaptchaType.SMS_CODE, "检测到短信验证码"
            else:
                self._captcha_count += 1
                return True, CaptchaType.EMAIL_CODE, "检测到邮件验证码"

        # 二维码
        qr_keywords = [
            "扫码", "二维码", "用qq/微信扫码", "qr code",
            "scan with", "请使用微信扫码", "请使用qq扫码"
        ]
        if any(kw in combined for kw in qr_keywords):
            self._captcha_count += 1
            return True, CaptchaType.QR_SCAN, "检测到二维码验证"

        # 行为验证码（极验）
        behavior_keywords = [
            "尝试次数过多", "行为验证", "security check",
            "geetest", "极验", "gt3", "completing"
        ]
        if any(kw in combined for kw in behavior_keywords):
            self._captcha_count += 1
            return True, CaptchaType.BEHAVIOR, "检测到行为验证码"

        return False, None, ""

    def get_route(self, captcha_type: CaptchaType) -> "CaptchaRoute":
        """
        根据验证码类型返回路由策略
        """
        routes = {
            CaptchaType.SLIDER: CaptchaRoute(
                type=captcha_type,
                strategy="ocr" if self.ocr_enabled else "human",
                actions=["detect_slider_position", "calculate_trajectory", "simulate_drag"],
                fallback="human"
            ),
            CaptchaType.CLICK_SELECT: CaptchaRoute(
                type=captcha_type,
                strategy="image_match" if self.image_match_enabled else "human",
                actions=["detect_click_positions", "match_images", "execute_clicks"],
                fallback="skip_task"
            ),
            CaptchaType.SMS_CODE: CaptchaRoute(
                type=captcha_type,
                strategy="manual",
                actions=["wait_for_sms", "detect_sms_from_notification"],
                fallback="skip_task"
            ),
            CaptchaType.EMAIL_CODE: CaptchaRoute(
                type=captcha_type,
                strategy="manual",
                actions=["wait_for_email", "fetch_email_code"],
                fallback="skip_task"
            ),
            CaptchaType.QR_SCAN: CaptchaRoute(
                type=captcha_type,
                strategy="human",
                actions=["alert_user_scan_qr"],
                fallback="skip_task"
            ),
            CaptchaType.BEHAVIOR: CaptchaRoute(
                type=captcha_type,
                strategy="wait" if self.ocr_enabled else "human",
                actions=["wait_for_auto_pass", "detect_slider", "simulate_behavior"],
                fallback="escape_hatch"
            ),
        }
        return routes.get(captcha_type, CaptchaRoute(
            type=captcha_type,
            strategy="human",
            actions=["alert_human"],
            fallback="escape_hatch"
        ))

    def should_notify_human(self) -> bool:
        """判断是否需要通知人工"""
        return self._captcha_count >= self.human_tolerance

    def record_captcha(self, captcha_type: CaptchaType, outcome: str):
        """记录验证码历史"""
        self._captcha_history.append({
            "type": captcha_type.value,
            "outcome": outcome,
            "timestamp": time.time()
        })
        # 保留最近10条
        self._captcha_history = self._captcha_history[-10:]


@dataclass
class CaptchaRoute:
    """验证码路由策略"""
    type: CaptchaType
    strategy: str          # "ocr" | "image_match" | "manual" | "wait" | "human"
    actions: List[str]     # 执行步骤
    fallback: str          # 兜底策略


# 滑块轨迹生成器（用于模拟人类滑动）
@dataclass
class SliderTrajectoryGenerator:
    """
    生成人类化的滑块轨迹
    核心：不是直线，而是不规则加速/减速曲线
    """

    @staticmethod
    def generate_trajectory(distance: int, duration_ms: int = 1500) -> List[Tuple[int, float]]:
        """
        生成滑块轨迹点
        Args:
            distance: 目标距离（像素）
            duration_ms: 滑动时长（毫秒）
        Returns: [(x, timestamp_ms), ...]
        """
        import random

        points = []
        num_steps = int(duration_ms / 16)  # 约60fps
        t = 0

        # 使用缓动函数（先快后慢，模拟人类）
        # 贝塞尔曲线近似：t^2 * (3 - 2t) = 6t^5 - 15t^4 + 10t^3

        for i in range(num_steps + 1):
            progress = i / num_steps
            # 缓动曲线
            eased = progress * progress * (3 - 2 * progress)

            # 添加随机抖动（模拟人类不稳定）
            jitter = random.uniform(-2, 2) if i > num_steps * 0.1 else 0

            x = int(eased * distance + jitter)
            points.append((x, t))

            t += 16  # 约60fps

        # 确保最后一点精确到达目标
        points[-1] = (distance, t)

        return points

    @staticmethod
    def generate_human_pause_points(num_pauses: int = 2) -> List[Tuple[int, int]]:
        """
        生成人类会在滑动中停顿的位置
        Returns: [(position, pause_duration_ms), ...]
        """
        import random
        pauses = []
        for _ in range(num_pauses):
            # 在20%-80%路程之间随机位置停顿
            pos = random.uniform(0.2, 0.8)
            duration = random.randint(100, 400)  # 停顿100-400ms
            pauses.append((pos, duration))
        return pauses


# 全局单例
_captcha_router: Optional[CaptchaRouter] = None


def get_captcha_router() -> CaptchaRouter:
    global _captcha_router
    if _captcha_router is None:
        _captcha_router = CaptchaRouter()
    return _captcha_router
