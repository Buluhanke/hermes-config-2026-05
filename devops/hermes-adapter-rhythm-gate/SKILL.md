---
name: hermes-adapter-rhythm-gate
description: 给 hermes-agent 的 platform adapter（如 telegram/feishu/weixin/qqbot）加 rhythm/通知门控的工作流。dry-run 默认开，按 zone×urgency 决定直发还是入队。Step 1 of "Hermes 真人化" — 4 个真实坑。
---

# Hermes Adapter Rhythm Gate

## 目标
在 `gateway/platforms/<platform>.py` 的 `send()` 方法顶部加节奏判断。深夜/morning zone 只放 critical；其它等级入队 `~/.hermes/queue/messages.jsonl`（由 cron `drain_watchdog.sh` flush）。

## 接入配方（已验证 for telegram.py，2026-06-04）

### 1. 顶部 import 块（紧跟 `logger = logging.getLogger(__name__)` 之后）
```python
import sys
from pathlib import Path
# 顶部已经有 logging/os 的话直接加这两行

# --- Hermes rhythm gate ---
# Wrap every <platform> outbound in should_send_message() so 深夜只发 critical。
# Dry-run by default: set HERMES_RHYTHM_DRY_RUN=0 to actually gate.
_RHYTHM_DRY_RUN = os.getenv("HERMES_RHYTHM_DRY_RUN", "1") == "1"
_RHYTHM_SCRIPTS = str(Path.home() / ".hermes" / "scripts")
if _RHYTHM_SCRIPTS not in sys.path:
    sys.path.insert(0, _RHYTHM_SCRIPTS)

# hermes module logger 默认 WARNING — 提 INFO 才能在 gateway.log 看到拦截日志
if logger.getEffectiveLevel() > logging.INFO:
    logger.setLevel(logging.INFO)

try:
    from hermes_notify import should_send_message as _rhythm_should_send
    from hermes_notify import queue_message as _rhythm_queue
    from hermes_notify import get_rhythm as _rhythm_get
    _RHYTHM_AVAILABLE = True
except Exception as _rhythm_import_err:
    logger.warning("rhythm gate unavailable: %s — sends will not be gated", _rhythm_import_err)
    _RHYTHM_AVAILABLE = False
    _RHYTHM_DRY_RUN = True  # 强制 dry-run，绝不静默 drop
    from typing import Any as _Any
    def _rhythm_should_send(level: str) -> bool:
        return True
    def _rhythm_queue(msg: str, level: str) -> _Any:
        return "unavailable"
    def _rhythm_get() -> _Any:
        return None
```

### 2. send() 入口（whitespace check 之后、原 try: 之前）
```python
        # Skip whitespace-only text...
        if not content or not content.strip():
            return SendResult(success=True, message_id=None)

        # --- Rhythm gate (Hermes Step 1) ---
        if _RHYTHM_AVAILABLE:
            urgency = "medium"
            if metadata:
                md_urg = metadata.get("urgency")
                if isinstance(md_urg, str) and md_urg in ("low", "medium", "high", "critical_only"):
                    urgency = md_urg
            try:
                _ctx = _rhythm_get()
                if not _rhythm_should_send(urgency):
                    if _RHYTHM_DRY_RUN:
                        logger.info(
                            "[rhythm DRY-RUN] would queue: urgency=%s zone=%s cap=%s chat_id=%s preview=%r",
                            urgency, _ctx.zone.value, _ctx.urgency_cap, chat_id, (content or "")[:60],
                        )
                    else:
                        qid = _rhythm_queue(content, urgency)
                        logger.info("[rhythm] queued: id=%s ...", qid)
                        return SendResult(
                            success=True, message_id=None,
                            raw_response={"rhythm": "queued", "queue_id": qid},
                        )
            except Exception as _rg_err:
                logger.warning("rhythm gate error, falling through to send: %s", _rg_err)

        try:  # 原 send body
```

## 4 个真实坑（必读）

1. **`__name__` 守卫**：从用户给的自包含脚本导入时，文件末尾的 demo print **必须** `if __name__ == "__main__":` 守卫。漏了守卫，import 时顶层 print 触发，看起来像"主程序跑了"——rhythm.py 第一次就是这问题，污染 import 链。

2. **hermes module logger 默认 WARNING**：INFO 静默。patch 里加 `if logger.getEffectiveLevel() > INFO: logger.setLevel(INFO)` 才能在 `~/.hermes/logs/gateway.log` 看到 `[rhythm DRY-RUN]` 日志。

3. **launchd plist 真重启**：`hermes gateway start` 只更新配置不真 load。**真重启一行**：`launchctl load -w ~/Library/LaunchAgents/ai.hermes.gateway.plist` — 自动顶替旧的 `gateway run --replace` 进程。

4. **`hermes send` CLI 不走 adapter.send**：走 `send_message_tool` 独立路径。**adapter 层拦截只在 "agent 主动响应 telegram 消息" 时触发**——`hermes send "msg"` 测试不到。要测就用真消息进。

## 验证清单

- [ ] 模块 import 加载 rhythm（`_RHYTHM_AVAILABLE=True, _RHYTHM_DRY_RUN=True`）
- [ ] 8 个 zone×urgency 组合行为正确（用 fake ctx 或真 rhythm 模块）
- [ ] 异常 import 退化 dry-run（删 ~/.hermes/scripts 看是否 warning + 放行）
- [ ] Enforce mode 真入队（设 HERMES_RHYTHM_DRY_RUN=0，跑 night+medium 看队列文件多行）
- [ ] `launchctl load -w` 重启后 `gateway.log` 有 `[rhythm DRY-RUN]` 日志
- [ ] 已有 `_bot`/`_send_path_degraded`/`whitespace` 检查行为不变

## 风险

- 改 hermes-agent 源码，每个 patch 是产品级爆炸半径
- dry-run 必须默认开（`HERMES_RHYTHM_DRY_RUN=1` 默认值）— 上线切 enforce 前用户必须显式确认
- 任何被改的 adapter，**测试时**用 `object.__new__()` 绕开 __init__（注释里说测试用此方法），不要拉起真实 bot
- 队列文件 `~/.hermes/queue/messages.jsonl` 需要 cron flush（drain_watchdog.sh，job b2ad855429b2，每 5 分钟）
