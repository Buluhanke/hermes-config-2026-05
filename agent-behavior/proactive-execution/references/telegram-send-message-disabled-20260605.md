# Telegram 会话里禁用 `send_message` 工具转发 (2026-06-05)

> 用户原话: *"我们现在的对话就是在Telegram，你不用转发了"*
> 适用: 当前对话渠道 = Telegram 时, 禁用 `send_message` 工具

## 根因

assistant 在 Telegram 对话里既回文字内容（直接发到对话），又调 `send_message` 工具把"我发了什么"重新发一遍 → 用户看到两条一模一样的消息，纯粹噪音。

## 正解

- **Telegram 会话中**: 只用文字回复用户, **禁止**调 `send_message` 工具
- **跨平台推送** (Feishu/Weixin/QQ bot/未在当前对话的频道): 才用 `send_message`
- **判断标准**: 当前对话渠道 = Telegram → 不转发; 其他平台 → 转发

## 触发词

用户说 "你不用转发了" / "别再发一遍" / "别重复" → 立刻停 `send_message` 行为, 只回文字

## send_message 用法 (跨平台推送时)

```python
# MCP 工具版 (Hermes 工具)
send_message(action="send", target="telegram", message="...")

# 跨频道推送
send_message(action="send", target="discord:#engineering", message="...")

# 列出可用频道 (推送前先 list)
send_message(action="list")
```

## 反面教材 (6/5 真实事件)

我回复了 "**发完了** (13585)" 等冗余内容, 又调 `send_message` 把同样消息转发到当前 Telegram 对话 → 用户看到两条, 当面纠正。

修法: 在 Telegram 对话里**只发文字内容**给用户, **不再做 send_message 转发**。send_message 工具是给其他平台或还没在对话的频道用的。

## self-check (Telegram 会话时)

```
□ 我要发消息到当前 Telegram 对话? → 走文字回复, 不调 send_message
□ 我要发到 Feishu/Weixin/QQ bot? → 调 send_message
□ 我要发到 Telegram 的非 home channel? → 调 send_message + target
```

## 配套: 用户的"真反馈" vs "信息"

**真反馈** (需要 send_message 转发的):
- 用户说 "推送到 Feishu" / "告诉 QQ bot" / "通知 Discord"
- 跨平台任务 (Telegram 上接, Feishu 上交付)

**信息** (不需要转发的):
- 给当前对话里的用户回的内容
- 自己做完事后的内部分析
- 报错 / 重试日志

判断: 用户在对话里**就在等我回**, 我回的每条都直接给他看, 不用再"转一次"。
