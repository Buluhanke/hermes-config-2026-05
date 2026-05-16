# MOSS-TTS-Nano 已知问题

## CPU 超时问题（2026-05-16 新发现）

**问题描述**：在 M4 Mac mini 上运行 `infer.py`，模型加载完成后（Loading weights 100%）卡住，180秒超时无输出。

**结论**：MOSS-TTS-Nano 在 Apple Silicon Mac 上 CPU 推理极不稳定，**生产环境一律用 Edge TTS**。

## 短中文文本输出极短

**问题描述**：输入短中文文本（5-15字）时，经常只生成约0.5秒音频（43帧@48kHz），内容被截断。

**原因**：模型生成分帧数量不稳定，是模型层面的内在问题，不是调用方式的错。

**复现**：
```bash
cd /Users/aimac/MOSS-TTS-Nano
.venv312/bin/python infer.py --text "你好" --mode voice_clone \
  --prompt-audio-path assets/audio/zh_3.wav \
  --output-audio-path /tmp/test.wav \
  --disable-wetext-processing --disable-normalize-tts-text
# 经常输出 ~0.5秒
```

**建议**：
- 中文语音回复优先使用 Edge TTS（`edge-tts` 命令，已在 PATH），稳定可靠
- MOSS-TTS-Nano 仅在 Edge TTS 不可用时作为备选
- 如果必须用 MOSS-TTS-Nano，输入文本尽量长（如30字以上）

## tts.py 参数冲突（已修复）

`--voice` 参数与 `infer.py` 的 `--voice-clone-*` 参数冲突。已在 2026-05-16 修复为 `--voice-name`。
