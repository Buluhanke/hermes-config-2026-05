# 模型切换诊断流程

## 场景：用户问"切换了吗？"

当用户问模型/供应商是否已切换，需要查**四层**才能给出完整答案。

### 第1层：config.yaml 的 model.default（用户的意图层）

```bash
hermes config show | grep -A5 "Model"
# 或直接查看
grep "default:" ~/.hermes/config.yaml
# → model.default: MiniMax-M2.7-highspeed  ← 用户的切换意图
```

### 第2层：当前会话的 provider（实际运行层）

**关键洞察：`config.model.default` 只影响新会话，不影响当前已运行的会话。**

当前会话的 provider 在会话启动时固定下来，中途不会变。即使改了 config，这个 session 仍然用启动时的 provider。

```bash
# 查看当前会话的 provider（从 session metadata）
# 如果她在 CLI 会话里问"切换了吗"，她就是当前这个 session
# → 检查启动时的 --provider / -m 参数，或默认值
```

外部渠道（QQ/微信/Dashboard）开的会话也一样——会话启动时读 config 快照。

### 第3层：.env 的 API keys（能否通）

切换模型只是改了模型名，还得看对应的 API key 配了没：

```bash
grep -E "API_KEY|BASE_URL" ~/.hermes/.env | grep -v "^#"
```

注意 key 是否指向正确的 base_url：
- MiniMax 国内（aicodee 代理）→ `MINIMAX_CN_API_KEY` + `MINIMAX_CN_BASE_URL=https://v2.aicodee.com/v1`
- DeepSeek → `DEEPSEEK_API_KEY` + `DEEPSEEK_BASE_URL=https://api.deepseek.com`
- OpenRouter → `OPENROUTER_API_KEY`

### 第4层：Ollama 本地模型（local fallback）

如果切到本地模型（Qwen3/Qwen2.5VL 等），检查是否已拉好：

```bash
ollama list
# 预期：qwen2.5vl:7b / qwen3:8b / qwen3-fast:latest 等
```

### 第5层：模型在供应商侧是否可用（路由验证）

config 里写了模型名 ≠ 这个模型能通。必须验证路由。

**验证命令**：
```bash
# 列出 OpenRouter 上某供应商的所有模型
curl -s "https://openrouter.ai/api/v1/models" \
  | python3 -c "import json,sys; data=json.load(sys.stdin)
for m in data.get('data',[]):
    if 'minimax' in m.get('id','').lower():
        print(m['id'])"

# 直接测试模型（通过aicodee代理或直接API）
curl -s -X POST https://v2.aicodee.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $MINIMAX_CN_API_KEY" \
  -d '{"model":"模型名","messages":[{"role":"user","content":"hi"}],"max_tokens":10}'
```

**检查内置 provider 插件**（有时模型存在于插件代码而非文档）：
```bash
cat ~/.hermes/hermes-agent/plugins/model-providers/minimax/__init__.py
```

**重点：MiniMax 供应商路由（2026-05-15 验证）**

Hermes 内置三个 MiniMax provider：

| provider | 路由 | api_mode | 可用模型 | 本机状态 |
|---|---|---|---|---|
| `minimax` | `MINIMAX_API_KEY`→`api.minimax.io/anthropic` | anthropic_messages | MiniMax-M2.7 | ❌ key注释 |
| `minimax-cn` | `MINIMAX_CN_API_KEY`→`api.minimaxi.com/anthropic` | anthropic_messages | MiniMax-M2.7 | ⚠️ base_url被改aicodee |
| `minimax-oauth` | OAuth浏览器登录 | anthropic_messages | MiniMax-M2.7-highspeed | ❌ 未登录 |

**关键陷阱**：`minimax-cn` 用 `anthropic_messages` 格式，aicodee 代理是 OpenAI 格式。若 Hermes 通过 `minimax-cn` + aicodee base_url 调用，可能格式不匹配导致失败。

**模型名可用性**：
- OpenRouter: `minimax/minimax-m2.7` ✅（无 highspeed 变体，`minimax/minimax-m2.7-highspeed` 返回 400）
- aicodee 代理: `MiniMax-M2.7-highspeed` ✅（已验证）
- MiniMax 原生: `MiniMax-M2.7-highspeed`（minimax-oauth 的 default_aux_model）

### 第6层：模型名的 provider 前缀解析

无前缀的模型名（如 `MiniMax-M2.7-highspeed`）路由逻辑：
1. OpenRouter key 存在 → 通过 OpenRouter 路由（模型名作 slug）
2. 匹配内置 provider 的 default_aux_model → 用该 provider
3. 仅自定义 key → custom provider 路由

### 整合判断

| config.default | 当前 session provider | .env 有key? | 结论 |
|---|---|---|---|
| MiniMax | DeepSeek | ✅ | Config已切，但当前会话还是DeepSeek。新开会话走MiniMax |
| MiniMax | MiniMax | ✅ | ✅ 切换已生效 |
| MiniMax | MiniMax | ❌ | Config切了但key没配，会失败 |

### 汇报模板

向用户汇报时用三段式：

```
**✅ Config已切换**
- model.default → [新模型]
- [其他配置变更]

**⚠️ 当前会话仍跑在[旧模型]上**
这个session在你改config之前就启动了，新开会话才走新模型

**[如有] ⚠️ [模型名]路由情况：**
- OpenRouter: 状态
- 原生API/代理: 状态
- Hermes内置provider: 格式兼容性提示
```

完整示例：
```
**✅ Config已切换**
- model.default → MiniMax-M2.7-highspeed

**⚠️ 当前会话仍跑在deepseek上**
这个session在你改config之前就启动了，新开会话才走新模型

**⚠️ MiniMax-M2.7-highspeed 路由情况：**
- OpenRouter: 无此模型（只有 minimax/minimax-m2.7）
- aicodee代理: 可用 ✅
- Hermes内置 provider minimax-cn: anthropic_messages格式，与aicodee OpenAI格式可能不匹配
```
