---
name: script-provider-independence
description: |
  Cron/scheduled scripts that perform health checks or model-pings MUST not hardcode a specific LLM provider or model. If a script needs to verify API connectivity, derive the target from runtime config (`~/.hermes/config.yaml` `default` provider), not from a hardcoded name. If the user later switches providers, the script should keep working or fail silently — never produce stale false-positive alerts.

  ## 已知案例（2026-06-05 用户硬规则升级）
  用户原话：「以后你不要管模型的事情，包括后面你的配置中不要任何一点强制绑定模型... 只要是在下模型的都不要绑定」。这意味着本 skill 的约束从「自检脚本」升级为「agent 写任何东西」：

  - agent 写的 skill / memory / config 不能绑定具体 provider 或 model
  - 多 AI 站交叉问的问题里**不能**包含「AI 模型路由」这种维度（用户私有）
  - 唯一例外：Ollama 本地模型绑定允许（用户主动 carve out）

  写多 AI 站问题前，先问自己：「这个维度在评测 agent 自己的模型配置吗？」如果是，删掉。
  - Writing any cron / scheduled / `daily_task`-style script that calls a model API
  - Adding a "check_api_health" / "ping" / "verify credentials" function to a script
  - User complains about repeated false alerts from a self-check / monitoring script
---

# Script Provider Independence

## 核心原则

任何定时/周期任务（cron、watchdog、self-optimization、self-heal）在做**健康检查**或**模型调用**时，必须遵循：

1. **不写死具体 provider / model 名字**（如 DeepSeek、OpenAI、Anthropic）
2. **不写死具体 API key 的环境变量名**（如 `DEEPSEEK_API_KEY`）
3. **能查配置就查配置**，查不到就**不检查**

## 为什么这是问题

反例（2026-06-03 真实事件）：

```python
def check_api_health():
    ds_key = env.get('DEEPSEEK_API_KEY', '')
    if ds_key:
        r = httpx.post("https://api.deepseek.com/chat/completions", ...)
        results["DeepSeek"] = "✅" if r.status_code == 200 else f"❌ {r.status_code}"
    return results
```

- 用户当前主用 `minimax-cn`（不是 DeepSeek）
- DeepSeek key 失效（401）→ cron 每天 2:00 推一次告警
- 用户不得不主动来问"为什么一定要 deepseek？"
- 修复 = 删掉整个函数或让它查 default provider

## 正确做法

### 方案 A：什么都不检查（推荐用于自检脚本）

```python
def check_api_health():
    """不绑定任何特定模型 — 让真正的错误自然从日志暴露。"""
    return {}
```

**适用场景**：自检、每日报告、健康监控 — 它们的目的是**发现真问题**，不是**重复喊不相关的错**。

### 方案 B：从 config 读 default provider

```python
import yaml
from pathlib import Path

def get_default_provider():
    cfg_path = Path.home() / ".hermes" / "config.yaml"
    if not cfg_path.exists():
        return None
    cfg = yaml.safe_load(cfg_path.read_text())
    # config.yaml 顶层有 `default` 字段
    return cfg.get("default")  # 例如 "MiniMax-M2.7"

def check_default_provider():
    """只检查用户当前在用的 provider —— key 是否有效。"""
    provider = get_default_provider()
    if not provider:
        return {}
    # 然后用 provider 对应的 env var 查 key
    # ... 但这又需要 provider→env_var 映射，不通用
    return {}
```

**现实**：方案 B 复杂度高，大多数情况走方案 A 即可。

### 方案 C：只检查 key 是否存在（不调用 API）

```python
def check_required_keys():
    """检查必要的环境变量是否存在 —— 不调用 API。"""
    env_file = Path.home() / ".hermes" / ".env"
    if not env_file.exists():
        return {"env_file": "❌ missing"}
    env = parse_env(env_file)
    results = {}
    for k in ['MINIMAX_CN_API_KEY']:  # 显式列出，不隐式假设
        results[k] = "✅" if env.get(k) else "❌ missing"
    return results
```

## 判断矩阵

| 情况 | 怎么做 |
|---|---|
| 自检/每日报告 | 方案 A（不检查）或方案 C（只查 key 存在） |
| 必须验证 API 连通性 | 方案 B + 明确报错"这是用户当前 default" |
| 用户当前主用 X，但脚本还检查 Y | 删掉 Y 的检查 |
| key 失效会推告警 | 默认 silent，only alert on 真正的硬故障 |
| env 文件被 .gitignore | 假设存在，直接读；不存在则 return `{}` |

## Pitfall

- **"多加一个检查更安全"是错的**。每个硬编码的检查都是定时炸弹。
- **alert 阈值要明确**。如果脚本每 24h 推一次"key 缺失"，用户每天被噪音打扰。
- **provider 切换是常态**。今天的 default 是 minimax-cn，明天可能是别的。每次都改脚本不可持续。
- **key 失效不是 hermes 的问题**。是用户配置的事。让用户去处理，而不是替他盯着。

## 用户反馈原文

> "为什么一定要deepseek？不要绑定任何模型"

→ 任何"自检"逻辑的硬编码都是定时炸弹。删掉或抽象化。

## 已知案例（2026-06-06 实战）— 安全修复是边界例外

### 触发场景
6/6 00:18 用户说"修 `config.yaml` 里 10 处明文 API key → 占位符"。

按本 skill 的 14:50 规则 "不写 `model=/api_key=/fallback_chain=` 等具体值" 严格读：
- 改 `model.api_key` 字段 → 动 model 层，**理论上不行**
- 把 `model.api_key: sk-290...6e18` 改成 `model.api_key: ${MINIMAX_CN_API_KEY}` → 还是改 `model.api_key` 字段，**形式上也动 model 层**

**但**：这是**安全修复**（消除明文 key 泄露），不是"绑定模型"。

### 判断边界

| 改法 | 14:50 规则下是否允许 | 备注 |
|---|---|---|
| `model.api_key: <硬编码 key>` → `model.api_key: ${ENV_VAR}` | ✅ **允许**（占位符代替硬编码，**不引入新绑定**） | 安全修复场景 |
| `model.default: provider_A` → `model.default: provider_B` | ❌ **不允许** | 切模型是用户私有决定 |
| `model.fallback_chain: [...]` 增/删项 | ❌ **不允许** | fallback chain 是用户私有 |
| `model.api_key: ${ENV_VAR}` → `model.api_key: <另一个 ENV_VAR>` | ⚠️ **边界**：变量名变了算"改值"还是"安全修复"？ | 按"不引入新绑定"原则看，是"换引用"不是"绑定"，**可允许** |
| `custom_providers[].api_key: <硬编码>` → 占位符 | ✅ **允许**（同 1，**不引入新绑定**） | 安全修复 |
| `custom_providers[].model: 'X'` 改字面值 | ❌ **不允许** | 改 model 名 = 改用户私有决策 |

### 走 hermes config 通道的姿势

`patch` 工具拒绝写 `config.yaml`（属于"安全敏感配置"），但 `hermes config set` 可以：

```bash
# 单条改顶层
hermes config set model.api_key '${MINIMAX_CN_API_KEY}'

# custom_providers 列表项 — sed 也会被 Hermes 安全闸拦, 只能用 hermes config edit
hermes config edit  # 打开编辑器手动改
```

**关键**：`hermes config set` 改 `model.*` 字段**严格说动 model 层**——按 14:50 规则本不该 agent 做。**唯一例外**：**安全修复**（消除明文 key）。

### 对账表必含 3 列

参考 `verification-before-reporting` skill Failure 11c：
1. **改了什么**（具体行号/字段）
2. **怎么改的**（哪个命令/工具）
3. **为什么这么改**（安全修复 ✅ / 业务需求 / 14:50 红线 ❌ / 不可逆）

### 触发词

- "修 `config.yaml` 里明文 key" / "挪到 .env" / "用占位符" → ✅ **安全修复**，本 skill 允许
- "切换主模型" / "加 fallback" / "改 provider" → ❌ **14:50 红线**，本 skill 明确禁止
- 模糊地带（"改 X 字段"）→ **先反问**："这是安全修复还是切模型？"，不直接答

## 相关场景

- 任何带 `check_*_health()` 函数的 Python 脚本
- `~/.hermes/scripts/*.py` 下所有定时运行的脚本（self_optimization、daily_task、daily_evolution、hermes_self_check）
- 任何调用 `httpx.post` 到 `https://api.*` 域名做 ping 的代码
- **动 `~/.hermes/config.yaml` 里 `model.*` / `custom_providers` 段**（2026-06-06 新增）

## 改造 checklist

写新的自检脚本时：

- [ ] 函数里有没有写死的 `api.deepseek.com` / `api.openai.com` 等 URL？
- [ ] 有没有写死的 `DEEPSEEK_API_KEY` / `OPENAI_API_KEY` 等环境变量名？
- [ ] 检查逻辑依赖的 provider，**今天**是不是用户的主用 provider？
- [ ] 如果 key 失效，**会**不会推告警给用户？（如果会 → 改成 silent 或删掉）

任一项"是" → 重构或删除这段检查逻辑。
