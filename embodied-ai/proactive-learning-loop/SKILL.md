---
name: proactive-learning-loop
description: Hermes主动学习循环 - 屏幕变化触发→感知→评估→学习→行动
triggers:
  - screen change detected (screen_watcher.py fires ~/.hermes/screenshots/.changed)
  - cron job every 5 minutes (fallback polling)
  - manual trigger via cron
---

# Hermes Proactive Learning Loop

## Trigger
每当日志文件 `~/.hermes/screenshots/.changed` 被创建（屏幕显著变化）时触发。

## Loop 流程

1. **感知阶段** - 截图 + OCR/视觉分析
   - screencapture 当前屏幕
   - 百度OCR识别文字内容
   - 判断：有意义的新信息？还是只是UI变化？

2. **评估阶段** - 判断是否值得学习
   - 新供应商信息？→ 存入 supplier_notes
   - 价格/规格变化？→ 更新 memory
   - 系统弹窗/错误？→ 诊断并修复
   - 仅仅是UI动画？→ 忽略

3. **学习阶段** - 获取补充信息
   - 搜索相关背景知识
   - 更新相关 skill 或 memory

4. **行动阶段** - 应用学到的东西
   - 如果是1688相关→ 检查是否需要找货
   - 如果是系统问题→ 修复或创建 skill
   - 如果是业务机会→ 记录并通知

## 防抖规则
- 15秒内只触发一次（screen_watcher 已过滤）
- loading/animation 序列（4+个不同hash在5秒内）→ 忽略直到稳定
- 重复内容→ 衰减报告

## 输出
- 学习到的知识 → memory
- 新技能/修复 → skill_manage
- 有价值发现 → 汇报给用户