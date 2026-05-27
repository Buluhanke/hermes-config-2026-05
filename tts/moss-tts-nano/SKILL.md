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

## 依赖

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

```python
# 1. 生成音频（venv路径务必用 .venv312，不是 .venv）
result = terminal(
    "/Users/aimac/MOSS-TTS-Nano/.venv312/bin/python "
    "/Users/aimac/.hermes/skills/tts/moss-tts-nano/scripts/tts.py "
    "-t '你好，这是语音回复' --voice-name Xiaoyu -o /tmp/moss_voice.wav"
)
# 2. 发送给用户
send_message(message="MEDIA:/tmp/moss_voice.wav", target="origin")
```

### 用户语音偏好（重要）

**默认规则：用户发语音 → 优先用语音回复。** 这是用户的明确偏好，触发条件为：
- 用户发送了语音消息
- 任何涉及"语音"、"说话"、"声音"相关的请求

生成语音后：
- Telegram/微信/Discord → 直接发送语音（MEDIA 文件自动作为原生语音）
- **QQ** → 语音文件会被丢弃，改为在文字消息末尾附上路径，告知用户"语音已生成，请点击播放"
  - 示例：`好的，我来解释一下这个功能。[语音已生成，可播放] /tmp/moss_voice.wav`
  - 更好的方案：引导用户切换到 Telegram（支持原生语音）

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
