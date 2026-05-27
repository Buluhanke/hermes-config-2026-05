---
name: local-stt
description: 本地语音转文字（Speech-to-Text）— faster-whisper 等开源 STT 引擎在 Mac mini M4 上的部署、转译与集成。
triggers:
  - "语音转文字"
  - "音频转写"
  - "视频字幕"
  - "转写"
  - "whisper"
  - "faster-whisper"
  - "本地语音识别"
  - "离线转写"
version: 1.0.0
pitfalls:
  - key: "导入名错误"
    content: |
      faster-whisper v1.x 的正确导入是 `from faster_whisper import WhisperModel`，
      不是 README 中示例的 `FasterWhisper`（旧版 API）。运行前先验证 import 能过。
  - key: "CUDA包兼容性"
    content: |
      Mac mini M4 上的 ctranslate2 是 CPU 版，不支持 CUDA。
      使用 `device='cpu'` + `compute_type='int8'` 即可。
      不要尝试 `device='cuda'` 会报错 "CTranslate2 package was not compiled with CUDA support"。
  - key: "模型选择"
    content: |
      small 模型在 M4 Mac mini CPU 上转写约 2-3x realtime，够用。
      large-v3 精度最高但慢；turbo 最快但精度较低。
      有独显的机器可试 large-v3 + float16。
---

## 快速开始

```python
from faster_whisper import WhisperModel

model = WhisperModel('small', device='cpu', compute_type='int8')
segments, info = model.transcribe(
    'audio.wav',
    language='zh',
    beam_size=1
)
print(f'语言: {info.language}, 概率: {info.language_probability:.2f}')
for seg in segments:
    print(f'[{seg.start:.1f}s-{seg.end:.1f}s] {seg.text.strip()}')
```

## 环境信息（aimac Mac mini M4）

- faster-whisper: **1.2.1**（Homebrew Python 3.14）
- ctranslate2: CPU 版（无 CUDA）
- 推荐配置: `device='cpu', compute_type='int8'`
- 模型下载: HuggingFace Hub（自动缓存到 `~/.cache/huggingface/`）

## 支持的引擎

| 引擎 | 特点 | 推荐场景 |
|------|------|----------|
| faster-whisper (CTranslate2) | 4x 提速，int8量化，MIT协议 | 首选，本地转写 |
| whisper (openai) | 原生版，较慢 | benchmark对比 |

## 验证脚本

每次新 session 可运行以下脚本确认环境正常：

```
hermes tools execute --path ~/.hermes/skills/voice/local-stt/references/verify-faster-whisper.py
```

## Hermes 集成（语音对话场景）

STT 在 Hermes 中由 `tools.transcription_tools.py` 统一管理，`gateway/run.py` 中的 `_enrich_message_with_transcription()` 负责处理各平台的语音消息。

### 配置路径（~/.hermes/config.yaml）

```yaml
stt:
  enabled: true
  provider: local              # 可选: local, groq, openai, none
  local:
    model: small               # tiny/base/small/medium/large-v3
    language: ''               # 留空自动检测
  openai:
    model: whisper-1
```

修改后用 `grep -A2 "local:" ~/.hermes/config.yaml` 确认生效。

### 平台 ASR 路由

| 平台 | 主ASR | 备选 | 说明 |
|------|-------|------|------|
| QQ bot | 腾讯ASR（`asr_refer_text`，免费，平台内置） | local faster-whisper | 腾讯失败才走本地 |
| Telegram | local faster-whisper（直连） | 无 | 每次语音都用本地模型 |
| 命令行 | local faster-whisper | 无 | `hermes voice` 模式 |

> 修改 `stt.local.model` 只影响 local ASR 的场景。QQ 主链路走腾讯ASR，仅腾讯失败时 fallback 到 local。

### 内存占用

| 模型 | 加载内存 | 说明 |
|------|---------|------|
| tiny | ~500MB | M4 24GB 无忧 |
| base | ~1GB | 默认值 |
| small | ~1-2GB | 推荐，中文精度明显优于base/ |
| medium | ~3-4GB | 更高精度，CPU 较慢 |

模型仅在处理语音时加载进内存，处理完释放，非驻留。

### 验证生效

```bash
# 确认配置已写入
grep -A2 "local:" ~/.hermes/config.yaml

# 直测 faster-whisper 加载（带模型下载）
python3 -c "
from faster_whisper import WhisperModel
model = WhisperModel('small', device='cpu', compute_type='int8')
print('OK')
"
```

## 集成方向

- n8n workflow 调用本地转写服务
- 视频文件 → 字幕 → 文档
- 语音备忘录批量处理
- 与 TTS 形成完整语音链路
