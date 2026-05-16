#!/bin/bash
# 自动更新 OpenRouter 免费模型到 Hermes 配置
# 每天凌晨3点由 launchd 运行

HERMES_HOME="$HOME/.hermes"
CONFIG="$HERMES_HOME/config.yaml"
LOG="$HERMES_HOME/logs/auto_update_free.log"

mkdir -p "$(dirname "$LOG")"

echo "=== $(date) ===" >> "$LOG"

# 使用 Python 更新（忽略 SSL 验证）
python3 - <<'PYEOF' >> "$LOG" 2>&1
import json, yaml, subprocess, sys
from pathlib import Path

def get_openrouter_key():
    config_path = Path.home() / ".hermes" / "config.yaml"
    config = yaml.safe_load(open(config_path))
    providers = config.get("providers", {})
    if isinstance(providers, dict):
        or_config = providers.get("openrouter", {})
        if isinstance(or_config, dict):
            return or_config.get("api_key")
    return None

def fetch_free_models(api_key):
    import urllib.request, ssl
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/models",
        headers={"Authorization": f"Bearer {api_key}"}
    )
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
            data = json.loads(resp.read().decode())
    except Exception as e:
        print(f"获取失败: {e}", file=sys.stderr)
        return []
    models = data.get("data", [])
    free = []
    seen = set()
    for m in models:
        mid = m.get("id", "")
        if ":free" in mid and mid not in seen:
            seen.add(mid)
            free.append(mid)
    return free

def update_config(free_models):
    config_path = Path.home() / ".hermes" / "config.yaml"
    config = yaml.safe_load(open(config_path))
    existing = config.get("fallback_providers", [])
    non_or = [p for p in existing if p.get("provider") != "openrouter"]
    new_or = [{"provider": "openrouter", "model": mid} for mid in free_models]
    config["fallback_providers"] = new_or + non_or
    yaml.dump(config, open(config_path, "w"), allow_unicode=True, default_flow_style=False)
    return len(new_or)

key = get_openrouter_key()
if not key:
    print("未找到 OpenRouter API key")
    sys.exit(1)

print("正在获取免费模型...")
free_models = fetch_free_models(key)
if not free_models:
    print("未获取到免费模型")
    sys.exit(1)

print(f"获取到 {len(free_models)} 个免费模型")
count = update_config(free_models)
print(f"更新完成，共 {count} 个免费模型")
PYEOF

# 重启 gateway
launchctl kickstart -k "gui/$(id -u)/ai.hermes.gateway" >> "$LOG" 2>&1

echo "完成" >> "$LOG"
