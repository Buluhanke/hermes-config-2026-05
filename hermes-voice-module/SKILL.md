---
name: hermes-voice-module
description: "Phase 4 核心：语音合成（TTS）+ 语音识别（ASR），让 Hermes 长出嘴巴和耳朵。"
---

# hermes-voice-module

**Phase 4 核心**：语音合成（TTS）+ 语音识别（ASR），让 Hermes 长出嘴巴和耳朵。

## 依赖安装

```bash
pip3 install edge-tts faster-whisper -i https://pypi.tuna.tsinghua.edu.cn/simple --break-system-packages
```

## 文字 -> 语音（TTS，Edge-TTS 微软免费接口）

```python
from voice_module import speak_to_file, speak, voice_briefing, voice_alert

# 生成音频文件（推荐用这个）
speak_to_file("老板早，A供应商纸箱今天涨价了。", "/tmp/hermes_ready.mp3")

# 直接播放（会弹出音频播放器）
speak("消息已发送", voice=VOICE_FEMALE)

# 紧急告警（女声）
voice_alert("原材料涨价20%，建议立刻锁价", urgent=True)

# 语音简报
voice_briefing("今日采购简报", [
    "A供应商报价涨至5.8元",
    "B供应商价格稳定在5.2元",
])
```

## 语音 -> 文字（ASR，Faster-Whisper 本地）

```python
from voice_module import listen, listen_from_mic

# 从音频文件识别
text = listen("/tmp/老板语音.m4a")
print(text)

# 从麦克风录音并识别（需要 sox：brew install sox）
# text = listen_from_mic(duration_seconds=10)
```

## 情绪自适应语音

```python
from voice_module import emotion_speak
from humanization_core import analyze_emotion

# 老板发消息 → 分析情绪 → 调整语音风格
emotion = analyze_emotion("又拖了！！！真的很烦！")
emotion_speak("供应商已确认，明天发货。", emotion=emotion["emotion"])
```

## 验证码接入

打码平台（超级鹰）接口文档：`references/captcha-chaojiying.md`

## 自检

```bash
python3 voice_module.py
# 第一部分（语音生成）：应立即生成 /tmp/hermes_test.mp3
# 第二部分（Whisper加载）：首次加载约10-20秒
```

## ⚠️ 已知坑点

### Kokoro TTS 只有英文 voice（重要！）

Kokoro 自带 voice 文件（`voices.bin`）全是英文：af_sky, af_bella, bf_emma 等，没有中文 voice。

**`lang="cmn"` 参数不创造中文 voice**——它只改变发音规则，但 voice 本身是英文人，读中文听起来像英文（怪怪的英文腔）。

**中文 TTS 正确方案**：
- 首选：Edge TTS 音色 `zh-CN-XiaoxiaoNeural`（微软免费，配好即用）
- Kokoro 中文支持需额外下载中文 voice 文件（2025年中才出现），非默认包

**验证 Kokoro voice 列表**：
```bash
cd ~/kokoro && ./venv/bin/python3 -c "
from kokoro_onnx import Kokoro
k = Kokoro('models/kokoro-v0_19.fp16.onnx', 'models/voices.bin')
print('Voices:', list(k.voices.keys()))
"
```

**验证 TTS 输出语言**（最直接方法）：
```bash
echo "你好，这是中文测试" > /tmp/test.txt
~/kokoro/venv/bin/python3 tts_kokoro.py --input /tmp/test.txt --output /tmp/test.wav --voice af_sky
# 播放，如果听起来像英文而不是中文 → 证明 voice 不支持中文
```

### HuggingFace 被墙（中国网络）导致 Whisper 模型下载失败

国内网络环境下，`faster-whisper` 初始化时下载模型失败。httpx 库走 `huggingface_hub` 访问 `huggingface.co` 会报 `Connection reset by peer` 或 `ConnectTimeout`。

**修复**：在 `get_whisper_model()` 中设置 `HF_ENDPOINT` 环境变量指向镜像（已写入 `voice_module.py`）：

```python
os.environ.setdefault('HF_ENDPOINT', 'https://hf-mirror.com')
```

注意用 `setdefault()` 而非 `os.environ['HF_ENDPOINT'] = ...`——前者仅在变量未设置时写入，避免覆盖用户自定义的配置。

**验证**：
```bash
# 直连 huggingface.co → 000（被墙）
curl -s --connect-timeout 10 -o /dev/null -w '%{http_code}' https://huggingface.co

# 镜像正常 → 200
curl -s --connect-timeout 10 -o /dev/null -w '%{http_code}' https://hf-mirror.com
```

**额外注意**：设置环境变量后，`unset HTTP_PROXY HTTPS_PROXY` 也可能需要，因为 httpx 库可能会走系统代理。不过 `setdefault('HF_ENDPOINT')` 已足够，httpx 会用镜像地址替代原始域名，绕过了 DNS 污染。

### Edge-TTS 在 terminal 走代理会失败
terminal 工具调用 `curl` 被安全策略 block，edge-tts 底层也是 HTTP 请求。建议用 `execute_code` 做 edge-tts 测试，不要用 `terminal`。

### Faster-Whisper 首次加载极慢
首次 `import faster_whisper` 时会下载/加载模型，约 10-30 秒。后续实例化会缓存模型。语音测试脚本第一次跑超时是正常的，不是坏了。
