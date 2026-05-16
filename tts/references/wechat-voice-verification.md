# WeChat 语音消息验证记录

## 验证结果（2026-05-16）

| 平台 | 语音发送 | 备注 |
|------|---------|------|
| 微信 | ✅ 成功 | MEDIA标签直接发送，自动播放 |
| 企业微信 | ❌ 未配置 | 需要配置 |
| Telegram | ⚠️ 超时 | 文件过大或格式问题 |
| QQ | ❌ 不支持 | 原生语音气泡无法发送，MEDIA文件被丢弃 |

## 微信发送方式

```python
send_message(
    message="MEDIA:/tmp/voice.ogg",
    target="weixin:o9cq809dmcoo6iWTUvp2vkPyS0wg@im.wechat"
)
# 或简写（发送到 home channel）
send_message(message="MEDIA:/tmp/voice.ogg", target="weixin")
```

## 微信语音限制

微信将音频作为**媒体附件**播放，**不是**"按住说话"原生语音气泡。用户看到的是可点击播放的音频卡片，而非微信原生语音消息形式。
