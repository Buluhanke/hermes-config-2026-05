# WeCom Platform Setup (企业微信机器人)

## Config Location

WeCom credentials go under `platforms.wecom.extra` in `~/.hermes/config.yaml`. NOT under the `model` or `custom_providers` sections.

```yaml
platforms:
  wecom:
    enabled: true
    extra:
      bot_id: "your-bot-id"
      secret: "your-secret"
      websocket_url: "wss://openws.work.weixin.qq.com"
      dm_policy: "open"          # open | allowlist | disabled
      group_policy: "open"       # open | allowlist | disabled
      group_allow_from: []       # list of allowed group IDs
```

## Bot ID vs AppID

- **Bot ID** (企业微信机器人): Found in 企业微信管理后台 → 应用管理 → your bot → 基础信息
- Looks like: `aibRODF-ClY8HEBFS1Zu_aNcXH3WCmeYfMK` (starts with `aib`)
- NOT the Corp ID or App ID

## How It Works

The WeCom adapter uses the WeCom AI Bot WebSocket gateway:
1. Authenticates via `aibot_subscribe`
2. Receives inbound `aibot_msg_callback` events
3. Sends outbound messages via `aibot_send_msg`

## Verification

After config change, restart gateway:
```bash
hermes gateway restart
```

Check logs for successful connection:
```bash
hermes logs --level info | grep -i wecom
```

Expected output:
```
✓ wecom connected
[Wecom] Connected to wss://openws.work.weixin.qq.com
```

## ⚠️ Config Loss When Changing Models — DISASTER RECOVERY

`hermes model` or `hermes setup` can OVERWRITE `config.yaml` and DROP the entire `platforms` section (not just wecom). This is a confirmed failure mode — it has happened multiple times and wiped QQ, WeChat, AND WeCom configs simultaneously.

**Prevention**: Before running ANY model change command, dump ALL platform configs:
```bash
# Dump all platform credentials (run before hermes model / hermes setup)
grep -A 15 "^platforms:" ~/.hermes/config.yaml
```

**Scope of the failure**: The `platforms` section is NOT just wecom. It contains ALL messaging platform adapters:
- `platforms.qqbot` — QQ机器人
- `platforms.weixin` — 微信个人版
- `platforms.wecom` — 企业微信
- `platforms.telegram`, `platforms.discord`, etc.

When the `platforms` section is wiped, the gateway still runs with in-memory config from before the wipe (so messaging continues to work until next restart). After a restart, ALL messaging platforms go dark.

### Known-Good Platform Configs (aimac @ Mac mini 192.168.0.4)

Recover with these values from `.env`:
```yaml
platforms:
  qqbot:
    enabled: true
    extra:
      app_id: 1903873816
      client_secret: RtLoHlFkFlHoMuT2cCnO0cFsWApUAqXE
  weixin:
    enabled: true
    extra:
      account_id: "878a655764aa@im.bot"
      token: "878a655764aa@im.bot:060000867a04e5e66567adbd916d9237304fc0"
      base_url: "https://ilinkai.weixin.qq.com"
      cdn_base_url: "https://novac2c.cdn.weixin.qq.com/c2c"
      dm_policy: "pairing"
      group_policy: "disabled"
      allow_all_users: false
  api_server:
    host: 0.0.0.0
```

> Note: `platforms.qqbot` uses `app_id` + `client_secret` (NOT the same as `QQ_APP_ID` / `QQ_CLIENT_SECRET` env vars — those are legacy). The numeric ID `1903873816` is the app_id. `client_secret` is the string from the QQ Open Platform developer console.

### WeCom-specific Recovery

```bash
hermes config set platforms.wecom.enabled true
hermes config set platforms.wecom.extra.bot_id "YOUR_BOT_ID"
hermes config set platforms.wecom.extra.secret "YOUR_SECRET"
hermes config set platforms.wecom.extra.websocket_url "wss://openws.work.weixin.qq.com"
hermes config set platforms.wecom.extra.dm_policy "open"
hermes config set platforms.wecom.extra.group_policy "open"
hermes gateway restart
```

### Post-Restore Verification

After restoring, verify ALL platforms are connected:
```bash
tail -30 ~/.hermes/logs/gateway.log | grep -E "Ready|Connected|platforms"
```

Expected: QQBot `[QQBot:1903873816]` shows `Ready` / `Connected`.

## Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| 401 invalid token | `bot_id` or `secret` wrong | Double-check credentials in 管理后台 |
| WebSocket connection refused | Network/firewall | Check outbound port 443 to `openws.work.weixin.qq.com` |
| Bot silent | Process died; check `hermes logs` | Restart gateway |
| "No LLM provider configured" | `platforms.wecom` section dropped from config | Restore via disaster recovery steps above |

## Multiple Platforms

- WeChat personal (微信) uses `platforms.weixin` — no extra config needed, connects via `weixin` channel directory
- WeCom (企业微信) uses `platforms.wecom` — requires bot_id + secret in `platforms.wecom.extra`
- **两者是不同的 adapter**，不要混淆。Gateway 日志里 wecom 显示 `gateway.run: ✓ wecom connected/disconnected`，weixin 显示 `gateway.run: ✓ weixin connected/disconnected`

## 检测当前配置的命令

检查当前 config.yaml 中有哪些 platform 配置：
```bash
grep -A8 "^platforms:" ~/.hermes/config.yaml
```

检查 wecom 是否在配置中：
```bash
grep "wecom\|WeCom" ~/.hermes/config.yaml
```

检查 weixin 是否在配置中：
```bash
grep "weixin\|Weixin" ~/.hermes/config.yaml
```

检查 Gateway 日志中的连接状态（最近10条）：
```bash
grep "wecom\|WeCom\|weixin\|Weixin" ~/.hermes/logs/gateway.log | grep "connected\|disconnected" | tail -10
```

## Related

- WeChat personal (微信) uses a different adapter: `platforms.weixin` — no extra config needed, connects via `weixin` channel directory
- Both WeCom and WeChat appear in logs as `platform=weixin` for inbound messages
