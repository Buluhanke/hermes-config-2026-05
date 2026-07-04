# Idle Trigger Pitfalls — 触发器自洽性 5 问 + 双轨时间戳模板

> v1.16.0 新增 (2026-07-01)。Failure 60 反例库配套模板。
> 写任何"多久没动 / 是否停滞 / 该触发了"类判断前必读。
> SKILL.md v1.16.0 changelog 引用本文件。

---

## 为什么需要这文件

v3.4 时间循环落地当天 (`2026-07-01 05:41`) idle_driver.py 心跳写了 `last_beat`, check_idle() 又用 `last_beat` 判断"是否 idle"。心跳每 5 分钟写一次 → 永远到不了 600s 阈值 → **4 小时 0 次 orchestrator, today_log 30+ 行全是 💓**。用户三次质问"6点到现在没动过"。

这是**结构问题不是行为问题**: agent 没偷懒, 是触发器本身有 bug。Failure 41-58 改规则改行为就行, **Failure 60 必须改代码 + 加测试 + 改 cron 频率**。

---

## 触发器自洽性 5 问 (写 idle / watchdog / cron 类脚本前必走)

任何判断"多久没动 / 是否停滞 / 该触发了"的逻辑, 落地前**0 思考**答这 5 问:

```
① 这个时间戳字段会不会被"会自己跑"的进程周期性更新?
   - 心跳脚本会更新 last_beat → ❌ 不能用作"多久没动"判断源
   - 监控脚本会更新 last_check → ❌ 不能用作"监控是否运行"判断源
   - cron 跑的健康检查会更新 last_health → ❌ 不能用作"系统是否健康"判断源

② 如果是 → 必须分两轨: last_beat (活着) + last_action (在干活)

③ last_action_at 只被"有意义的动作"更新 — 哪些算"有意义"?
   - ✅ orchestrator 跑完 / cron 任务完成 / 用户任务完成 / 看门狗告警
   - ❌ 心跳本身 / 健康检查本身 / 系统日志写入本身

④ 阈值配比满足 heartbeat_interval < idle_threshold / 2 ?
   - 改前: heartbeat=5min, idle_threshold=10min (5 < 5, 临界, 必踩)
   - 改后: heartbeat=5min, idle_threshold=20min (5 < 10, 安全)
   - 或:   heartbeat=2min, idle_threshold=10min (2 < 5, 安全)
   - 临界 = 易踩坑, 永远留 2x 安全余量

⑤ 兜底: 单 cron 漏了, 心跳能补吗?
   - heartbeat 阶段同步检测 idle_state, is_idle → 立即触发行动池
   - cron idle */N 单独再跑一次兜底
   - 双保险, 永远有一个在跑
```

**5 问任何一项答错 → 别进 cron, 必先改代码**。

---

## 双轨时间戳模板 (Python, 直接复用)

```python
import json
import time
from pathlib import Path

STATE = Path.home() / ".hermes" / "state"
HEARTBEAT_FILE = STATE / "heartbeat.json"


def now() -> int:
    return int(time.time())


def read_hb() -> dict:
    if HEARTBEAT_FILE.exists():
        try:
            return json.loads(HEARTBEAT_FILE.read_text())
        except Exception:
            pass
    return {}


def write_hb(hb: dict) -> None:
    HEARTBEAT_FILE.write_text(json.dumps(hb, ensure_ascii=False, indent=2))


# ── 核心: 心跳不算"活动" ─────────────────────────────
def beat(stage: str = "heartbeat") -> dict:
    """写心跳, 但 last_action_at 只被非心跳动作更新"""
    hb = read_hb()
    t = now()
    hb["last_beat"] = t
    hb["last_stage"] = stage
    hb.setdefault("last_action_at", t)   # 初始化兜底
    write_hb(hb)
    return hb


# ── 核心: 真动作必须显式调 ─────────────────────────────
def mark_action(name: str) -> None:
    """任何'有意义的动作' (orchestrator/看门狗/用户任务完成) 调用一次"""
    hb = read_hb()
    hb["last_action_at"] = now()
    hb["last_action"] = name
    write_hb(hb)


# ── 核心: idle 判断用 last_action_at ─────────────────────
def check_idle(idle_threshold_s: int = 300) -> dict:
    hb = read_hb()
    last = hb.get("last_action_at") or hb.get("last_beat", 0)
    since = now() - last if last else 999999
    return {
        "since_last_action_s": since,
        "last_action": hb.get("last_action", "init"),
        "is_idle": since >= idle_threshold_s,
        "is_stuck": since >= 3600,
        "is_stalled": since >= 7200,
    }


# ── 核心: 心跳阶段同步检测 (双保险) ─────────────────────
def main():
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else "heartbeat"

    if cmd == "heartbeat":
        beat()
        idle = check_idle()
        if idle["is_idle"]:
            # 不等 cron, 心跳阶段就触发
            run_idle_action_pool()
        return idle

    if cmd == "mark":
        # 外部 cron / 任务完成后调一次
        mark_action(sys.argv[2] if len(sys.argv) > 2 else "manual")
        return {"marked": True}
```

---

## 4 个反例代码片段 (Failure 60 + 同类已知陷阱)

### 反例 A: 心跳重置 idle (Failure 60 本体)

```python
# ❌ 错
def check_idle():
    since = now() - hb.last_beat  # 心跳每 5min 写 → 永远 < 600
    return {"is_idle": since >= 600}

# ✅ 对
def check_idle():
    since = now() - hb.last_action_at  # 只被真动作写
    return {"is_idle": since >= 300}
```

### 反例 B: 健康检查自我重置"系统健康时间戳"

```python
# ❌ 错 (监控系统自己跑健康检查, 永远显示"刚检查过, 健康")
def check_health():
    last_health = hb.last_health
    if now() - last_health > 3600:
        alert("health check overdue")  # 永远不触发, 因为 cron 自己会写 last_health

# ✅ 对 (用 last_actual_health_data_received_at, 跟 health-check-process-last-ran 分开)
def check_health():
    last_data = hb.last_actual_health_data
    if now() - last_data > 3600:
        alert("data overdue")  # 真信号
```

### 反例 C: "上次任务完成" 用调度时间戳, 不用实际完成时间戳

```python
# ❌ 错
def should_alert_stuck_task():
    task = load_task()
    if now() - task.scheduled_at > 3600:  # 排定 1h 后没动 = 警告
        alert("task stuck")
    # 但: 任务可能 30min 就完成了, 只是记录没更新, 错误告警

# ✅ 对
def should_alert_stuck_task():
    task = load_task()
    if task.status == "running" and now() - task.last_progress_at > 3600:
        alert("task no progress")
    # 用"上次有进展"而不是"上次排定"
```

### 反例 D: "用户最近活跃" 用 session 启动时间, 不用最后输入时间

```python
# ❌ 错
def user_idle_minutes():
    return now() - user.session_started_at  # 用户可能 session 开着但 8h 没说话

# ✅ 对
def user_idle_minutes():
    return now() - user.last_input_at  # 真"最近输入"
```

---

## 设计落地当天必验证 (硬规则)

任何 idle / watchdog / cron-style 触发脚本落地后, **当天必须模拟 N 分钟无动作跑一遍**:

```bash
# 1. 模拟 idle N 分钟
python3 -c "
import json, time
hb = json.load(open('state/heartbeat.json'))
hb['last_action_at'] = int(time.time()) - 700  # 11min40s 前
open('state/heartbeat.json', 'w').write(json.dumps(hb, indent=2))
print('模拟完成')
"

# 2. 跑一次心跳, 看是否触发行动池
python3 idle_driver.py heartbeat

# 3. 检查 today_log 立即写入 "💓→⚡ 心跳检测到 idle (XXXs), 立即跑行动池"
tail -3 ~/.hermes/state/today_log.md

# 4. 不触发 = bug, 不接受"代码逻辑看起来对"的嘴炮验证
```

**验证通过 → 才进 cron**。不接受"应该会跑"的嘴炮, 真实测一遍才是验证。

---

## cron 频率兜底原则

```
[绝对临界]  heartbeat_interval >= idle_threshold   → 触发器必然失效
[临界]      heartbeat_interval ≈ idle_threshold    → 易踩坑, 必留余量
[安全]      heartbeat_interval < idle_threshold/2  → 推荐
[最安全]    heartbeat_interval ≤ idle_threshold/3  → 极端场景用
```

| heartbeat | idle_threshold | 状态 |
|---|---|---|
| 5min | 5min | ❌ 绝对临界, 永远触发不了 |
| 5min | 10min | ⚠️ 临界, 易踩坑 |
| 5min | 20min | ✅ 安全 (2x 余量) |
| 2min | 10min | ✅ 安全 (5x 余量) |
| 2min | 15min | ✅ 最安全 |

**默认推荐**: heartbeat=`*/2 * * * *`, idle_threshold=10min — 5x 余量, 单次 cron 漏跑都不会有事。

---

## 写新触发器前的 checklist (打印贴墙)

```
□ 时间戳字段不会被"会自己跑"的进程更新? (5问①)
□ 分两轨: last_beat + last_action_at? (5问②)
□ mark_action() 在每个真动作后调用? (5问③)
□ heartbeat_interval < idle_threshold / 2? (5问④)
□ 心跳阶段同步检测 idle, is_idle → 立即触发? (5问⑤)
□ 设计落地当天模拟 N 分钟无动作跑一遍验证? (硬规则)
□ today_log 立即写入 "💓→⚡ 心跳检测到 idle (XXXs), 立即跑行动池"? (验证信号)
```

任何一项没勾 → 别进 cron, 必先改。

---

## 关联

- SKILL.md v1.16.0 changelog — Rule 10 触发器自洽性铁律
- references/failure-cases.md — Failure 60 完整 transcript
- 实战参考: `~/.hermes/scripts/idle_driver.py` v3.5 修复后版本 (双轨 + 心跳阶段同步检测)