# Kokoro TTS 安装 & 使用指南

安装时间：2026-05-28
机器：Mac mini M4 (arm64)

## 安装步骤

```bash
# 1. 创建虚拟环境
mkdir -p ~/kokoro && cd ~/kokoro
python3 -m venv venv
source venv/bin/activate

# 2. 安装依赖
pip install kokoro-onnx soundfile "misaki[zh]" num2words

# 3. 下载模型文件（走代理）
cd ~/kokoro/models
curl -x http://127.0.0.1:7897 -L -o kokoro-v0_19.fp16.onnx \
  https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files/kokoro-v0_19.fp16.onnx
curl -x http://127.0.0.1:7897 -L -o voices.bin \
  https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files/voices.bin

# 4. 下载 espeak-ng 数据（中文需要）
curl -x http://127.0.0.1:7897 -L -o espeak-ng-data-v1.51.tar.gz \
  https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files/espeak-ng-data-v1.51.tar.gz
tar xzf espeak-ng-data-v1.51.tar.gz

# 5. 将 espeak-ng 数据复制到 espeakng_loader 目录
cp -R espeak-ng-data/* ~/kokoro/venv/lib/python3.14/site-packages/espeakng_loader/espeak-ng-data/
```

## speak.py

见 `~/kokoro/speak.py`。关键参数：
- `voice="af_sky"` — 女性中文语音
- `lang="cmn"` — 必须用 cmn，不能用 zh
- `speed=1.0`

## 测试

```bash
cd ~/kokoro && source venv/bin/activate
python speak.py "你好，我是 Hermes"
```

## 清理

```bash
rm -rf ~/kokoro/venv ~/kokoro/models ~/kokoro/speak.py
```
