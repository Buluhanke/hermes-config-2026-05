---
name: voice-reply-rules
description: 语音/文字回复规则固化
version: 3.0.0
---

## 规则
用户发语音 → 语音回复（auto_tts=true）
用户发文字 → 文字回复
不混用，规则已固化

**通道对应硬规则（用户 2026-06-04 拍板）**：
- 语音来信 → 一定用语音回（不混文字）
- 文字来信 → 一定用文字回（不发语音）
- 跨 session 重建后同样遵守
- 语音通道默认 TTS 引擎：Edge TTS zh-CN-XiaoxiaoNeural（见下）

**🔒 硬规则（用户 2026-06-04 明确指令）：**
- 语音来信 → 必须语音回（不掺文字）
- 文字来信 → 必须文字回（不发语音气泡）
- 收到空语音（录音失败） → 用 TTS 告诉用户"没听到内容"，不要替用户猜意图
- 跨 session 重建后同样遵守

**TTS 引擎：Edge TTS（唯一方案，已固化 2026-06-04）**
```yaml
tts:
  provider: edge
  edge:
    voice: zh-CN-XiaoxiaoNeural
```

**为什么用 Edge：**
- 中文质量稳，免费，无需本地模型
- Kokoro 已卸载（169MB 模型 + venv + 技能全清，2026-06-04）
- Kokoro 中文听感差（英文 voice 硬读 cmn 注音）

**切换 Edge 音色方法：**
```bash
edge-tts --voice zh-CN-XiaoxiaoNeural --text "测试" --write-media /tmp/sample.ogg
hermes config set tts.edge.voice zh-CN-XiaoxiaoNeural
```

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

## 中断系统（TODO - 待实现）

用户要求加入以下功能，让 Hermes 说话时可被打断：

- [ ] **Silero VAD** — 后台监听麦克风，检测用户说话
- [ ] **Interrupt Event** — VAD 检测到用户说话时触发中断信号
- [ ] **Audio Cancel** — 中断信号立即停止当前 TTS 播放

实现后效果：Hermes 说话时用户可以直接插嘴 → Hermes 立刻闭嘴开始听

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
