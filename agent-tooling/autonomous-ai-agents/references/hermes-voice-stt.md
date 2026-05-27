# Hermes Voice/STT 架构与配置

## 平台ASR优先级

| 平台 | ASR优先级 | 说明 |
|------|----------|------|
| **Telegram** | 本地 faster-whisper（强制） | 下载音频后直接走 `transcription_tools.transcribe_audio()` |
| **QQ** | 1.腾讯内置 `asr_refer_text` 2.本地 faster-whisper fallback | 腾讯ASR免费且优先，失败才用本地 |
| **Discord** | 本地 faster-whisper | 走统一 `transcription_tools` |

## 核心配置文件

```yaml
# ~/.hermes/config.yaml
stt:
  enabled: true
  provider: local
  local:
    model: small    # tiny/base/small/medium/large-v3
    language: ''
```

## 平台对应实现

- **Telegram** (`gateway/platforms/telegram.py`): 下载 `.ogg` → `_enrich_message_with_transcription()` → `transcribe_audio()`，直接使用 `stt.local.model`
- **QQ** (`gateway/platforms/qqbot/adapter.py`): 优先 `asr_refer_text`（腾讯ASR），为空才走本地 STT
- **统一入口** (`gateway/run.py` `_enrich_message_with_transcription()`): 调用 `tools.transcription_tools.transcribe_audio()`

## 模型选择（M4 Mac mini 24GB）

| 模型 | 内存 | 速度 | 推荐 |
|------|------|------|------|
| base | ~400MB | 快 | ~~（已弃用）~~ |
| **small** | ~1-2GB | 中等 | **生产推荐** |
| medium+ | 5GB+ | 慢 | 需要GPU |

## 关键结论

- **Telegram语音** → 用到 `stt.local.model`（当前small）✓
- **QQ语音** → 默认走腾讯ASR，本地模型仅作fallback
- 模型非常驻内存，处理时加载跑完即释放
