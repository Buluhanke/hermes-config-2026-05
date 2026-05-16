# Hermes Agent 全面审计检查清单

## 用途
定期或问题排查时，对 Hermes Agent 部署做全面检查的标准流程。

---

## 1. 版本 & Git 状态

```bash
cd ~/.hermes/hermes-agent
git rev-parse HEAD                                    # 本地 commit
git ls-remote origin main 2>&1 | head -3             # 远程 commit
git fetch origin main && git diff HEAD origin/main    # 落后几个 commit
```

**判断标准**: 本地 `git rev-parse HEAD` 与 `git ls-remote origin main` 的 SHA 不一致 → 需要更新。

---

## 2. 配置文件完整性检查

### 2.1 YAML 格式正确性（关键！）
```python
import yaml
with open('~/.hermes/config.yaml') as f:
    c = yaml.safe_load(f)
# 检查 custom_providers 是否为 list 而非 string
cp = c.get('custom_providers')
print(type(cp), len(cp) if cp else 0)
```

**本 session 发现**: `custom_providers` 被存成了字符串 `'[{...}]'` 而不是 YAML list `[{...}]`，导致解析异常。症状：Python 迭代时报 `AttributeError: 'str' object has no attribute 'get'`。

**修复方法**: 手动修正 config.yaml 中的 `custom_providers` 行，从字符串格式改为正确的 YAML list 格式。

### 2.2 platforms 配置检查
```python
# 检查 platforms 节点是否包含所有活跃平台
for k, v in c.get('platforms', {}).items():
    print(f"{k}: enabled={v.get('enabled')}")
```

**本 session 发现**: weixin 和 qqbot 的配置全靠 `.env` 注入，config.yaml platforms 里只有 wecom。功能正常但不符合规范（credentials 应统一在 config.yaml）。

### 2.3 .env 与 config.yaml 分离原则
```
config.yaml  → settings（platforms, model, agent, toolsets 等）
.env         → secrets（API keys, tokens, passwords）
```
**原则**: platform credentials（QQ_APP_ID, QQ_CLIENT_SECRET 等）应写在 `config.yaml platforms.<platform>.extra` 下，不要只写在 `.env`。代码优先读 config.yaml。

---

## 3. Gateway 运行状态

```bash
# Gateway 进程（macOS 上进程名是 Python，不是 hermes）
ps aux | grep hermes_cli | grep gateway

# launchd 服务
launchctl list | grep -E "hermes|ai\."

# Gateway 日志（检查连接状态）
tail -50 ~/.hermes/logs/gateway.log | grep -E "Starting|Started|Ready|Error|connected|disconnected"
```

**正常输出示例**:
```
✓ wecom connected
✓ weixin connected
✓ qqbot connected
Gateway running with 3 platform(s)
```

---

## 4. 模型 & Provider 连通性验证

### 4.1 主模型（当前配置）
```python
# 当前配置
model: {provider: custom, default: MiniMax-M2.7-highspeed, base_url: https://v2.aicodee.com/v1}
```

### 4.2 Ollama（Mac mini 本地）
```bash
curl -s --max-time 5 http://192.168.0.4:11434/v1/models \
  -H "Authorization: Bearer ollama" | python3 -c "import sys,json; d=json.load(sys.stdin); [print(m['name']) for m in d.get('models',[])]"
```
**本 session 发现**: Mac mini (192.168.0.4) 无响应 → Ollama 可能已关闭或网络不通。

### 4.3 fallback_providers 数量
```python
len(c.get('fallback_providers', []))  # 正常应 > 20
```

### 4.4 providers 配置完整性
```bash
# 检查各 provider 的 api_key 是否完整（非截断）
# NVIDIA API Key 格式应为 NVIDAPI_REDACTED开头 + 约32字符
grep "nvidia:" config.yaml
```

---

## 5. Launchd 服务检查

```bash
# 检查所有 Hermes 相关服务
launchctl list | grep -E "hermes|ai\."

# 正常应看到：
# 36529  ai.hermes.gateway  (数字=PID，- 表示服务不存在)
# -      ai.hermes.auto_update_free  (短横线=服务未安装)
```

**本 session 发现**: `ai.hermes.auto_update_free` 短横线 → launchd plist 未正确安装。

---

## 6. 本 session 发现的问题汇总

| # | 问题 | 影响 | 状态 |
|---|------|------|------|
| 1 | `custom_providers` 存成字符串 | 配置解析异常 | ⚠️ 待修复 |
| 2 | weixin/qqbot 不在 config.yaml | 规范问题 | ⚠️ 建议迁移 |
| 3 | Ollama 192.168.0.4 无响应 | fallback 失败 | ⚠️ 待确认 |
| 4 | NVIDIA API Key 格式可疑 | 可能是截断 | ⚠️ 待核实 |
| 5 | auto_update_free launchd 未安装 | 免费模型不自动更新 | ⚠️ 待修复 |
| 6 | Gateway 落后 origin/main 2 commits | 缺少最新修复 | ⚠️ 待更新 | — |
| 7 | `model.model` 字段冲突 | 主模型被覆盖为 gemma | ✅ 已修复（删除该字段） | 2026-05 |
| 8 | `credential_pool_strategies.latency_based_routing: true` | 无效配置项 | ✅ 已修复（删除该字段） | 2026-05 |
| 9 | `model_catalog` 配置块冗余 | 无实际作用 | ✅ 已修复（删除该字段） | 2026-05 |
| 10 | qwen3-fast:latest 未加入 fallback | 本地模型未优先 | ✅ 已修复（加为 fallback 第一位） | 2026-05 |

### Provider 免费层实测（2026-05）

| Provider | 免费模型 | 状态 |
|----------|---------|------|
| OpenRouter | 29个 `:free` | ✅ 正常 |
| Groq | 免费层 403 Forbidden | ❌ key 无效 |
| Cerebras | 无免费模型，403 Forbidden | ❌ key 权限不足 |
| NVIDIA | 免费层已过期，404 | ❌ key 无效 |
| Google | 无真正免费（Gemini/gemma 全付费） | ❌ 付费按量 |

**结论**: 该用户配置的 5 个 provider，只有 OpenRouter 有真正免费 fallback。

---

## 7. 快速诊断命令（一次性）

```bash
#!/bin/bash
echo "=== Hermes Agent Quick Audit ==="
echo ""
echo "[1] Git status"
cd ~/.hermes/hermes-agent
LOCAL=$(git rev-parse HEAD)
REMOTE=$(git ls-remote origin main | cut -f1)
echo "Local:  $LOCAL"
echo "Remote: $REMOTE"
[ "$LOCAL" != "$REMOTE" ] && echo "⚠️  OUT OF DATE" || echo "✅  UP TO DATE"
echo ""

echo "[2] Gateway process"
ps aux | grep hermes_cli | grep gateway | grep -v grep | head -1 || echo "⚠️  NOT RUNNING"
echo ""

echo "[3] Platform connections"
tail -30 ~/.hermes/logs/gateway.log 2>/dev/null | grep -E "✓|✗|connected|disconnected" | tail -10
echo ""

echo "[4] custom_providers type check"
python3 -c "
import yaml
with open('$HOME/.hermes/config.yaml') as f:
    c = yaml.safe_load(f)
cp = c.get('custom_providers')
print(f'type: {type(cp).__name__}')
print(f'is string: {isinstance(cp, str)}')
" 2>&1
echo ""

echo "[5] Launchd services"
launchctl list | grep -E "hermes|ai\." 2>&1
echo ""

echo "[6] Disk usage (largest)"
du -sh ~/.hermes/hermes-agent/*/ ~/.hermes/* 2>/dev/null | sort -h | tail -5
```

---

## 8. 更新步骤

```bash
# 8.1 更新 Hermes 到最新
cd ~/.hermes/hermes-agent && git pull origin main

# 8.2 重启 Gateway
launchctl kickstart -k gui/$(id -u)/ai.hermes.gateway
# 或
hermes gateway restart

# 8.3 修复 custom_providers 格式（手动编辑 config.yaml）
# 从:  custom_providers: '[{"name": "cerebras", ...}]'
# 改为: custom_providers:
#        - name: cerebras
#          base_url: https://api.cerebras.ai/v1
#          api_key: cYOUR_API_KEY
#          model: cerebras/llama-3.3-70b
```
