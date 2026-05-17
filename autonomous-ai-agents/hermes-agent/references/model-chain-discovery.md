# MiniMax Provider 真相清单

## 两个 MiniMax provider 的本质区别

| Provider | 真实 endpoint | 可用模型 | 状态 |
|----------|--------------|---------|------|
| `minimax` (minimax.io) | https://api.minimax.io/v1 | 列表有 M2.7 | **假的**，无真实渠道 |
| `minimax-cn` (minimaxi.com) | https://api.minimaxi.com/v1 | M2.7, M2.5, M2.1 | **真的**，官方渠道 |

## V2.aicodee.com 中转

- 列表有 `MiniMax-M2.7-highspeed`
- 实际调用返回 503 `model_not_found` = distributor 上没有可用渠道
- **中转已死，但配置里依然填主模型位置**，等它恢复
- Fallback 触发条件：503 + `model_not_found` 不在标准 fallback 条件里，需要代码修复

## 当前模型链（config.yaml）

```yaml
# 2026-05-17 更新：已切到 minimax-cn 直连
# V2.aicodee.com 主链路 503 无法恢复，直接走 minimaxi.com 官方 API
model:
  default: minimax-cn/MiniMax-M2.7
  temperature: 0.7
  top_p: 0.95
  max_tokens: 8192
  provider: minimax-cn
```

之前的状态（已废弃）：

```yaml
model:
  default: V2.aicodee.com/MiniMax-M2.7-highspeed  # 503 model_not_found
  provider: custom
  fallback_model:
  - provider: minimax-cn      # Fallback 1
    model: MiniMax-M2.7
  - provider: deepseek        # Fallback 2
    model: deepseek-v4-flash
  base_url: https://v2.aicodee.com/v1
```

## 手动切换命令

切到 minimax-cn（minimaxi.com）直接用：
```bash
sed -i '' 's/default: V2.aicodee.com\/MiniMax-M2.7-highspeed/default: minimax-cn\/MiniMax-M2.7/' ~/.hermes/config.yaml
```

恢复 V2.aicodee.com 主模型：
```bash
sed -i '' 's/default: minimax-cn\/MiniMax-M2.7/default: V2.aicodee.com\/MiniMax-M2.7-highspeed/' ~/.hermes/config.yaml
```

## 问题：model_not_found 不触发 fallback

V2.aicodee.com 返回的 503 `model_not_found`（错误码在 response body 里）不在标准 fallback 触发条件中。需要修复 fallback 代码对这个错误的处理。

## 如何从 model picker 中移除一个 provider

如果某个 provider（如 minimax.io 国际版）在 `/model` picker 里显示但从未使用过，可以被隐藏：

### 步骤

1. 找到该 provider 对应的 API key 环境变量
   - `minimax` → `MINIMAX_API_KEY`（国际 minimax.io）
   - `minimax-cn` → `MINIMAX_CN_API_KEY`（国内 minimaxi.com）
   - 其他 provider：查 `~/.hermes/hermes-agent/agent/models_dev.py` 里的 `PROVIDER_TO_MODELS_DEV` 映射

2. 注释掉 `.env` 中对应的 key（**不要用 sed，key 含特殊字符会炸**）：
   ```bash
   python3 -c "
   with open('/Users/aimac/.hermes/.env', 'r') as f:
       lines = f.readlines()
   for i, line in enumerate(lines):
       if line.startswith('MINIMAX_API_KEY=') and not line.startswith('#'):
           lines[i] = '# ' + line.replace(' MINIMAX_API_KEY=', ' ', 1).replace('MINIMAX_API_KEY=', '# MINIMAX_API_KEY=\n', 1)
           lines[i] = '# MINIMAX_API_KEY=\n'
           break
   with open('/Users/aimac/.hermes/.env', 'w') as f:
       f.writelines(lines)
   "
   ```

3. **重启 gateway** 让 QQ/微信/Telegram 等消息渠道生效：
   ```bash
   hermes gateway restart
   ```
   或 kill 老进程让 launchd/systemd 自动拉起。

## 从 model picker 中删除一个 provider（彻底）

如果某个 provider（如 minimax.io 国际版）不仅 key 无效，你想从 `/model` picker 和所有 provider 列表中彻底移除：

### 方法 1：注释 .env key（推荐，可恢复）

```bash
# 注释掉 key
sed -i '' 's/^MINIMAX_API_KEY=/# MINIMAX_API_KEY=/' ~/.hermes/.env
```
然后重启 gateway 或终端重开即可。

### 方法 2：清空 `_PROVIDER_MODELS`（从所有列表中删除）

编辑 `hermes_cli/models.py`，找到 `_PROVIDER_MODELS` 字典，将该 provider 的模型列表设为空列表：

```python
# 修改前：
"minimax": ["minimax-m2.7", "minimax-m2.5", "minimax-m2.1", "minimax-m2"],
# 修改后：
"minimax": [],
```

效果：`/model` picker 中该 provider 不再显示模型列表。但该 provider 条目本身仍然存在（只是 "0 models"）。

### 重要：不要误删 OpenRouter/Vercel 目录中的同名条目

`models.py` 中还有几处 `minimax/minimax-m2.7` 出现在：
- `OPENROUTER_MODELS` (line 55) — OpenRouter 的静态目录，实际走 OpenRouter 渠道
- `VERCEL_AI_GATEWAY_MODELS` (line 80) — Vercel AI Gateway 的目录
- `opencode-go` 列表里的 `minimax-minimax-m2.7` (line 184) — OpenCode Go 支持的模型列表

**这些是 OpenRouter/Vercel/OpenCode 的模型目录条目，跟 minimax.io 这个 provider 本身无关。** 删它们会阻止正确的模型路由。只动 `_PROVIDER_MODELS["minimax"] = []`。

### 注意事项

- 终端 CLI 和新会话立即生效（因为重启时重新加载 models.py）
- 已有 gateway 进程需要重启
- 不影响同名国内版（如 `minimax-cn` 有独立的 key `MINIMAX_CN_API_KEY`）

## 验证方法

```bash
hermes status 2>/dev/null | grep -E "Model|Provider"
```

## 终端/model vs 消息渠道模型差异诊断

**现象**：终端 `hermes --tui` 或 CLI 里 `/model` 查看 provider，某个 provider 显示 "no models" / 空列表，但 QQ/微信/Telegram 等消息渠道仍然正常工作。

**根因**：多个 provider 同名不同 endpoint 时，`/model` 展示 ALL configured providers 的模型列表。某个 provider 空 = 该特定 provider 的 key/endpoint 有问题，不代表另一个同名 provider（国内版）有问题。

具体到 MiniMax：
- `/model` 里的 `minimax` = minimax.io 国际版，key 过期/无模型
- QQ/微信实际走 `minimax-cn` = minimaxi.com 国内版，key 有效
- **两个是独立 provider**，各自有自己的 key 和 endpoint

**诊断步骤**：
1. `cat ~/.hermes/.env | grep -i mini` — 确认两个 key 都存在且不同
2. `cat ~/.hermes/config.yaml | grep -A 10 "fallback_model"` — 确认模型链里有哪个 provider
3. 终端 `/model` 展示的是 provider 级别的模型列表；实际推理走的是 `model.default` + `fallback_model` 链
4. 消息渠道的工作与否，取决于 `fallback_model` 链里有没有可用的 provider，跟 `/model` 空不空没有直接关系

**一句话**：终端 `/model` 是"市场价目表"，模型链是"实际采购单"。价目表上某个供货商没写价格，不影响你从另一个供货商拿货。

---

---

## DeepSeek V4 可用路径诊断

**现象**：配置了 DeepSeek V4 通过网页端授权（OAuth / env key），但不确定在哪里启用。

**两个实际可用的 deepseek-v4-flash 路径**：

| 路径 | Provider | 端点 | 配置方式 |
|------|----------|------|---------|
| 官方直连 | `deepseek` | `api.deepseek.com` | `.env` → `DEEPSEEK_API_KEY` |
| OpenRouter 中转 | `openrouter` | `openrouter.ai/v1` | `.env` → `OPENROUTER_API_KEY`，模型名 `deepseek/deepseek-v4-flash` |

**诊断步骤**（通用模型可用性排查）：

```bash
# 1. 看有哪些凭据池
hermes auth list | grep -A5 deepseek

# 2. 看 .env 有什么 key
grep -i deepseek ~/.hermes/.env

# 3. 看 config.yaml 当前用的什么模型和 provider
grep -A5 "model:" ~/.hermes/config.yaml | head -10

# 4. 看内置 provider 有哪些模型
grep -A20 '"deepseek":' ~/.hermes/hermes-agent/hermes_cli/models.py | head -25

# 5. 看第三方 relay 有没有 deepseek
curl -s "RELAY_URL/v1/models" -H "Authorization: Bearer $KEY" | python3 -m json.tool
```

**关键**：`hermes auth list` 看到的是**凭据池**（credential pool），不是 provider 列表。一个 provider 可以有多条凭据（env key + manual key）。`model.default` 指定的模型路径才是实际走哪条路。

**参见**：`references/channel-model-management.md` — 渠道模型配置约束（无 per-channel 模型）
