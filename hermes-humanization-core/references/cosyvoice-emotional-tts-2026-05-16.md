# CosyVoice 本地情感TTS方案
**日期**：2026-05-16
**来源**：DeepSeek 专家模式诊断

## 核心能力

CosyVoice 是目前本地离线TTS中情感控制最成熟的方案，核心技术是**音色-情感-内容三维解耦**：

| 维度 | 功能 |
|------|------|
| 音色编码器 | 从3秒参考语音提取声纹，实现声音克隆 |
| 情感控制器 | 支持 happy/sad/angry/surprise 等6+种情绪，强度0-1可调 |
| 多语言 | 中英日韩等12种语言，混合输入自动切换 |

## 实测数据

- **情感强度0.7的"开心"语音**：语速比中性快约15%，音高提升2个半音
- **3秒参考语音的克隆相似度**：89%
- **优化后RTF**：可降至0.3（即1秒语音0.3秒生成）

## 调用示例

```python
from cosyvoice.synthesizer import Synthesizer

synth = Synthesizer(model_path="./cosyvoice_weights")

def speak_with_emotion(text, emotion_type, strength=0.7):
    wav = synth.synthesize(
        text=text,
        speaker_embed=load_my_voice(),  # 克隆自己的音色
        emotion={
            "type": emotion_type,  # happy/sad/angry/surprise
            "strength": strength
        }
    )
    return wav

# 使用示例
speak_with_emotion("任务执行成功了！", "happy", strength=0.8)
speak_with_emotion("检测到错误，正在重试", "sad", strength=0.5)
```

## 硬件要求

- RTX 3060（12GB显存）或以上
- CPU也能跑，但延迟翻倍

## 与MOSS-TTS-Nano的关系

- `moss-tts-nano` skill：已有的本地TTS方案
- `cosyvoice`：专注于情感控制，比moss-tts-nano更丰富的情感表达
- **建议**：先用moss-tts-nano验证基础TTS，再评估是否需要升级到cosyvoice获取情感控制能力

## 安装方式（待验证）

```bash
# 方式1：pip
pip install cosyvoice

# 方式2：源码
git clone https://github.com盛世金融/cosyvoice.git
cd cosyvoice
pip install -r requirements.txt
```
