---
name: voice-reply-rules
description: 语音/文字回复规则固化
version: 1.1.0
---

## 规则
用户发语音 → 语音回复（auto_tts=true，Moss-TTS-Nano 本地合成，Xiaoyu音色）
用户发文字 → 文字回复
不混用，规则已固化

## Voice优先原则
收到语音消息时，直接TTS回复，不做任何前置检查（不查日志/不验证状态/不跑终端命令）。用户要的是响应速度，不是诊断报告。

**⚠️ 语音回复内容必须匹配对话话题（硬规则）**
- 用户用中文提问 → 必须用中文回复，不能用英文
- 回复内容必须围绕用户的问题展开，不能跑题
- 跨 session 重建后同样遵守此规则
- 例外：用户明确要求换语言（如"用英文回答"）

违反这条规则会导致"语音对不上聊的内容"，用户体验为"声音正常但答非所问"。

**⚠️ 历史记录不存在时，立即告知而非猜测**
- 用户要求查"某时间点的配置/对话"时，先确认记录是否存在
- 数据库/日志查不到 → 明确告知"该时段无记录"
- 不凭记忆生成答案，不尝试拼凑，不反复查找
- 用户纠正后立即承认，不要解释过程

**TTS音频质量投诉处理流程**
用户报告"都是杂音"时：
1. 不发 mp3，发刚生成的原始 WAV（绕过 Telegram 转码干扰判断）
2. 用实际 TTS 命令生成：`/Users/aimac/MOSS-TTS-Nano/.venv312/bin/python .../tts.py -t '测试内容' --voice-name Xiaoyu -o /tmp/test.wav`
3. 发到 Telegram 后等待用户确认是"能听清但不是那个声音"还是"完全杂音"
4. 区分：生成杂音（模型问题）vs 播放杂音（平台/设备问题）

**当前配置（2026-05-27）**：
- `tts.provider = edge`（**实际运行配置**，不是 moss）
- `tts.edge.voice = en-US-AriaNeural`（英文音色，合成中文会失败）
- `voice.auto_tts = true`（收到语音自动触发TTS回复）
- 目标音色：zh-CN-XiaoxiaoNeural（中文，需手动改 config.yaml 生效）

**Moss-TTS 目标配置（供参考）**：
```yaml
tts:
  provider: moss
  providers:
    moss:
      type: command
      command: "/Users/aimac/MOSS-TTS-Nano/.venv312/bin/python /Users/aimac/.hermes/skills/tts/moss-tts-nano/scripts/tts.py -t '{text}' --voice-name Xiaoyu -o {output_path}"
```

**Moss-TTS 调用方式**：
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