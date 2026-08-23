# Hermes Provider 级联失败（2026-07-24）

## 触发
用户：「为什么本机的模型很多都消失或者不肯用了，包括 hermes 官方授权的 hy3 免费模型等」

## 根因：三层叠加

### 第 1 层（最深层）：`custom_providers` YAML 写成 list
- **文件**：`~/.hermes/config.yaml`
- **根因**：YAML 中 `custom_providers` 写成 `- name: cerebras` 的 list 格式
- Python 加载为 `list` 而非 `dict`，导致 cerebras/nvidia/nvidia2/cerebras2 全部失效
- **症状**：所有 fallback provider 静默消失，Hermes 只有默认 MiniMax

**正确格式（dict）：**
```yaml
custom_providers:
  cerebras:
    api_key: csk-...
    base_url: https://api.cerebras.ai/v1
```

**错误格式（list）：**
```yaml
custom_providers:
- name: cerebras
  api_key: csk-...
```

### 第 2 层：`tencent/hy3:free` 被 OpenRouter 下线
- **证据**：`gateway.error.log` HTTP 404
```
This model is unavailable for free.
The paid version is available now - use this slug instead: tencent/hy3
```
- OpenRouter 近期变更，免费版 hy3 已移除

### 第 3 层：OpenRouter 余额几乎归零
- **证据**：`gateway.error.log` HTTP 402
```
You requested up to 65536 tokens, but can only afford 998.
```

## 诊断命令（本次实测完整路径）
```bash
# 1. 日志查 HTTP 错误码
tail -100 ~/.hermes/logs/gateway.error.log | grep "HTTP"

# 2. 验证 custom_providers 结构
python3 -c "
import yaml
with open('~/.hermes/config.yaml') as f:
    cfg = yaml.safe_load(f)
print(type(cfg.get('custom_providers')))
"

# 3. 验证 OpenRouter 余额
curl -s https://openrouter.ai/api/v1/credits \
  -H "Authorization: Bearer $OPENROUTER_API_KEY"

# 4. 查模型目录缓存
cat ~/.hermes/cache/model_catalog.json | python3 -c "
import json,sys
d=json.load(sys.stdin)
for p,v in d.items():
    models = v.get('models',[])
    hy3 = [m for m in models if 'hy3' in m.get('id','').lower()]
    if hy3: print(p, hy3)
"

# 5. 确认 Nous Portal vs OpenRouter 是两套独立体系
# Nous auth 每15秒刷新 JWT
grep "NAS invoke JWT" ~/.hermes/logs/agent.log
```

## 关键发现
- OpenRouter 的 `model_catalog.json` 缓存 vs 实际可用模型是两回事
- Nous Portal（NAS invoke JWT）和 OpenRouter（API key）是两套认证体系，不能混用
- HTTP 404 背后往往有更深层配置问题，不能只看到 404 就下结论
