---
name: hermes-provider-debugging
description: Hermes 模型 provider 配置诊断 — custom_providers YAML结构、provider可用性、API余额、模型目录缓存问题
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [macos, linux]
triggers:
  - 模型消失
  - 模型不肯用
  - provider 失效
  - 模型 404 402
  - hy3 free 模型不可用
  - custom_providers 配置问题
---

# Hermes Provider Debugging

## 触发词
- 「模型消失」「模型不肯用」
- 「provider 失效」
- 任何模型报 HTTP 404/402/401
- 用户问「为什么 XX 模型用不了」

## 诊断顺序（必须按序）

### 第 0 步：验证 Gateway 在跑
Gateway 停了先修 Gateway，其他诊断免谈。

### 第 1 步：查日志错误码
```
tail -100 ~/.hermes/logs/gateway.error.log | grep "HTTP 4[0-9]{2}"
tail -50 ~/.hermes/logs/agent.log | grep "API call failed"
```
找 HTTP 状态码：402=余额不足，404=模型不存在，401=认证失败，500=provider内部错误。

### 第 2 步：验证 `custom_providers` YAML 结构
```python
python3 -c "
import yaml
with open('~/.hermes/config.yaml') as f:
    cfg = yaml.safe_load(f)
cp = cfg.get('custom_providers')
print('type:', type(cp).__name__)
"
```
- `type: dict` = 正确
- `type: list` = 所有 fallback provider 静默失效

正确格式（dict）：
```yaml
custom_providers:
  cerebras:
    api_key: csk-...
    base_url: https://api.cerebras.ai/v1
```

错误格式（list，会静默失效）：
```yaml
custom_providers:
- name: cerebras
  api_key: csk-...
```

### 第 3 步：验证 API 余额
```bash
curl -s https://openrouter.ai/api/v1/credits \
  -H "Authorization: Bearer $OPENROUTER_API_KEY"
```

### 第 4 步：确认两套认证体系独立
- OpenRouter：直接 API key（sk-or-v1-...）
- Nous Portal：NAS invoke JWT（每15秒刷新）
- 不能混用，余额独立

## 常见失败模式
| 错误码 | 含义 | 解决方案 |
|--------|------|---------|
| HTTP 404 | 模型下线/不存在 | 查 model_catalog.json 是否过期 |
| HTTP 402 | 余额不足 | 去平台充值 |
| HTTP 401 | 认证失败 | 查 API key |
| type: list | custom_providers 结构错误 | 改为 dict 格式 |

## 日志文件
- `~/.hermes/logs/gateway.error.log`
- `~/.hermes/logs/agent.log`
- `~/.hermes/logs/gateway.log`
- `~/.hermes/logs/gateway-exit-diag.log`
