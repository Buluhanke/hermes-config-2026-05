---
name: kokoro-tts
description: "Kokoro 本地 ONNX TTS — Mac 本地部署，免费，支持多 voice。关键限制：自带 voice 全部是英文，中文需额外配置 lang=cmn 但听感不如专业中文 TTS。"
permissions:
  - filesystem
required_paths:
  - /Users/aimac/kokoro
required_commands: []
required_packages: []
---

# Kokoro TTS

本地 ONNX TTS，Mac M 系列芯片可用，免费。

## 快速配置（Hermes）

```yaml
tts:
  provider: kokoro
  kokoro:
    type: command
    command: /Users/aimac/kokoro/venv/bin/python3 /Users/aimac/kokoro/tts_kokoro.py
      --input {input_path} --output {output_path} --voice {voice} --speed {speed}
    voice: af_sky
    speed: 1.0
    format: wav
```

## 自带 Voice（全部英文）

```
af, af_bella, af_nicole, af_sarah, af_sky   # 美式女声
am_adam, am_michael                          # 美式男声
bf_emma, bf_isabella                          # 英式女声
bm_george, bm_lewis                           # 英式男声
```

**中文能力**：加 `lang="cmn"` 参数可以让英文 voice 尝试读中文注音，但听感是"老外说中文"，不适合正式场景。

## 中文方案对比

| 方案 | 中文听感 | 成本 | 配置难度 |
|------|----------|------|----------|
| Kokoro + lang=cmn | 差（英文口音） | 免费 | 简单 |
| Edge TTS zh-CN-XiaoxiaoNeural | 好 | 免费 | 已配置 |
| 微软 Azure 语音 | 很好 | 付费 | 需API Key |
| IndexTTS 中文 voice | 很好 | 免费 | 需GPU |

## 切换到 Edge 中文 TTS

如果中文语音是刚需，改一行配置：

```yaml
tts:
  provider: edge
  edge:
    voice: zh-CN-XiaoxiaoNeural
```

## 删除 MOSS-TTS-Nano

如需彻底移除：
- 删除 `config.yaml` 中的 `providers.moss` 块
- 删除 `/Users/aimac/MOSS-TTS-Nano/` 目录
- 删除 `~/.hermes/skills/tts/moss-tts-nano/` skill 目录

## Pitfalls

- **Kokoro 自带 voice 无中文**：即使设 `lang="cmn"`，voices.bin 里的 11 个 voice 都是英文训练，中文听感差
- **stdin 不支持**：tts_kokoro.py 不认 `-` 作 stdin，输入必须用 `--input <文件路径>`
- **命令审批**：删除 MOSS-TTS-Nano 目录需要 `rm -rf`，系统会触发命令审批提示
