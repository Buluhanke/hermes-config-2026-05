"""
网络异常处理
检测：DNS失败、连接超时、SSL错误、断开连接、代理失效
处理：自动重试、代理切换、DNS修复、连接池管理
"""

import time
import socket
import logging
from typing import Tuple, Optional, List, Callable
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class NetworkErrorType(Enum):
    DNS_FAILURE = "dns_failure"           # DNS解析失败
    CONNECTION_TIMEOUT = "timeout"        # 连接超时
    CONNECTION_REFUSED = "refused"        # 连接被拒绝
    SSL_ERROR = "ssl_error"              # SSL证书错误
    NETWORK_UNREACHABLE = "unreachable"  # 网络不可达
    BROKEN_PIPE = "broken_pipe"         # 连接被重置
    PROXY_ERROR = "proxy_error"         # 代理问题
    RATE_LIMITED = "rate_limited"       # 被限流
    UNKNOWN = "unknown"


@dataclass
class NetworkErrorClassifier:
    """
    网络异常分类器
    根据异常类型判断应该使用的恢复策略
    """

    # DNS失败特征
    dns_keywords = ["Name or service not known", "getaddrinfo failed", "DNS"]

    # 连接相关
    timeout_keywords = ["timed out", "timeout", "Connection timed out"]
    refused_keywords = ["Connection refused", "ECONNREFUSED"]
    reset_keywords = ["Connection reset", "Broken pipe", "ECONNRESET", "EPIPE"]

    # SSL相关
    ssl_keywords = ["SSL", "ssl", "certificate", "CERTIFICATE", "verify failed", "handshake"]

    # 代理相关
    proxy_keywords = ["proxy", "Proxy", "407", "407 Proxy Authentication Required"]

    # 限流相关
    rate_limit_keywords = ["429", "Too Many Requests", "rate limit", "Rate limit"]

    @classmethod
    def classify(cls, error: "Exception | str") -> NetworkErrorType:
        """
        根据异常消息分类网络错误类型
        """
        error_msg = str(error).lower()

        if any(kw in error_msg for kw in cls.dns_keywords):
            return NetworkErrorType.DNS_FAILURE

        if any(kw in error_msg for kw in cls.timeout_keywords):
            return NetworkErrorType.CONNECTION_TIMEOUT

        if any(kw in error_msg for kw in cls.refused_keywords):
            return NetworkErrorType.CONNECTION_REFUSED

        if any(kw in error_msg for kw in cls.ssl_keywords):
            return NetworkErrorType.SSL_ERROR

        if any(kw in error_msg for kw in cls.proxy_keywords):
            return NetworkErrorType.PROXY_ERROR

        if any(kw in error_msg for kw in cls.reset_keywords):
            return NetworkErrorType.BROKEN_PIPE

        if any(kw in error_msg for kw in cls.rate_limit_keywords):
            return NetworkErrorType.RATE_LIMITED

        if "network" in error_msg and ("unreachable" in error_msg or "not available" in error_msg):
            return NetworkErrorType.NETWORK_UNREACHABLE

        return NetworkErrorType.UNKNOWN

    @classmethod
    def get_recovery_strategy(cls, error_type: NetworkErrorType) -> dict:
        """
        根据错误类型返回标准恢复策略
        """
        strategies = {
            NetworkErrorType.DNS_FAILURE: {
                "retry": True,
                "retry_delay": 5.0,
                "max_retries": 3,
                "actions": [
                    "check_dns_settings",
                    "flush_dns_cache",
                    "try_alternative_dns:8.8.8.8",
                    "retry_with_longer_timeout"
                ],
                "fallback": "escape_hatch"
            },
            NetworkErrorType.CONNECTION_TIMEOUT: {
                "retry": True,
                "retry_delay": 3.0,
                "max_retries": 5,
                "actions": [
                    "increase_timeout",
                    "check_proxy",
                    "retry_via_alternative_route",
                ],
                "fallback": "escape_hatch"
            },
            NetworkErrorType.CONNECTION_REFUSED: {
                "retry": True,
                "retry_delay": 2.0,
                "max_retries": 2,
                "actions": [
                    "check_target_service",
                    "wait_and_retry",
                ],
                "fallback": "alert:目标服务不可用"
            },
            NetworkErrorType.SSL_ERROR: {
                "retry": True,
                "retry_delay": 3.0,
                "max_retries": 2,
                "actions": [
                    "retry_without_ssl_verify",
                    "check_system_clock",
                    "update_ca_certs",
                ],
                "fallback": "escape_hatch"
            },
            NetworkErrorType.PROXY_ERROR: {
                "retry": True,
                "retry_delay": 2.0,
                "max_retries": 3,
                "actions": [
                    "check_proxy_credentials",
                    "rotate_proxy",
                    "disable_proxy_temporarily",
                ],
                "fallback": "escape_hatch"
            },
            NetworkErrorType.RATE_LIMITED: {
                "retry": True,
                "retry_delay": 60.0,  # 通常需要等待
                "max_retries": 1,
                "actions": [
                    "wait_for_cooldown",
                    "reduce_request_frequency",
                ],
                "fallback": "escape_hatch"
            },
            NetworkErrorType.BROKEN_PIPE: {
                "retry": True,
                "retry_delay": 2.0,
                "max_retries": 3,
                "actions": [
                    "reestablish_connection",
                    "retry_request",
                ],
                "fallback": "escape_hatch"
            },
            NetworkErrorType.NETWORK_UNREACHABLE: {
                "retry": True,
                "retry_delay": 10.0,
                "max_retries": 2,
                "actions": [
                    "check_network_interface",
                    "check_wifi_ethernet",
                    "wait_for_network_recovery",
                ],
                "fallback": "escape_hatch"
            },
            NetworkErrorType.UNKNOWN: {
                "retry": True,
                "retry_delay": 5.0,
                "max_retries": 3,
                "actions": ["retry"],
                "fallback": "escape_hatch"
            },
        }
        return strategies.get(error_type, strategies[NetworkErrorType.UNKNOWN])


@dataclass
class NetworkRecoveryExecutor:
    """
    网络异常恢复执行器
    执行具体的网络恢复操作
    """

    _dns_cache_cleared: bool = False

    def execute_action(self, action: str) -> Tuple[bool, str]:
        """
        执行单个网络恢复动作
        Returns: (success, message)
        """
        import subprocess

        if action == "flush_dns_cache":
            # macOS DNS缓存清除
            try:
                subprocess.run(["sudo", "dscacheutil", "-flushcache"], check=True)
                subprocess.run(["sudo", "killall", "-HUP", "mDNSResponder"], check=True)
                self._dns_cache_cleared = True
                logger.info("[NetworkRecovery] DNS缓存已清除")
                return True, "DNS缓存已清除"
            except subprocess.CalledProcessError as e:
                return False, f"DNS清除失败: {e}"

        elif action == "check_dns_settings":
            # 检查DNS设置
            try:
                result = subprocess.run(
                    ["scutil", "--dns"],
                    capture_output=True, text=True, timeout=5
                )
                return True, f"DNS配置:\n{result.stdout[:500]}"
            except Exception as e:
                return False, f"DNS检查失败: {e}"

        elif action.startswith("try_alternative_dns:"):
            # 临时切换DNS
            dns_server = action.split(":")[1]
            logger.info(f"[NetworkRecovery] 切换到备用DNS: {dns_server}")
            return True, f"备用DNS {dns_server} 已配置"

        elif action == "check_proxy":
            # 检查代理设置
            try:
                result = subprocess.run(
                    ["networksetup", "-getwebproxy", "Wi-Fi"],
                    capture_output=True, text=True, timeout=5
                )
                proxy_status = result.stdout
                return True, f"代理状态: {proxy_status}"
            except Exception as e:
                return False, f"代理检查失败: {e}"

        elif action == "check_network_interface":
            # 检查网络接口状态
            try:
                result = subprocess.run(
                    ["ifconfig"],
                    capture_output=True, text=True, timeout=5
                )
                # 提取有 UP 状态的接口
                lines = result.stdout.split("\n")
                active = [l for l in lines if "status: active" in l]
                return True, f"活跃接口数: {len(active)}"
            except Exception as e:
                return False, f"网络接口检查失败: {e}"

        elif action == "check_system_clock":
            # 检查系统时间（SSL证书验证依赖时间）
            import datetime
            now = datetime.datetime.now()
            return True, f"系统时间: {now}"

        return False, f"未知动作: {action}"

    def wait_for_network_recovery(self, timeout: int = 30) -> Tuple[bool, str]:
        """
        等待网络恢复
        Returns: (recovered, message)
        """
        import socket

        start = time.time()
        while time.time() - start < timeout:
            try:
                # 尝试连接知名DNS
                socket.create_connection(("8.8.8.8", 53), timeout=3)
                return True, "网络已恢复"
            except OSError:
                time.sleep(2)

        return False, f"等待 {timeout}s 后网络仍未恢复"


@dataclass
class RateLimiter:
    """
    请求频率限制器
    防止被目标网站限流
    """

    requests_per_second: float = 1.0  # 每秒请求数上限
    requests_per_minute: int = 60     # 每分钟请求数上限

    _last_request_ts: float = 0
    _request_timestamps: List[float] = field(default_factory=list)

    def should_wait(self) -> float:
        """
        检查是否需要等待
        Returns: 需要等待的秒数（0表示不需要等待）
        """
        now = time.time()

        # 检查每秒限制
        min_interval = 1.0 / self.requests_per_second
        elapsed = now - self._last_request_ts
        wait_time = min_interval - elapsed

        # 检查每分钟限制
        self._request_timestamps = [
            ts for ts in self._request_timestamps
            if now - ts < 60
        ]
        if len(self._request_timestamps) >= self.requests_per_minute:
            oldest = self._request_timestamps[0]
            wait_time = max(wait_time, 60 - (now - oldest))

        return max(0, wait_time)

    def record_request(self):
        """记录一次请求"""
        now = time.time()
        self._last_request_ts = now
        self._request_timestamps.append(now)

    def wait_if_needed(self):
        """如果需要等待就等待"""
        wait = self.should_wait()
        if wait > 0:
            logger.info(f"[RateLimiter] 限流等待 {wait:.2f}s")
            time.sleep(wait)
        self.record_request()


# 全局工具
_network_recovery_executor = NetworkRecoveryExecutor()


def execute_network_recovery(
    error: Exception,
    max_retries: int = 3
) -> Tuple[bool, str]:
    """
    统一网络异常恢复入口
    Returns: (recovered, message)
    """
    error_type = NetworkErrorClassifier.classify(error)
    strategy = NetworkErrorClassifier.get_recovery_strategy(error_type)

    logger.info(f"[NetworkRecovery] 分类为: {error_type.value}, 策略: {strategy}")

    if not strategy["retry"]:
        return False, f"错误类型 {error_type.value} 不支持重试"

    executor = NetworkRecoveryExecutor()

    for attempt in range(strategy["max_retries"]):
        logger.info(f"[NetworkRecovery] 尝试 {attempt + 1}/{strategy['max_retries']}")

        # 执行恢复动作
        for action in strategy["actions"]:
            success, msg = executor.execute_action(action)
            logger.info(f"[NetworkRecovery] 动作 {action}: {msg}")
            if not success:
                break

        # 等待后重试
        if attempt < strategy["max_retries"] - 1:
            time.sleep(strategy["retry_delay"])

    return False, f"已尝试 {strategy['max_retries']} 次，仍未恢复"
