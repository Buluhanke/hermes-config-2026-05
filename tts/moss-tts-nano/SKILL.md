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

### 方式一：手动终端调用（直接，绕过 gateway TTS）

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

### 方式二：通过 gateway text_to_speech_tool（需正确配置）

**⚠️ 配置要求**：如果要让 gateway 的 `text_to_speech_tool(provider="moss", ...)` 自动走 MOSS，
必须在 `~/.hermes/config.yaml` 里声明 command provider，否则会**静默 fallback 到 Edge TTS**。

config.yaml 需要加入这段：

```yaml
tts:
  provider: moss          # 已有
  providers:
    moss:
      type: command
      command: "/Users/aimac/MOSS-TTS-Nano/.venv312/bin/python /Users/aimac/.hermes/skills/tts/moss-tts-nano/scripts/tts.py -t '{text}' --voice-name Xiaoyu -o {output_path}"
```

**静默 fallback 症状**（排查用）：
- 日志出现 `Generating speech with Edge TTS...` 但配置 `provider: moss`
- 输出文件是 Edge TTS 音色而非 MOSS 音色
- 原因：MOSS 不在 `BUILTIN_TTS_PROVIDERS`（edge/elevenlabs/openai/minimax/xai/mistral/gemini/neutts/kittentts/piper），且 config 里没有 `tts.providers.moss: type: command`

**验证是否真正使用了 MOSS**：
```bash
grep "provider: moss" ~/.hermes/logs/agent.log | tail -5
# 看是否有 "TTS audio saved (provider: moss)"
# 如果看到 "provider: edge" 说明是 fallback
```

## 当前生产配置（2026-05-28 更新）

**MOSS-TTS-Nano 已不稳定，不要用于生产语音回复。**

当前稳定方案：`tts.provider: edge` + `zh-CN-XiaoxiaoNeural`

```bash
# 当前配置（Edge TTS，已验证可用）
hermes config set tts.provider edge

# Edge TTS 验证命令（直接测试，不走 gateway）
python3 -c "import asyncio, edge_tts; asyncio.run(edge_tts.Communicate('测试', 'zh-CN-XiaoxiaoNeural').save('/tmp/test.mp3'))"
```

MOSS-TTS-Nano 在 CPU 模式下首次推理超过 60s 超时，生成不稳定（短文本只输出 0.5 秒），**已降级为实验/备用**。

## 已知问题

| 问题 | 原因 | 解法 |
|------|------|------|
| Edge TTS 报 "No audio was received" | config 里 voice 是英文音色（如 `en-US-AriaNeural`），但说了中文 → Edge TTS 无法合成，直接失败 | 手动改 `~/.hermes/config.yaml` 中 `tts.edge.voice` 为 `zh-CN-XiaoxiaoNeural` |
| 配置了 `provider: moss` 但实际走 Edge TTS | MOSS 不在内置名单且未在 config 声明 command provider | 在 config.yaml 加 `tts.providers.moss.type: command` 并填入 command |
| 日志显示 "Generating speech with Edge TTS" 但用了 moss provider | 同上，静默 fallback | 同上 |
| config.yaml 是受保护文件，不能直接 patch | 安全限制 | 用 `hermes config set tts.provider edge` 命令修改配置 |
| MOSS 进程超时（>60s）无响应 | venv 环境问题或 MOSS 推理卡住 | 立即切换 `tts.provider` 为 `edge`，用 `hermes config set tts.provider edge` |
| 日志显示 "provider: moss" 但实际走 Edge | 配置有但没生效，排查同第一行 | 用手动测试验证，不依赖日志 |
| Edge TTS provider 不检查语音-语言匹配 | Edge TTS 收到不匹配语言的文本会静默失败（"No audio was received"）而不是 fallback | 直接调终端 `edge-tts --text "中文" --voice zh-CN-XiaoxiaoNeural --write-media /tmp/test.mp3` 验证，不要依赖 gateway 的 provider 选择逻辑 |

## 注意事项

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

## 语音回复内容匹配规则（重要）

**voice_reply 必须匹配當下對話話題，不能跑題。** 用戶抱怨「語音回覆對不上聊的內容」= 直接質量投訴。

觸發語音回覆時：
1. 先確認用戶在問什麼 → 用戶語音消息的內容
2. 回覆的內容必須針對該問題，不能是「今年學了什麼」在語音回覆裡變成「介紹Hermes的學習成果」
3. 如果對話主題不明確，先用文字確認再語音回覆

## TTS Provider 降级规则（重要）

**当 MOSS TTS 出现任何问题时，立即切换到 Edge TTS，不要等。**

判断标准（任一即切换）：
- 终端调用 MOSS 超过 60s 无输出
- `text_to_speech` 调用超时或返回错误
- 用户反馈语音没声音/声音不对

切换命令：
```bash
hermes config set tts.provider edge
```

Edge TTS 优势：已安装（`/Library/Frameworks/Python.framework/Versions/3.14/bin/edge-tts`），响应快，无需额外配置。

## 手动测试 TTS 音色的正确步骤

当需要验证 TTS 是否真正工作时（尤其是修复后验证）：

```bash
# 1. 手动生成一个测试音频（绕过 gateway，直接调 MOSS）
# 2. 通过 send_message MEDIA: 发送给用户听
# 3. 不要依赖 gateway 日志中的 "provider: moss" 判断——日志可能假阳性
#    必须：用户亲自听 + 对话内容是否相关
```

## 平台语音发送支持

| 平台 | 原生语音支持 | 备注 |
|------|------------|------|
| Telegram | ✅ | 直接发送 .wav/.mp3 |
| 微信 | ✅ | 原生语音消息 |
| QQ | ❌ | 不支持原生语音发送，MEDIA 文件会被丢弃 |
| Discord | ✅ | 原生语音支持 |

**QQ 替代方案**：将音频文件路径告知用户，让用户手动播放；或切换到 Telegram 发送。
