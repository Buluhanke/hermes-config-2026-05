---
name: hermes-model-switching
description: Hermes `/model` 命令故障诊断 — provider 不识别、key 过期、位置放错、API 连通性
version: 1.0.0
triggers:
  - /model 报错 Unknown provider
  - 模型切换失败
  - agnes unknown provider
  - provider 配置正确但切换不了
---

# Hermes 模型切换故障诊断

## 诊断路径（按顺序）

```
症状 → 根因排查
```

### Step 1：找 HTTP 状态码

```bash
tail -100 ~/.hermes/logs/gateway.error.log | grep "HTTP 4[0-9][0-9]"
```

| 状态码 | 含义 | 下一步 |
|--------|------|--------|
| 401 | API key 过期或无效 | 查 .env |
| 402 | 余额不足 | 去平台充值 |
| 404 | 模型不存在/下线 | 换模型名 |
| 200 但回答错误 | 连通但配置位置错 | 转 Step 2 |

### Step 2：验证 API 连通性（与 Hermes 无关）

```python
import urllib.request, json

# 读取 .env 中的 key
with open('~/.hermes/.env') as f:
    for line in f:
        if line.startswith('AGNES_API_KEY'):
            key = line.split('=', 1)[1].strip()

for model in ['agnes-2.0-flash', 'agnes-2.5-flash']:
    req = urllib.request.Request(
        'https://apihub.agnes-ai.com/v1/chat/completions',
        data=json.dumps({'model': model, 'messages': [{'role': 'user', 'content': 'hi'}]}).encode(),
        headers={'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'}
    )
    try:
        r = urllib.request.urlopen(req, timeout=10)
        print(f'✅ {model} OK {r.status}')
    except Exception as e:
        print(f'❌ {model} {e}')
```

**如果这里返回 401**：key 真的失效了，去 provider 官网刷新 key 并更新 `.env`。

**如果这里返回 200**：API 本身正常，问题在 Hermes 配置层，转 Step 3。

### Step 3：确认 provider 放在正确位置

**最常见错误**：provider 放在了 `providers:` 块里，但 `/model` 命令只认 `custom_providers:`。

```python
import yaml
with open('~/.hermes/config.yaml') as f:
    cfg = yaml.safe_load(f)

cp = cfg.get('custom_providers')
print('custom_providers type:', type(cp).__name__)  # 必须是 dict，不能是 list
print('providers count:', len(cfg.get('providers', [])))
```

| 症状 | 根因 | 修复 |
|------|------|------|
| `Unknown provider 'agnes'` | provider 在 `providers:` 不在 `custom_providers:` | 挪到 `custom_providers:` |
| `custom_providers type: list` | 格式错误，整个 fallback 链失效 | 改为 dict 格式 |
| `providers count: 0` | providers 块为空或被覆盖 | 检查 YAML 结构 |

### Step 4：正确的 `custom_providers` 格式

```yaml
custom_providers:
- name: agnes
  base_url: https://apihub.agnes-ai.com/v1
  key_env: AGNES_API_KEY    # .env 中的变量名（不带 $）
  models:
  - agnes-2.0-flash
  - agnes-2.5-flash
```

> 注意：`key_env` 是**变量名**，不是 API key 本身。Hermes 启动时从此变量读取实际 key。

### Step 5：Python 脚本改 Config（绕过 patch 工具限制）

```python
import re

with open('~/.hermes/config.yaml') as f:
    content = f.read()

# 删掉 providers: 块里的 agnes 条目（避免重复）
content = re.sub(
    r'- name: agnes\n  model: agnes-2\.5-flash\n  base_url: https://apihub\.agnes-ai\.com/v1\n',
    '', content
)

# 在 custom_providers: 插入 agnes
content = re.sub(
    r'(group_sessions_per_user: true)',
    r'custom_providers:
- name: agnes
  base_url: https://apihub.agnes-ai.com/v1
  key_env: AGNES_API_KEY
  models:
  - agnes-2.0-flash
  - agnes-2.5-flash

\1',
    content
)

# 更新默认模型
content = re.sub(
    r'^model:\n  default: .+\n  provider: .+\n  base_url: .+',
    'model:\n  default: agnes-2.0-flash\n  provider: agnes\n  base_url: https://apihub.agnes-ai.com/v1',
    content, flags=re.MULTILINE
)

with open('~/.hermes/config.yaml', 'w') as f:
    f.write(content)
```

### Step 6：重启 Gateway

配置修改后需重启让新 config 生效：

```
hermes gateway restart
```

（不能从 gateway 进程内部重启，需在另一个终端窗口执行）

## 两套 Provider 位置的区别

| 配置块 | 被谁使用 |
|--------|----------|
| `providers:` | fallback chain、工具调用等核心逻辑 |
| `custom_providers:` | `/model` 命令、CLI 模型选择 |

**教训**：`providers:` 和 `custom_providers:` 是完全独立的两套路径，把 provider 放进 `providers:` 不等于 `/model` 能找到它。

## 相关技能

- `hermes-config-tricks`：config.yaml 格式陷阱
- `hermes-provider-debugging`：Provider 层面的诊断
- `provider-config-verification`：API 连通性验证
