---
name: script-provider-independence
description: |
  Cron/scheduled scripts that perform health checks or model-pings MUST
  not hardcode a specific LLM provider or model. If a script needs to
  verify API connectivity, derive the target from runtime config
  (`~/.hermes/config.yaml` `default` provider), not from a hardcoded
  name. If the user later switches providers, the script should keep
  working or fail silently — never produce stale false-positive alerts.
triggers:
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

## 相关场景

- 任何带 `check_*_health()` 函数的 Python 脚本
- `~/.hermes/scripts/*.py` 下所有定时运行的脚本（self_optimization、daily_task、daily_evolution、hermes_self_check）
- 任何调用 `httpx.post` 到 `https://api.*` 域名做 ping 的代码

## 改造 checklist

写新的自检脚本时：

- [ ] 函数里有没有写死的 `api.deepseek.com` / `api.openai.com` 等 URL？
- [ ] 有没有写死的 `DEEPSEEK_API_KEY` / `OPENAI_API_KEY` 等环境变量名？
- [ ] 检查逻辑依赖的 provider，**今天**是不是用户的主用 provider？
- [ ] 如果 key 失效，**会**不会推告警给用户？（如果会 → 改成 silent 或删掉）

任一项"是" → 重构或删除这段检查逻辑。
