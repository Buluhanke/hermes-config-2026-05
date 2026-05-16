# aicodee (v2.aicodee.com) 配置故障排查

## 快速配置（方式 A — 直接写 key）

```yaml
model:
  api_key: YOUR_API_KEY
  base_url: https://v2.aicodee.com/v1
  default: MiniMax-M2.7-highspeed
  model: MiniMax-M2.7-highspeed
  provider: custom
```

**关键点**：`provider: custom` 而非 provider name。

---

## 三个常见配置错误（按发生频率排序）

### ❌ 错误 1：base_url 缺少 `/v1` 后缀
```yaml
# 错误
base_url: https://v2.aicodee.com

# 正确
base_url: https://v2.aicodee.com/v1
```
**症状**：API 返回空 content 或 404。

### ❌ 错误 2：api_key 未写入 model 配置
```yaml
# 错误 — 只在 .env 里写了变量，但名字也不对
# .env: AICODEE_API_KEY=YOUR_API_KEY  ← 对不上
model:
  apiKey: ''   # 空的

# 正确 — 直接写在 model 下
model:
  api_key: YOUR_API_KEY
```
**症状**："Empty response from model" / "API call failed"。

### ❌ 错误 3：provider 值错误
```yaml
# 错误 — 用了 custom_providers 的 name
model:
  provider: aicodee (v2)   # ← 错

# 正确 — 写 "custom"
model:
  provider: custom
```

---

## 三步检查清单

1. `grep "base_url.*aicodee" ~/.hermes/config.yaml` → 确认有 `/v1`
2. `grep "api_key:" ~/.hermes/config.yaml | head -3` → 确认 model.api_key 非空
3. `grep "provider:" ~/.hermes/config.yaml | head -3` → 确认是 `custom`

---

## 验证命令

```bash
# 直接测试 API 连通性
curl -s -X POST https://v2.aicodee.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{"model":"MiniMax-M2.7-highspeed","messages":[{"role":"user","content":"hi"}],"max_tokens":50}'
```

期望：返回 200，有 `choices[0].message.content`（可能同时有 `reasoning_content`）。

---

## 重启生效
```bash
launchctl kickstart -k gui/$(id -u)/ai.hermes.gateway
```

---

## 相关文件

- 飞书配置文档：https://lcnwoe31c51t.feishu.cn/wiki/A892wYxnVippRXkviJRcw7LBnGV
