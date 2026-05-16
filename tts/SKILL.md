---
name: tts
description: "Use this skill whenever the user wants to convert text into speech, generate audio from text, or produce voiceovers. Triggers include: any mention of 'TTS', 'text to speech', 'speak', 'say', 'voice', 'read aloud', 'audio narration', 'voiceover', 'dubbing', or requests to turn written content into spoken audio. Also use when converting EPUB/PDF/SRT/articles to audio, cloning voices from reference audio, controlling emotion or speed in speech, aligning speech to subtitle timelines, or producing per-segment voice-mapped audio."
permissions:
  - network
  - filesystem
metadata: {"openclaw": {"primaryEnv": "NOIZ_API_KEY"}}
---

# tts

Convert any text into speech audio. Supports two backends (Kokoro local, Noiz cloud), two modes (simple or timeline-accurate), and per-segment voice control.

## Triggers

- text to speech / tts / speak / say
- voice clone / dubbing 
- epub to audio / srt to audio / convert to audio
- 语音 / 说 / 讲 / 说话


## Simple Mode — text to audio

`speak` is the default — the subcommand can be omitted:

```bash
# Basic usage (speak is implicit)
python3 skills/tts/scripts/tts.py -t "Hello world"          # add -o path to save
python3 skills/tts/scripts/tts.py -f article.txt -o out.mp3

# Voice cloning — local file path or URL
python3 skills/tts/scripts/tts.py -t "Hello" --ref-audio ./ref.wav
python3 skills/tts/scripts/tts.py -t "Hello" --ref-audio https://example.com/my_voice.wav -o clone.wav

# Voice message format
python3 skills/tts/scripts/tts.py -t "Hello" --format opus -o voice.opus
python3 skills/tts/scripts/tts.py -t "Hello" --format ogg -o voice.ogg
```

Third-party integration (Feishu/Telegram/Discord) is documented in [ref_3rd_party.md](ref_3rd_party.md).

## Timeline Mode — SRT to time-aligned audio

For precise per-segment timing (dubbing, subtitles, video narration).

### Step 1: Get or create an SRT

If the user doesn't have one, generate from text:

```bash
python3 skills/tts/scripts/tts.py to-srt -i article.txt -o article.srt
python3 skills/tts/scripts/tts.py to-srt -i article.txt -o article.srt --cps 15 --gap 500
```

`--cps` = characters per second (default 4, good for Chinese; ~15 for English). The agent can also write SRT manually.

### Step 2: Create a voice map

JSON file controlling default + per-segment voice settings. `segments` keys support single index `"3"` or range `"5-8"`.

Kokoro voice map:

```json
{
  "default": { "voice": "zf_xiaoni", "lang": "cmn" },
  "segments": {
    "1": { "voice": "zm_yunxi" },
    "5-8": { "voice": "af_sarah", "lang": "en-us", "speed": 0.9 }
  }
}
```

Noiz voice map (adds `emo`, `reference_audio` support). `reference_audio` can be a local path or a URL (user’s own audio; Noiz only):

```json
{
  "default": { "voice_id": "voice_123", "target_lang": "zh" },
  "segments": {
    "1": { "voice_id": "voice_host", "emo": { "Joy": 0.6 } },
    "2-4": { "reference_audio": "./refs/guest.wav" }
  }
}
```

**Dynamic Reference Audio Slicing**:
If you are translating or dubbing a video and want each sentence to automatically use the audio from the original video at the exact same timestamp as its reference audio, use the `--ref-audio-track` argument instead of setting `reference_audio` in the map:
```bash
python3 skills/tts/scripts/tts.py render --srt input.srt --voice-map vm.json --ref-audio-track original_video.mp4 -o output.wav
```

See `examples/` for full samples.

### Step 3: Render

```bash
python3 skills/tts/scripts/tts.py render --srt input.srt --voice-map vm.json -o output.wav
python3 skills/tts/scripts/tts.py render --srt input.srt --voice-map vm.json --backend noiz --auto-emotion -o output.wav
```

## 语音回复 vs 微信原生语音消息

### 1. 音频附件（当前技术可实现，且已验证可用）
- 生成 `.ogg` / `.wav` 音频文件
- 通过 `send_message(message="MEDIA:/path/to/file.ogg", target="weixin")` 发送
- 微信显示为可播放的音频附件（媒体文件形式）
- **实测验证（2026-05-16）**：微信能正常接收和播放，与 Telegram 体验一致
- Edge TTS 生成的中文语音 → 微信发送 → 手机播放，全流程通过

### 2. 微信原生语音气泡（当前技术无法实现）
- 需要通过微信客户端的实时录音接口
- 模拟"按住说话"的交互模式
- 目前没有可靠的技术方案绕过微信的录音限制

**结论**：微信语音（音频附件）可用，Edge TTS → send_message 流程已验证稳定。用户无需知道底层细节，直接使用即可。
## Voice Reply Workflow — info → audio → send as voice message

This is a recurring pattern: user asks for information and wants the reply as an audio voice message. The workflow is:

1. **Gather the information** (search, extract, compute, etc.)
2. **Construct natural spoken text** — write for the ear, not the eye. Use conversational Chinese (or the user's language). Break into short sentences. Include key data points (dates, temperatures, numbers). Avoid markdown, formatting, or complex structure.
3. **Select TTS backend — Edge TTS for Chinese first, MOSS-TTS-Nano as fallback:**
   - **Edge TTS** (微软, `~/.hermes/hermes-agent/venv/bin/edge-tts`): 稳定可靠，中文效果好，优先使用
   - **MOSS-TTS-Nano** (本地, 无API key): 对短中文文本经常只生成0.5秒音频（是模型层面的不稳定问题），优先 Edge
4. **Generate audio** via terminal calling the appropriate TTS script
5. **Send as voice message** — use `send_message(message="MEDIA:/path/to/file.wav", target="...")` so QQ/WeChat plays it as audio. Note: this sends as an audio attachment, NOT as WeChat native voice message (see above).

### Edge TTS 推荐参数（首选方案）

`text_to_speech` 工具本身有失败率，推荐直接用终端调用 edge-tts：

```bash
~/.hermes/hermes-agent/venv/bin/edge-tts \
  --text "语音回复的文本内容" \
  --voice "zh-CN-XiaoxiaoNeural" \
  --write-media ~/.hermes/audio_cache/voice_reply.ogg
```

然后通过 send_message 发送（telegram / weixin 均已验证可用）。

**流程**：搜索信息 → 组织口语化回复文本 → edge-tts 生成音频 → send_message 发送 → 全程无需调用 text_to_speech 工具。

**已验证可用**：Edge TTS → 微信播放、Telegram 播放，均正常。

| 音色 | 性别/风格 |
|------|----------|
| `zh-CN-XiaoxiaoNeural` | 女声（默认） |
| `zh-CN-YunxiNeural` | 男声 |
| `zh-CN-XiaoyiNeural` | 女声（年轻） |
| `zh-CN-YunyangNeural` | 男声（新闻腔） |

用户偏好默认 Xiaoxiao，切换音色时先让用户试听确认。

### MOSS-TTS-Nano — CPU 模式不稳定，慎用

**已知问题（实测）：**
- CPU 模式（`--device cpu`）加载慢，首次推理 180s 仍超时
- 模型加载完成后生成过程也不稳定，短时间内无法产出
- 短中文文本（5-15字）经常只输出 0.5 秒，是模型 token 数量不稳定问题
- wrapper 参数修复无效

**实测结论：**
- 180s 超时仍无法完成一次生成 → 不推荐用于生产
- 如需本地离线 TTS，优先考虑 Kokoro（已集成在 `tts.py` 中）

**Edge TTS 是当前最可靠的中文语音方案（已验证 WeChat 发送成功）。**

**Pitfalls:**
- Edge TTS can fail with "No audio was received" — fall back to MOSS-TTS-Nano (local) or Noiz
- MOSS-TTS-Nano first run downloads models (~hundreds of MB from HF), subsequent runs are fast
- Ensure user wants voice before generating — some channels don't support MEDIA or the user may prefer text
- Voice text should be self-contained: user won't see supporting text/charts with the audio
- Audio is sent as a media attachment, NOT as WeChat native voice message — set expectation with user if they specifically asked for "按住说话" style
- **用户偏好**：中文语音回复默认使用 `zh-CN-XiaoxiaoNeural`（女声），所有中文语音优先选这个
- **音频缓存**：`~/.hermes/audio_cache/` 用于存放语音文件，用户要求15天自动清理。配合 cronjob `no_agent=true` 使用清理脚本时，`script` 参数必须为相对路径（相对于 `~/.hermes/scripts/`），不能是绝对路径

See `references/wechat-voice-verification.md` for WeChat voice send verification records.

## When to Choose Which

| Need | Recommended |
|------|-------------|
| Just read text aloud, no fuss | Kokoro (default) |
| EPUB/PDF audiobook with chapters | Kokoro (native support) |
| Voice blending (`"v1:60,v2:40"`) | Kokoro |
| Local inference, no API needed | **MOSS-TTS-Nano** |
| Voice cloning from reference audio | Noiz |
| Emotion control (`emo` param) | Noiz |
| Exact server-side duration per segment | Noiz |

### MOSS-TTS-Nano (local, no API key)

`/Users/aimac/MOSS-TTS-Nano` — 0.1B parameter multilingual TTS, CPU-capable, supports voice cloning.

**Setup notes / pitfalls:** See [moss-tts-nano-pitfalls.md](references/moss-tts-nano-pitfalls.md) — `.venv312` only, asset path is `assets/audio/` not `prompts/`, always use `--disable-wetext-processing`.

```bash
/Users/aimac/MOSS-TTS-Nano/.venv312/bin/python \
  /Users/aimac/.hermes/skills/tts/moss-tts-nano/scripts/tts.py \
  -t "你好" --voice Xiaoyu -o /tmp/moss.wav
```

Voice cloning from reference audio:
```bash
--ref-audio /path/to/ref.wav --prompt-text "音频里说的内容"
```

> **MOSS-TTS-Nano caveat:** First run downloads models (~hundreds of MB). Subsequent runs are local. No API key needed.

> When the user needs emotion control + voice cloning + precise duration together, Noiz is the only backend that supports all three.

## Guest Mode (no API key)

When no API key is configured, `tts.py` automatically falls back to **guest mode** — a limited Noiz endpoint that requires no authentication. Guest mode only supports `--voice-id`, `--speed`, and `--format`; voice cloning, emotion, duration, and timeline rendering are not available.

```bash
# Guest mode (auto-detected when no API key is set)
python3 skills/tts/scripts/tts.py -t "Hello" --voice-id 883b6b7c -o hello.wav

# Explicit backend override to use kokoro instead
python3 skills/tts/scripts/tts.py -t "Hello" --backend kokoro
```

Available guest voices (15 built-in):

| voice_id | name | lang | gender | tone |
|---|---|---|---|---|
| `063a4491` | 販売員（なおみ） | ja | F | 喜び |
| `4252b9c8` | 落ち着いた女性 | ja | F | 穏やか |
| `578b4be2` | 熱血漢（たける） | ja | M | 怒り |
| `a9249ce7` | 安らぎ（みなと） | ja | M | 穏やか |
| `f00e45a1` | 旅人（かいと） | ja | M | 穏やか |
| `b4775100` | 悦悦｜社交分享 | zh | F | Joyful |
| `77e15f2c` | 婉青｜情绪抚慰 | zh | F | Calm |
| `ac09aeb4` | 阿豪｜磁性主持 | zh | M | Calm |
| `87cb2405` | 建国｜知识科普 | zh | M | Calm |
| `3b9f1e27` | 小明｜科技达人 | zh | M | Joyful |
| `95814add` | Science Narration | en | M | Calm |
| `883b6b7c` | The Mentor (Alex) | en | M | Joyful |
| `a845c7de` | The Naturalist (Silas) | en | M | Calm |
| `5a68d66b` | The Healer (Serena) | en | F | Calm |
| `0e4ab6ec` | The Mentor (Maya) | en | F | Calm |

## Security & data disclosure

This skill performs the following file and network operations at runtime:

- **Credential storage**: When you run `config --set-api-key`, the key is saved to `~/.config/noiz/api_key` (permissions `0600`). The `NOIZ_API_KEY` environment variable is also supported as an alternative.
- **Legacy key migration**: If `~/.noiz_api_key` exists and `~/.config/noiz/api_key` does not, the key is **copied** (not deleted) to the new location. A message is printed; the old file is left untouched for you to remove manually.
- **Network calls (Noiz backend)**: Text and optional reference audio are uploaded to `https://noiz.ai/v1/` for synthesis. No data is sent unless you invoke a Noiz command.
- **Reference audio download**: When `--ref-audio` is a URL, the file is downloaded to a temp file, used for the API call, then deleted. If no voice-id or ref-audio is provided, a default reference audio is downloaded from `storage.googleapis.com` or `noiz.ai`.
- **Temp files**: Temporary audio/text files may be created during synthesis and are cleaned up after use.
- **ffmpeg**: Invoked only in timeline `render` mode to assemble the final audio.

No files outside the output path and `~/.config/noiz/` are modified. The Kokoro backend runs entirely offline with no network access.

## Requirements

- `ffmpeg` in PATH (timeline mode only)
- `requests` package: `uv pip install requests` (required for Noiz backend)
- Get your API key at [Noiz Developer](https://developers.noiz.ai/api-keys), then run `python3 skills/tts/scripts/tts.py config --set-api-key YOUR_KEY` (guest mode works without a key but has limited features)
- Kokoro: if already installed, pass `--backend kokoro` to use the local backend

### Noiz API authentication

Use **only** the base64-encoded API key as `Authorization`—no prefix (e.g. no `APIKEY ` or `Bearer `). Any prefix causes 401.

For backend details and full argument reference, see [reference.md](reference.md).
