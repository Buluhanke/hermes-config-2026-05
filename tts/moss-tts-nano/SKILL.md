---
name: moss-tts-nano
description: "MOSS-TTS-Nano 本地语音合成 — 调用 /Users/aimac/MOSS-TTS-Nano 生成音频。支持内置音色（中文/英文）和参考音频克隆。触发词：moss、语音合成、moss tts。"
permissions:
  - network
  - filesystem
required_paths:
  - /Users/aimac/MOSS-TTS-Nano
required_commands:
  - /Users/aimac/MOSS-TTS-Nano/.venv312/bin/python
required_packages: []
---

# moss-tts-nano

将文字转换为语音，使用 MOSS-TTS-Nano（0.1B 参数，CPU 可运行）。

## edge-tts 备选方案（已验证可用）

若 MOSS-TTS-Nano 不可用，edge-tts 是稳定替代：

```python
import asyncio
from edge_tts import communicate

async def tts_weather():
    text = "义乌今天天气晴，气温30~19℃，湿度82%，东南风2.7米每秒，气压1004百帕"
    cm = communicate(text, voice="zh-CN-XiaoxiaoNeural")
    await cm.save("/Users/aimac/.hermes/audio_cache/weather.mp3")

asyncio.run(tts_weather())
```

**验证结果**：76,896 字节，3.36 秒生成完成，XiaoxiaoNeural 中文发音自然。

---

## 核心依赖

MOSS-TTS-Nano 已安装在 `/Users/aimac/MOSS-TTS-Nano`，依赖已在该环境内。

## 使用方式

### 内置音色

所有音色位于 `assets/audio/`，必须存在于该目录中才可用：

| 音色名 | 文件 | 语言 |
|--------|------|------|
| Junhao | zh_1.wav | 中文 |
| Xiaoyu | zh_3.wav | 中文 |
| Yuewen | zh_4.wav | 中文 |
| Lingyu | zh_6.wav | 中文 |
| Minglang | zh_10.wav | 中文 |
| Yujie | zh_11.wav | 中文 |
| Ava | en_2.wav | 英文 |
| Bella | en_3.wav | 英文 |
| Adam | en_4.wav | 英文 |
| Nathan | en_6.wav | 英文 |

⚠️ `zh_2.wav`(Zhiming), `zh_5.wav`(Junhao2), `zh_7-9.wav` 等文件不存在，**不要使用**。

## 在 Hermes 中调用

生成音频后用 `MEDIA:/path/to/file.wav` 发送即可：

```python
# 1. 生成音频
result = terminal(
    "/Users/aimac/MOSS-TTS-Nano/.venv312/bin/python "
    "/Users/aimac/.hermes/skills/tts/moss-tts-nano/scripts/tts.py "
    "-t '你好，这是语音回复' --voice-name Xiaoyu -o /tmp/moss_voice.wav"
)
# 2. 发给用户（QQ/微信会自动作为语音消息播放）
send_message(message="MEDIA:/tmp/moss_voice.wav", target="origin")
```

## 平台语音发送支持矩阵

| 平台 | TTS文件发送 | 原生语音消息 | 备注 |
|------|------------|------------|------|
| **Telegram** | ✅ 可行 | ✅ 支持 | 语音消息直接发送 |
| **QQ** | ❌ 不支持 | ❌ 不支持 | MEDIA标签被忽略，无其他绕过方式 |
| **微信** | ❌ 不支持 | ❌ 不支持 | 同QQ，平台级限制无法绕过 |
| **Discord** | ✅ 可行 | ✅ 支持 | |

**结论**：TTS 生成 → Telegram 发送是唯一可用的语音通道。微信/QQ 无法以语音消息发送。

**如果用户要求语音回复**：先确认当前对话在 Telegram 还是微信。微信/QQ 只能文字，解释原因即可，不要浪费算力重复尝试。

## 注意事项

- 正确 venv：`/Users/aimac/MOSS-TTS-Nano/.venv312`（含 torch），`.venv` 不含 torch 不可用
- 音色路径在 `assets/audio/`，脚本以 MOSS-TTS-Nano 目录为 cwd 运行，所以写相对路径 `assets/audio/zh_X.wav` 即可
- 输出格式：48kHz, 立体声 WAV
- 首次运行下载模型（约数百 MB），之后本地运行
- 支持参考音频克隆：`--ref-audio /path/to/audio.wav --prompt-text \"音频里说的话\"`

## 平台语音发送支持

| 平台 | 原生语音支持 | 备注 |
|------|------------|------|
| Telegram | ✅ | 直接发送 .wav/.mp3 |
| 微信 | ✅ | 原生语音消息 |
| QQ | ❌ | 不支持原生语音发送，MEDIA 文件会被丢弃 |
| Discord | ✅ | 原生语音支持 |

**QQ 替代方案**：将音频文件路径告知用户，让用户手动播放；或切换到 Telegram 发送。
