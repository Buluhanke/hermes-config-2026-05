# 2026-06-05 Telegram OGG → faster-whisper STT 实战

## 场景
用户在 Telegram 发语音, 问 "晚上一天自我进化的目标和方向是什么" (实际是 "夜间"
, STT 转对了, 我猜错了)。

## 落盘路径
`~/.hermes/audio_cache/audio_92225838744e.ogg` (22578 bytes, 5-6 秒)
- 文件名 = `audio_<随机hex>.ogg` (gateway 落盘)
- codec = opus (Telegram 端录音)
- 不需要 ffmpeg 手动转码, faster-whisper 内部处理

## 一行 STT (实测)
```python
from faster_whisper import WhisperModel
model = WhisperModel('small', device='cpu', compute_type='int8')
segments, info = model.transcribe(
    '/Users/aimac/.hermes/audio_cache/audio_92225838744e.ogg',
    language='zh', beam_size=1
)
for seg in segments:
    print(seg.text.strip())
# → "晚上夜間自我進化的目標和方向是什麼"
```

输出:
- language=zh, probability=1.00 (强制 language=zh 才稳)
- 5.6 秒转完 (M4 Mac mini CPU, small 模型)
- 文本: "晚上夜間自我進化的目標和方向是什麼" (繁简都识别, "進" 是台湾用法)

## 关键点
1. `language='zh'` 必传, 不传小模型被静音概率带偏
2. `beam_size=1` 速度 vs 精度平衡
3. .ogg 文件直接吃, 不要中间转 wav
4. 0 字节空文件会 hang, 先 stat 再转
5. ~/.hermes/audio_cache 不自动清理, 需纳入 cleanup_hermes_logs

## 验证步骤
```bash
# 1. 确认音频在
ls -la ~/.hermes/audio_cache/ | tail -5

# 2. 确认 faster-whisper 可用
python3 -c "from faster_whisper import WhisperModel; print('OK')"

# 3. 转写
python3 -c "
from faster_whisper import WhisperModel
m = WhisperModel('small', device='cpu', compute_type='int8')
s, i = m.transcribe('~/.hermes/audio_cache/audio_xxx.ogg', language='zh', beam_size=1)
print(i.language, i.language_probability)
for x in s: print(x.text)
"
```

## 失败模式
- 模型没下载: 第一次 WhisperModel('small') 会下载 ~460MB, M4 上 ~30 秒
  → 在 venv 提前跑一次预热
- 路径错: `transcribe()` 不存在, 因为 `whisper` 库有这个方法
  但 `faster_whisper.WhisperModel` 才有 `transcribe()` (1.x API)
- language 写错: 写 `lang=` 报 TypeError, 正确是 `language=`
- 静音太长: small 模型在长静音上耗时长, 短语音 5-10s 最优

## 整合方向
下次用户发 Telegram 语音, 可在 gateway 内部直接 STT 后送入模型,
不需要用户先转文字。但当前实现是 ogg 直接送 VAD, 暂未集成。

参考: `voice/local-stt/SKILL.md` (umbrella 文档)
