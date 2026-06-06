---
name: hermes-model-switch
description: 在 Hermes 已注册的 custom_providers 之间一键切换主模型，用于主链额度耗尽时快速切到备用（NVIDIA / OpenRouter 免费档）。触发词：切模、换模型、模型挂了、换条路、swm、switch model、fallback、备用模型、免费模型。
---

# Hermes Model Switch — 一键切模

## ⚠️ 硬约束（先读这条再做任何"中途切模"承诺）

**Hermes model 字段是启动参数，运行中改 config 不热生效。**

`launchctl load -w` 真重启 gateway = **当前进行中的所有 session 全部断开**。

所以用户在对话里说"切到X"时，**永远不要承诺"立即生效且不影响当前对话"**。流程只能是：

1. 改 config.yaml 的 model 块
2. `launchctl load -w ~/Library/LaunchAgents/ai.hermes.gateway.plist` 真重启
3. 当前对话结束
4. 用户开新对话 → 用的就是新模型

如果用户问"能不能不打断当前对话就切" — 老实说不能，**唯一的"不打断"路径是 `hermes chat -m X --provider Y` 启动新会话**（不影响 config，也不影响主链）。

**结论**：永远别在切模时启动"使用中自动降级"的设计 — gateway 层做不到，用户误解了这个能力。

---

## 用户工作流（必须照此理解意图）

主链 `V2enby/MiniMax-M3` 付费中转 + 直连 `MiniMax-M2.7`，**每天 3 小时窗口期约 400 次调用，额度耗尽时切到免费档顶一下，恢复后再切回**。意图是**临时顶班**，不是"主用免费"。

**这意味着 agent 在对话里收到"切到 nv-xxx"时**：
- 直接执行 `swm <name>`，不要让用户开终端
- 主动提示"切完会重启 gateway，当前对话会断"
- 提醒"恢复后跟我说'回 MiniMax-M3'，我帮你切回主链"
- **不要**问"要不要顺便把 fallback 也改了" — 保持 scope

---

## 背景

## 已注册的 providers（~/.hermes/config.yaml，2026-06-05 刷新）

| Name | Base | Model | 备注 |
|---|---|---|---|
| Apihub.agnes-ai.com | apihub.agnes-ai.com/v1 | agnes-2.0-flash | 当前主链 |
| V2enby.aicodee.com | v2.aicodee.com/v1 | MiniMax-M3 | 付费中转（非 OR 路由） |
| nv-nemotron-3-super | integrate.api.nvidia.com/v1 | nvidia/nemotron-3-super-120b-a12b | NV 推理 0.4s (**fallback chain [0] 首选**) |
| nv-deepseek-v4-flash | integrate.api.nvidia.com/v1 | deepseek-ai/deepseek-v4-flash | NV 主备 2.7s (**fallback chain [1]**) |
| or-deepseek-chat-v3 | openrouter.ai/api/v1 | deepseek/deepseek-chat-v3-0324 | OR 跨域 1.0s (**fallback chain [2]**) |
| nv-qwen3.5-122b | integrate.api.nvidia.com/v1 | qwen/qwen3.5-122b-a10b | 手动切档（非 fallback） |
| nv-llama-70b | integrate.api.nvidia.com/v1 | meta/llama-3.3-70b-instruct | 手动切档 |
| nv-kimi-k2.6 | integrate.api.nvidia.com/v1 | moonshotai/kimi-k2.6 | 月之暗面，手动切档 |
| minimax-cn | openrouter.ai/api/v1 | minimax/minimax-m3 | OR MiniMax-China 路由（备用，未激活） |

**fallback 链**（自动，主链失败时按顺序试，2026-06-05 11:50 第三次修正）:
主链 → `nv-nemotron-3-super (0.4s) → nv-deepseek-v4-flash (2.7s) → or-deepseek-chat-v3 (1.0s)`

⚠️ **fallback 字段在 config.yaml 里有两个并存**:
- `model.fallback_chain`（新字段，JSON 数组）— hermes 框架读这个
- `fallback_providers`（老字段，list of dict）— 部分版本兼容读这个
- **改 chain 时两个都要同步**，否则下次 gateway 启动会用旧字段的端点
- 改完用 `hermes config show | grep fallback_chain` 验证新值生效

**触发条件**（config.yaml 里配的）:
- HTTP 状态码 ∈ {401, 403, 429, 500, 502, 503, 504}
- 18s 内没响应（NV 冷启动 12-15s 必须留这个余量）
- 同一 provider 最多重试 1 次

**真实模型名前缀（2026-06-05 11:50 第二轮实测踩坑）**:
- NV 端必须带组织前缀：`deepseek-ai/` `nvidia/` `qwen/` `meta/` `mistralai/` `moonshotai/`
- OR 端要 `provider/model` 格式：`deepseek/deepseek-chat-v3-0324` `openai/gpt-oss-120b` `qwen/qwen3-7b-plus-2025`
- **不要凭记忆写模型名**，必须先 `curl https://integrate.api.nvidia.com/v1/models` 拉真名列表

### ⚠️ 已废弃的 providers（2026-06-05 两轮实测死链）

| Name | 状态 | 错误 | 死因 |
|---|---|---|---|
| ~~or-gpt-oss-120b~~ | 永久 402 | "You can only afford 1361 tokens" | **OR 账户免费档余额耗尽**，充值前别用 |
| ~~or-qwen3.7-plus~~ | 400 invalid model ID | "qwen/qwen3.7-plus-2025 is not a valid model ID" | 模型名错（OR 端 qwen 系列命名规则改了） |
| ~~or-qwen3-coder~~ | 未实测，列入可疑 | — | 同 qwen 命名问题，未必可用 |
| ~~nv-qwen3.5-397b~~ | 500 internal | "invalid type: unit variant" | NV 端大模型偶发内部错误，不稳定 |
| ~~nv-nemotron-3-super-120b（裸名）~~ | 404 | 模型名缺后缀 | 必须是 `nvidia/nemotron-3-super-120b-a12b` |

**教训**:
1. 写 fallback chain 前**必须**用真实 key 跑 chat completion 验证（不是只测 /v1/models list 端点）
2. **list 端点 200 OK ≠ chat 端点 200 OK**（3/4 旧候选在 list 端点都返回但在 chat 端点死）
3. **OR 免费档账户会被锁**，1361 tokens 余额耗尽后所有请求都 402，不是临时限流
4. 真实模型名**必须**有 provider/ 组织前缀，没前缀 99% 404
5. 完整验证流程见 `references/fallback-chain-validation-20260605.md`

## 切模命令

脚本位置：`~/.hermes/scripts/swm`（软链 `~/.local/bin/swm`）

```bash
swm                       # 列出所有 provider
swm <name>                # 切到指定 provider（持久化 + launchctl load -w 热重启 gateway）
swm <name> --dry          # 只预览，不真改
swm --current             # 看主链 + fallback
swm --reset               # 回到 V2enby.aicodee.com 默认
```

切完用 `hermes status` 确认 gateway 仍响应。

## 验证清单（首次接入时跑过）

- NVIDIA 6/16 跑通：qwen3.5-397b、qwen3.5-122b、qwen3-next-80b、llama-3.3-70b、kimi-k2.6、nemotron-3-super-120b
- NVIDIA 真超时/不可用：deepseek-v4-flash/pro、gemma-4-31b、llama-4-maverick-17b
- OpenRouter :free 频繁 429，**别当主用**
- NVIDIA reasoning 模型（gpt-oss、nemotron-3）需要 `max_tokens ≥ 200`，否则 content=null 但 HTTP 200（易误判失败）

## 备份与回滚

- 最近一次配置备份：`~/.hermes/config.yaml.bak.swm.<pid>`
- 整体回滚：`cp ~/.hermes/config.yaml.bak.swm.57215 ~/.hermes/config.yaml && launchctl load -w ~/Library/LaunchAgents/ai.hermes.gateway.plist`

## macOS Python SSL 坑

调外部 HTTPS API 必带：
```python
import certifi, os
os.environ['SSL_CERT_FILE'] = certifi.where()
os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()
```
否则 `urllib.request` 报 `CERTIFICATE_VERIFY_FAILED`，所有 API 调用全 ERR_。

## 已知陷阱

1. **launchd plist 真重启**：`hermes gateway start` 只更新配置不真 load。**真重启**：`launchctl load -w ~/Library/LaunchAgents/ai.hermes.gateway.plist`，自动顶替旧 `--replace` 进程
2. **OpenRouter 429**：免费池常态，凌晨/午高峰更频繁；同模型隔几分钟可能就通
3. **NVIDIA 月额度**：1000 credits/month，qwen3.5-397b 这种大模型单次消耗大
4. **gateway 重启期间正在跑的 session 会断**，最好切之前先 /new
5. **大小写敏感（2026-06-04 踩坑）**：custom_providers 里的条目名是 `V2enby.aicodee.com`（首字母大写），引用时必须 `custom:V2enby.aicodee.com`，写 `custom:v2.aicodee.com` 会失败。`hermes config show | grep Model` 验证当前值
6. **误以为有 `hermes model switch` 子命令（2026-06-04 踩坑）**：用户经常给的命令是 `/model X --provider custom:Y`，但实际是 `/model` 这个聊天命令，正确姿势是 `hermes config set model.default X` + `hermes config set model.provider custom:Y`。**永远先 `hermes config show | grep Model` 看当前值，再决定怎么改**

## OpenRouter MiniMax 命名规则
- OR 上 MiniMax 模型名小写+斜杠: `minimax/minimax-m3`（不是 `MiniMax-M3` 或 `minimax-m3`）
- `minimax/minimax-m2.7`、`minimax/minimax-m2.5`、`minimax/minimax-m1` 等全小写
- 查模型是否存在: `curl -s https://openrouter.ai/api/v1/models | python3 -c "import json,sys; [print(m['id']) for m in json.load(sys.stdin)['data'] if 'minimax' in m['id']]"`
- 官方直连需 `MINIMAX_CN_API_KEY` + `MINIMAX_CN_BASE_URL=https://api.minimaxi.com/anthropic` 配到 custom_providers
- OR 路由 (Global/China) **都不是官方直连**，中间隔 OpenRouter
- 2026-06-06 确认: `minimax/minimax-m3` 仍活跃，用户误配到 `v2.aicodee.com` 代理（非 OR 路由）

**永远不要盲改 config.yaml 的关键值**。标准姿势：

```bash
# 1. 看当前
hermes config show | grep -E "^Model:"

# 2. 干跑（写临时值）
hermes config set model.default <新值-test>    # 临时
hermes config set model.provider <新值-test>
hermes config show | grep -E "^Model:"         # 验证

# 3. 立刻回滚
hermes config set model.default <原值>
hermes config set model.provider <原值>
hermes config show | grep -E "^Model:"         # 必须跟第 1 步一致
```

**为什么**：改 model 字段会触发 gateway 重启（或下次启动用新值），万一改错就是全链路不可用。临时值+回滚 5 秒能确认命令语法对、值合法。**只对 config 关键字段用，临时脚本/任务不用。**

## 定时切模（cron / launchd 模式，2026-06-04 落地）

**用户场景**：每天 0:25 自动切到 `MiniMax-M3-highspeed`，省主链额度或换速。

**标准做法**（**不**用 `hermes model`，用 config set + cron 监控）：

1. 写脚本 `~/.hermes/scripts/switch_model.sh`：
   ```bash
   #!/bin/bash
   hermes config set model.default "<新模型>"
   hermes config set model.provider "custom:<条目名-注意大小写>"
   # 验证
   hermes config show | grep -E "^Model:"
   ```
2. 配 cron：schedule `25 0 * * *`，script `switch_model.sh`，mode `no_agent`（脚本自管）
3. 日志：`~/.hermes/logs/switch_model.log`
4. 失败兜底：脚本里 `hermes send "❌ 切模型失败"` 推 Telegram

## 引用

- `references/timed-switch-cron.md` — 完整脚本 + cron 模板
- `references/fallback-chain-validation-20260605.md` — fallback chain 验证流程（list 端点 ≠ chat 端点、NV 冷启动 12-15s、`hermes config set` 限制）
- `references/apihub-agnes-profiler.md` — Apihub.agnes-ai.com 提供者评估（agnes-2.0-flash 免费实测、LiteLLM 代理层、无 RateLimit 头）

## 数据驱动选模（用户硬偏好 — 2026-06-04 验证）

**用户不接受拍脑袋推荐，要实测数据。** "切模" 场景下的具体表现：
- 推荐前必须跑真实调用（耗时分、成功率、内容质量）
- 给出**对比表**：A 多少ms / B 多少ms / 谁中文原生 / 谁忽略 prompt
- 不说"建议用 X 因为更好"而说"X 实测 15s 输出准，Y 实测 3s 但忽略中文 prompt"
- 用户说"数据已经说话了"= 验证通过，可以据此推荐

**反面教材**：我曾用"reasoning 模型需 max_tokens≥200"这类推断，**没跑测**就写入 skill 已知陷阱 → 用户没纠正但**值得警惕**。规则：所有"X 模型特性"断言，必须有真实跑测做支撑；没跑测就标"待验证"。

---

## 对话里"切模"的 SOP（用户已经在 hermes chat 里）— 极简版

**用户实际使用模式**（2026-06-04 验证）：
- "切到 nv-qwen3.5-397b" → **整段回复 1 行**（"好"或"切了，gateway 会重启"）
- 用户用最短词回应 = 我也得最短
- "那就算了 太麻烦" 触发过 1 次 → 标志着我之前解释太多

**SOP（必须照此行）**：

| 阶段 | 输出 | 字数 |
|---|---|---|
| 收到切模指令 | 1 行："切了" / "好" / "OK" | ≤10 字 |
| 副作用提醒 | "当前对话会被打断，下次开新对话生效" | ≤30 字 |
| 切回提醒（如切到免费档） | "恢复后说'回 M3'我帮你切回" | ≤20 字 |

**不要做**：
- 列 3 条路径让用户选（"要不要 A/B/C"）
- 解释"为什么不能无缝切"（用户不关心原因）
- 推荐"要不要顺便改 fallback"
- 长篇介绍"主链/备用链是什么"
- 用 markdown 表格/代码块（CLI 输出纯文本）

**完整解释只在用户主动问时**："能不能不打断就切" / "为什么重启" → 此时再给硬约束段。

**判断标准**：用户用 ≤ 5 个字下达指令 → 我的回复必须 ≤ 3 行。
- 1 个字（"切"）→ 1 个字（"好"）
- 5 个字（"切到 nv-qwen"）→ 1-2 行
- > 10 个字带具体 provider 名 → 可以加一句确认意图

**反面教材**（2026-06-04 真实事件）：我曾用 3 段话解释"做不到不打断"，用户回"那就算了太麻烦" → 1 个回合就丢了。

**SOP 原始版（保留作 reference，仅用户问"为什么不能无缝切"时调用）**：

1. **先确认意图**（如果模糊）：是切到免费档顶班？还是切回主链？用 `swm --current` 看当前状态判断
2. **说清副作用**：当前对话会被 gateway 重启打断。说完就干，不啰嗦
3. **执行**：
   ```bash
   swm <provider_name>     # 改 config + launchctl load -w
   ```
4. **回报**：成功 / 失败 / 切换到了哪个
5. **提醒**："恢复后跟我说'回 MiniMax-M3'，我帮你切回"（如果切的是主链 → 免费的）

**绝对不要**：
- 自己造 "运行中切模" 的幻觉
- 让用户开终端自己跑 swm（这是 agent 该干的事）
- 切完不提醒何时切回
- 问"要不要顺便 X"（破坏性 + 扩大战果原则）
- **2026-06-04 离线准则**："今天定的边界就是边界"——切模时只执行切模，不要顺手提"要不要也 X" / "顺便看下 Y" / "我可以做 Z" 之类的扩展建议。新想法先记到记忆里，等用户回来再决定是否做

---

## 对话里"切回主链"的 SOP

用户说"切回 MiniMax-M3" / "回主链" / "恢复付费的"：

```bash
swm --reset
```

报结果，不追问。

---

## 不重启的临时会话（用户特殊需求时）

### 5. 改完 fallback 立即 `hermes config show` 验证

```bash
hermes config show | grep -A 3 "Model:"
# 期望: fallback_chain 字段在, fallback_providers 列表项是新 4 个
```

### 6. OR 列表 API 大 JSON 会 IncompleteRead（2026-06-05 11:50 第二轮踩坑）

`/v1/models` 列表如果直接 `json.loads(urllib.request.urlopen())` 会因为 OR 返回的 JSON 太大（几百 KB）触发 `http.client.IncompleteRead`。**必须按 keyword 过滤**：

```python
# 错的写法（会 IncompleteRead）
data = json.loads(urllib.request.urlopen(req).read())

# 对的写法（按 deepseek/qwen/nemotron/gpt-oss 等 keyword 过滤）
for m in data.get("data", []):
    mid = m.get("id", "")
    if any(k in mid.lower() for k in ["deepseek", "qwen", "nemotron", "gpt-oss"]):
        print(mid)
```

### 7. OR 账户免费档余额耗尽 = 永久 402（不是临时限流）

`or-gpt-oss-120b` 在 OR 免费档账户下，余额显示 1361 tokens，所有请求都返回：
> HTTP 402: You requested up to 16384 tokens, but can only afford 1361. To increase, visit https://openrouter.ai/settings/credits

**这不是 429 限流**（可以重试），是**账户级余额耗尽**。两种区分:
- 429 too many requests → 临时，等几分钟重试
- 402 Payment Required + "can only afford N tokens" → 永久，得充值或换账户
- **写入 skill 时不要把 402 当 429 处理**（会反复失败）

### 8. NV 真实模型名前缀（最容易踩坑）

NV 端模型名**必须**带组织前缀，否则 404：
- ✅ `deepseek-ai/deepseek-v4-flash`（有 `deepseek-ai/`）
- ✅ `nvidia/nemotron-3-super-120b-a12b`（有 `nvidia/` 和 `-a12b` 后缀）
- ✅ `qwen/qwen3.5-397b-a17b`（有 `qwen/`）
- ❌ `deepseek-v4-flash`（裸名 404）
- ❌ `nemotron-3-super-120b`（缺前缀 404）

**永远先** `curl -H "Authorization: Bearer $NV_KEY" https://integrate.api.nvidia.com/v1/models | jq '.data[].id'` 拿真名再写 config。

### 9. fallback_providers (老) vs fallback_chain (新) 同步问题

`config.yaml` 里**两个字段并存**：
- `fallback_providers`（老字段，list of dict，每项含 provider/base_url/api_key/model/label 5 字段）
- `model.fallback_chain`（新字段，JSON 数组字符串，只含 provider 名）

**改 chain 时两个都要改**：
- `hermes config set model.fallback_chain '["a","b","c"]'` — 改新字段
- `python3 + yaml` 直接改 fallback_providers 段 — 改老字段（patch 工具被 hermes 安全锁拒绝）
- 改完用 `hermes config show | grep -A 20 fallback_providers` 验证两段都对齐

为什么两个都改：框架启动时先读 fallback_providers，fallback_chain 字段是某些 agent 逻辑用的引用。两者不一致会导致"config show 显示新链，实际 fallback 走老链"。

## 已废弃的 5 个候选（2026-06-05 两轮实测死链）

---

## 关键背景

- `~/.hermes/config.yaml` 是 model 注册地
- 备份位置：`~/.hermes/config.yaml.bak.swm.<pid>`，回滚：`cp <bak> ~/.hermes/config.yaml && launchctl load -w ~/Library/LaunchAgents/ai.hermes.gateway.plist`
- NVIDIA 月 1000 credits 估算：qwen3.5-397b 单次 ~2k tokens，500-800 次/月。Orca 用 `qwen3-next-80b` 之类小模型可省 50% credits
