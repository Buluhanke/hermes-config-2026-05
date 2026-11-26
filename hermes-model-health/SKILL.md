---
name: hermes-model-health
description: "模型不可用诊断（零绑定·手动切换）。Use when 模型消失/报错/404/402。"
version: 2.0.0
author: Hermes Agent
license: MIT
platforms: [macos, linux]
triggers:
  - 模型消失
  - 模型不肯用
  - 模型报错
  - 模型不可用
  - model unavailable
  - HTTP 402
  - HTTP 404 free
  - can only afford
---

# Hermes 模型不可用诊断（零绑定版）

## 0. 铁律先行（覆盖旧版全部自动切换描述）

用户铁律：**不绑定任何模型——给什么模型就用什么模型；失效时手动切换，不自动兜底。**

| 禁止（发现即清） | 不算违规（别误删） |
|---|---|
| `hermes fallback add/set`、非空 `hermes fallback list` | `config.yaml` 里 `auxiliary.{vision,compression,approval,title_generation,web_extract}.fallback_chain`（辅助任务备用链，与主模型无关） |
| `fallback_providers` 非空、`fallback_model` 固定绑定 | 名字含 fallback 但属抓站/备份的脚本：`broadcast_fallback.py`、`hermes_terabox_fallback.md` |
| cron job 带 `pinned` / `model` 字段 | `moa` 预设里 `enabled: false` 的 `reference_models` |
| `model_health_daemon.py` / `model_router.py` 进程或自动轮替守护脚本 | —— |

清空命令是交互式的：`printf 'y\n' | hermes fallback clear`，之后必须 `hermes fallback list` 与 `hermes config get fallback_providers` 复验为空。**本技能绝不重建 fallback 链、不启动守护进程、不逐个 cron 改模型。**模型失效只产出「候选可用 slug + 证据」，由用户手动切主链。

## 1. 诊断顺序（按速度）

```
1. 网关活着吗：curl -s --max-time 5 http://127.0.0.1:8642/health  （8642 是正确端口，18789 是错的）
2. 零绑定巡检：hermes fallback list / hermes config get fallback_providers / ps aux | grep -Ei 'model_health|model_router|fallback' / hermes cron list 查 pinned
3. custom_providers 是否为 dict（list 会让全部 provider 静默失效）
4. provider key 是否被遮罩 / 余额是否耗尽
5. 实时探测可用 slug（唯一判定标准，不信静态清单）
```

配置读写：`~/.hermes/config.yaml` 是受保护安全配置，`patch`/`write_file` 会拒写。改配置走 `hermes config set/unset`，改完 `hermes config check` 校验 + `search_files` 复核。

## 2. custom_providers 结构致命陷阱

```bash
python3 - <<'PY'
import yaml, os
p=os.path.expanduser('~/.hermes/config.yaml')
cfg=yaml.safe_load(open(p))
cp=cfg.get('custom_providers',{})
print('type:',type(cp).__name__,'keys:', list(cp) if isinstance(cp,dict) else 'BROKEN')
PY
```
必须是 dict；list 会让所有 provider 静默失效。转换后写回要用 `hermes config set` 或经用户确认，勿绕过安全配置保护。

## 3. key / 余额检查

- `curl` 在 terminal 常被政策拦截（超时 28 或拒接）；优先 `execute_code` + `http.client`。
- `.env` 里 `sk-...87b6` 这类**遮罩值**不是真 key：`len<30` 或含 `...` 即遮罩。检测时只打印长度/状态，禁止打印 key 本身。
- `HTTP 402` = 余额不足；`404 requires available credits` = 付费档无余额（与免费池无关）；`401` = key 无效/过期；`403 region` = 区域限制。

## 4. 实时探测可用 slug（唯一判定标准）

免费池天天变：旧的 `hy3:free`/`solar-pro4:free` 会下线，新 `:free` 持续上架。**不要据记忆中的清单断言「免费档全结束」**。

配方：从 `.env` 读 key（不打印）→ GET `https://inference-api.nousresearch.com/v1/models` 取 `data[].id` 过滤 `:free` → 逐个 POST `/v1/chat/completions` → 记录 HTTP 状态/耗时/回答文本；OpenRouter 同理走 `https://openrouter.ai/api/v1/credits` 与 chat 端点。

**探针铁律（防误判）**：reasoning 模型 `max_tokens` 太小时 token 全花在思考上，`message.content=null`、正文在 `reasoning_content`/`reasoning_details`——按「content 空=失败」会把可用模型误判失效。探针 `max_tokens>=200`，或判 `content`/`reasoning_content` 任一非空即成功。HTTP 200 却解析出 `NoneType` 时先打印原始响应体再下结论。

## 5. 常见错误码

| 错误 | 含义 | 处理（只报告，不自动改） |
|---|---|---|
| `HTTP 402` | 余额不足 | 报告，建议用户换 `:free` slug 或充值 |
| `404 unavailable for free` | OpenRouter `:free` slug 下线 | 报告同名付费 slug 供用户手动切 |
| `404 requires credits` | Nous 付费档无余额 | 实时拉免费池给候选，勿据旧清单判定 |
| `400 missing tags` | Nous 免费 slug 需特殊参数 | 换其他 slug，不硬凑参数 |
| `SSL CERTIFICATE_VERIFY_FAILED` | 系统 CA 问题 | 用 venv Python 而非系统 Python |
| `403 Forbidden` | key 过期/权限 | 报告需更新 key |
| `Connection refused` | provider/OmniRoute 挂了 | 报告并等恢复；`curl --max-time 3 http://localhost:20128/health` 查 OmniRoute |

## 6. 交付格式

只输出：诊断结论 + 实测证据（HTTP 状态/时间戳/PID）+ 候选 slug 列表 + 「请手动切换」一句话。不写 fallback 配置、不启守护进程、不 pin cron。

## 版本历史

- v1.0.0：含 fallback 链修复与 model_health 自愈守护架构（已被用户铁律否决）。
- v2.0.0（2026-11-26）：整篇重写为零绑定诊断版，删除所有自动切换/守护进程指令，保留并强化实时探测、探针防误判、遮罩 key 检测；`references/health-monitoring.md` 同步降级为废弃架构说明。
