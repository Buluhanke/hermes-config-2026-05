# Hermes /model picker 行为参考（2026-06-04 实测）

QQbot / Telegram / Discord 上的 `/model` 命令列表由 `hermes_cli/model_switch.py:list_picker_providers()`（Telegram/Discord 交互式键盘）或 `list_authenticated_providers()`（QQbot 文本列表）渲染。

## 4 段渲染机制（按顺序拼接）

`list_authenticated_providers()` 返回的列表是 4 段拼接的，**不是并集去重**，是**按顺序追加**：

1. **Section 1 — built-in canonical provider 列表**（OpenRouter / Nvidia / Ollama Cloud / Nous / Gemini / Copilot / Z.AI / MiniMax-CN / DeepSeek 等）
   - 只显示 `auth.py:PROVIDER_REGISTRY` 里有 key 环境变量的 provider
   - 走 `cached_provider_model_ids()` 拿 curated + live /v1/models 合并列表

2. **Section 2 — 内置但有 env 覆盖的**（少见）

3. **Section 3 — `providers:` 字段**（v12+ 新 schema，键值对）
   - 当前环境 `providers: {}`（空）
   - 所以这一段没产出

4. **Section 4 — `custom_providers:` 字段**（legacy 列表）
   - 当前环境：
     ```yaml
     custom_providers:
       - name: V2enby.aicodee.com
         base_url: https://v2enby.aicodee.com/v1
         api_key: sk-290...6e18
         model: MiniMax-M3
     ```
   - 这一段会按 `(api_url, credential_identity, api_mode)` 分组
   - **关键**：`fetch_api_models(api_key, api_url)` 会**覆盖** entry 里的 `model` 字段

## v2enby 中转在 QQbot 列表里的真实表现（实测）

直接调 `list_picker_providers(max_models=5)`（QQbot fallback 路径）的输出：

```
count: 10
1. OpenRouter        slug=openrouter         is_current=True   models=[claude-opus-4.8, ...]  total=23
2. Nvidia            slug=nvidia             is_current=False  models=[yi-large, ...]         total=119
3. Ollama Cloud      slug=ollama-cloud       is_current=False  models=[qwen3.5:397b, ...]     total=40
4. Nous Portal       slug=nous               is_current=False  models=[step-3.7-flash, ...]   total=22
5. Google            slug=gemini             is_current=False  models=[3.1-flash-lite, ...]   total=11
6. GitHub Copilot    slug=copilot            is_current=False  models=[claude-opus-4.7, ...]  total=10
7. Z.AI              slug=zai                is_current=False  models=[glm-4.5, ...]          total=7
8. MiniMax (minimaxi.com)  slug=minimax-cn   is_current=False  models=[MiniMax-M3, M2.7, ...]  total=5
9. V2enby.aicodee.com      slug=custom:v2enby.aicodee.com  is_current=False  models=[MiniMax-M2.1, M2.5, M2.5-highspeed]  total=5
10. DeepSeek        slug=deepseek           is_current=False  models=[deepseek-chat, deepseek-reasoner]  total=2
```

→ **V2enby 中转在第 9 位**，但用户视觉上感觉"看不到"是因为：
1. 排在最后（OpenRouter 抢了第 1 位 + `is_current=True` 标签）
2. **显示的 model 列表是错的** — config 配的是 M3，但 picker 显示 M2.1/M2.5/M2.5-highspeed（v2enby 端点 `/v1/models` 探测返回的目录）
3. `is_current=False`（因为 `current_provider` 被默认解析成 `openrouter`）

## 根因：`/v1/models` 探测覆盖 `custom_providers` entry 里的 `model` 字段

`model_switch.py` section 4 的处理逻辑（`list_picker_providers` 注释里明确说）：

> "Prefer the endpoint's live /models list when credentials are available... so the picker never offers a model the user can't call."

→ 听起来很合理，但**用户的 `custom_providers` entry 是手动配的**，里面 `model: MiniMax-M3` 是用户**明确指定的主用模型**。live `/v1/models` 探测不应该**覆盖**这个字段，应该**合并**（live 目录 - 用户 config）才对。

代码位置：`model_switch.py` section 4（around line 1662-1669）：
```python
if api_url and api_key and discover:
    try:
        from hermes_cli.models import fetch_api_models
        live_models = fetch_api_models(api_key, api_url)
        if live_models:
            models_list = live_models  # ← 这里直接覆盖了 entry.model
    except Exception:
        pass
```

→ 这是 picker 的一个**行为 bug**，不是配置问题。

## 修复方案（待确认）

A. **修 picker 行为**（推荐）— 改 `model_switch.py` section 4：`live_models` 不覆盖，只补充（live ∪ entry.model）保持 entry.model 在第一位
B. **绕过 picker** — 用户手动 `/model MiniMax-M3 --provider custom:v2enby.aicodee.com`
C. **改 config schema** — 把 `custom_providers` 改成 v12+ 的 `providers:` 字段形式（section 3 处理逻辑可能不一样，待验证）

A 改一处，20 行内，验证后可以 PR 上游。

## 复现命令

```bash
cd ~/.hermes/hermes-agent && source venv/bin/activate
python3 -c "
import sys; sys.path.insert(0, '.')
from hermes_cli.model_switch import list_picker_providers
from hermes_cli.config import load_config, get_compatible_custom_providers
cfg = load_config()
cp = get_compatible_custom_providers(cfg)
result = list_picker_providers(
    current_provider='custom',  # ← 用 config.yaml 实际值
    current_base_url='https://v2enby.aicodee.com/v1',
    current_model='MiniMax-M3',
    user_providers=cfg.get('providers'),
    custom_providers=cp,
    max_models=50,
)
for r in result:
    print(f\"  {r['name']!r} slug={r['slug']!r} is_current={r.get('is_current')} models_count={len(r.get('models', []))}\")
"
```

## 关联坑

- **`current_provider` 默认值**：gateway `_handle_model_command` 里 `current_provider = "openrouter"`（fallback），但 `model.default` 实际可能是 `custom` 或别的。→ 任何 picker 调用都先传 `cfg['model']['provider']` 真实值
- **Q1 行为差异**：Telegram/Discord 走 `list_picker_providers`（用 inline keyboard，只显示前 max_models 个），QQbot 走 `list_authenticated_providers`（纯文本列表，全部展开）
- **`is_user_defined` 决定是否显示空 models 行**：custom endpoint 即使 models 为空也保留，built-in 空 models 会被 `list_picker_providers` 过滤掉

## 教训（写进 proactive-execution 规则 14）

**用户报 UI bug 时，grep config 只能验证"字段在不在"，验证不了"用户能不能用"。**
**必走"调渲染函数 + 对比实际输出"流程，不要省这一步。**
