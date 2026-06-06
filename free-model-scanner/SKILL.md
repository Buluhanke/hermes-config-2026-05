---
name: free-model-scanner
description: 自动扫描 ~/.hermes/.env 里所有配置的 LLM provider（OpenRouter / v2enby / Gemini / GLM / DeepSeek / Groq / Cerebras / Nvidia NIM 等），探测 key 有效性 + 列出可用模型 + 实测强候选是否能正常回复。覆盖"做减法前哪些真能打"的全盘审计场景。
triggers:
  - 扫描模型
  - 哪些模型能用
  - 找可用模型
  - 探测 provider
  - 模型可用性审计
  - provider扫描
  - 哪些 key 失效了
  - 推荐备用模型
---

# 全 Provider 模型可用性审计

## 适用场景
- 用户说"现在哪些模型还能用""做减法前先盘点""哪个 provider 还活着"
- 配置了多个 LLM key，需要先验证再决定留哪些
- 准备做"主模型 + fallback"切换前的健康盘点

## 一次扫描覆盖的 9 家 provider（按本环境 .env 实际配置）
1. **v2enby (aicodee)** — anthropic 协议，主用接口
2. **OpenRouter** — 21+ 免费模型
3. **Google Gemini** — 直连，pro/flash 全系
4. **智谱 GLM** — 官方 + OR 双通道
5. **DeepSeek** — 直连
6. **Groq** — OpenAI 协议
7. **Cerebras** — OpenAI 协议
8. **Nvidia NIM** — integrate.api.nvidia.com
9. **Moonshot/Kimi** — 经 OR

## 工具
- **审计脚本**：`scripts/audit_all_providers.py`（替代旧的 `scan_free_models.py`，覆盖全 9 家）
- **历史实测数据**：`references/audit-results-2026-06-03.md`
- **2026-06-04 更新参考**：`references/audit-results-2026-06-04.md` — 21 OR 免费模型 + 119 NVIDIA 模型 + SSL 修复 recipe
- **2026-06-05 fallback 实战**：`references/audit-results-2026-06-05-fallback-debug.md` — 4 端点全死根因 + 真模型名规则（NV `deepseek-ai/` 前缀/OR `provider/model` 格式/OR 免费档 1361 tokens 永久限额/OR 列表 API IncompleteRead）+ 4 端点实测脚本
- **Picker 行为参考**：`references/hermes-picker-behavior.md` — `/model` 列表 4 段渲染机制、`/v1/models` 探测覆盖 `custom_providers.model` 的 bug、v2enby 中转在 QQbot 列表的真实位置（2026-06-04 实测）

## 标准审计流程（4 步）

### 1. 抓 .env 里的 key 和 base_url
```python
env = {}
with open(os.path.expanduser("~/.hermes/.env")) as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env[k] = v
```
匹配模式：`*_API_KEY` / `*_BASE_URL`

### 2. 探测每个 provider 的可用模型
- **OpenRouter**: `GET https://openrouter.ai/api/v1/models` → 过滤 `:free`
- **Gemini**: `GET .../v1beta/models?key={KEY}` → 过滤 `generateContent` 能力
- **GLM**: `GET {GLM_BASE_URL}/models`
- **其他 (v2enby/Groq/Cerebras/Nvidia/Moonshot)**: `GET {base}/models` 走 OpenAI 协议

### 3. 实测强候选（用最小 prompt "1+1=几?只回数字"）
**关键陷阱**：
- 推理型模型（nemotron-super、gpt-oss）的 content 走 `message.reasoning`，不要只读 `content`
- Gemini 2.5/3 flash 系列可能返回 `content: {}`（safety 拦截），用 `parts[0].text` 鲁棒提取
- 限流 429 ≠ 永久失效，等几秒重试
- 余额不足 1113 ≠ key 失效，是资源包空
- **SSL 错误通常是 Mac 网络代理或 key 被改**。macOS 自带 Python 的 cert chain 经常不全，urllib 会抛 `SSL: CERTIFICATE_VERIFY_FAILED`，连请求都发不出去。**修复（实测可用）**：
  ```python
  import os, certifi
  os.environ["SSL_CERT_FILE"] = certifi.where()
  os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()
  ```
  注入这两行后再跑 urllib 调用即可。如果连 certifi 都没有：`/Applications/Python\ 3.XX/Install\ Certificates.command` 跑一下，或 `pip install certifi`。注意：脚本在 `~/.hermes/.env` 里加 key 不够，`load_env()` 只是 `os.environ.setdefault` — 如果当前进程已经 import 过 `ssl`，还得显式重设上面的变量。

### 4. 输出三档分类
```
🟢 真能打 — 推荐用
🟡 凑合能用 — 兜底
🔴 失效/不要碰 — 从 config 删
```

## Fallback 触发失败的诊断（2026-06-05 实战新增）

**核心区分**：用户报 "fallback 没起作用" 时，**两类失败**诊断路径完全不同。

| 现象 | 真实原因 | 诊断命令 | 修复路径 |
|---|---|---|---|
| 日志里**没有** `switching to fallback` 字样 | 框架**根本没触发** fallback（503 重试 3 次后直接挂）| `grep "switching to fallback" ~/.hermes/logs/gateway.log` | 配 `model.fallback_chain` / `fallback_on_status` / `fallback_on_timeout` |
| 日志里有 `switching to fallback` 但**全部失败** | **chain 端点本身死的**（4 个里 3 个 404/402/400）| `grep -A 5 "switching to fallback" ~/.hermes/logs/gateway.log` 看每个 chain 端点错误码 | 重测每个端点 + 换真模型名 |

**4 端点全死常见根因速查**（详细见 `references/audit-results-2026-06-05-fallback-debug.md`）：
- NV 端必须 `deepseek-ai/` `nvidia/` `qwen/` `meta/` 前缀（裸名 → 404）
- OR 端必须 `provider/model` 格式（裸名 → 400 `is not a valid model ID`）
- OR `gpt-oss-120b` 免费档账户**永久 1361 token 限额**（大请求必 402），**不要进 fallback 链**
- NV 端冷启动 12-15s，`fallback_on_timeout` 必须 ≥ 18s

**诊断第一步**永远是 `grep -A 5 "switching to fallback" gateway.log` 看 chain 切过去后的具体错误码，**不是** `hermes config show` 看 chain 有没有配。

## Pitfalls
- **不要把"key 存在"和"模型能用"混为一谈**。DeepSeek key 在但 401，Groq key 在但 SSL 断。
- **provider 协议不一**：v2enby 用 anthropic（`x-api-key` header + `/v1/messages`），其他都用 OpenAI 协议（`Authorization: Bearer` + `/chat/completions`）。脚本要分支处理。
- **模型 vs 资源包**：GLM 4.5-air 免费，4.5/5/5.1 收费资源包耗尽是常态。区分 free/paid 模型。
- **quota 限流有规律**：Gemini Pro 几乎一定是 quota 满，flash 可能被 safety 拦，OR 大模型 429 是上游 provider 限流（不是 OR）。
- **不要每次都重跑**：审计 9 家 × 20+ 模型 ≈ 1-2 分钟，调度跑。日常单点探测用 `curl` 即可。
- **本环境的真实可用池**（2026-06-04 实测，更新自 2026-06-03）：
  - 主力：v2enby MiniMax-M3
  - **OpenRouter 免费档 21 个模型**（key 正常，0 限流可全用）
    - 推理/通用强候选：openai/gpt-oss-120b:free (131K)、nvidia/nemotron-3-super-120b-a12b:free (1000K)、nousresearch/hermes-3-llama-3.1-405b:free
    - 长上下文：qwen/qwen3-coder:free (1049K)、nvidia/nemotron-3-super-120b-a12b:free (1000K)
    - 中文：moonshotai/kimi-k2.6:free (262K)、z-ai/glm-4.5-air:free (131K)
    - 编码：qwen/qwen3-coder:free
  - **NVIDIA build.nvidia.com 119 个模型全部免费档**（月 1000 credits，跟 OR 完全不重叠）
    - 顶级：qwen/qwen3.5-397b-a17b、qwen/qwen3-coder-480b-a35b-instruct、nvidia/nemotron-3-super-120b-a12b、openai/gpt-oss-120b
    - 轻量快：nvidia/nemotron-3-nano-30b-a3b、deepseek-ai/deepseek-v4-flash
  - **Nous Portal（Hermes 官方）1 个**：stepfun/step-3.7-flash:free
  - 兜底：Gemini 2.5-flash-lite
  - 死的：DeepSeek（401，key 失效）、Cerebras（403 Cloudflare ban，key 没绑）

## 用户偏好（写入 skill 而非 memory）
> "做减法"思维 — 加新 provider 前先审计旧的；列推荐清单 ≠ 执行令；不绑定任何特定模型。
> 审计结果输出要三档分类，不要只给数字。
> **扫描完只汇报，不自动接 fallback 链**。本次明确表态"不用"，规则：除非用户主动说"接上/配进去"，否则扫描结果 + 推荐位 + 一句"要不要接"问句就停，**不要列执行令直接改 config.yaml**。

## Agent 触发守则 (2026-06-05 14:50 用户硬规则)

- 本 skill 在用户**主动说**"扫描/盘点/找可用模型/做减法"时调用 — 输出三档分类
- **agent 自身不要主动调用** (即使触发词匹配), 因为模型配置是用户私有资产 (见 script-provider-independence "已知案例" 段)
- agent 自己写配置/代码/脚本时, **不能**因为本 skill 存在就引入具体 model= / api_key= / provider= 值
- 唯一例外: 用户明确说"用 Ollama 本地模型 + 写死"才允许

## 关联技能
- **script-provider-independence** — 父级原则：cron 脚本里不能硬编码 provider
- **provider-connectivity-diagnostics** — 父级诊断和切换流程
