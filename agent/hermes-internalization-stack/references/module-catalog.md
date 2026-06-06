# Module Catalog (2026-06-04)

`~/.hermes/scripts/` 下的所有 hermes 内部模块。**新增/删除模块请同步更新本表**。

| 模块 | Archetype | 状态文件 | 状态 | 角色 | 测试场景数 |
|------|-----------|----------|------|------|------------|
| `rhythm.py` | Computed-Context | — | ✓ stable | 时段判断、是否可主动 | 4 zone + critical_only 旁路 |
| `hermes_notify.py` | Queue | `~/.hermes/queue/messages.jsonl` | ✓ stable | 通知门控、JSONL 队列、drain | zone_check / force / 并发 lock / max_per_tick |
| `drain_watchdog.sh` | Shell-Watchdog | — | ✓ stable | cron 静默 drain | silent-on-empty 验证过 |
| `relationship.py` | Mutable-State | `~/.hermes/relationship.json` | ✓ stable | mood / followup / sensitive_topics | 6 场景：空/添加/标 done/负面/敏感/重置 |
| `persona.py` | Constants-Only | — | ✓ stable | 人格 + system prompt 构造 | 双 import 名兼容、439 字符 prompt |
| `blind_spots.py` | Mutable-State | `~/.hermes/blind_spots.json` | ✓ stable | 知识盲区、置信度 | 未知→记录→部分验证→完全验证 |

## 数据流 (组合用法)

```
用户消息
   │
   ├── rhythm.get_rhythm()        ──→ 当前 zone/cap/proactive
   │
   ├── hermes_relationship.get_greeting_context()
   │       └──~/.hermes/relationship.json  (state)
   │
   ├── persona.build_system_prompt(
   │       task_context=...,               # 任务
   │       relationship_hint=...,          # 上面那个
   │   )
   │
   ├── blind_spots.should_verify_before_answer(topic)
   │       └──~/.hermes/blind_spots.json   (state)
   │
   └── hermes_notify.hermes_notify(msg, level)
           ├── should_send_message(level)  ──→ 直发 OR
           └── queue_message(msg, level)   ──→ ~/.hermes/queue/messages.jsonl
                                                │
                                                └── cron */5 → drain_watchdog.sh
                                                      └── drain_queue()
```

## 还没建的 (backlog)

- `~/.hermes/scripts/feedback.py` — 记录 user 对每次回复的"👍/👎"反馈，注入到下次 system prompt
- `~/.hermes/scripts/skill_usage.py` — 统计哪个 skill 被调了多少次、是否产生有效输出（评估 skill 价值）
- `~/.hermes/scripts/dream.py` — 后台 self-consolidation：把日记/对话里的事实提炼到 fact_store
- `hermes_init.py` — facade 何时建？等 ≥3 个模块被同时 import 时建
