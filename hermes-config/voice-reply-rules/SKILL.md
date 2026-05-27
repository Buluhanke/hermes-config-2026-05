---
name: voice-reply-rules
description: 语音/文字回复规则固化
version: 1.1.0
---

## 规则
用户发语音 → 语音回复（text_to_speech, edge, zh-CN-XiaoxiaoNeural）
用户发文字 → 文字回复
不混用，规则已固化

## Voice优先原则
收到语音消息时，直接TTS回复，不做任何前置检查（不查日志/不验证状态/不跑终端命令）。用户要的是响应速度，不是诊断报告。

## Session恢复验证
每次长context或session重建后，被问"XX功能没丢吧"时：
1. 不废话，直接验证
2. 语音验证：发一条语音确认
3. 终端验证：`echo ok && date` 直接跑
4. 验证完直接回"正常/有问题"，不解释过程

## References
- `references/capability-verification.md` — 验证流程细节