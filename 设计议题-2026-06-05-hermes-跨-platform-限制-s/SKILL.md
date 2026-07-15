---
name: 设计议题-2026-06-05-hermes-跨-platform-限制-s
version: 0.1
description: |
  【设计议题-2026-06-05】Hermes 跨 platform 限制: skills/scripts/MEMORY/USER/fact_store 物理共享, 但会话上下文/任务历史/临时 context 隔离。用户在 Telegram 跟 QQ bot 跟飞书跟微信 聊的内容各自独立, 共享层只有 fact_store 单向写入。改进方案(待用户拍板): ① 跨平台 platform_in
triggers:
  - "设计议题-2026-06-05-hermes-跨-platform-限制-s"
trigger_type: auto_crystallized
tags: ['cross_platform', 'isolation', 'user_question', '20260605']
created: 2026-07-15
来源: fact_store (id=87, ret=1, trust=0.90)
---
# 设计议题-2026-06-05-hermes-跨-platform-限制-s

【设计议题-2026-06-05】Hermes 跨 platform 限制: skills/scripts/MEMORY/USER/fact_store 物理共享, 但会话上下文/任务历史/临时 context 隔离。用户在 Telegram 跟 QQ bot 跟飞书跟微信 聊的内容各自独立, 共享层只有 fact_store 单向写入。改进方案(待用户拍板): ① 跨平台 platform_inbox.md 汇总 ② 每日 daily_notes.md 沉淀 ③ 查官方 cross-platform session 方案。