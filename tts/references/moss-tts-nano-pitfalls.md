# MOSS-TTS-Nano 已知问题

## 短中文文本输出极短

**问题描述**：输入短中文文本（5-15字）时，经常只生成约0.5秒音频（43帧@48kHz），内容被截断。

**原因**：模型生成分帧数量不稳定，是模型层面的内在问题，不是调用方式的错。

**复现**：
```bash
cd /Users/aimac/MOSS-TTS-Nano
.venv312/bin/python infer.py --text "你好" --mode voice_clone --prompt-audio-path assets/audio/zh_3.wav --output-audio-path /tmp/test.wav --disable-wetext-processing --disable-normalize-tts-text
# 经常输出 ~0.5秒
```

**影响**：直接调 `infer.py` 和通过 `tts.py` wrapper 调用都有此问题，无法通过参数调整完全规避。

**建议**：
- 中文语音回复优先使用 Edge TTS（`~/.hermes/hermes-agent/venv/bin/edge-tts`），稳定可靠
- MOSS-TTS-Nano 仅在 Edge TTS 不可用时作为备选
- 如果必须用 MOSS-TTS-Nano，输入文本尽量长一些（如30字以上），提高稳定输出概率

## tts.py 参数冲突（已修复）

`--voice` 参数与 `infer.py` 的 `--voice-clone-*` 参数冲突，导致 argparse 报 ambiguous error。已在 2026-05-16 修复为 `--voice-name`。

如再次遇到 ambiguous error，直接调 `infer.py`：
```bash
.venv312/bin/python infer.py --text "文本" --mode voice_clone --prompt-audio-path assets/audio/zh_3.wav --output-audio-path /tmp/out.wav --disable-wetext-processing --disable-normalize-tts-text
```
