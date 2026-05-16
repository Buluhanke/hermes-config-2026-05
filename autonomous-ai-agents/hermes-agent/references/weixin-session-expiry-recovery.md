# Weixin (微信个人版) Session 过期恢复指南

## 症状

gateway.log 多次出现：
```
ERROR gateway.platforms.weixin: [Weixin] Session expired; pausing for 10 minutes
```

微信渠道完全不可用，用户发消息无回复。

## 根因

WeChat 个人版（ilink 协议）的 session token 有时效限制（通常约 8~48 小时）。token 过期后无法自动续期，需要手动更新。

## 恢复步骤

### 1. 检查当前配置

```bash
grep -A 6 "^  weixin:" ~/.hermes/config.yaml
```

预期看到：
```yaml
weixin:
    enabled: true
    extra:
      account_id: xxx@im.bot
      token: xxx@im.bot:xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
      base_url: https://ilinkai.weixin.qq.com
```

### 2. 检查是否有更新的 token 文件

WeChat adapter 在扫码登录时会自动保存新 token 到 `~/.hermes/weixin/accounts/`：

```bash
ls -lt ~/.hermes/weixin/accounts/
```

每个 `xxx@im.bot.json` 文件的内容格式：
```json
{
  "token": "xxx@im.bot:xxxxx",
  "base_url": "https://ilinkai.weixin.qq.com",
  "user_id": "o9cq809d...@im.wechat",
  "saved_at": "2026-05-10T01:47:04Z"
}
```

**关键判断**：比较 config.yaml 中用的 account_id 和目录里最新 json 文件的 account_id。如果有一个**更新但不同的** json 文件，说明适配器曾经自动保存了新 token 但没写入 config.yaml。

### 3. 更新配置

```bash
# 确认最新 token 文件内容
cat ~/.hermes/weixin/accounts/最新@im.bot.json

# 用 patch 工具更新 config.yaml 的 account_id 和 token 两个字段
```

修改两处：
- `account_id` → 新的 `xxx@im.bot`
- `token` → 新的完整 token 字符串

### 4. 重启 gateway

```bash
~/.hermes/hermes-agent/venv/bin/hermes gateway restart
```

### 5. 验证

检查 gateway.log 确认连接成功：
```bash
sleep 5
tail -20 ~/.hermes/logs/gateway.log | grep -E "weixin|Connected|Ready"
```

预期输出：
```
INFO gateway.run: Connecting to weixin...
INFO gateway.platforms.weixin: [Weixin] Connected account=新account_id base=https://ilinkai.weixin.qq.com
INFO gateway.run: ✓ weixin connected
```

## 如果 config 里已经有最新 token 但仍然 Session expired

说明**所有已保存的 token 都过期了**。需要用户重新扫码登录：

1. 停止 gateway（可选，但建议做）
2. 删除 `~/.hermes/weixin/accounts/` 下的过期 token 文件（保留目录结构）
3. 启动 gateway + 监控日志，等 WeChat 适配器输出二维码
4. 用微信手机客户端扫码

适配器输出的二维码可以截图转发给用户扫描。

## 注意

- WeChat 个人版使用 ilink 协议通过 `ilinkai.weixin.qq.com` 连接
- 和企微（WeCom）是不同的适配器，不要混用配置
- token 更新后不需要改 `.env`，信息全在 `config.yaml` 的 `platforms.weixin.extra` 段
- session sync 文件（`*.sync.json`）由适配器自动维护，一般不需要手动修改
