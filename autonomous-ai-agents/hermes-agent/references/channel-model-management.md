# 渠道模型管理

## 核心约束

**Hermes 没有 per-channel 模型配置**。所有消息渠道（QQ、微信、Telegram、Discord 等）共享同一个 gateway 进程，使用同一个全局 `model.default`。

```
config.yaml → model.default (全局) → gateway 进程 → QQ / 微信 / Telegram / ...
```

没有单独的 model override 字段 —— 不能单独给 QQ 设 A 模型、给微信设 B 模型。

## Auth-to-Enable Pipeline（关键认知缺口）

**授权 ≠ 启用**。这是最常见的困惑来源。

### 完整链路

```
Web Portal / hermes auth / .env  ← 授权层（认证通过）
         ↓
credential pool 显示已认证       ← 确认层（key有效）
         ↓
model.default 未更改 ✗           ← 启用层（实际使用）
         ↓
需要显式设置 model.default        ← 激活（见下方）
```

### 「授权已完成，但模型没在跑」—— 诊断

| 现象 | 根因 | 解决 |
|------|------|------|
| Portal/`hermes auth` 显示 DeepSeek 已认证，但对话还是 MiniMax | `.env` 有 `DEEPSEEK_API_KEY`，但 `config.yaml` 的 `model.default` 还是旧模型 | 改 `model.default` |
| CLI `/model` 能看到 DeepSeek 模型列表 | provider 已认证，模型可查询 | 同上 |
| QQ/微信发消息还是旧模型 | gateway 进程加载的是旧 `model.default` | 改配置 + 重启 gateway |

### 正确的「启用」操作

三种方式，按使用场景分：

**方式 A：临时切换（仅当前 CLI 会话）**
```
/model deepseek-v4-flash
```
当前会话立即生效，新开会话恢复 `config.yaml` 的默认值。

**方式 B：持久切换（全局默认 + gateway 所有渠道）**
```
# 1. 改 config.yaml
hermes config set model.default deepseek/deepseek-v4-flash

# 2. 重启 gateway（让 QQ/微信/Telegram 等走新模型）
ps aux | grep "hermes.*gateway" | grep -v grep | awk '{print $2}' | xargs kill
```

**方式 C：CLI 指定模型启动**
```
hermes chat --provider deepseek --model deepseek-v4-flash
```

### 各类 provider 的授权方式

| Provider | 授权方式 | 写入位置 |
|----------|---------|---------|
| DeepSeek | API key | `DEEPSEEK_API_KEY` → `.env` |
| MiniMax | API key | `MINIMAX_API_KEY` / `MINIMAX_CN_API_KEY` → `.env` |
| OpenAI | API key / Portal OAuth | `OPENAI_API_KEY` → `.env` / `auth.json` |
| Google Gemini | Portal OAuth | `auth.json` (webauth token) |
| Nous Portal | OAuth 网页授权 | `auth.json` |
| GitHub Copilot | `gh auth` / `hermes auth` | `auth.json` (OAuth token) |

### 关键原则

- **Web Portal / `hermes auth` 只负责「开账户」，不负责「选模型当默认」**
- 新模型授权后，必须手动设置 `model.default` 才能在任何渠道实际使用
- QQ/微信/Telegram 等所有消息渠道共享同一个 `model.default`，没有 per-channel 单独配置

## 如何切换某个渠道的模型

唯一的方案：改全局 default → 重启 gateway。

```bash
# 1. 修改 config.yaml
# model.default: minimax-cn/MiniMax-M2.7

# 2. 重启 gateway
ps aux | grep "hermes.*gateway" | grep -v grep | awk '{print $2}' | xargs kill
```

gateway 如果带 `--replace` 参数会自动拉起，不需要手动启动。

**注意**：
- 重启后所有渠道都会切换到新模型，无法只影响某一个渠道
- 当前对话（未结束的 session）可能因 gateway 重启而断开，用户需要重新发消息触发新 session
- QQ `/new` 指令会重置为新 session，但模型仍用 config.yaml 的全局默认值

## 判断当前各渠道使用哪个模型

| 检查方法 | 说明 |
|----------|------|
| `cat ~/.hermes/config.yaml \| grep "default:"` | 全局默认模型 |
| `cat ~/.hermes/config.yaml \| grep -A 10 "fallback_model"` | 降级链条 |
| 任意渠道 `/model`（新对话） | 显示当前 session 的模型 |
| 重启 gateway 后发条消息 | 确认新模型生效 |

## Nous Portal（hermes网页端）

"hermes网页端" 指的是 **Nous Portal** (https://hermes-agent.nousresearch.com/portal) —— 这是 Hermes 的官方 Web 管理界面，支持：
- OAuth 授权（Google Gemini、xAI、Qwen 等）
- 显示已授权的 provider 和 key 状态
- API key 管理入口

Portal 上授权的 provider 最终会写入 `~/.hermes/.env` 作为环境变量。DeepSeek 是普通 API key（`DEEPSEEK_API_KEY`），不走 OAuth，但可以在 Portal 上填写 key。
