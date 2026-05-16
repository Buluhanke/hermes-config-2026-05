# QQ Bot 500错误断开恢复

## 症状
- `gateway_state.json` 显示 `qqbot: { "state": "disconnected" }`
- `gateway.log` 出现：`Reconnect failed: Failed to get QQ Bot gateway URL: Server error '500 Internal Server Error'`
- 之后持续 `WebSocket error: WebSocket closed` → `Reconnecting in 2s...` → 再失败，最终放弃

## 根因
腾讯 QQ 开放平台的 gateway API 偶发返回 500，Bot SDK 的重试机制在多次 500 后放弃重连。此时 Bot 进程本身没有崩溃，只是进入 disconnected 状态等待人工干预。

## 恢复步骤（先试这个，不用动 credentials）

```bash
# 1. 重启整个 gateway（不是 --platform qqbot，没有这个参数）
cd ~/.hermes/hermes-agent && ./venv/bin/python -m hermes_cli.main gateway restart

# 2. 等待 5 秒后验证
sleep 5 && cat ~/.hermes/gateway_state.json | python3 -c "
import sys, json
d = json.load(sys.stdin)
qq = d['platforms']['qqbot']
print(f\"QQ state: {qq['state']}, updated: {qq['updated_at']}\")
"
```

**通常一次 restart 就能恢复**（实测 2026-05-12）。500 是腾讯 API 瞬时不稳，重启后 Bot 用同一组 app_id/client_secret 重新认证即可。

## 什么时候需要真的更新 credentials

真正 credential 失效的特征：
- 多次（3次以上）`hermes gateway restart` 后仍然 `Reconnect failed: Cannot connect to host api.sgroup.qq.com`
- `check_qqbot.py` 持续返回 `100016`（credential 被拒绝）
- `curl https://api.sgroup.qq.com` 返回 404 但 Bot 仍然连不上

真正需要更新 credentials 的场景：
- `100007` = app_id 或 client_secret 为空或缺失
- `100016` 持续（credential 被平台拒绝）

详见 `references/qqbot-diagnostic-check.md`

## 日志关键字

```
Reconnect failed: Failed to get QQ Bot gateway URL: Server error '500 Internal Server Error'
WebSocket error: WebSocket closed
Reconnecting in 2s (attempt 1)...
```

500 错误后 Bot 进入 disconnect 状态，gateway 进程本身仍在运行（QQ/微信/API_server 其他平台可能正常）。
