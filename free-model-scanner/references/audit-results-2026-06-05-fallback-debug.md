# 2026-06-05 Fallback 实战：从 503 看真实失败链路

## 关键发现：**fallback 触发了 ≠ fallback 成功**

今早 09:19 V2enby 返回 `HTTP 503: No available channel for model MiniMax-M3-highspeed`，3 次重试失败，**框架确实切了 fallback**——日志清楚打印 `🔄 Primary model failed — switching to fallback: openai/gpt-oss-120b via or-gpt-oss-120b`，但切过去后 402 余额不足，再切下一个还是 402/404/400。

**两类不同的"fallback 失败"，诊断路径完全不同**：

| 现象 | 真实原因 | 诊断命令 | 修复路径 |
|---|---|---|---|
| 日志里**没有** "switching to fallback" 字样 | fallback 框架**根本没触发** | `grep "switching to fallback" gateway.log` | 配 `model.fallback_chain` / 配 `fallback_on_status` / 配 `fallback_on_timeout` |
| 日志里有 "switching to fallback" 但**全部失败** | **chain 端点本身死的**（4 个里 3 个） | `grep -A 5 "switching to fallback" gateway.log` 看每个 chain 端点的错误码 | 重测每个端点 + 换真模型名 |

**第一次诊断千万别只看"fallback 触发了没"** — 必须看 fallback 切过去后**每个 chain 端点的具体错误**（404 = 模型名错、402 = OR 账户免费档没钱、400 = OR `provider/model` 格式错、500 = 上游 NV 内部错）。

## 实测：4 个旧 chain 端点为什么全死

| Chain 配置名 | 实际错误 | 根因 |
|---|---|---|
| `nv-deepseek-v4-flash` | HTTP 404 | 缺前缀，NV 真名是 `deepseek-ai/deepseek-v4-flash` |
| `or-gpt-oss-120b` | HTTP 402 (免费档 1361 tokens 耗尽) | OR 免费档 quota 限制，大请求必 402 |
| `or-qwen3.7-plus` | HTTP 400 `is not a valid model ID` | OR 真名是 `qwen/qwen3-7b-plus-2025` 不是裸 `qwen3.7-plus` |
| `nv-nemotron-3-super-120b` | HTTP 404 | 缺前缀 + 缺后缀，NV 真名是 `nvidia/nemotron-3-super-120b-a12b` |

**新 chain 3/3 活的**（实测响应时间 2026-06-05 10:25）：

```python
TESTS = [
    ("nv-nemotron-3-super",     "https://integrate.api.nvidia.com/v1/chat/completions", env['NVIDIA_API_KEY'],   "nvidia/nemotron-3-super-120b-a12b",  8),  # 0.4s ✅ 首选
    ("nv-deepseek-v4-flash",    "https://integrate.api.nvidia.com/v1/chat/completions", env['NVIDIA_API_KEY'],   "deepseek-ai/deepseek-v4-flash",       8),  # 2.7s ✅
    ("or-deepseek-chat-v3",     "https://openrouter.ai/api/v1/chat/completions",       env['OPENROUTER_API_KEY'], "deepseek/deepseek-chat-v3-0324",     8),  # 1.0s ✅
]
```

写回 config：
```bash
hermes config set model.fallback_chain '["nv-nemotron-3-super","nv-deepseek-v4-flash","or-deepseek-chat-v3"]'
hermes config set model.fallback_on_timeout 18   # NV 端冷启动 12-15s 实测
hermes config set model.fallback_max_retries 1
```

## 4 个真模型名规则（不能再错）

### NVIDIA NIM (integrate.api.nvidia.com)
- ✅ 必须有 namespace 前缀：`deepseek-ai/` `nvidia/` `qwen/` `meta/` `mistralai/` `moonshotai/` `google/` `openai/` `z-ai/`
- ✅ 真实存活 119 个模型（2026-06-04 全量列表见 `audit-results-2026-06-04.md`）
- ✅ 拉列表：`curl -H "Authorization: Bearer $NVIDIA_API_KEY" https://integrate.api.nvidia.com/v1/models`
- ❌ 常见错：写成 `deepseek-v4-flash`（缺 `deepseek-ai/`）/ `nemotron-3-super-120b`（缺 `nvidia/` 和 `-a12b` 后缀）

### OpenRouter (openrouter.ai/api/v1)
- ✅ 必须 `provider/model` 格式：`deepseek/deepseek-chat-v3-0324` / `nvidia/nemotron-3-super-120b-a12b:free`
- ✅ 免费档后缀 `:free`，但免费档有 quota 限制（大请求 402）
- ❌ 常见错：写成 `qwen3.7-plus`（OR 不认裸名）/ `gpt-oss-120b`（必须是 `openai/gpt-oss-120b`）
- ⚠️ **坑**：拉列表 API（`/v1/models`）返回 ~1MB JSON，urllib 会抛 `IncompleteRead(347906 bytes read)`。解决：分页或按 keyword 过滤后再 requests。

## 实战脚本：4 端点一次性实测连通

```python
import urllib.request, json, time
from pathlib import Path

env = {}
for line in (Path.home() / ".hermes" / ".env").read_text().splitlines():
    if "=" in line and not line.startswith("#"):
        k, v = line.split("=", 1); env[k.strip()] = v.strip()

TESTS = [
    ("nv-nemotron-3-super",  "https://integrate.api.nvidia.com/v1/chat/completions", env['NVIDIA_API_KEY'],   "nvidia/nemotron-3-super-120b-a12b", 8),
    ("nv-deepseek-v4-flash", "https://integrate.api.nvidia.com/v1/chat/completions", env['NVIDIA_API_KEY'],   "deepseek-ai/deepseek-v4-flash",      8),
    ("or-deepseek-chat-v3",  "https://openrouter.ai/api/v1/chat/completions",       env['OPENROUTER_API_KEY'], "deepseek/deepseek-chat-v3-0324",    8),
    # 加任何候选都按这个格式
]

for name, url, key, model, mt in TESTS:
    payload = json.dumps({"model": model, "messages": [{"role": "user", "content": "hi"}], "max_tokens": mt}).encode()
    req = urllib.request.Request(url, data=payload, method="POST", headers={
        "Authorization": f"Bearer {key}", "Content-Type": "application/json"
    })
    try:
        t0 = time.time()
        with urllib.request.urlopen(req, timeout=20) as r:
            body = json.loads(r.read().decode())
            content = body.get("choices", [{}])[0].get("message", {}).get("content", "")[:40]
            print(f"✅ {name:30s} HTTP {r.status} ({time.time()-t0:.1f}s) resp={content!r}")
    except urllib.error.HTTPError as e:
        body = e.read().decode()[:200]
        print(f"❌ {name:30s} HTTP {e.code} {body[:160]}")
    except Exception as e:
        print(f"❌ {name:30s} {type(e).__name__}: {str(e)[:100]}")
```

## OR `gpt-oss-120b` 永久不要放 fallback 链

实测 OR 账户免费档 quota 只有 **1361 tokens**，任何大请求必 402（"You requested up to 16384 tokens, but can only afford 1361"）。**这不是暂时挂，是账户级永久限制**。如要 OR，必须用付费档或换其他便宜 provider。

## 给 future session 的检查清单

1. ✅ 配置 chain 前**先实测每个端点**（用上面脚本）
2. ✅ 优先 NVIDIA（自己 quota 独立，cross-failover 价值高）
3. ✅ OR 端只放 **付费档** 或 **真正免费的小模型**
4. ✅ `fallback_on_timeout` ≥ 18s（NV 冷启动 12-15s 实测）
5. ❌ 永远不要只信 `hermes config show` 看到有 chain 就以为通了——**必须实测**
6. ❌ OR 列表 API 大 JSON → IncompleteRead，按 keyword 过滤再 requests
