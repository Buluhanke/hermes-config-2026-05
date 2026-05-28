# TTS 供应商选择指南（2026-05-29 实测）

## Kokoro TTS — 已删除（不要回退）

**关键发现**：Kokoro 自带的 `voices.bin` 只有 **11个英文 voice**：
```
af, af_bella, af_nicole, af_sarah, af_sky,
am_adam, am_michael, bf_emma, bf_isabella, bm_george, bm_lewis
```

**错误理解**：之前以为 `lang="cmn"` 可以让 Kokoro 读中文。

**实测结论**：`lang="cmn"` 参数只是语言提示码，voice 本身是英文音素训练的。硬传 `cmn` 出来的声音是英文口音的中文，**不可接受**。

**操作**：已删除：
- `/Users/aimac/kokoro/` 整个目录
- `config.yaml` 中的 `providers.moss` 配置行（残留）
- `~/.hermes/skills/tts/moss-tts-nano/` skill 目录
- `/Users/aimac/MOSS-TTS-Nano/` 整个目录
- `tts.provider` 从 `kokoro` 改为 `edge`

## Edge TTS — 当前在用

**配置**（`~/.hermes/config.yaml`）：
```yaml
tts:
  provider: edge
  edge:
    voice: zh-CN-XiaoxiaoNeural
    speed: 1.0
```

**优点**：
- 免费，无需 API key
- 内置中文普通话音色（微软神经网络声音）
- 立即可用，无需下载模型

**适用场景**：中文语音回复、Telegram 语音消息。

## Kokoro 何时适用

如果未来有中文 voice pack 发布，Kokoro 可以重新启用。但当前官方的 `voices.bin` 不支持中文。

**验证本地 voices.bin 的方法**：
```bash
unzip -l ~/kokoro/models/voices.bin
# 或
python3 -c "
from kokoro_onnx import Kokoro
k = Kokoro('models/kokoro-v0_19.fp16.onnx', 'models/voices.bin')
print('Voices:', list(k.voices.keys()))
"
```

## 切换 TTS provider 步骤

1. 修改 `~/.hermes/config.yaml` 的 `tts.provider`
2. 重启 gateway 使配置生效（或 gateway 自动检测）
3. 用 `text_to_speech` 工具测试

**不需要改 skill**：Kokoro 的 skill 描述（`moss-tts-nano`）已删除，新的 Edge 配置直接写死在 `config.yaml` 中。
