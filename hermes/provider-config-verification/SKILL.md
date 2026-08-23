---
name: provider-config-verification
version: 1.0.0
description: "用真实 HTTP POST 自检 Hermes provider/model 是否真可用。触发：自检模型设置。"
triggers:
  - 模型设置都错了吗 / 模型配置检查
  - 自检本机所有 provider 可用性
  - auxiliary / moa 失效排查
  - OpenRouter 403 region / 国内网络 provider 不通
  - custom_providers 结构是否正确
  - 验证 API key / 端点是否真能用
created_by: agent
tags: [hermes, config-audit, provider-verification, openrouter, nous, cn-network]
---

# Provider Config Verification

诊断 Hermes 的模型/provider 配置时，**永远用真实 HTTP 请求验证，不要读 config 猜"应该能用"**。本机会话里一个 provider 在 config 写得再对，也可能因为地区封锁、key 失效、模型下线而全挂。

## 核心原则

1. **实测优先**：对每个 provider 发一个最小 `/chat/completions` POST（messages 一句话，max_tokens 小），看真实 status code。不要靠 `config.yaml` 里的名字判断。
2. **curl 在 terminal 里可用**：直接 `curl -X POST .../chat/completions` 即可执行（安全扫描可能标 HIGH 但 `smart approval` 自动放行，不真拦）。旧文档称 curl 被 hardline 拦截已过时；curl 与 Python `http.client` 二选一，curl 更短。
3. **主模型 ≠ 全部配置**：主模型走 `model.base_url`+`model.api_key`（独立于 `custom_providers`）所以主对话正常，不代表 fallback/auxiliary 也正常。

## 实测诊断流程

```bash
# 1) custom_providers 结构（list 还是 dict 都合法，见下）
python3 -c "import yaml;c=yaml.safe_load(open('~/.hermes/config.yaml'));print(type(c.get('custom_providers')).__name__)"

# 2) 跑真实探测脚本（见 scripts/verify_providers.py）
./venv/bin/python3 /Users/aimac/.hermes/diag_providers.py
```

## ⚠️ CN 网络致命坑：OpenRouter 地区封锁

机器在中国大陆 IP 时，OpenRouter 上几乎所有模型返回 **`403 This model is not available in your region`**。这会让：
- `auxiliary.vision/web_extract/compression/approval/title` 全部静默失效（每轮对话都在用的后台）
- `moa` 聚合层（reference + aggregator 走 openrouter 上的 claude-opus-4.8 / gpt-5.5）全部失效
这比 fallback 失效影响面大得多——fallback 只在主模型挂时才用，auxiliary 是常驻。

**已实测可用的替代通道（2026-08-02）**：
- Nous Portal：`https://inference-api.nousresearch.com/v1/chat/completions`，model `tencent/hy3:free`，key 用 `NOUS_API_KEY` → **200 OK**（免费版有速率限制，监控 429）
- 主模型自有通道 `123.56.67.77:9100` → MiniMax-M2.7-highspeed → **200 OK**

把失效的 auxiliary/moa 改到 Nous 即可复活（不碰 fallback、不动 custom_providers）。

## custom_providers 结构（旧 skill 已过时）

早期 skill 说"`custom_providers` 必须是 dict，写成 list 全部 provider 静默失效"——**已过时**。当前代码 `hermes_cli/config.py` 的 `get_compatible_custom_providers`（约 L1561）与 `model_switch.py:124` **接受 YAML list 格式**，用户写成 list 完全合法、主模型正常工作。判断结构正确性以 `config.py` 源码为准。

## 常见 endpoint 错误码速查

| 错误码 | 含义 | 方向 |
|--------|------|------|
| 200 | 正常 | — |
| 401 Invalid API Key | key 无效/名字不匹配 | 核对 api_key_env 指向的 env key |
| 402 reject_no_credit | 账户余额=0（反滥用） | 充值或换免费模型 |
| 403 region | 地区封锁（CN→OpenRouter） | 换 Nous / 本地通道 |
| 403 Forbidden | 账户无权用该模型 / key 错 | 换模型或 key |
| 403 code 1009 | 端点拒绝（区域/模型不存在） | 换模型名 |
| 404 invalid_model / page not found | 模型名在该端点不存在 | 核对模型 id |
| Timeout | 网络抖动或端点不可达 | 重试一次，再判死 |

## 平台实际模型路由审计（audit.db 才是真相）

config 里的 `model.default` / `provider` 只是**全局默认**，不保证每个平台真走它。平台级路由可能把流量导到别的 provider（见 2026-08-07 QQ 机器人实测：default 是 `tencent/hy3:free`，但实际 735+ 次调用都走了 `custom:123.56.67.77:9100` 的 MiniMax）。要确认某平台到底用了什么模型，**查审计库**：

```bash
python3 ~/.hermes/skills/hermes/provider-config-verification/scripts/audit_platform_models.py qqbot
# 不传参 = 列出所有平台的 provider/model 分布
```

审计库路径：`~/.hermes/plugins/audit_to_db/data/audit.db`，关键表 `api_calls` 字段：`platform, provider, model, timestamp`。这是判断"XX 平台现在跑的啥模型"的唯一权威来源——比读 config 可靠。

## ⚠️ Nous Portal `/v1/models` 拉模型列表不可靠

Nous Portal 的模型枚举端点（`inference.nousresearch.com/v1/models` 与 `portal.nousresearch.com/v1/models`）实测会落到 **Vercel Security Checkpoint（HTML 401/429）** 或 **连接超时（HTTP 000）**，拿不到 JSON 列表。不要靠它枚举可用模型：
- 列可用模型：以 `config.yaml` 里 `custom_providers` / `model` 段为准。
- 列某平台实际用量：用上面的 audit.db 审计脚本。
- 验证某 key 是否活：**直接发 `/v1/chat/completions` POST 看 status code**（200=活，401=key 失效，000=网络/CN 封锁，429=限流但端点活着）。

## 注意：无效冗余字段

`config.yaml` 里 `streaming: {enabled: false}` 是**无效字段**——真正生效的是 `display.streaming`（cli.py:4291）。顶层那条没被读，留着无害，但不代表关了流式。
