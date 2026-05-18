"""
Resilience Engine - 自愈引擎
Watchdog + 熔断器 + 恢复策略链

模块:
- watchdog: 核心看门狗（超时检测 + 策略执行 + 熔断）
- stuck_detector: 卡死检测器（鼠标静止、页面僵死、JS无响应）
- blank_screen_detector: 白屏检测器（纯白/黑屏、DOM空、渲染失败）
- captcha_router: 验证码路由（滑块/点选/短信/二维码 → 策略分发）
- login_detector: 登录失效检测 + 自动重登
- network_handler: 网络异常分类 + 恢复执行
- checkpoint: 断点续传（状态快照 + 恢复 + 跨会话）
"""

from resilience_engine.watchdog import (
    Watchdog,
    RecoveryStrategy,
    CircuitState,
    get_watchdog,
)

from resilience_engine.stuck_detector import (
    StuckDetector,
    StuckType,
    ScreenHasher,
    get_stuck_detector,
)

from resilience_engine.blank_screen_detector import (
    BlankScreenDetector,
    BlankScreenType,
    BlankScreenRecovery,
    get_blank_screen_detector,
)

from resilience_engine.captcha_router import (
    CaptchaRouter,
    CaptchaType,
    CaptchaRoute,
    SliderTrajectoryGenerator,
    get_captcha_router,
)

from resilience_engine.login_detector import (
    LoginDetector,
    LoginState,
    AutoRelogin,
    get_login_detector,
)

from resilience_engine.network_handler import (
    NetworkErrorType,
    NetworkErrorClassifier,
    NetworkRecoveryExecutor,
    RateLimiter,
    execute_network_recovery,
)

from resilience_engine.checkpoint import (
    Checkpoint,
    CheckpointStatus,
    CheckpointManager,
    TaskStep,
    get_checkpoint_manager,
)

__all__ = [
    # 核心
    "Watchdog",
    "RecoveryStrategy",
    "CircuitState",
    "get_watchdog",

    # 卡死检测
    "StuckDetector",
    "StuckType",
    "ScreenHasher",
    "get_stuck_detector",

    # 白屏检测
    "BlankScreenDetector",
    "BlankScreenType",
    "BlankScreenRecovery",
    "get_blank_screen_detector",

    # 验证码路由
    "CaptchaRouter",
    "CaptchaType",
    "CaptchaRoute",
    "SliderTrajectoryGenerator",
    "get_captcha_router",

    # 登录检测
    "LoginDetector",
    "LoginState",
    "AutoRelogin",
    "get_login_detector",

    # 网络处理
    "NetworkErrorType",
    "NetworkErrorClassifier",
    "NetworkRecoveryExecutor",
    "RateLimiter",
    "execute_network_recovery",

    # 断点续传
    "Checkpoint",
    "CheckpointStatus",
    "CheckpointManager",
    "TaskStep",
    "get_checkpoint_manager",
]
