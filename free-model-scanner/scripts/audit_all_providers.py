#!/usr/bin/env python3
"""
全 provider 模型可用性审计 — 替代过时的 scan_free_models.py

覆盖 ~/.hermes/.env 里所有 LLM 相关 key，逐个探测：
  - key 是否有效（list models）
  - 列出可用模型
  - 实测强候选是否能正常回复

输出三档分类：
  🟢 真能打 — 推荐用
  🟡 凑合能用 — 兜底
  🔴 失效/不要碰 — 从 config 删

用法：
  python3 audit_all_providers.py                # 全跑
  python3 audit_all_providers.py --probe-only   # 只探测 key 有效性，不实测模型
  python3 audit_all_providers.py --provider openrouter  # 只跑一家

数据沉淀：~/.hermes/skills/free-model-scanner/references/audit-results-<date>.md
"""
import os, sys, json, time, argparse, urllib.request, urllib.error
from pathlib import Path

HOME = Path.home()
ENV_FILE = HOME / ".hermes" / ".env"
TIMEOUT = 20
SCRIPT_DIR = Path(__file__).parent
REFS_DIR = SCRIPT_DIR.parent / "references"


def load_env():
    env = {}
    if not ENV_FILE.exists():
        return env
    for line in ENV_FILE.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env[k] = v
    return env


def http(url, headers, body=None, timeout=TIMEOUT, method=None):
    try:
        data = json.dumps(body).encode() if body else None
        req = urllib.request.Request(
            url, data=data, headers=headers, method=method or ("POST" if body else "GET")
        )
        t0 = time.time()
        resp = urllib.request.urlopen(req, timeout=timeout)
        ms = int((time.time() - t0) * 1000)
        return {"ok": True, "status": resp.status, "ms": ms, "data": json.loads(resp.read())}
    except urllib.error.HTTPError as e:
        return {"ok": False, "status": e.code, "body": e.read().decode()[:300]}
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}


# ===== Provider 探测定义 =====

def probe_v2enby(env):
    """anthropic 协议 — 没有 list 接口，直接用 messages 试"""
    key = env.get("MINIMAX_CN_API_KEY", "")
    base = env.get("MINIMAX_CN_BASE_URL", "").rstrip("/")
    if not key or not base:
        return {"ok": False, "status": "NO_KEY", "models": []}
    r = http(
        f"{base}/v1/messages",
        {"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
        {"model": "MiniMax-M3", "max_tokens": 20, "messages": [{"role": "user", "content": "1+1=几?只回数字"}]},
    )
    if r["ok"]:
        text = r["data"]["content"][0]["text"].strip()
        return {"ok": True, "models": ["MiniMax-M3 (主)"], "probe_reply": text, "ms": r["ms"]}
    return {"ok": False, "status": r.get("status"), "body": r.get("body", r.get("error", "")), "models": []}


def probe_openrouter(env):
    key = env.get("OPENROUTER_API_KEY", "")
    if not key:
        return {"ok": False, "status": "NO_KEY", "models": []}
    r = http("https://openrouter.ai/api/v1/models", {"Authorization": f"Bearer {key}"})
    if not r["ok"]:
        return {"ok": False, "status": r.get("status"), "body": r.get("body", r.get("error", ""))[:200], "models": []}
    free = [m["id"] for m in r["data"]["data"] if ":free" in m.get("id", "")]
    return {"ok": True, "models": free, "count": len(free), "ms": r["ms"]}


def probe_gemini(env):
    key = env.get("GEMINI_API_KEY", "")
    if not key:
        return {"ok": False, "status": "NO_KEY", "models": []}
    r = http(f"https://generativelanguage.googleapis.com/v1beta/models?key={key}", {})
    if not r["ok"]:
        return {"ok": False, "status": r.get("status"), "models": []}
    models = [m["name"].split("/")[-1] for m in r["data"]["models"]
              if "generateContent" in m.get("supportedGenerationMethods", [])]
    return {"ok": True, "models": models, "count": len(models), "ms": r["ms"]}


def probe_glm(env):
    key = env.get("GLM_API_KEY", "")
    base = env.get("GLM_BASE_URL", "https://open.bigmodel.cn/api/paas/v4")
    if not key:
        return {"ok": False, "status": "NO_KEY", "models": []}
    r = http(f"{base.rstrip('/')}/models", {"Authorization": f"Bearer {key}"})
    if not r["ok"]:
        return {"ok": False, "status": r.get("status"), "body": r.get("body", r.get("error", ""))[:200], "models": []}
    models = [m.get("id", "?") for m in r["data"].get("data", [])]
    return {"ok": True, "models": models, "count": len(models), "ms": r["ms"]}


def probe_generic_openai(env, name, key_env, base):
    key = env.get(key_env, "")
    if not key:
        return {"ok": False, "status": "NO_KEY", "models": [], "provider": name}
    r = http(f"{base.rstrip('/')}/models", {"Authorization": f"Bearer {key}"})
    if not r["ok"]:
        return {"ok": False, "status": r.get("status"), "body": r.get("body", r.get("error", ""))[:200],
                "models": [], "provider": name}
    models = [m.get("id", "?") for m in r["data"].get("data", [])]
    return {"ok": True, "models": models, "count": len(models), "ms": r["ms"], "provider": name}


# ===== 实测强候选 =====

def extract_gemini_text(d):
    c = d.get("candidates", [{}])[0]
    parts = c.get("content", {}).get("parts", [])
    if parts and isinstance(parts, list):
        return parts[0].get("text", "").strip()
    return ""


def extract_or(d):
    ch = d["choices"][0]
    msg = ch.get("message") or {}
    return (msg.get("content") or "").strip(), (msg.get("reasoning") or "")[:80]


PROBE_PROMPT = {
    "messages": [
        {"role": "system", "content": "直接答,不要解释,不要重复问题。"},
        {"role": "user", "content": "1+1=几?只回数字"},
    ]
}


def test_or_model(model, key, max_tokens=80):
    body = {"model": model, "max_tokens": max_tokens, "temperature": 0, **PROBE_PROMPT}
    r = http("https://openrouter.ai/api/v1/chat/completions",
             {"Authorization": f"Bearer {key}", "content-type": "application/json"}, body)
    if r["ok"]:
        t, reasoning = extract_or(r["data"])
        return {"ok": True, "ms": r["ms"], "text": t, "reasoning": reasoning}
    return {"ok": False, "status": r.get("status"), "body": r.get("body", r.get("error", ""))[:100]}


def test_gemini_model(name, key):
    body = {"contents": [{"parts": [{"text": "1+1=几?只回数字"}]}],
            "generationConfig": {"maxOutputTokens": 20, "temperature": 0}}
    r = http(f"https://generativelanguage.googleapis.com/v1beta/models/{name}:generateContent?key={key}",
             {"content-type": "application/json"}, body)
    if r["ok"]:
        return {"ok": True, "ms": r["ms"], "text": extract_gemini_text(r["data"])}
    return {"ok": False, "status": r.get("status"), "body": r.get("body", "")[:100]}


def test_glm_model(name, key, base):
    body = {"model": name, "max_tokens": 30, "temperature": 0,
            "messages": [{"role": "user", "content": "1+1=几?只回数字"}]}
    r = http(f"{base.rstrip('/')}/chat/completions",
             {"Authorization": f"Bearer {key}", "content-type": "application/json"}, body)
    if r["ok"]:
        t = r["data"]["choices"][0]["message"]["content"].strip()
        return {"ok": True, "ms": r["ms"], "text": t}
    return {"ok": False, "status": r.get("status"), "body": r.get("body", "")[:100]}


# ===== 主流程 =====

PROVIDERS = {
    "v2enby":    probe_v2enby,
    "openrouter": probe_openrouter,
    "gemini":    probe_gemini,
    "glm":       probe_glm,
    "deepseek":  lambda e: probe_generic_openai(e, "DeepSeek", "DEEPSEEK_API_KEY",
                                                e.get("DEEPSEEK_BASE_URL") or "https://api.deepseek.com"),
    "groq":      lambda e: probe_generic_openai(e, "Groq", "GROQ_API_KEY",
                                                "https://api.groq.com/openai/v1"),
    "cerebras":  lambda e: probe_generic_openai(e, "Cerebras", "CEREBRAS_API_KEY",
                                                "https://api.cerebras.ai/v1"),
    "nvidia":    lambda e: probe_generic_openai(e, "Nvidia NIM", "NVIDIA_API_KEY",
                                                "https://integrate.api.nvidia.com/v1"),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--probe-only", action="store_true", help="只探测 key 有效性，不实测模型")
    ap.add_argument("--provider", help="只跑一个 provider (e.g. openrouter, gemini)")
    args = ap.parse_args()

    env = load_env()
    if not env:
        print("❌ ~/.hermes/.env 不存在或为空")
        return 1

    results = {}

    print("=" * 80)
    print("  全 provider 模型可用性审计")
    print("=" * 80)

    # Phase 1: probe
    for name, fn in PROVIDERS.items():
        if args.provider and args.provider != name:
            continue
        print(f"\n【{name}】探测中...")
        r = fn(env)
        results[name] = r
        if r.get("ok"):
            ms = r.get("ms", "?")
            count = r.get("count", len(r.get("models", [])))
            print(f"  ✅ {ms}ms  可用模型 {count} 个")
        else:
            print(f"  ❌ {r.get('status', '?')}  {r.get('body', r.get('error', ''))[:80]}")

    if args.probe_only:
        return 0

    # Phase 2: 实测强候选
    print("\n" + "=" * 80)
    print("  Phase 2 — 实测强候选 (1+1)")
    print("=" * 80)

    test_results = {}

    # OR 强候选
    if "openrouter" in results and results["openrouter"].get("ok"):
        or_key = env.get("OPENROUTER_API_KEY", "")
        candidates = [
            "nvidia/nemotron-3-super-120b-a12b:free",
            "nvidia/nemotron-3-nano-30b-a3b:free",
            "moonshotai/kimi-k2.6:free",
            "google/gemma-4-26b-a4b-it:free",
            "z-ai/glm-4.5-air:free",
        ]
        for m in candidates:
            r = test_or_model(m, or_key)
            test_results[f"OR:{m}"] = r
            if r["ok"]:
                print(f"  OK {m:<48} {r['ms']:>5}ms  回:{r['text'][:15]!r}  r:{r['reasoning'][:30]!r}")
            else:
                print(f"  ER {m:<48} {r.get('status','?')}  {r.get('body','')[:50]}")

    # Gemini
    if "gemini" in results and results["gemini"].get("ok"):
        gkey = env.get("GEMINI_API_KEY", "")
        for m in ["gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.5-flash-lite",
                  "gemini-3-pro-preview", "gemini-3.1-pro-preview"]:
            r = test_gemini_model(m, gkey)
            test_results[f"Gemini:{m}"] = r
            if r["ok"]:
                print(f"  OK {m:<28} {r['ms']:>5}ms  {r['text'][:20]!r}")
            else:
                print(f"  ER {m:<28} {r.get('status','?')}  {r.get('body','')[:50]}")

    # GLM
    if "glm" in results and results["glm"].get("ok"):
        glm_key = env.get("GLM_API_KEY", "")
        glm_base = env.get("GLM_BASE_URL", "https://open.bigmodel.cn/api/paas/v4")
        for m in ["glm-4.5", "glm-4.5-air", "glm-4.6", "glm-5", "glm-5.1"]:
            r = test_glm_model(m, glm_key, glm_base)
            test_results[f"GLM:{m}"] = r
            if r["ok"]:
                print(f"  OK {m:<18} {r['ms']:>5}ms  {r['text'][:20]!r}")
            else:
                print(f"  ER {m:<18} {r.get('status','?')}  {r.get('body','')[:50]}")

    # 三档分类
    print("\n" + "=" * 80)
    print("  三档分类")
    print("=" * 80)

    green, yellow, red = [], [], []
    for k, r in test_results.items():
        if not r["ok"]:
            red.append((k, r.get("status", "?"), r.get("body", "")[:40]))
        elif r.get("text") and any(c.isdigit() for c in r["text"][:5]):
            green.append((k, r.get("ms", "?"), r["text"][:15]))
        else:
            extra = (" r:" + r.get("reasoning","")[:20]) if r.get("reasoning") else ""
            yellow.append((k, r.get("ms", "?"), r.get("text", "[empty]")[:20] + extra))

    print("\n真能打 (推荐用):")
    for k, ms, t in green:
        print(f"  {k:<40} {ms:>5}ms  {t!r}")
    print("\n凑合能用 (兜底层):")
    for k, ms, t in yellow:
        print(f"  {k:<40} {ms:>5}ms  {t!r}")
    print("\n失效 (从 config 删):")
    for k, st, body in red:
        print(f"  {k:<40} {st}  {body}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
