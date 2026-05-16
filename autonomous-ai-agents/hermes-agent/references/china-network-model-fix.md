# Mac mini 模型配置（国内网络环境）

## 症状

Mac mini (192.168.0.4) 每条消息报超时：
```
API call failed after 3 retries: Gemini streaming request failed: timed out
```

## 根因

Mac mini 所在网络**完全无法访问 Google API**（generativelanguage.googleapis.com 超时），且 Google 对该 IP 返回 400（地区不支持）。

## 最终方案：aicodee (v2.aicodee.com) custom provider

**三步完成：**

### 1. .env 加 API key
```bash
ssh -i ~/.ssh/hermes_agent aimac@192.168.0.4 \
  "echo 'AICODEE_API_KEY=YOUR_API_KEY' >> ~/.hermes/.env"
```

### 2. config.yaml 加 custom provider
```yaml
custom_providers:
- name: aicodee (v2)
  base_url: https://v2.aicodee.com
  api_key_env_var: AICODEE_API_KEY
  model: MiniMax-M2.7-highspeed

model:
  default: MiniMax-M2.7-highspeed
  provider: aicodee (v2)
```

### 3. 重启
```bash
ssh -i ~/.ssh/hermes_agent aimac@192.168.0.4 \
  "launchctl kickstart -k gui/\$(id -u)/ai.hermes.gateway"
```

## 同时修复 launchd 代理环境变量

launchd 启动的进程不继承系统代理，需在 plist 手动配置：
```xml
<key>EnvironmentVariables</key>
<dict>
    <key>HTTP_PROXY</key>
    <string>http://127.0.0.1:7897</string>
    <key>HTTPS_PROXY</key>
    <string>http://127.0.0.1:7897</string>
</dict>
```

详见：`references/launchd-environment-variables-macos.md`

## 坑

- `provider` 字段必须引用 `custom_providers` 里的 `name`，**不是 base_url**
- API key 变量名在 `.env` 和 `api_key_env_var` 必须完全一致
- 完整配置指南：`references/custom-provider-config.md`

## 相关检测命令

```bash
# aicodee 连通性
ssh -i ~/.ssh/hermes_agent aimac@192.168.0.4 \
  "curl -s --max-time 10 -H 'Authorization: Bearer <key>' \
     'https://v2.aicodee.com/v1/models'"

# OpenRouter（备用）
ssh -i ~/.ssh/hermes_agent aimac@192.168.0.4 \
  "curl -s -o /dev/null -w '%{http_code}' --max-time 15 \
     'https://openrouter.ai/api/v1/models'"
```
