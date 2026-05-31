# API Key 集中化管理流程

## 原则

1. **所有 API key 存 `.env`**，config.yaml 只用 `api_key_env: KEY_NAME` 引用
2. **测试优先**：key 必须实际测通才写入 `.env`，不用过期/无效 key 覆盖有效 key
3. **config.yaml 当前值 =实际生效值**：不依赖 .env 里的旧值，以 config.yaml 为准

## 标准流程

### 1. 收集 config.yaml 中所有硬编码 secret

```python
import re, os

with open('/Users/aimac/.hermes/config.yaml', 'r') as f:
    content = f.read()

# 找硬编码 api_key / api_key_env / secret 等
patterns = [
    (r'api_key:\s+[\'"]?([A-Za-z0-9_\-]+)', 'api_key (inline)'),
    (r'api_key_env:\s+[\'"]?([A-Za-z0-9_]+)', 'api_key_env (ref)'),
    (r'app_secret:\s+[\'"]?([A-Za-z0-9_\-]+)', 'app_secret (inline)'),
    (r'app_secret_env:\s+[\'"]?([A-Za-z0-9_]+)', 'app_secret_env (ref)'),
]
```

### 2. 从 .env 读取当前值（原始字节，避免 TTY 脱敏）

```python
env_keys = {}
with open('/Users/aimac/.hermes/.env', 'rb') as f:
    for line in f:
        line = line.decode('utf-8', errors='replace').rstrip()
        if '=' in line and not line.startswith('#'):
            k, v = line.split('=', 1)
            env_keys[k] = v
```

### 3. 测试连通性（每个 key 都要测）

```bash
# OpenAI 兼容格式
curl -s -w '\n%{http_code}' -X POST '<BASE_URL>/chat/completions' \
  -H "Authorization: Bearer $KEY" \
  -H 'Content-Type: application/json' \
  -d '{"model":"<model>","messages":[{"role":"user","content":"ping"}],"max_tokens":5}'

# 200 =成功，403 = key无效/过期，429 = 额度耗尽但key有效
```

### 4. 写入 .env

```python
updates = {
    'NEW_KEY_NAME': 'actual_key_value',
}
with open('/Users/aimac/.hermes/.env', 'a') as f:
    for k, v in updates.items():
        f.write(f'{k}={v}\n')
```

### 5. 更新 config.yaml 用 env 引用

```python
# 替换硬编码为 api_key_env
content = content.replace(
    'api_key: sk-xxx...',
    'api_key_env: KEY_NAME'
)
```

### 6. 验证 config.yaml YAML parse 正常

```bash
python3 -c "import yaml; yaml.safe_load(open('/Users/aimac/.hermes/config.yaml')); print('OK')"
```

## 当前系统中的 Key状态（2026-06-02）

### 已测通（实际可用）
| Key | Provider | 状态 |
|-----|----------|------|
| `AICODEE_API_KEY` | V2.aicodee.com | ✅ 200 |
| `DEEPSEEK_API_KEY` | api.deepseek.com | ✅ 200 |
| `OPENROUTER_API_KEY` | openrouter.ai | ✅ 200 |

### 配置了但暂不通
| Key | Provider | 状态 |原因 |
|-----|----------|------|------|
| `MINIMAX_CN_API_KEY` | minimax-cn | ⚠️ 429 | 额度耗尽，key 本身有效 |
| `GEMINI_API_KEY` | Gemini |⚠️ 超时 | 网络/墙问题，配置正确 |
| `CEREBRAS_API_KEY` | Cerebras |❌ 403/1009 | 账号级别拒绝 |
| `GROQ_API_KEY` | Groq | ❌ 403 | key 被 Groq 拒绝 |

### 平台 Token
- `TELEGRAM_BOT_TOKEN` / `WEIXIN_TOKEN` / `QQ_CLIENT_SECRET` / `FEISHU_APP_SECRET`
- `GITHUB_MCP_TOKEN` + `GITHUB_PERSONAL_ACCESS_TOKEN`

### 工具 Key
- `BAIDU_API_KEY` / `BAIDU_SECRET_KEY` / `BAIDU_ACCESS_TOKEN`
- `FIRECRAWL_API_KEY` / `BOCHA_API_KEY` / `EXA_API_KEY`
- `FREELLMAPI_KEY` / `GLM_API_KEY` / `NVIDIA_API_KEY` / `OLLAMA_API_KEY`

## 已知问题

### Groq/Cerebras 403 错误码1009
- **表现**：`{"error":{"message":"forbidden","code":1009}}`
- **含义**：API key 被服务端拒绝（可能是地区限制、账号被封、key 从未激活）
- **注意**：新旧 key 都返回同样错误 =账号问题，与 key 本身无关
- **当前状态**：Groq 和 Cerebras key 都从 .env 移除（避免误用）

### TTY 显示脱敏陷阱
- `grep` / `sed` 等命令对 API key 有 TTY 层脱敏，显示 `***` 或截断
- **永远不要**从 grep/sed 输出提取 key 值
- **永远用** Python 读原始文件字节：`open(file, 'rb')`