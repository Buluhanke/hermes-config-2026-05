---
name: custom-provider-config
description: Custom Provider 配置参考
version: 1.1.0
---

# Custom Provider 配置参考

## 两种配置方式：推荐 vs 不推荐

**推荐：named provider + env var 引用**

```yaml
model:
  default: MiniMax-M2.7-highspeed
  provider: aicodee          # 引用 providers 段定义的名称

providers:
  aicodee:
    api_key_env_var: AICODEE_API_KEY   # 引用 .env 变量
    base_url: https://v2.aicodee.com/v1

# .env：
# AICODEE_API_KEY=YOUR_API_KEY
```

**不推荐：直接写死在 model 段（当前 config 里就是这种混乱写法）**

```yaml
model:
  default: MiniMax-M2.7-highspeed
  provider: custom           # ← 意味着"不引用任何 provider，用下面内嵌的 base_url/key"
  base_url: https://v2.aicodee.com/v1
  api_key: YOUR_API_KEY
```

这种写法当时能工作，但造成配置混乱：
- `providers.aicodee` 虽然定义了但没被引用
- `custom_providers` 里也有一条 aicodee 重复定义
- 辅助模型（vision/compression 等）配置引用的是 deepseek，和主模型配置风格不一致
- 维护困难，分不清哪个才是真的

## custom_providers（第三方中转场景）

`custom_providers` 适合走非标准端点的场景（如 Ollama、厂商中转）。格式：

```yaml
custom_providers:
- name: MiniMax Relay (v2.aicodee.com)   # name 唯一标识
  key_env: AICODEE_API_KEY                # custom_providers 用 key_env，不是 api_key_env_var
  base_url: https://v2.aicodee.com/v1
  model: MiniMax-M2.7-highspeed
```

注意：`custom_providers` 的字段是 `key_env`（不是 `api_key_env_var`）。

## 排查 aicodee 返回 401 的正确步骤

不要看到 401 就以为 key 失效。先直接 Python 测：

```bash
~/.hermes/hermes-agent/venv/bin/python3 -c "
from openai import OpenAI
c = OpenAI(api_key='YOUR_API_KEY', base_url='https://v2.aicodee.com/v1')
r = c.chat.completions.create(model='MiniMax-M2.7-highspeed', messages=[{'role':'user','content':'hi'}], max_tokens=5, timeout=15)
print('OK:', r.choices[0].message.content)
"
```

- 返回 `OK:`（空内容但无错误）= key 有效，配置方式错误
- 返回 `AuthenticationError` = key 真的失效
- 超时/连接失败 = 网络或端点问题

## 常见错误

| 错误写法 | 正确写法 |
|---|---|
| `provider: https://v2.aicodee.com` | `provider: aicodee`（引用 providers 段） |
| `api_key_env_var` 在 custom_providers 里 | `key_env` 在 custom_providers 里 |
| `base_url: https://v2.aicodee.com`（缺 /v1） | `base_url: https://v2.aicodee.com/v1` |
| key 直接写在 config.yaml | key 写在 .env，用 `api_key_env_var` 引用 |

## 重启生效

```bash
hermes gateway restart
```
