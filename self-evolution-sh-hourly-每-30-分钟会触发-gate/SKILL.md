---
name: self-evolution-sh-hourly-每-30-分钟会触发-gate
version: 0.1
description: |
  self_evolution.sh hourly 每 30 分钟会触发 gateway SIGTERM, 根因是 TG>5/h 误判 + 没 resumed 检查 + 没 cooldown; v2.1 修法: 阈值 30/h + 看 polling resumed + 2h cooldown + last_gateway_restart_ts 文件
triggers:
  - "self-evolution-sh-hourly-每-30-分钟会触发-gate"
trigger_type: auto_crystallized
tags: ['gateway', 'sigterm', 'self_evolution', 'launchctl', 'cooldown', 'telegram', 'bug_fix', 'self_evolution_gateway_restart_loop_20260611']
created: 2026-07-15
来源: fact_store (id=138, ret=1, trust=0.95)
---
# self-evolution-sh-hourly-每-30-分钟会触发-gate

self_evolution.sh hourly 每 30 分钟会触发 gateway SIGTERM, 根因是 TG>5/h 误判 + 没 resumed 检查 + 没 cooldown; v2.1 修法: 阈值 30/h + 看 polling resumed + 2h cooldown + last_gateway_restart_ts 文件