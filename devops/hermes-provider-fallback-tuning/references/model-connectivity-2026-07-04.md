# 模型连通性测试快照 — 2026-07-04（更新 Gemini 结论 + 新 3 段探针协议）

## 与 2026-07-03 的差异（必读）

2026-07-03 的快照把 **Gemini** 标为 ❌ 401。今天（2026-07-04）重测结果：

| 模型 | 2026-07-03 结论 | 2026-07-04 结论 | 根因 |
|------|----------------|----------------|------|
| Gemini | ❌ 401 | ✅ 200 | 2026-07-03 那次脱代理方法先 grep 再 source，`.env` 首行 Chrome 路径报错导致 source 失败 → 测的时候 key 其实是空字符串 → Gemini 收到空 key 判 401（403/401 区分详见 SKILL.md Pitfalls）。今天改用 `awk -F=` 绕开 source → 真 key 测出 200 |

**教训**：报告某模型"失败"前，必须确保测的时候 key 真的不是空字符串。今天发现的 AWK 提取法比 python 逐行读更短更稳，下面给。

## 3 段探针协议（验证 X 模型当前能否调用）

3 段依次进行。任一段失败就停在这一段诊断：

### 段 1：key 真的进了 shell 吗

```bash
KEY=$(awk -F= '/^GEMINI_API_KEY=/{print $2; exit}' ~/.hermes/.env | tr -d '\r\n\"')
echo "前缀 ${KEY:0:8}... 长度 ${#KEY}"
# 期望：长度 > 30，前缀是 provider 的特征串（Google = AQ.Ab8RN，DeepSeek = sk-，NVIDIA = nvapi-）
# 不期望：长度 0（说明 .env 那行被空格截了或值空了）
```

**AWK 为什么比 python 短稳**：
- `awk -F=` 自动按 `=` 切，对引号、特殊字符无感
- `tr -d '\r\n\"'` 只剥换行/CR/双引号，单引号本身在 `.env` 里出现就保留
- 单行命令，可直接塞进终端

**Python 等价写法（备选）**：

```python
key = next((l.split('=',1)[1].strip().strip('"\'') for l in open(os.path.expanduser('~/.hermes/.env')) if l.startswith('GEMINI_API_KEY=')), '')
```

### 段 2：列出可用模型（最便宜的连通性测试）

不同 provider 用不同端点：

| Provider | URL | 鉴权方式 |
|---------|-----|---------|
| Gemini | `https://generativelanguage.googleapis.com/v1beta/models?key=$KEY` | Query string |
| OpenAI 系 (GLM/DeepSeek/Cerebras/Or) | `https://API_BASE/v1/models` | `Authorization: Bearer $KEY` header |
| NVIDIA | `https://integrate.api.nvidia.com/v1/models` | Bearer |

```bash
# Gemini 版（带 key 查询串）
curl -sS -o /tmp/probe.json -w "HTTP %{http_code}  耗时 %{time_total}s\n" \
  "https://generativelanguage.googleapis.com/v1beta/models?key=${KEY}"
python3 -c "
import json
d = json.load(open('/tmp/probe.json'))
if 'models' in d: print(f'✅ {len(d[\"models\"])} 个模型可用')
else: print('❌', json.dumps(d, ensure_ascii=False)[:300])
"
```

**判定**：
- 200 + models 数组：`段 2 ✅` key 有效 + 鉴权通过
- 401：`key 失效或 key_env 映射错`（见 SKILL.md Pitfalls）
- 403：`key 有效但账户无权限`（NVIDIA 常踩，详见 SKILL.md "403 根因"）
- network error：先脱代理再测（见下方"脱代理"）

### 段 3：实际生成（最小 token 请求 + thinking 预算）

```bash
curl -sS -o /tmp/g.json -w "HTTP %{http_code}  耗时 %{time_total}s\n" \
  -H "Content-Type: application/json" \
  -d '{"contents":[{"parts":[{"text":"ping"}]}],"generationConfig":{"maxOutputTokens":512}}' \
  "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=${KEY}"
python3 -c "
import json
d = json.load(open('/tmp/g.json'))
if 'candidates' in d:
    parts = d['candidates'][0]['content'].get('parts', [])
    txt = ''.join(p.get('text','') for p in parts)
    print(f'✅ modelVersion={d.get(\"modelVersion\")} text=\"{txt[:60]}\"')
else:
    print('❌', json.dumps(d, ensure_ascii=False)[:300])
"
```

**判定**：
- 200 + `modelVersion` 字段：`段 3 ✅` 模型能真实推理
- 200 + `finishReason: MAX_TOKENS` + 无 text：thinking 模型给的 token 太少（见下方"thinking 模型"）
- 4xx/5xx：回到段 2 看分类

## Gemini 2.5 Flash thinking 预算陷阱（关键）

**症状**：段 3 返回 HTTP 200 但 `candidates[0].content.parts` 为空，错误以为是失败。

**根因**：gemini-2.5-flash 是 "thinking" 模型（隐式开启），给 `maxOutputTokens: 4` 会把 4 个 token 全花在内部思考，输出部分 0 token → `finishReason: MAX_TOKENS`。

**验证（2026-07-04 实测）**：
- `maxOutputTokens: 4` → `MAX_TOKENS`，parts 为空（bug 假象）
- `maxOutputTokens: 512` → 正常输出，`modelVersion: gemini-2.5-flash`

**生产调用硬规则**：对任何 Gemini 2.5 系列调用，`maxOutputTokens` 必须 **≥ 256**（建议 512+），否则你以为是模型挂了其实是预算全烧思考。

**延伸**：OpenAI o1/o3、Claude with extended thinking、Qwen QwQ 都同坑。**通用建议**：连通性 smoke test 用 `maxOutputTokens: 512`，不要抠 token。

## 脱代理测试（防止 500 假象）

Mac 上只要开了 Clash/Xproxy，必须在子进程里清代理变量：

```bash
python3 -c "
import os, subprocess
env = os.environ.copy()
for k in ['https_proxy','http_proxy','HTTPS_PROXY','HTTP_PROXY','ALL_PROXY','all_proxy']:
    env.pop(k, None)
r = subprocess.run(['curl','-s','--connect-timeout','15','-X','POST',
    'URL', '-H','Authorization: Bearer '+open('/dev/stdin').read().strip(),
    '-H','Content-Type: application/json', '-d','BODY'],
    capture_output=True, text=True, timeout=20, env=env)
print(r.stdout[:300])
" <<< "$KEY"
```

**判定**：同一接口，有代理 500 vs 无代理 403 = 代理在掩盖错误码（Clash 7897 端口已知踩这坑）。

## 实测结果汇总（2026-07-04）

| Provider | 段 1 (key) | 段 2 (list) | 段 3 (gen) | 结论 |
|---------|-----------|-------------|-----------|------|
| Gemini 2.5 Flash | ✅ AQ.Ab8RN... 53字符 | ✅ HTTP 200, 50 模型 | ✅ HTTP 200, modelVersion=gemini-2.5-flash | 完全可用 |
| NV Qwen 3.5 397B | ✅ | ✅ 在 models 列表 | (未测，套用 7/3 结论) 403 | 账户无权限 |

## 一键脚本草稿（用户多次要求"测 X 能不能用"再正式 ship）

形态建议：

```bash
#!/bin/bash
# 用法: bash probe-model.sh <ENV_VAR_NAME> <BASE_URL> <MODEL_NAME>
# 例:   bash probe-model.sh GEMINI_API_KEY https://generativelanguage.googleapis.com/v1beta gemini-2.5-flash

ENV_VAR=$1
BASE_URL=$2
MODEL=$3
KEY=$(awk -F= "/^${ENV_VAR}=/{print \$2; exit}" ~/.hermes/.env | tr -d '\r\n\"')
MAX_TOKENS=${4:-512}

echo "[1] key 前缀 ${KEY:0:8}... 长度 ${#KEY}"
echo "[2] 列出模型..."
curl -sS -o /tmp/probe.json -w "HTTP %{http_code}\n" "${BASE_URL}/models?key=${KEY}"
echo "[3] 实际生成 (max_tokens=${MAX_TOKENS})..."
curl -sS -o /tmp/gen.json -w "HTTP %{http_code}\n" \
  -H "Content-Type: application/json" \
  -d "{\"contents\":[{\"parts\":[{\"text\":\"ping\"}]}],\"generationConfig\":{\"maxOutputTokens\":${MAX_TOKENS}}}" \
  "${BASE_URL}/models/${MODEL}:generateContent?key=${KEY}"
```

注：脚本未本会话写入 `scripts/`，因为用户没明确要持久化。下次若用户多次要求"测这个能不能用"再正式 ship 到 scripts/probe-model.sh。
