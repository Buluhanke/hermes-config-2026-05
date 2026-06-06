# 定时切模 — Cron 模板（2026-06-04 落地版）

## 场景

每天固定时间自动切模型（省主链额度 / 切速 / 切到不同的免费档）。
**用户实际请求**："0 点 25 以后换 /model MiniMax-M3-highspeed --provider custom:v2.aicodee.com"

## 三个常见坑（先把坑说清）

### 坑 1：`hermes model switch` 这个子命令**不存在**

用户经常给的命令格式 `/model X --provider custom:Y` 来自 Claude/GPT 的 `/model` slash 概念，
但 **Hermes** 没有 `hermes model switch` 这个子命令。`hermes model` 是交互式选 model 的 TUI。

**正确姿势**：

```bash
# 1. 设 model.default
hermes config set model.default "<新模型名>"

# 2. 设 model.provider（必须用 custom_providers 里的条目名，区分大小写）
hermes config set model.provider "custom:<条目名>"

# 3. 验证
hermes config show | grep -E "^Model:"
```

### 坑 2：大小写敏感

`custom_providers` 里的条目名是 `V2enby.aicodee.com`（V 大写），引用时必须 `custom:V2enby.aicodee.com`，
写 `custom:v2.aicodee.com` 会失败/警告。

查真实条目名：

```bash
grep -A 12 "^custom_providers:" ~/.hermes/config.yaml | head -50
```

### 坑 3：改完不重启 gateway 不热生效

切模后**当前对话还会用旧模型**，新会话才生效。如果你想立即生效要：

```bash
launchctl load -w ~/Library/LaunchAgents/ai.hermes.gateway.plist
```

但这会打断所有正在跑的 session。**所以定时切模一般不重启 gateway，让它下个 session 自然切**。

## 完整脚本

`~/.hermes/scripts/switch_model.sh`：

```bash
#!/bin/bash
# 每日定时切模（cron 调，no_agent mode）

LOG="$HOME/.hermes/logs/switch_model.log"
mkdir -p "$(dirname "$LOG")"

ts() { date '+%Y-%m-%d %H:%M:%S'; }

{
    echo "[$(ts)] 开始切模型 → MiniMax-M3-highspeed (custom:V2enby.aicodee.com)"

    # 干跑+回滚模式（详见 SKILL.md 干跑+回滚验证模式）
    current=$(hermes config show 2>&1 | grep -E "^Model:" | head -1)
    echo "[$(ts)] 当前: $current"

    # 1) 设 model.default
    hermes config set model.default "MiniMax-M3-highspeed" 2>&1
    rc1=$?

    # 2) 设 model.provider（条目名首字母大写！）
    hermes config set model.provider "custom:V2enby.aicodee.com" 2>&1
    rc2=$?

    # 3) 验证
    new=$(hermes config show 2>&1 | grep -E "^Model:" | head -1)
    echo "[$(ts)] 切后: $new"

    if [ $rc1 -eq 0 ] && [ $rc2 -eq 0 ]; then
        echo "[$(ts)] ✅ 切模型成功"
    else
        echo "[$(ts)] ❌ 切模型失败 rc1=$rc1 rc2=$rc2"
        # 失败兜底：推 Telegram
        hermes send "❌ 切模型失败: MiniMax-M3-highspeed (rc1=$rc1 rc2=$rc2)" 2>/dev/null || true
    fi
} | tee -a "$LOG"
```

`chmod +x`：

```bash
chmod +x ~/.hermes/scripts/switch_model.sh
```

## Cron 配置

通过 Hermes 自带的 cronjob 工具（而不是 launchd plist 或系统 crontab）：

```python
cronjob(
    action="create",
    schedule="25 0 * * *",       # 每天 0:25
    name="switch-to-highspeed-0025",
    script="switch_model.sh",     # 在 ~/.hermes/scripts/ 下
    no_agent=True,                # 脚本自管，不开 LLM
    deliver="local",              # 日志本地，不推送
)
```

**已落地的 cron job**（2026-06-04）：`eaaec727b762`
- 名称：`switch-to-highspeed-0025`
- 调度：`25 0 * * *`（每天 00:25）
- 模式：no_agent
- 脚本：`~/.hermes/scripts/switch_model.sh`
- 日志：`~/.hermes/logs/switch_model.log`
- 失败兜底：`hermes send` 推 Telegram

## 验证清单

| 检查 | 命令 |
|---|---|
| cron 注册了 | `hermes cron list \| grep highspeed` |
| 脚本可执行 | `bash -n ~/.hermes/scripts/switch_model.sh`（语法）<br>`ls -la ~/.hermes/scripts/switch_model.sh`（权限） |
| 干跑一遍 | `bash ~/.hermes/scripts/switch_model.sh`（会真改，干跑要看一眼）|
| 验证当前值 | `hermes config show \| grep -E "^Model:"` |

## 改时间/改模型的姿势

只改 schedule / model 名 / provider，不动脚本框架：

```bash
# 1) 先 list 拿到 job_id
hermes cron list | grep highspeed
# → eaaec727b762

# 2) update（schedule 字段）
cronjob(action="update", job_id="eaaec727b762", schedule="30 0 * * *")

# 3) update（script 字段要换新路径）— 先改脚本内容再 update
# 4) 或者直接 remove 旧的 + create 新的
```

## 已知限制

- **不重启 gateway → 不热生效**：下一个 session 才是新模型。如果用户要立即生效，得 `launchctl load -w` 重启。
- **失败告警依赖 `hermes send`**：要确保 Telegram adapter 在线。可以在脚本里也写一条到 `~/.hermes/state/alert.json` 让 watchdog 拾取。
- **没做"切完自动回滚"**：如果新模型不通，下次切换前用户感知不到。建议加个 health check（见 `references/scheduled-task-audit.md` 模式）。
