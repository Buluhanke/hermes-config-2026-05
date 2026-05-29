# MiniMax Provider 真相清单

## 两个 MiniMax provider 的本质区别

| Provider | 真实 endpoint | 可用模型 | 状态 |
|----------|--------------|---------|------|
| `minimax` (minimax.io) | https://api.minimax.io/v1 | 列表有 M2.7 | **假的**，无真实渠道 |
| `minimax-cn` (minimaxi.com) | https://api.minimaxi.com/v1 | M2.7, M2.5, M2.1 | **真的**，官方渠道 |

## V2.aicodee.com 中转（当前主链路）

- 列表有 `MiniMax-M2.7-highspeed`（实际可通）
- 中转 key 写在 `custom_providers[0].api_key`
- Fallback 走 minimax-cn 官方

## 当前模型链（2026-05-29 更新）

```yaml
model:
  default: MiniMax-M2.7-highspeed
  provider: custom:v2.aicodee.com
  fallback: MiniMax-M2.7
  max_tokens: 8192

providers:
  minimax-cn:
    api_key_env: MINIMAX_CN_API_KEY
    base_url_env: MINIMAX_CN_BASE_URL

fallback_model:
  provider: deepseek
  model: deepseek/deepseek-v4-flash

fallback_model_autoswitch: true

custom_providers:
- name: V2.aicodee.com
  base_url: https://v2.aicodee.com/v1
  api_key: YOUR_API_KEY***  # 已填入
```

**模型链优先级**：
1. MiniMax-M2.7-highspeed → V2.aicodee.com（主）
2. MiniMax-M2.7 → minimax-cn（备用，官方 API）
3. deepseek-v4-flash → deepseek 直连（兜底）

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

---

## Provider 模型命名惯例：`prefix/model-name`

**现象**：`/model` picker 里看到 `deepseek/deepseek-v4-flash` 和 `nous/deepseek-v4-pro`，两个都是 deepseek 模型但前缀不同。

**命名规则**：`provider/模型名`
- `deepseek/xxx` = 走内置 `deepseek` provider（`api.deepseek.com` 直连）
- `nous/xxx` = 走 `nous` provider（Nous Portal，OAuth 网页授权）
- `minimax-cn/xxx` = 走 `minimax-cn` provider（minimaxi.com 国内）
- `openrouter/xxx` = 走 OpenRouter 中转

**三种 provider 类型在 `/model` picker 里的表现**：

| Provider 类型 | 配置方式 | `/model` picker 是谁的列表？ | 价格来源 |
|---|---|---|---|
| 内置 API-key provider（`deepseek`, `minimax-cn` 等） | `.env` → `XXX_API_KEY` | `_PROVIDER_MODELS` 静态列表 | DeepSeek / MiniMax 官方定价 |
| OAuth 网页授权 provider（`nous`） | `hermes auth` → 浏览器 OAuth | Nous Portal 动态/静态混合列表 | Nous Portal 定价（有免费档） |
| 自定义 provider（`custom:xxx`） | `config.yaml` → `custom_providers` | 调用 `/v1/models` 动态拉取 | 无价格信息 |

**如何区分同一个模型的两个路径**：

以 `deepseek-v4-flash` 为例：
- `deepseek/deepseek-v4-flash` = 直连付费，走 `api.deepseek.com`
- `nous/deepseek-v4-flash` = Nous Portal 网页授权，走 Nous Portal 的推理端点

**注意**：同一个模型名（如 `deepseek-v4-flash`）在不同 provider 下可能是**不同的定价策略**。Nous Portal 上有免费额度，而 DeepSeek 官方直连是按量付费。

**诊断：当前 `/model` picker 显示的是哪个 provider 的列表？**

看 picker 顶部的 `Active provider:` 行：
```
Current model:    nous/deepseek-v4-flash
Active provider:  Nous Portal
```

这意味着你当前正在浏览 **Nous Portal 的模型列表**，而不是 `deepseek` 直连的列表。要看到直连的列表，需要：
1. `hermes config set model.provider deepseek`
2. 重启会话后再 `hermes model`

**一句话**：`/model` picker 显示的模型列表 = 当前 `model.provider` 的列表。不同 provider 的模型列表完全独立。

**二、Model Picker UX 行为详解（2026-05-17 实测）**：

`hermes model` 现在是一个**两层选择器**：

1. **第一层：Provider 选择**
   ```
   ╭─ ⚙ Model Picker — Select Provider ─────╮
   │ Current: deepseek/deepseek-v4-flash on Nous Portal
   │ ❯ Nous Portal (24 models)  ← current
   │   DeepSeek (4 models)
   │   ...
   ```
   顶部显示当前生效的模型和 provider。列表是**所有可用的 provider**。

2. **第二层：模型选择（以 Nous Portal 为例）**
   ```
   ╭─ ⚙ Model Picker — Nous Portal ────────╮
   │ Select a model (24 available)
   │   ...
   │   deepseek/deepseek-v4-pro       $0.43  $0.87  $0.00
   │   ← Back
   │ ❯ Cancel
   ```
   上方 24 个是**收费模型**（标价）。往下翻到底，有独立的 **"Available free models"** 区域：
   ```
   Available free models:
   ->   deepseek/deepseek-v4-flash  free  free  free
        stepfun/step-3.5-flash      free  free  free
        Enter custom model name
        Skip (keep current)
   ```

**关键发现**：
- Nous Portal 的免费模型（`deepseek-v4-flash`, `stepfun-3.5-flash`）**不在那 24 个列表里**，需要往下翻到底才能看到
- `deepseek/deepseek-v4-pro` 在收费列表里（$0.43/$0.87），`deepseek/deepseek-v4-flash` 在免费区
- **同一个模型名在不同 provider 下对应完全不同的定价策略**

**回答用户关于 provider 识别问题的正确方式**：
当用户问 `/model` 选择器里哪个是哪个时，直接回答：**左边的前缀就是 provider 名**。`deepseek/xxx` = 直连付费，`nous/xxx` = 网页授权免费。不要解释架构、不要绕弯子。

**用户沟通铁律（针对模型/provider 问题）**：
- 用户问"哪个是哪个" → **直接说前缀区分**，不要说架构背景
- 用户已经打开 picker 了 → **告诉他在当前界面怎么操作**，不要让他退出重进
- 用户说"这里面没有" → **确认是否在底部/滚动区域外**，不要质疑用户看错了
