#!/usr/bin/env python3
"""
Provider 连通性诊断脚本
使用方式：
    source ~/.hermes/.env 2>/dev/null
    python3 /path/to/this/script.py

测试所有已配置 provider 的 API 连通性。
结果按 主模型 → fallback_model → fallback_providers 顺序逐个测。
"""
import json, os, sys, urllib.request

def test_provider(label, url, key, model, timeout=15):
    """测试单个 provider 是否可连通。返回 (label, status, detail)。"""
    if not key:
        return (label, "NO_KEY", "无 API Key 配置")
    
    payload = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": "Say pong"}],
        "max_tokens": 5,
    }).encode()
    
    req = urllib.request.Request(
        url, data=payload,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    
    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
        data = json.loads(resp.read())
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        model_used = data.get("model", "")
        return (label, "OK", f"✅ {content.strip()[:30]} (model: {model_used})")
    except urllib.error.HTTPError as e:
        body = e.read().decode()[:150]
        return (label, f"HTTP_{e.code}", f"❌ {e.code}: {body[:80]}")
    except Exception as e:
        return (label, "ERROR", f"❌ {e}")


def main():
    env = os.environ
    
    tests = [
        ("1. v2.aicodee.com 主力 / MiniMax-M2.7-highspeed", 
         "https://v2.aicodee.com/v1/chat/completions",
         env.get("AICODEE_API_KEY", ""),
         "MiniMax-M2.7-highspeed"),
        
        ("2. minimax-cn 备用1 / MiniMax-M2.7",
         "https://api.minimaxi.com/v1/chat/completions",
         env.get("MINIMAX_CN_API_KEY", ""),
         "MiniMax-M2.7"),
        
        ("3. DeepSeek 直连 / deepseek-chat",
         (env.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")) + "/chat/completions",
         env.get("DEEPSEEK_API_KEY", ""),
         "deepseek-chat"),
        
        ("4. OpenRouter / deepseek/deepseek-v4-flash",
         "https://openrouter.ai/api/v1/chat/completions",
         env.get("OPENROUTER_API_KEY", ""),
         "deepseek/deepseek-v4-flash"),
    ]
    
    results = []
    
    print("=" * 60)
    print("  Hermes Provider 连通性诊断")
    print("=" * 60)
    
    for label, url, key, model in tests:
        key_preview = key[:10] + "..." if key else "未配置"
        print(f"\n  ▶ {label}")
        print(f"    URL: {url}")
        print(f"    Key: {key_preview}")
        
        label_out, status, detail = test_provider(label, url, key, model)
        print(f"    {detail}")
        results.append((label_out, status, detail))
    
    print("\n" + "=" * 60)
    print("  总  结")
    print("=" * 60)
    ok_count = sum(1 for _, s, _ in results if s == "OK")
    for label, status, detail in results:
        icon = "✅" if status == "OK" else "❌"
        short = label.split(" / ")[0]
        print(f"  {icon} {short}: {status}")
    print(f"\n  {ok_count}/{len(results)} 个可用")
    
    # Machine-readable
    print("\n\n---MACHINE_OUTPUT---")
    print(json.dumps([(l, s) for l, s, _ in results]))


if __name__ == "__main__":
    main()
