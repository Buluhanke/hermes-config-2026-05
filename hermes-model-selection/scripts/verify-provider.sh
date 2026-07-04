#!/usr/bin/env bash
# verify-provider.sh — 三步验证一个 OpenAI 兼容的 LLM provider
# 用法: verify-provider.sh <base_url> <api_key> <model_name>
# 例:   verify-provider.sh https://apihub.agnes-ai.com/v1 $AGNES_API_KEY agnes-2.0-flash
#
# 返回: 0 = 全绿, 1 = /models 失败, 2 = /chat 失败, 3 = python 不可用
# 设计: 纯 stdlib (urllib), 不依赖 curl/jq, 适配 hermes execute_code sandbox

set -u
BASE="${1:-}"
KEY="${2:-}"
MODEL="${3:-}"

if [[ -z "$BASE" || -z "$KEY" || -z "$MODEL" ]]; then
    echo "用法: $0 <base_url> <api_key> <model_name>" >&2
    echo "例:   $0 https://apihub.agnes-ai.com/v1 \$AGNES_API_KEY agnes-2.0-flash" >&2
    exit 3
fi

if ! command -v python3 >/dev/null 2>&1; then
    echo "❌ python3 不可用" >&2
    exit 3
fi

python3 - "$BASE" "$KEY" "$MODEL" <<'PYEOF'
import sys, json, time, urllib.request, urllib.error

base, key, model = sys.argv[1], sys.argv[2], sys.argv[3]
exit_code = 0

def http(method, path, body=None):
    url = f"{base}{path}"
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(
        url, data=data, method=method,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    )
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read().decode()), (time.time()-t0)*1000
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:300], (time.time()-t0)*1000
    except Exception as e:
        return 0, f"{type(e).__name__}: {e}", (time.time()-t0)*1000

# Step 1: GET /models
print(f"=== 验证 1/2: GET {base}/models ===")
status, body, ms = http("GET", "/models")
if status == 200 and isinstance(body, dict):
    models = body.get("data", [])
    print(f"  ✅ HTTP 200 in {ms:.0f}ms — {len(models)} models")
    for m in models[:6]:
        print(f"     - {m.get('id')}")
    if len(models) > 6:
        print(f"     ... +{len(models)-6} more")
    if ms > 2000:
        print(f"  ⚠️  /models 耗时 {ms:.0f}ms 偏慢, 标记 slow-fallback")
else:
    print(f"  ❌ HTTP {status} in {ms:.0f}ms: {body}")
    print(f"  诊断: 见 references/provider-token-verification.md §1 4 类 401 分类")
    exit_code = 1

# Step 2: POST /chat/completions (实跑)
print(f"\n=== 验证 2/2: POST {base}/chat/completions (model={model}) ===")
status, body, ms = http("POST", "/chat/completions", {
    "model": model,
    "messages": [{"role": "user", "content": "回复一个词: pong"}],
    "max_tokens": 20,
    "stream": False,
})
if status == 200 and isinstance(body, dict):
    choice = body.get("choices", [{}])[0]
    msg = choice.get("message", {}).get("content", "")
    usage = body.get("usage", {})
    print(f"  ✅ HTTP 200 in {ms:.0f}ms — reply: {msg!r}")
    print(f"  usage: prompt={usage.get('prompt_tokens')} completion={usage.get('completion_tokens')} total={usage.get('total_tokens')}")
    print(f"  model: {body.get('model')}  id: {body.get('id','?')[:40]}")
    if ms > 15000:
        print(f"  ⚠️  chat 耗时 {ms:.0f}ms 偏慢, 建议移到 fallback 链尾")
else:
    print(f"  ❌ HTTP {status} in {ms:.0f}ms: {body}")
    print(f"  诊断: 见 references/provider-token-verification.md §1 4 类 401 分类")
    exit_code = 2 if exit_code == 0 else exit_code

# 总结
print()
if exit_code == 0:
    print(f"✅ Provider 完全可用 — {base} 配 {model} 一切正常")
else:
    print(f"❌ Provider 验证失败 (exit={exit_code}) — 不要写 fact_store 说已激活")

sys.exit(exit_code)
PYEOF
