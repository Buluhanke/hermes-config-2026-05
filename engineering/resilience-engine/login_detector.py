"""
登录失效检测 + 自动重登
检测：Cookie失效、Session过期、跳转登录页、401/403响应
自动重登：保存凭证 → 检测失效 → 重登 → 恢复任务
"""

import time
import json
import logging
from typing import Tuple, Optional, List, Callable
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class LoginState(Enum):
    UNKNOWN = "unknown"
    LOGGED_IN = "logged_in"
    LOGGED_OUT = "logged_out"
    EXPIRED = "expired"           # 过期（cookie还在但失效）
    NEED_REFRESH = "need_refresh"  # 需要刷新token


@dataclass
class LoginDetector:
    """
    登录失效检测器
    """

    # 检测参数
    check_interval: int = 60        # 定期检查间隔（秒）
    session_timeout: int = 3600     # Session超时时间（默认1小时）

    # 登录指标（需要根据目标网站调整）
    logged_in_indicators: List[str] = field(default_factory=lambda: [
        "退出", "我的", "个人中心", "设置", "logout", "sign out",
        "account", "profile", "会员", "已登录"
    ])
    logged_out_indicators: List[str] = field(default_factory=lambda: [
        "登录", "login", "sign in", "注册", "免费试用"
    ])

    # 登录检测URL（API端点，通常返回当前用户信息）
    check_url: Optional[str] = None
    check_api_fn: Optional[Callable[[], dict]] = None  # 异步检查函数

    # 状态
    _last_check_ts: float = field(default_factory=time.time)
    _last_login_ts: Optional[float] = None
    _login_state: LoginState = LoginState.UNKNOWN
    _failure_count: int = 0

    def reset(self):
        self._last_check_ts = time.time()
        self._login_state = LoginState.UNKNOWN
        self._failure_count = 0

    def mark_logged_in(self):
        """标记为已登录"""
        self._login_state = LoginState.LOGGED_IN
        self._last_login_ts = time.time()
        self._failure_count = 0
        logger.info("[LoginDetector] 标记为已登录")

    def mark_logged_out(self):
        """标记为已登出"""
        self._login_state = LoginState.LOGGED_OUT
        logger.info("[LoginDetector] 标记为已登出")

    def check_by_page_text(
        self,
        page_text: str,
        page_url: str = ""
    ) -> Tuple[LoginState, str]:
        """
        通过页面文本检测登录状态
        Returns: (login_state, reason)
        """
        combined = page_text.lower()
        url_lower = page_url.lower()

        # 登出指标检测
        for indicator in self.logged_out_indicators:
            if indicator in combined:
                # 特殊判断：如果URL是登录页本身
                if "login" in url_lower or "signin" in url_lower:
                    self._login_state = LoginState.LOGGED_OUT
                    return LoginState.LOGGED_OUT, f"当前在登录页: {indicator}"

                # 如果页面同时有登录和登出指标，可能是错误页
                for li in self.logged_in_indicators:
                    if li in combined:
                        # 两者都有，不确定
                        return LoginState.UNKNOWN, f"登录/登出指标同时存在"

                # 纯登出指标
                self._login_state = LoginState.LOGGED_OUT
                return LoginState.LOGGED_OUT, f"检测到登出指标: {indicator}"

        # 已登录指标检测
        for indicator in self.logged_in_indicators:
            if indicator in combined:
                self._login_state = LoginState.LOGGED_IN
                self._last_login_ts = time.time()
                return LoginState.LOGGED_IN, f"检测到已登录指标: {indicator}"

        # 检查URL是否在登录相关的路径上
        login_paths = ["/login", "/signin", "/auth/login", "/account/login"]
        if any(path in url_lower for path in login_paths):
            self._login_state = LoginState.LOGGED_OUT
            return LoginState.LOGGED_OUT, "URL显示在登录页"

        # 无法判断
        return LoginState.UNKNOWN, "页面文本无法判断登录状态"

    def check_by_api(
        self,
        api_check_fn: Callable[[], Tuple[bool, dict]]
    ) -> Tuple[LoginState, str]:
        """
        通过API检查登录状态（更可靠）
        Args:
            api_check_fn: 返回 (is_logged_in, response_dict)
        Returns: (login_state, reason)
        """
        try:
            is_logged_in, resp = api_check_fn()

            if is_logged_in:
                self._login_state = LoginState.LOGGED_IN
                self._last_login_ts = time.time()
                self._failure_count = 0
                return LoginState.LOGGED_IN, "API确认已登录"

            # API返回未登录
            if resp.get("code") in [401, 403]:
                self._login_state = LoginState.EXPIRED
                return LoginState.EXPIRED, f"API返回认证失败: {resp.get('code')}"

            self._login_state = LoginState.LOGGED_OUT
            return LoginState.LOGGED_OUT, "API确认未登录"

        except Exception as e:
            logger.warning(f"[LoginDetector] API检查失败: {e}")
            return LoginState.UNKNOWN, f"API检查异常: {e}"

    def check_by_http_status(
        self,
        status_code: int,
        response_url: str
    ) -> Tuple[LoginState, str]:
        """
        通过HTTP状态码检测登录失效
        Args:
            status_code: HTTP状态码
            response_url: 响应URL
        """
        # 401/403 通常是认证失败
        if status_code in [401, 403]:
            self._login_state = LoginState.EXPIRED
            return LoginState.EXPIRED, f"HTTP {status_code}: 认证失效"

        # 302/301 重定向到登录页
        if status_code in [302, 301]:
            if "login" in response_url.lower():
                self._login_state = LoginState.LOGGED_OUT
                return LoginState.LOGGED_OUT, "重定向到登录页"

        return LoginState.UNKNOWN, ""

    def needs_recheck(self) -> bool:
        """检查是否需要重新验证登录状态"""
        elapsed = time.time() - self._last_check_ts
        if elapsed > self.check_interval:
            self._last_check_ts = time.time()
            return True
        return False

    def is_session_expired(self) -> bool:
        """检查session是否过期（基于时间）"""
        if self._last_login_ts is None:
            return True
        elapsed = time.time() - self._last_login_ts
        return elapsed > self.session_timeout


@dataclass
class AutoRelogin:
    """
    自动重登流程
    """

    # 重登配置
    max_relogin_attempts: int = 3
    relogin_retry_delay: float = 5.0   # 重试间隔（秒）
    credentials_file: str = "~/.hermes/login_credentials.json"

    # 状态
    _relogin_count: int = 0
    _credentials: Optional[dict] = None

    def load_credentials(self) -> Optional[dict]:
        """从文件加载保存的登录凭证"""
        import os
        path = os.path.expanduser(self.credentials_file)
        if not os.path.exists(path):
            logger.warning(f"[AutoRelogin] 凭证文件不存在: {path}")
            return None

        try:
            with open(path, 'r') as f:
                self._credentials = json.load(f)
            logger.info("[AutoRelogin] 已加载登录凭证")
            return self._credentials
        except Exception as e:
            logger.error(f"[AutoRelogin] 加载凭证失败: {e}")
            return None

    def save_credentials(self, credentials: dict):
        """保存登录凭证到文件"""
        import os
        path = os.path.expanduser(self.credentials_file)
        os.makedirs(os.path.dirname(path), exist_ok=True)

        with open(path, 'w') as f:
            json.dump(credentials, f, indent=2)
        logger.info("[AutoRelogin] 已保存登录凭证")
        self._credentials = credentials

    def clear_credentials(self):
        """清除保存的凭证"""
        import os
        path = os.path.expanduser(self.credentials_file)
        if os.path.exists(path):
            os.remove(path)
            logger.info("[AutoRelogin] 已清除登录凭证")

    def relogin(
        self,
        login_fn: Callable[[dict], bool],
        credentials: Optional[dict] = None,
        extra_context: Optional[dict] = None
    ) -> Tuple[bool, str]:
        """
        执行自动重登
        Args:
            login_fn: 登录函数，接收credentials dict，返回是否成功
            credentials: 登录凭证（用户名、密码等）
            extra_context: 额外上下文（page、browser等）
        Returns: (success, message)
        """
        creds = credentials or self._credentials or self.load_credentials()

        if not creds:
            return False, "无可用登录凭证，需要人工输入"

        for attempt in range(1, self.max_relogin_attempts + 1):
            logger.info(f"[AutoRelogin] 重登尝试 {attempt}/{self.max_relogin_attempts}")

            try:
                success = login_fn(creds)
                if success:
                    self._relogin_count = 0
                    logger.info("[AutoRelogin] 重登成功")
                    return True, "重登成功"

            except Exception as e:
                logger.warning(f"[AutoRelogin] 重登失败: {e}")

            if attempt < self.max_relogin_attempts:
                time.sleep(self.relogin_retry_delay)

        self._relogin_count += 1
        return False, f"重登失败，已尝试 {self.max_relogin_attempts} 次"

    def get_relogin_count(self) -> int:
        return self._relogin_count


# 全局单例
_login_detector: Optional[LoginDetector] = None


def get_login_detector() -> LoginDetector:
    global _login_detector
    if _login_detector is None:
        _login_detector = LoginDetector()
    return _login_detector
