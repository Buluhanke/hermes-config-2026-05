# Kokoro TTS → Hermes 集成指南

## 安装总结

### 1. 环境准备
```bash
mkdir -p ~/kokoro && cd ~/kokoro
python3 -m venv venv
source venv/bin/activate
pip install kokoro-onnx soundfile "misaki[zh]"
pip install num2words  # misaki[zh] 的缺失依赖
```

### 2. 模型下载（走代理，GitHub 直连超时）
```bash
export PROXY="-x http://127.0.0.1:7897"
cd ~/kokoro/models

# ❌ 以下 URL 不存在（v1.0 是过时信息）：
#   kokoro-v1.0.onnx → 404
#   voices-v1.0.bin → 404
# ✓ 实际可用的：
curl $PROXY -L -o kokoro-v0_19.fp16.onnx \
  https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files/kokoro-v0_19.fp16.onnx
curl $PROXY -L -o voices.bin \
  https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files/voices.bin
# 中文语音数据：
curl $PROXY -L -o espeak-ng-data-v1.51.tar.gz \
  https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files/espeak-ng-data-v1.51.tar.gz
tar xzf espeak-ng-data-v1.51.tar.gz
```

### 3. 中文语言码（最大坑）
kokoro-onnx 的 `create(text=..., lang="zh")` 会报错：
```
RuntimeError: language "zh" is not supported by the espeak backend
```
**必须用 `"cmn"`**（ISO 639-3 标准，espeak-ng 的实际语言码）。
`"yue"`（粤语）也支持。

### 4. 中文语音数据
`espeakng_loader` 默认的 espeak-ng-data 没有中文数据，需要覆盖：
```bash
cp -R ~/kokoro/models/espeak-ng-data/* \
  /path/to/venv/lib/python3.14/site-packages/espeakng_loader/espeak-ng-data/
```

### 5. Hermes 集成配置
Command Provider 格式（`~/.hermes/config.yaml`）：
```yaml
tts:
  provider: kokoro
  kokoro:
    type: command
    command: "/Users/aimac/kokoro/venv/bin/python3 /Users/aimac/kokoro/tts_kokoro.py
      --input {input_path} --output {output_path} --voice {voice} --speed {speed}"
    voice: af_sky
    format: wav
```

Command Provider 占位符：
| 占位符 | 说明 | Kokoro 映射 |
|-------|------|------------|
| `{input_path}` | 文本文件路径 | `--input {input_path}` |
| `{output_path}` | 音频输出路径 | `--output {output_path}` |
| `{voice}` | 音色名称 | `--voice {voice}` |
| `{speed}` | 语速 | `--speed {speed}` |
| `{format}` | 输出格式 | wav（硬编码） |

## 音色参考（均为英文，中文质量差）

| 音色 | 特点 | 中文质量 |
|------|------|---------|
| `af_sky` | 中性女声 | ❌ 差（老外读中文口音） |
| `af_sarah` | 明亮女声 | ❌ 差 |
| `am_adam` | 年轻男声 | ❌ 差 |
| `bm_george` | 英式男声 | ❌ 差 |

**结论**：Kokoro 自带 voice 全部英文，中文场景用 Edge TTS（zh-CN-XiaoxiaoNeural）。

## 注意事项
- `onnxruntime-silicon` 在 Python 3.14 上不可用，普通 `onnxruntime` 在 M4 上足够
- 首次加载模型较慢（~3秒），后续缓存后快
- 输出为 WAV 格式（Hermes 平台会自行处理格式转换）
