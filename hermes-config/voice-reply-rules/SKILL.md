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

**平台限制注意**：Edge TTS 在本环境不通（网络限制）。使用 Moss-TTS-Nano 本地生成：
```bash
/Users/aimac/MOSS-TTS-Nano/.venv312/bin/python \
  /Users/aimac/.hermes/skills/tts/moss-tts-nano/scripts/tts.py \
  -t '回复内容' --voice-name Xiaoyu -o /tmp/moss_voice.wav
```
QQ平台不支持原生语音，生成后告知用户文件路径让他手动播放；Telegram/微信/Discord 可直接 MEDIA 发送。

## 平台能力速查

| 平台 | 原生语音支持 | TTS方案 |
|------|------------|---------|
| Telegram | ✅ | 直接发送 MEDIA |
| 微信 | ✅ | 直接发送 MEDIA |
| QQ | ❌ | Moss-TTS 生成，告知路径 |
| Discord | ✅ | 直接发送 MEDIA |

## Session恢复验证
每次长context或session重建后，被问"XX功能没丢吧"时：
1. 不废话，直接验证
2. 语音验证：发一条语音确认
3. 终端验证：`echo ok && date` 直接跑
4. 验证完直接回"正常/有问题"，不解释过程

## References
- `references/capability-verification.md` — 验证流程细节