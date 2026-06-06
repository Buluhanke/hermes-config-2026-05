import datetime
from dataclasses import dataclass
from enum import Enum

# ============================================================================
# 时段定义 — 根据用户实际作息调整
# ============================================================================
class TimeZone(Enum):
    WORK = "work"        # 工作时间
    EVENING = "evening"  # 傍晚/回家
    NIGHT = "night"      # 深夜
    MORNING = "morning"  # 清晨

@dataclass
class RhythmContext:
    hour: int
    weekday: int          # 0=周一 6=周日
    zone: TimeZone
    is_weekend: bool
    should_proactive: bool
    urgency_cap: str      # 允许的最高打扰等级

# ============================================================================
# 节奏决策 — 纯函数，零副作用
# ============================================================================
def get_rhythm() -> RhythmContext:
    now = datetime.datetime.now()
    h, wd = now.hour, now.weekday()
    is_weekend = wd >= 5

    # 边界值按用户实际作息调整。常见配置：
    #   工作日 9-18 = work, 18-22 = evening, 22-6 = night, 6-9 = morning
    #   周末 全天 evening 边界
    if 9 <= h < 18 and not is_weekend:
        zone = TimeZone.WORK
        proactive = True
        cap = "high"
    elif 18 <= h < 22:
        zone = TimeZone.EVENING
        proactive = True
        cap = "medium"
    elif h >= 22 or h < 6:
        zone = TimeZone.NIGHT
        proactive = False
        cap = "critical_only"
    else:
        zone = TimeZone.MORNING
        proactive = False
        cap = "medium"

    return RhythmContext(h, wd, zone, is_weekend, proactive, cap)


# ============================================================================
# 决策辅助
# ============================================================================
def should_send_message(level: str) -> bool:
    """决策：此刻是否应发送某等级的消息。

    Levels: low (0), medium (1), high (2), critical_only (3)
    Cap:   low (0), medium (1), high (2), critical_only (99)
    """
    ctx = get_rhythm()
    priority = {"low": 0, "medium": 1, "high": 2, "critical_only": 3}
    cap_val = {"low": 0, "medium": 1, "high": 2, "critical_only": 99}
    if not ctx.should_proactive and level != "critical_only":
        return False
    return priority.get(level, 0) <= cap_val.get(ctx.urgency_cap, 0)


# ============================================================================
# 使用示例 — 必须包在 if __name__ == "__main__": 里，否则 import 时会触发！
# 详见 proactive-execution 规则18
# ============================================================================
if __name__ == "__main__":
    ctx = get_rhythm()
    print(f"当前时区: {ctx.zone.value}, 可主动: {ctx.should_proactive}, cap: {ctx.urgency_cap}")
    for lvl in ["low", "medium", "high", "critical_only"]:
        print(f"  发送 {lvl}: {should_send_message(lvl)}")
