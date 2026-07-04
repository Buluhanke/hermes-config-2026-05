# Hermes 渠道架构 — 6+ Messaging Platform 目录结构

## 真实在跑的渠道 (2026-06-26)

来源：`~/.hermes/gateway_state.json` 实时查询：

```bash
cat ~/.hermes/gateway_state.json | python3 -c "
import json, sys
d = json.load(sys.stdin)
for k, v in d['platforms'].items():
    if v['state'] == 'connected':
        print(f'  ✅ {k}')"
```

**实际连接** (本会话观察到):
- `qqbot` (QQ 机器人)
- `telegram`
- `weixin` (微信)
- `feishu` (飞书)
- `wecom` (企业微信)
- `discord`
- `api_server` (本地 HTTP API)
- `webhook` (入站 HTTP 回调)

## 22 个 PLATFORMS 元数据 (hermes_cli/platforms.py)

源代码：`~/.hermes/hermes-agent/hermes_cli/platforms.py` 第 18-44 行

**全部 22 个**:
```
cli / telegram / discord / slack / whatsapp / whatsapp_cloud /
signal / bluebubbles / email / homeassistant / mattermost / matrix /
dingtalk / feishu / wecom / wecom_callback / weixin / qqbot /
yuanbao / webhook / api_server / cron
```

**注意**: 22 个里很多是**预留 adapter**，不一定实配/连上。

## 渠道 Adapter 目录结构 (两套)

Hermes 有**两套**平台 adapter 目录：

### 套 1: `gateway/platforms/<name>/` (新, 推荐)
```
~/.hermes/hermes-agent/gateway/platforms/
├── qqbot/         ← 真实 QQBot 在这里
│   ├── adapter.py
│   └── constants.py
├── telegram/      (可能迁移到 plugins/)
├── discord/       (可能迁移到 plugins/)
├── feishu/        (可能迁移到 plugins/)
├── wecom/         (可能迁移到 plugins/)
└── webhook.py     (单文件, 不是目录)
```

### 套 2: `plugins/platforms/<name>/` (旧, plugin 形式)
```
~/.hermes/hermes-agent/plugins/platforms/
├── dingtalk/ discord/ email/ feishu/ google_chat/ homeassistant/
├── irc/ line/ matrix/ mattermost/ nfy/ photon/ raft/ simplex/
├── slack/ sms/ teams/ telegram/ wecom/ whatsapp/
└── ...
```

**判断哪个在用**:
```bash
# 看哪个目录有非空 adapter.py + 有 __init__.py
for p in telegram discord feishu wecom weixin; do
  echo "=== $p ==="
  wc -l ~/.hermes/hermes-agent/gateway/platforms/$p/adapter.py 2>/dev/null
  wc -l ~/.hermes/hermes-agent/plugins/platforms/$p/adapter.py 2>/dev/null
done
```

## 注入点（agent 怎么跟用户对话）

**核心**: 不管哪个 adapter 收消息，最终都通过 gateway → AIAgent →
system prompt 装配（`prompt_builder.py`）→ LLM 调用。

**System prompt 装配顺序** (大致):
1. 身份段 (SOUL.md)
2. 上下文段 (AGENTS.md / .hermes.md / .cursorrules)
3. 能力段 (tools 列表 + skills 索引)
4. 渠道 hint (platform-specific notes)
5. 历史对话

**Skills 索引是能力段的一部分** → 跨渠道自动同步。

## 跟"行为铁律"相关的注入点

| 位置 | 用途 | 改它会影响 |
|---|---|---|
| `~/.hermes/SOUL.md` | 全局身份/铁律 | 全部渠道 |
| `~/.hermes/profiles/default/skills/<name>/SKILL.md` | 全局 SOP | 全部渠道 |
| `~/.hermes/hermes-agent/hermes_cli/config.py` 2130-2229 行 | 各渠道配置 (含 `channel_prompts`) | 单渠道 |
| `~/.hermes/hermes-agent/gateway/platforms/<p>/adapter.py` | 单渠道装配 | 单渠道 |

**改适配器 adapter.py 是最后手段** — 通常不需要，因为 SOUL.md + skill 已经覆盖。

## `channel_prompts` 字段的真相

**字段定义** (config.py 2143+ 行):
```python
"channel_prompts": {},  # Per-channel ephemeral system prompts
```

**用法**: 某个 Telegram 频道或 Discord 频道附加特定行为规则。
**示例** (config.yaml 实际为空):
```yaml
telegram:
  channel_prompts: {}  # 当前全空, 未使用
```

**陷阱**: 别把"全局行为铁律"塞进 `channel_prompts` — 那是 per-channel 字段，
不会跨渠道同步。

## 真实使用流程（用户消息从收到到回复）

```
用户消息
  ↓
[Adapter] (qqbot/telegram/.../api_server/webhook)
  ↓ gateway 路由
[AIAgent] (hermes_cli/gateway.py)
  ↓ 装配 system prompt
[PromptBuilder] (agent/prompt_builder.py)
  - SOUL.md 注入
  - AGENTS.md / .hermes.md 注入
  - Skills 索引注入  ← 本 skill 在这里被索引
  ↓
[LLM] (provider/model)
  ↓ 工具调用 (computer_use / terminal / browser / ...)
[Tool] → 反馈给 LLM
  ↓
[Adapter] send_message (qqbot/telegram/...)
  ↓
用户收到回复
```

**关键**: 装配函数是**共享**的 → 改一处 = 全部渠道同步。

## 验证跨渠道同步

```bash
# 1. 看 skill 是否在 prompt 索引
grep "channel-universal-sop" ~/.hermes/.skills_prompt_snapshot.json

# 2. 看 SOUL.md 是否含 v3.1
grep "v3.1 跨渠道铁律" ~/.hermes/SOUL.md

# 3. 跑完整验证
bash ~/.hermes/scripts/check_v31_compliance.sh
```

## 改 adapter prompt 的最简验证 (不需要时跳过)

如果某个渠道真的需要改本地 prompt（比如富文本格式）：

```python
# ~/.hermes/hermes-agent/gateway/platforms/telegram/adapter.py
def _build_extra_prompt(self) -> str:
    """Telegram 特有: rich message 提示"""
    return (
        "Use Telegram MarkdownV2 syntax for formatting. "
        "Tables and code blocks render natively."
    )
```

**改完**: gateway 重启 + 跑 `bash ~/.hermes/scripts/check_v31_compliance.sh`
确认 v3.1 还在。

## 常见混淆

| 混淆点 | 真相 |
|---|---|
| 改一个 adapter 能不能影响所有渠道？ | ❌ 不能，per-adapter |
| 改 SOUL.md 能不能影响所有渠道？ | ✅ 能，全局注入 |
| 改 skill 能不能影响所有渠道？ | ✅ 能，prompt_builder 索引全部 skills |
| `channel_prompts` 是全局字段？ | ❌ per-channel/chat |
| 22 个 PLATFORMS 都连了吗？ | ❌ 大部分是 adapter 预留，gateway_state 看实际 |
| QQBot 走哪个目录？ | `gateway/platforms/qqbot/`，不是 `plugins/platforms/` |