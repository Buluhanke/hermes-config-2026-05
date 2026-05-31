# Provider 直连测试结果（2026-06-02深夜复盘）

## 结论

| Provider | 模型 | 直连HTTP测试 | 结论 |
|----------|------|-------------|------|
| Groq | llama-3.3-70b-versatile | ✅ 200 OK | key正常，403是当时CF拦截 |
| Cerebras | zai-glm-4.7 | ✅ 200 OK | key正常，403是IP被禁 |
| OpenRouter | deepseek-v4-flash | ✅ 200 OK | 成本极低 |
| DeepSeek 直连 | deepseek-v4-flash | ❌ 401 | key无效，需重新获取 |
| MiniMax CN | MiniMax-M2.7 | ❌ 429/2056 | 额度耗尽 |

## 测试方法

用 Python 直接读 `.env` 和 `config.yaml` 中的 key，通过 HTTP 测试各 provider：

```python
import os, json, yaml, urllib.request

# 读 .env
for line in open(os.path.expanduser('~/.hermes/.env')):
    line = line.strip()
    if line and not line.startswith('#') and '=' in line:
        k, v = line.split('=', 1)
        os.environ[k] = v

# 读 config.yaml 中的 custom providers
with open(os.path.expanduser('~/.hermes/config.yaml')) as f:
    config = yaml.safe_load(f)

# 测试 Groq（从 config.yaml 读 key）
groq_key = None
for p in config.get('custom_providers', []):
    if 'groq' in p.get('name', '').lower():
        groq_key = p.get('api_key')
        break

resp = requests.post(
    'https://api.groq.com/openai/v1/chat/completions',
    headers={'Authorization': f'Bearer {groq_key}'},
    json={'model': 'llama-3.3-70b-versatile', 'messages': [{'role': 'user', 'content': 'ping'}], 'max_tokens': 5},
    timeout=15
)
# 200 = key正常可用
```

## 教训

- **直接 HTTP 401 不一定是 key 无效**：transit token（如 V2.aicodee.com 的 `sk-290...6e18`）直连 HTTP 401 是正常的，必须通过 Hermes provider 测试
- **403 可能是外部拦截**：Groq 403（Cerebras 403）是当时 Cloudflare/IP 被禁，不代表 key 失效
- **真正的 key 无效**：只有 DeepSeek 直连 401 才是 key 本身无效（key 存在但认证失败）

## 关键命令

```bash
# 查看 config.yaml 中的 custom providers
python3 -c "
import yaml
with open('~/.hermes/config.yaml') as f:
    cfg = yaml.safe_load(f)
for p in cfg.get('custom_providers', []):
    name = p.get('name', '')
    key = p.get('api_key', '')[:15] + '...'
    print(f'{name}: {key}')
"
```