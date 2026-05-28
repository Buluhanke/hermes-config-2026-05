---
name: voice-reply-rules
description: 语音/文字回复规则固化
version: 2.0.0
---

## 规则
用户发语音 → 语音回复（auto_tts=true，Kokoro 本地合成，af_sky 音色）
用户发文字 → 文字回复
不混用，规则已固化

## Voice优先原则
收到语音消息时，直接TTS回复，不做任何前置检查（不查日志/不验证状态/不跑终端命令）。用户要的是响应速度，不是诊断报告。

**⚠️ 语音回复内容必须匹配对话话题（硬规则）**
- 用户用中文提问 → 必须用中文回复，不能用英文
- 回复内容必须围绕用户的问题展开，不能跑题
- 跨 session 重建后同样遵守此规则
- 例外：用户明确要求换语言（如"用英文回答"）

违反这条规则会导致"语音对不上聊的内容"，用户体验为"声音正常但答非所问"。

**⚠️ 历史记录不存在时，立即告知而非猜测**
- 用户要求查"某时间点的配置/对话"时，先确认记录是否存在
- 数据库/日志查不到 → 明确告知"该时段无记录"
- 不凭记忆生成答案，不尝试拼凑，不反复查找
- 用户纠正后立即承认，不要解释过程

## 当前配置（已固化，2026-05-28 备份）

**主 TTS 引擎：Kokoro（本地 ONNX）**
```yaml
tts:
  provider: kokoro
  kokoro:
    type: command
    command: "/Users/aimac/kokoro/venv/bin/python3 /Users/aimac/kokoro/tts_kokoro.py --input {input_path} --output {output_path} --voice {voice} --speed {speed}"
    voice: af_sky
    format: wav
```

**备用（Edge TTS，中文女声）：**
```yaml
tts.edge.voice = zh-CN-XiaoxiaoNeural
```

**⚠️ 语音配置已固化，不可轻易改动。** 备份位置：
- 恢复脚本：`~/.hermes/backups/tts_config_backup.sh` — 运行 `bash ~/.hermes/backups/tts_config_backup.sh` 一键恢复
- 配置快照：`~/.hermes/backups/config_snapshot_20260528_语音固化.yaml`

**切换回 Edge TTS 的方法：**
```bash
hermes config set tts.provider edge
# 然后重启 gateway
```

## Kokoro TTS 详细说明

### 安装位置
```
~/kokoro/
├── tts_kokoro.py          # Hermes command provider wrapper
├── models/
│   ├── kokoro-v0_19.fp16.onnx  # 模型文件（169MB）
│   ├── voices.bin              # 音色文件
│   └── espeak-ng-data/         # 中文语音数据
├── venv/                  # 虚拟环境
└── speak.py               # 简易测试脚本
```

### Kokoro 音色列表
- `af_sky`（当前默认）- 美国女声，中性自然，中文效果最佳
- `af` / `af_bella` / `af_nicole` / `af_sarah` - 美国女声
- `am_adam` / `am_michael` - 美国男声
- `bf_emma` / `bf_isabella` - 英国女声
- `bm_george` / `bm_lewis` - 英国男声

### Kokoro 已知问题
| 坑 | 说明 |
|---|---|
| 模型文件名过时 | GitHub release 无 v1.0，实际是 v0_19 |
| 中文语言码 | `lang="zh"` 报错，必须用 `"cmn"` |
| espeak-ng 缺中文数据 | 需下载 espeak-ng-data-v1.51.tar.gz 覆盖 espeakng_loader 数据目录 |

### 测试命令
```bash
cd ~/kokoro && source venv/bin/activate && python speak.py "你好"
```

## 中断系统（TODO - 待实现）

用户要求加入以下功能，让 Hermes 说话时可被打断：

- [ ] **Silero VAD** — 后台监听麦克风，检测用户说话
- [ ] **Interrupt Event** — VAD 检测到用户说话时触发中断信号
- [ ] **Audio Cancel** — 中断信号立即停止当前 TTS 播放

实现后效果：Hermes 说话时用户可以直接插嘴 → Hermes 立刻闭嘴开始听

## 切换音色流程（Edge TTS）
```bash
edge-tts --voice zh-CN-XiaoxiaoNeural --text "测试" --write-media /tmp/sample.ogg
hermes config set tts.edge.voice zh-CN-XiaoxiaoNeural
```

## 平台能力速查

| 平台 | 原生语音支持 | TTS方案 |
|------|------------|---------|
| Telegram | ✅ | 直接发送 MEDIA |
| 微信 | ✅ | 直接发送 MEDIA |
| QQ | ❌ | 告知文件路径 |
| Discord | ✅ | 直接发送 MEDIA |

## Session恢复验证
每次长context或session重建后，被问"XX功能没丢吧"时：
1. 不废话，直接验证
2. 语音验证：发一条语音确认
3. 终端验证：`echo ok && date` 直接跑
4. 验证完直接回"正常/有问题"，不解释过程

## References
- `references/capability-verification.md` — 验证流程细节
