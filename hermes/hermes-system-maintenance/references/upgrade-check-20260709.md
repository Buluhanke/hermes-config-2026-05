# 配套升级检查 — 命令与结果记录

## 标准检查命令（一次性执行）

```bash
#!/bin/bash
# Hermes 配套升级检查
echo "=== Hermes Git ==="
cd ~/.hermes/hermes-agent && git fetch upstream --quiet && \
  echo "落后: $(git log --oneline HEAD..upstream/main 2>/dev/null | wc -l | tr -d ' ') commits"

echo "=== Chrome ==="
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --version

echo "=== SDK 版本 ==="
python3 -c "
import json, urllib.request
for pkg in ['openai', 'anthropic']:
    url = f'https://pypi.org/pypi/{pkg}/json'
    with urllib.request.urlopen(url, timeout=5) as r:
        data = json.loads(r.read())
        print(f'{pkg}: latest={data[\"info\"][\"version\"]}')
"
```

## 2026-07-09 检查结果

| 组件 | 当前 | 最新 | 落后 |
|------|------|------|------|
| Hermes | v0.18.0 (30e947e0) | upstream main (7426c09b) | **121 commits** |
| openai SDK | 2.30.0 | 2.44.0 | 中版本 |
| anthropic SDK | 0.76.0 | 0.116.0 | 中版本 |
| Chrome | 149.0.7827.201 | 150 (6/30发布) | 大版本 |

### Hermes 121 commits 主要内容（head）
```
feat(gateway): persist per-session /model overrides across gateway restarts
fix(interrupt): run user-approved commands from a clean interrupt slate
feat(secrets): adapt 1Password onto the SecretSource interface
fix(secrets): make 1Password bootstrap token reliable outside systemd
fix(secrets): remove unused masked_secret_prompt import from onepassword CLI
```

### Chrome 150 安全公告
- 382 个安全修复
- 15 个 Critical 级别
- 6/30/2026 推送 stable channel

## Git 网络超时问题
`git fetch upstream` 在慢速网络下会超时（30s），需要加 `--timeout=60` 或提前断开重试。

## 升级风险评估

**Hermes**：121 commits 以 bugfix 为主，无 breaking change，可以安全升级。  
**SDK**：建议 review changelog 后再升，先在测试环境验证。  
**Chrome**：升级后需要重启 CDP 端口（kill -9 Chrome PID 再重开）。  
