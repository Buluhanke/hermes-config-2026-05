# screen_trigger_handler.py 修复记录（2026-05-30）

**问题**：Telegram 推送失败，`from hermes_tools import send_message` 在 cron 环境报错 "No module named 'hermes_tools'"

**症状**：
```
[2026-05-30 00:14:01] Telegram推送失败: No module named 'hermes_tools'
[2026-05-30 00:14:01] 处理完成 [urgent]
```

**根因**：`hermes_tools` 在 cron 定时任务环境中不可用，send_message 不可用。

## 修复方案

### 修复前（失败）
```python
from hermes_tools import send_message
send_message(message=push_msg)
```

### 修复后（直接 Telegram Bot API）
```python
import urllib.request
bot_token = os.getenv('TELEGRAM_BOT_TOKEN', '')
chat_id = os.getenv('TELEGRAM_CHAT_ID', '')
if bot_token and chat_id:
    push_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    data = json.dumps({'chat_id': chat_id, 'text': push_msg}).encode()
    req = urllib.request.Request(push_url, data=data, headers={'Content-Type': 'application/json'})
    urllib.request.urlopen(req, timeout=10)
```

**要求的环境变量**：
- `TELEGRAM_BOT_TOKEN` — Telegram Bot Token
- `TELEGRAM_CHAT_ID` — 目标 Chat ID

**备选**：如果环境变量未配置，日志输出 "Telegram未配置（无BOT_TOKEN/CHAT_ID），跳过推送"，不报错。

## 其他修复

**场景分类 prompt 幻觉 bug**：

原始 prompt（中英文混合）导致 smolvlm2 输出 Python 代码（如 "type('seconds')"）而非场景名称。

修复后 prompt（全英文选项）：
```
[这是macOS系统截图，不是照片]
看这张截图，判断这是什么场景？
选项：browser/wechat/desktop/calculator/jingdong/1688/dingtalk/telegram/other
只回答一个选项，写作对应英文单词。不要其他文字，不要代码。
```

**验证**：日志中 "场景类型:" 应为英文单词（如 "calculator"），而非代码片段。

## 文件变更

- `~/.hermes/scripts/screen_trigger_handler.py` — 修复 send_message + prompt 幻觉
- 备份：`~/.hermes/scripts/screen_trigger_handler.py.bak.20260530`