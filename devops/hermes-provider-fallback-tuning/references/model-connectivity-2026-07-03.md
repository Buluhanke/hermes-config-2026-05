# 模型连通性测试快照 — 2026-07-03（更新）

## 测试方法（脱代理版）

由于代理（Clash 7897）会掩盖真实错误码，测 API 必须脱代理：

```bash
python3 -c "
import os, subprocess
with open(os.path.expanduser('~/.hermes/.env')) as f:
    for line in f:
        if line.startswith('API_KEY_VAR='):
            key = line.split('=',1)[1].strip().strip('\"').strip(\"'\")
            break
env = os.environ.copy()
for k in ['https_proxy','http_proxy','HTTPS_PROXY','HTTP_PROXY','ALL_PROXY','all_proxy']:
    env.pop(k, None)
r = subprocess.run(['curl','-s','--connect-timeout','15','-X','POST',
    'ENDPOINT_URL',
    '-H','Authorization: Bearer '+key,
    '-H','Content-Type: application/json',
    '-d','{\"model\":\"MODEL_NAME\",\"messages\":[{\"role\":\"user\",\"content\":\"hi\"}],\"max_tokens\":5}'],
    capture_output=True, text=True, timeout=20, env=env)
print(r.stdout[:300])
"
```

## 快速查找 API key（python 读 .env 绕过 source 报错）

`.env` 含空格路径未加引号，source 会报错。用 python 逐行读：

```python
with open(os.path.expanduser('~/.hermes/.env')) as f:
    for line in f:
        if line.startswith('NVIDIA_API_KEY='):
            key = line.split('=',1)[1].strip().strip('\"').strip("'")
            print(f'NV_KEY={key[:10]}...{key[-4:]}')  # 只打印首尾保护隐私
```

## 结果汇总（2026-07-03 深度检查）

| 模型 | 端点 | 有代理 | 无代理 | 真相 |
|------|------|--------|--------|------|
| Cerebras | `api.cerebras.ai/v1/chat/completions` | ✅ 200 | ✅ 200 | 正常 |
| GLM | `open.bigmodel.cn/api/paas/v4/chat/completions` | ✅ 200 | ✅ 200 | 正常 |
| OpenRouter qwen3-coder | `openrouter.ai/api/v1/chat/completions` | ✅ 200 | ✅ 200 | 正常 |
| OpenRouter free | `openrouter.ai/api/v1/chat/completions` | ✅ 200 | ✅ 200 | 正常 |
| NVIDIA Nemotron | `integrate.api.nvidia.com/v1/chat/completions` | ✅ 200 | ✅ 200 | 正常 |
| **Agnes Flash** | `apihub.agnes-ai.com/v1/chat/completions` | ✅ 200 | ✅ 200 | **配置正确，可用** |
| **NVIDIA Qwen3.5** | `integrate.api.nvidia.com/v1/chat/completions` | ❌ 500 | ❌ 403 | **key 有效，但账户无调用权限** |
| Gemini | `generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent` | ❌ 401 | ❌ 401 | key 或 endpoint 问题 |
| Custom 123.56.67.77 | `http://123.56.67.77:9100/v1/chat/completions` | ❌ 401 | — | 认证失败 |
| Ollama | `localhost:11434/api/tags` | ❌ 连接拒绝 | ❌ 连接拒绝 | 服务未运行 |

## 关键发现

### 1. 代理掩盖真实错误码
Clash 代理转发 NV API 时，403 在代理层变成 HTTP 500（`Missing request extension` 错误）。去掉代理后返回真实 403。
**教训**：测 API 必先脱代理，否则永远看不到真实错误。

### 2. NVIDIA 403 = 权限不足，非 key 失效
- key 本身有效（从 .env 正确读取，裸 curl 能通）
- `GET /v1/models` 返回 200，模型 `qwen/qwen3.5-397b-a17b` 存在于平台
- 但 `POST /v1/chat/completions` 返回 403 → 此 key 无权调用此模型
- **解决方案**：NVIDIA 账户需订阅/充值该模型，或换用有权限的模型

### 3. Agnes 真实端点
- 旧文档说 404（`api.agnes-ai.com`）
- 正确端点：`apihub.agnes-ai.com/v1/chat/completions`（已验证 200）

### 4. .env source 报错导致误判 key 为空
`source ~/.hermes/.env` 报错 `Chrome.app/Contents/MacOS/Google: No such file or directory`
→ 所有 key 都不加载
→ `echo $NVIDIA_API_KEY` 返回空
→ 误判为"key 未配置"
**根因**：`AGENT_BROWSER_EXECUTABLE_PATH=/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`（中间有空格未加引号）
**绕过**：python 逐行读 .env 而非 source

## NVIDIA 模型列表（2026-07-03 查询）

```
qwen/qwen3-next-80b-a3b-instruct
qwen/qwen3.5-122b-a10b
qwen/qwen3.5-397b-a17b  ← 配置里的模型，平台有，但 key 无权调用
nvidia/nemotron-3-super-120b-a12b  ← 这个 key 有权调用
```
